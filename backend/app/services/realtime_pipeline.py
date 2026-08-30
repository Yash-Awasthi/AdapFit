"""
Real-Time Health Data Pipeline — WebSocket-based streaming with sliding windows.

Provides real-time data ingestion, sliding window aggregations, anomaly detection,
circular buffers, and auto-downsampling for health sensor streams.
All pure functions for processing — WebSocket transport is pluggable.
"""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Enums and data structures
# ---------------------------------------------------------------------------

class StreamType(str, Enum):
    HEART_RATE = "heart_rate"
    SPO2 = "spo2"
    STEPS = "steps"
    TEMPERATURE = "temperature"
    HRV = "hrv"
    BLOOD_PRESSURE = "blood_pressure"
    SLEEP = "sleep"
    STRESS = "stress"
    CALORIES = "calories"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class DataQuality(str, Enum):
    GOOD = "good"
    DEGRADED = "degraded"
    POOR = "poor"


@dataclass
class DataPoint:
    """Single timestamped data point."""
    stream_type: StreamType
    value: float
    timestamp: float  # Unix timestamp
    source: str = "unknown"
    quality: DataQuality = DataQuality.GOOD
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WindowAggregate:
    """Aggregated data over a time window."""
    stream_type: StreamType
    window_seconds: int
    count: int
    mean: float
    min: float
    max: float
    std: float
    latest: float
    start_time: float
    end_time: float


@dataclass
class StreamAlert:
    """Real-time alert from stream monitoring."""
    stream_type: StreamType
    severity: AlertSeverity
    message: str
    value: float
    threshold: float
    timestamp: float
    acknowledged: bool = False


@dataclass
class StreamStatus:
    """Current status of a data stream."""
    stream_type: StreamType
    is_active: bool
    points_received: int
    points_per_second: float
    buffer_size: int
    buffer_capacity: int
    quality: DataQuality
    last_point_time: float
    alerts_count: int


@dataclass
class PipelineConfig:
    """Configuration for the data pipeline."""
    buffer_capacity: int = 86400  # 24hr at 1/sec
    window_sizes: List[int] = field(default_factory=lambda: [300, 900, 3600])  # 5min, 15min, 1hr
    anomaly_zscore_threshold: float = 3.0
    downsampling_threshold_1m: int = 3600  # After 1hr
    downsampling_threshold_5m: int = 86400  # After 24hr
    max_points_per_second: int = 1000
    alert_cooldown_seconds: int = 60


# ---------------------------------------------------------------------------
# Circular buffer
# ---------------------------------------------------------------------------

class CircularBuffer:
    """Fixed-size circular buffer for streaming data."""

    def __init__(self, capacity: int):
        self.capacity = capacity
        self._buffer: deque = deque(maxlen=capacity)
        self._total_added = 0

    def add(self, item: Any) -> None:
        self._buffer.append(item)
        self._total_added += 1

    def get_recent(self, n: int) -> List[Any]:
        return list(self._buffer)[-n:]

    def get_all(self) -> List[Any]:
        return list(self._buffer)

    def get_since(self, timestamp: float) -> List[Any]:
        return [p for p in self._buffer if hasattr(p, 'timestamp') and p.timestamp >= timestamp]

    @property
    def size(self) -> int:
        return len(self._buffer)

    @property
    def total_added(self) -> int:
        return self._total_added


# ---------------------------------------------------------------------------
# Sliding window aggregation
# ---------------------------------------------------------------------------

def aggregate_window(
    points: List[DataPoint],
    window_seconds: int,
    current_time: float,
) -> Optional[WindowAggregate]:
    """
    Compute aggregate statistics over a sliding window.
    
    Returns None if insufficient data in the window.
    """
    cutoff = current_time - window_seconds
    window_points = [p for p in points if p.timestamp >= cutoff]
    
    if not window_points:
        return None
    
    values = [p.value for p in window_points]
    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / max(1, n - 1)
    std = math.sqrt(variance)
    
    return WindowAggregate(
        stream_type=window_points[0].stream_type,
        window_seconds=window_seconds,
        count=n,
        mean=round(mean, 4),
        min=round(min(values), 4),
        max=round(max(values), 4),
        std=round(std, 4),
        latest=round(values[-1], 4),
        start_time=window_points[0].timestamp,
        end_time=window_points[-1].timestamp,
    )


def compute_moving_average(
    points: List[DataPoint],
    window_seconds: int,
    current_time: float,
) -> float:
    """Compute moving average over a time window."""
    agg = aggregate_window(points, window_seconds, current_time)
    return agg.mean if agg else 0.0


def compute_ema(
    points: List[DataPoint],
    alpha: float = 0.1,
) -> float:
    """Compute exponential moving average over a point series."""
    if not points:
        return 0.0
    
    ema = points[0].value
    for p in points[1:]:
        ema = alpha * p.value + (1 - alpha) * ema
    return ema


# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------

