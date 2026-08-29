"""
Health Trends Analytics — Advanced trend analysis and predictive modeling
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
import math


class HealthTrendsAnalytics:
    def __init__(self):
        self.metric_history: Dict[str, List[dict]] = {}
        self.insights: Dict[str, List[dict]] = {}

    def record_metric(self, user_id: str, metric_name: str, value: float, unit: str = "", source: str = "manual") -> dict:
        entry = {
            "id": str(uuid.uuid4()),
            "metric": metric_name,
            "value": value,
            "unit": unit,
            "source": source,
            "timestamp": datetime.now().isoformat(),
        }
        self.metric_history.setdefault(f"{user_id}_{metric_name}", []).append(entry)
        return entry

    def get_metric_trend(self, user_id: str, metric_name: str, days: int = 30) -> dict:
        key = f"{user_id}_{metric_name}"
        entries = self.metric_history.get(key, [])
        cutoff = datetime.now() - timedelta(days=days)
        recent = [e for e in entries if datetime.fromisoformat(e["timestamp"]) >= cutoff]

        if len(recent) < 2:
            return {"metric": metric_name, "status": "insufficient_data", "data_points": len(recent)}

        values = [e["value"] for e in recent]
        timestamps = [datetime.fromisoformat(e["timestamp"]) for e in recent]
        
        mean_val = sum(values) / len(values)
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)
        std_dev = math.sqrt(variance)
        
        time_diffs = [(timestamps[i] - timestamps[i-1]).total_seconds() / 3600 for i in range(1, len(timestamps))]
        avg_interval_hours = sum(time_diffs) / len(time_diffs) if time_diffs else 24
        
        recent_half = values[len(values)//2:]
        earlier_half = values[:len(values)//2]
        recent_avg = sum(recent_half) / len(recent_half)
        earlier_avg = sum(earlier_half) / len(earlier_half)
        
        change = recent_avg - earlier_avg
        pct_change = (change / abs(earlier_avg) * 100) if earlier_avg != 0 else 0
        
        direction = "increasing" if change > 0 else "decreasing" if change < 0 else "stable"
        volatility = "high" if std_dev / max(mean_val, 0.01) > 0.2 else "moderate" if std_dev / max(mean_val, 0.01) > 0.1 else "low"

        z_scores = [(v - mean_val) / max(std_dev, 0.001) for v in values]
        anomalies = [{"value": values[i], "z_score": round(z_scores[i], 2), "timestamp": recent[i]["timestamp"]} for i in range(len(values)) if abs(z_scores[i]) > 2]

        return {
            "metric": metric_name,
            "period_days": days,
            "data_points": len(recent),
            "current": values[-1],
            "mean": round(mean_val, 2),
            "std_dev": round(std_dev, 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "direction": direction,
            "change": round(change, 2),
            "percent_change": round(pct_change, 1),
            "volatility": volatility,
            "avg_logging_interval_hours": round(avg_interval_hours, 1),
            "anomalies": anomalies[:5],
            "recent_values": [{"value": v, "timestamp": recent[i]["timestamp"]} for i, v in enumerate(values[-5:])],
        }

    def get_correlation(self, user_id: str, metric1: str, metric2: str, days: int = 30) -> dict:
        key1 = f"{user_id}_{metric1}"
        key2 = f"{user_id}_{metric2}"
        entries1 = self.metric_history.get(key1, [])
        entries2 = self.metric_history.get(key2, [])
        cutoff = datetime.now() - timedelta(days=days)
        
        recent1 = {e["timestamp"][:13]: e["value"] for e in entries1 if datetime.fromisoformat(e["timestamp"]) >= cutoff}
        recent2 = {e["timestamp"][:13]: e["value"] for e in entries2 if datetime.fromisoformat(e["timestamp"]) >= cutoff}
        
        common = set(recent1.keys()) & set(recent2.keys())
        if len(common) < 3:
            return {"status": "insufficient_common_data", "common_points": len(common)}
        
        v1 = [recent1[k] for k in sorted(common)]
        v2 = [recent2[k] for k in sorted(common)]
        n = len(v1)
        m1, m2 = sum(v1)/n, sum(v2)/n
        num = sum((a-m1)*(b-m2) for a,b in zip(v1,v2))
        d1 = sum((a-m1)**2 for a in v1)**0.5
        d2 = sum((b-m2)**2 for b in v2)**0.5
        r = num/(d1*d2) if d1*d2 > 0 else 0
        
        strength = "strong" if abs(r) > 0.7 else "moderate" if abs(r) > 0.4 else "weak"
        direction = "positive" if r > 0 else "negative"
        
        return {"metric1": metric1, "metric2": metric2, "correlation": round(r, 3), "strength": strength, "direction": direction, "common_data_points": n}

    def generate_insights(self, user_id: str) -> List[dict]:
        insights = []
        metrics = set()
        for key in self.metric_history:
            if key.startswith(f"{user_id}_"):
                metrics.add(key.split("_", 1)[1])
        
        for metric in metrics:
            trend = self.get_metric_trend(user_id, metric, 30)
            if trend.get("status") != "insufficient_data":
                if trend["volatility"] == "high":
                    insights.append({"type": "volatility_alert", "metric": metric, "message": f"{metric} is showing high variability — consider more consistent tracking", "severity": "info"})
                if abs(trend["percent_change"]) > 20:
                    direction = "increased" if trend["direction"] == "increasing" else "decreased"
                    insights.append({"type": "significant_change", "metric": metric, "message": f"{metric} has {direction} by {abs(trend['percent_change'])}%", "severity": "warning"})
                if trend["anomalies"]:
                    insights.append({"type": "anomaly_detected", "metric": metric, "message": f"Unusual {metric} readings detected ({len(trend['anomalies'])} anomalies)", "severity": "attention"})
        
        self.insights[user_id] = insights
        return insights

    def get_dashboard_data(self, user_id: str, days: int = 30) -> dict:
        metrics = set()
        for key in self.metric_history:
            if key.startswith(f"{user_id}_"):
                metrics.add(key.split("_", 1)[1])
        
        trends = {}
        for metric in metrics:
            trends[metric] = self.get_metric_trend(user_id, metric, days)
        
        insights = self.generate_insights(user_id)
        
        return {"user_id": user_id, "period_days": days, "total_metrics": len(metrics), "trends": trends, "insights": insights, "generated_at": datetime.now().isoformat()}


health_trends = HealthTrendsAnalytics()
