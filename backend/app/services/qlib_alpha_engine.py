"""
Qlib Alpha Engine — Extracted from qlib's Alpha158 factor library.

Computes technical indicators as alpha factors:
- Price-based factors (ROC, MA, STD, etc.)
- Volume-based factors
- Cross-sectional factors (rank, zscore)
- Time-series factors (delta, ts_mean, ts_std)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class OHLCV:
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: float = 0.0


def ts_mean(values: List[float], window: int) -> float:
    """Rolling mean over window."""
    if len(values) < window:
        return sum(values) / max(len(values), 1)
    return sum(values[-window:]) / window


def ts_std(values: List[float], window: int) -> float:
    """Rolling standard deviation."""
    recent = values[-window:] if len(values) >= window else values
    if len(recent) < 2:
        return 0.0
    mean = sum(recent) / len(recent)
    var = sum((v - mean) ** 2 for v in recent) / (len(recent) - 1)
    return var ** 0.5


def ts_max(values: List[float], window: int) -> float:
    """Rolling max."""
    recent = values[-window:] if len(values) >= window else values
    return max(recent) if recent else 0.0


def ts_min(values: List[float], window: int) -> float:
    """Rolling min."""
    recent = values[-window:] if len(values) >= window else values
    return min(recent) if recent else 0.0


def ts_rank(values: List[float], window: int) -> float:
    """Rolling rank of last value within window."""
    recent = values[-window:] if len(values) >= window else values
    if not recent:
        return 0.0
    last = recent[-1]
    return sum(1 for v in recent if v <= last) / len(recent)


def ts_delta(values: List[float], period: int = 1) -> float:
    """Difference between current and period-ago value."""
    if len(values) <= period:
        return 0.0
    return values[-1] - values[-1 - period]


def ts_corr(x: List[float], y: List[float], window: int) -> float:
    """Rolling correlation between two series."""
    if len(x) < window or len(y) < window:
        return 0.0
    x_win = x[-window:]
    y_win = y[-window:]
    n = len(x_win)
    mx = sum(x_win) / n
    my = sum(y_win) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(x_win, y_win)) / n
    sx = sum((a - mx) ** 2 for a in x_win) / n
    sy = sum((b - my) ** 2 for b in y_win) / n
    denom = (sx * sy) ** 0.5
    return cov / denom if denom > 1e-10 else 0.0


class AlphaFactorEngine:
    """Compute Alpha158-style factors from OHLCV data."""

    def __init__(self, windows: Optional[List[int]] = None) -> None:
        self.windows = windows or [5, 10, 20, 60]

    def compute_factors(self, candles: List[OHLCV]) -> Dict[str, float]:
        """Compute all factors from a list of candles."""
        if not candles:
            return {}

        closes = [c.close for c in candles]
        opens = [c.open for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        volumes = [c.volume for c in candles]

        factors: Dict[str, float] = {}

        for w in self.windows:
            prefix = f"m{w}"
            factors[f"{prefix}ROC"] = ts_delta(closes, w) / closes[-1 - w] if len(closes) > w else 0.0
            factors[f"{prefix}MA"] = ts_mean(closes, w)
            factors[f"{prefix}STD"] = ts_std(closes, w)
            factors[f"{prefix}MAX"] = ts_max(highs, w)
            factors[f"{prefix}MIN"] = ts_min(lows, w)
            factors[f"{prefix}QTLU"] = ts_max(highs, w) - ts_mean(closes, w)
            factors[f"{prefix}QTLD"] = ts_mean(closes, w) - ts_min(lows, w)
            factors[f"{prefix}VMA"] = ts_mean(volumes, w)
            factors[f"{prefix}VSTD"] = ts_std(volumes, w)
            factors[f"{prefix}WVMA"] = ts_corr(closes, volumes, w)
            factors[f"{prefix}VSUM"] = sum(volumes[-w:]) if len(volumes) >= w else sum(volumes)
            factors[f"{prefix}RANK"] = ts_rank(closes, w)

        # Cross-sectional factors (relative to latest)
        if closes:
            factors["close_open"] = closes[-1] / opens[-1] if opens[-1] != 0 else 1.0
            factors["high_low"] = highs[-1] / lows[-1] if lows[-1] != 0 else 1.0
            factors["high_close"] = highs[-1] / closes[-1] if closes[-1] != 0 else 1.0
            factors["low_close"] = lows[-1] / closes[-1] if closes[-1] != 0 else 1.0
            factors["vwap"] = (highs[-1] + lows[-1] + closes[-1]) / 3.0

        # Time-series deltas
        for period in [1, 5, 10, 20]:
            factors[f"delta_{period}"] = ts_delta(closes, period)

        return factors

    def compute_correlation_factors(
        self,
        series_a: List[float],
        series_b: List[float],
    ) -> Dict[str, float]:
        """Compute correlation-based factors between two series."""
        return {f"corr_{w}": ts_corr(series_a, series_b, w) for w in self.windows}

    def detect_divergence(
        self,
        prices: List[float],
        indicator: List[float],
        window: int = 20,
    ) -> str:
        """Detect divergence between price and indicator."""
        if len(prices) < window or len(indicator) < window:
            return "neutral"

        price_trend = prices[-1] - prices[-window]
        ind_trend = indicator[-1] - indicator[-window]

        if price_trend > 0 and ind_trend < 0:
            return "bearish_divergence"
        elif price_trend < 0 and ind_trend > 0:
            return "bullish_divergence"
        return "neutral"