def detect_anomaly(
    point: DataPoint,
    recent_points: List[DataPoint],
    zscore_threshold: float = 3.0,
) -> bool:
    """
    Detect if a new data point is an anomaly using Z-score method.
    
    A point is anomalous if it's more than zscore_threshold standard
    deviations from the recent mean.
    """
    if len(recent_points) < 10:
        return False
    
    values = [p.value for p in recent_points]
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std = math.sqrt(variance)
    
    if std == 0:
        return False
    
    zscore = abs(point.value - mean) / std
    return zscore > zscore_threshold


def detect_trend(
    points: List[DataPoint],
    window_seconds: int,
    current_time: float,
) -> Tuple[str, float]:
    """
    Detect trend direction and strength in a stream.
    
    Returns (direction, strength) where direction is "up", "down", "stable"
    and strength is 0-1.
    """
    agg = aggregate_window(points, window_seconds, current_time)
    if not agg or agg.count < 5:
        return ("stable", 0.0)
    
    # Simple linear regression on window
    recent = [p for p in points if p.timestamp >= current_time - window_seconds]
    n = len(recent)
    x_mean = sum(p.timestamp for p in recent) / n
    y_mean = agg.mean
    
    num = sum((p.timestamp - x_mean) * (p.value - y_mean) for p in recent)
    den = sum((p.timestamp - x_mean) ** 2 for p in recent)
    
    slope = num / den if den != 0 else 0
    
    # Normalize slope to 0-1 strength
    if agg.mean != 0:
        relative_slope = abs(slope) / abs(agg.mean) * window_seconds
        strength = min(1.0, relative_slope)
    else:
        strength = 0.0
    
    if slope > 0.001:
        direction = "up"
    elif slope < -0.001:
        direction = "down"
    else:
        direction = "stable"
    
    return (direction, round(strength, 3))


# ---------------------------------------------------------------------------
# Downsampling
# ---------------------------------------------------------------------------

def downsample(
    points: List[DataPoint],
    target_interval: float,  # seconds between points
) -> List[DataPoint]:
    """
    Downsample a series by averaging points within each interval bucket.
    
    Used for data retention: 1s → 1min after 1hr, 1min → 5min after 24hr.
    """
    if not points or target_interval <= 0:
        return points
    
    buckets: Dict[int, List[DataPoint]] = {}
    
    for p in points:
        bucket_key = int(p.timestamp / target_interval)
        if bucket_key not in buckets:
            buckets[bucket_key] = []
        buckets[bucket_key].append(p)
    
    result = []
    for bucket_key in sorted(buckets.keys()):
        bucket = buckets[bucket_key]
        avg_value = sum(p.value for p in bucket) / len(bucket)
        result.append(DataPoint(
            stream_type=bucket[0].stream_type,
            value=round(avg_value, 4),
            timestamp=bucket[-1].timestamp,  # Use latest timestamp
            source=bucket[0].source,
            quality=bucket[0].quality,
        ))
    
    return result


def auto_downsample(
    points: List[DataPoint],
    current_time: float,
    config: Optional[PipelineConfig] = None,
) -> List[DataPoint]:
    """
    Auto-downsample based on data age.
    
    - Last 1hr: keep at original resolution
    - 1hr to 24hr: downsample to 1-minute intervals
    - Older than 24hr: downsample to 5-minute intervals
    """
    if config is None:
        config = PipelineConfig()
    
    cutoff_1m = current_time - config.downsampling_threshold_1m
    cutoff_5m = current_time - config.downsampling_threshold_5m
    
    recent = [p for p in points if p.timestamp >= cutoff_1m]
    mid = [p for p in points if cutoff_5m <= p.timestamp < cutoff_1m]
    old = [p for p in points if p.timestamp < cutoff_5m]
    
    result = recent
    result.extend(downsample(mid, 60))  # 1-minute intervals
    result.extend(downsample(old, 300))  # 5-minute intervals
    
    return sorted(result, key=lambda p: p.timestamp)


# ---------------------------------------------------------------------------
# Alert system
# ---------------------------------------------------------------------------

class AlertManager:
    """Manages real-time alerts with cooldown."""

    def __init__(self, cooldown_seconds: int = 60):
        self.cooldown_seconds = cooldown_seconds
        self._last_alerts: Dict[str, float] = {}
        self._active_alerts: List[StreamAlert] = []

    def check_threshold(
        self,
        stream_type: StreamType,
        value: float,
        warning_threshold: float,
        critical_threshold: float,
        timestamp: float,
    ) -> Optional[StreamAlert]:
        """Check if value crosses alert thresholds."""
        key = f"{stream_type.value}"
        last_time = self._last_alerts.get(key, 0)
        
        if timestamp - last_time < self.cooldown_seconds:
            return None
        
        if abs(value) >= abs(critical_threshold):
            alert = StreamAlert(
                stream_type=stream_type,
                severity=AlertSeverity.CRITICAL,
                message=f"{stream_type.value} critically high: {value}",
                value=value,
                threshold=critical_threshold,
                timestamp=timestamp,
            )
            self._last_alerts[key] = timestamp
            self._active_alerts.append(alert)
            return alert
        
        if abs(value) >= abs(warning_threshold):
            alert = StreamAlert(
                stream_type=stream_type,
                severity=AlertSeverity.WARNING,
                message=f"{stream_type.value} above normal: {value}",
                value=value,
                threshold=warning_threshold,
                timestamp=timestamp,
            )
            self._last_alerts[key] = timestamp
            self._active_alerts.append(alert)
            return alert
        
        return None

    def get_active_alerts(self) -> List[StreamAlert]:
        return [a for a in self._active_alerts if not a.acknowledged]

    def acknowledge(self, alert_index: int) -> bool:
        if 0 <= alert_index < len(self._active_alerts):
            self._active_alerts[alert_index].acknowledged = True
            return True
        return False


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class HealthDataPipeline:
    """
    Real-time health data pipeline with sliding windows and anomaly detection.
    
    Usage:
        pipeline = HealthDataPipeline()
        pipeline.ingest(DataPoint(StreamType.HEART_RATE, 72, time.time()))
        aggregates = pipeline.get_aggregates(StreamType.HEART_RATE)
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self._buffers: Dict[StreamType, CircularBuffer] = {}
        self._alert_manager = AlertManager(self.config.alert_cooldown_seconds)
        self._alert_rules: Dict[StreamType, Tuple[float, float]] = {}
        self._points_received = 0
        self._start_time = time.time()

    def ingest(self, point: DataPoint) -> Optional[StreamAlert]:
        """
        Ingest a data point into the pipeline.
        
        Returns an alert if thresholds are crossed, None otherwise.
        """
        self._points_received += 1
        
        # Get or create buffer for this stream type
        if point.stream_type not in self._buffers:
            self._buffers[point.stream_type] = CircularBuffer(self.config.buffer_capacity)
        
        buffer = self._buffers[point.stream_type]
        buffer.add(point)
        
        # Check anomaly
        recent = buffer.get_recent(100)
        is_anomaly = detect_anomaly(point, recent, self.config.anomaly_zscore_threshold)
        if is_anomaly:
            point.metadata["anomaly"] = True
        
        # Check alert thresholds
        alert = None
        if point.stream_type in self._alert_rules:
            warning, critical = self._alert_rules[point.stream_type]
            alert = self._alert_manager.check_threshold(
                point.stream_type, point.value, warning, critical, point.timestamp,
            )
        
        return alert

    def set_alert_rule(
        self,
        stream_type: StreamType,
        warning_threshold: float,
        critical_threshold: float,
    ) -> None:
        """Configure alert thresholds for a stream type."""
        self._alert_rules[stream_type] = (warning_threshold, critical_threshold)

    def get_aggregates(
        self,
        stream_type: StreamType,
        current_time: Optional[float] = None,
    ) -> Dict[int, WindowAggregate]:
        """Get aggregates for all configured window sizes."""
        if current_time is None:
            current_time = time.time()
        
        buffer = self._buffers.get(stream_type)
        if not buffer:
            return {}
        
        points = buffer.get_all()
        return {
            ws: agg
            for ws in self.config.window_sizes
            if (agg := aggregate_window(points, ws, current_time)) is not None
        }

    def get_history(
        self,
        stream_type: StreamType,
        minutes: int = 5,
    ) -> List[DataPoint]:
        """Get recent history for a stream type."""
        buffer = self._buffers.get(stream_type)
        if not buffer:
            return []
        
        cutoff = time.time() - minutes * 60
        return buffer.get_since(cutoff)

    def get_status(self, stream_type: StreamType) -> StreamStatus:
        """Get current status of a stream."""
        buffer = self._buffers.get(stream_type)
        if not buffer:
            return StreamStatus(
                stream_type=stream_type, is_active=False,
                points_received=0, points_per_second=0,
                buffer_size=0, buffer_capacity=self.config.buffer_capacity,
                quality=DataQuality.POOR, last_point_time=0, alerts_count=0,
            )
        
        elapsed = time.time() - self._start_time
        pps = buffer.total_added / elapsed if elapsed > 0 else 0
        
        return StreamStatus(
            stream_type=stream_type,
            is_active=buffer.size > 0,
            points_received=buffer.total_added,
            points_per_second=round(pps, 2),
            buffer_size=buffer.size,
            buffer_capacity=self.config.buffer_capacity,
            quality=DataQuality.GOOD if pps > 0 else DataQuality.POOR,
            last_point_time=buffer.get_all()[-1].timestamp if buffer.size > 0 else 0,
            alerts_count=len(self._alert_manager.get_active_alerts()),
        )

    def get_all_status(self) -> List[StreamStatus]:
        """Get status of all active streams."""
        return [self.get_status(st) for st in self._buffers]

    def downsample_old_data(self) -> Dict[str, int]:
        """Trigger auto-downsampling on all buffers. Returns counts per stream."""
        current_time = time.time()
        results = {}
        
        for stream_type, buffer in self._buffers.items():
            original_size = buffer.size
            points = buffer.get_all()
            downsampled = auto_downsample(points, current_time, self.config)
            
            # Rebuild buffer
            new_buffer = CircularBuffer(self.config.buffer_capacity)
            for p in downsampled:
                new_buffer.add(p)
            self._buffers[stream_type] = new_buffer
            
            results[stream_type.value] = original_size - new_buffer.size
        
        return results
