"""
Advanced Analytics Dashboard — Trends, Correlations, Predictive Insights

Features:
- Health score trends (daily, weekly, monthly, yearly)
- Feature usage statistics
- Correlation matrices between health metrics
- Predictive insights (trend forecasting)
- Comparative reports (week-over-week, month-over-month)
- Personalized health reports with charts data
"""
import time
import math
from typing import Optional
from dataclasses import dataclass, field


class AnalyticsDashboardService:
    """Comprehensive health analytics and reporting."""

    def __init__(self):
        self._health_scores: list[dict] = []
        self._feature_usage: dict[str, int] = {}
        self._metric_history: dict[str, list[dict]] = {}
        self._init_sample_data()

    def _init_sample_data(self):
        """Generate sample data for demo."""
        now = time.time()
        for i in range(30):
            day_offset = i * 86400
            ts = now - day_offset
            self._health_scores.append({
                "date": time.strftime("%Y-%m-%d", time.localtime(ts)),
                "score": max(30, min(100, 70 + int(math.sin(i * 0.3) * 15) + (i % 7 == 0 and -10 or 0))),
                "sleep": max(40, min(100, 75 + int(math.sin(i * 0.4) * 12))),
                "activity": max(20, min(100, 65 + int(math.cos(i * 0.5) * 20))),
                "nutrition": max(40, min(100, 70 + int(math.sin(i * 0.35) * 10))),
                "mental": max(50, min(100, 80 + int(math.cos(i * 0.25) * 8))),
            })
        self._metric_history = {
            "heart_rate": [{"date": time.strftime("%Y-%m-%d", time.localtime(now - i * 86400)), "value": 65 + int(math.sin(i * 0.3) * 8)} for i in range(30)],
            "weight": [{"date": time.strftime("%Y-%m-%d", time.localtime(now - i * 86400)), "value": 75.5 - i * 0.1} for i in range(30)],
            "sleep_hours": [{"date": time.strftime("%Y-%m-%d", time.localtime(now - i * 86400)), "value": 7 + math.sin(i * 0.4) * 1.5} for i in range(30)],
            "steps": [{"date": time.strftime("%Y-%m-%d", time.localtime(now - i * 86400)), "value": 8000 + int(math.sin(i * 0.5) * 3000)} for i in range(30)],
            "stress": [{"date": time.strftime("%Y-%m-%d", time.localtime(now - i * 86400)), "value": max(10, min(90, 40 + int(math.sin(i * 0.3) * 25)))} for i in range(30)],
        }
        self._feature_usage = {
            "workouts": 156, "meals_logged": 234, "sleep_sessions": 28,
            "mood_entries": 45, "bpm_measurements": 89, "stress_assessments": 34,
            "water_logged": 120, "medication_taken": 60, "content_viewed": 78,
            "community_posts": 12, "ai_coach_queries": 23,
        }

    def get_dashboard_summary(self, period: str = "30d") -> dict:
        days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}.get(period, 30)
        scores = self._health_scores[:days]
        if not scores:
            return {"error": "No data"}
        avg_score = sum(s["score"] for s in scores) / len(scores)
        avg_sleep = sum(s["sleep"] for s in scores) / len(scores)
        avg_activity = sum(s["activity"] for s in scores) / len(scores)
        avg_nutrition = sum(s["nutrition"] for s in scores) / len(scores)
        avg_mental = sum(s["mental"] for s in scores) / len(scores)
        trend = "improving" if scores[0]["score"] > scores[-1]["score"] else "declining"
        return {
            "period": period,
            "health_score": {"current": round(avg_score), "trend": trend, "change": round(scores[0]["score"] - scores[-1]["score"])},
            "breakdown": {"sleep": round(avg_sleep), "activity": round(avg_activity), "nutrition": round(avg_nutrition), "mental": round(avg_mental)},
            "total_records": sum(self._feature_usage.values()),
            "top_features": sorted(self._feature_usage.items(), key=lambda x: x[1], reverse=True)[:5],
        }

    def get_trend_data(self, metric: str, period: str = "30d") -> dict:
        days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)
        data = self._metric_history.get(metric, [])[:days]
        if not data:
            return {"error": f"No data for metric: {metric}"}
        values = [d["value"] for d in data]
        avg = sum(values) / len(values)
        std = (sum((v - avg) ** 2 for v in values) / len(values)) ** 0.5
        # Simple linear trend
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = avg
        slope = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values)) / max(1, sum((i - x_mean) ** 2 for i in range(n)))
        return {
            "metric": metric, "period": period,
            "data": data,
            "stats": {"min": round(min(values), 2), "max": round(max(values), 2), "avg": round(avg, 2), "std": round(std, 2)},
            "trend": {"direction": "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable", "slope": round(slope, 4)},
        }

    def get_correlation_matrix(self) -> dict:
        """Calculate correlations between metrics."""
        metrics = list(self._metric_history.keys())
        matrix = {}
        for m1 in metrics:
            matrix[m1] = {}
            v1 = [d["value"] for d in self._metric_history[m1]]
            for m2 in metrics:
                v2 = [d["value"] for d in self._metric_history[m2]]
                n = min(len(v1), len(v2))
                if n < 2:
                    matrix[m1][m2] = 0
                    continue
                x = v1[:n]
                y = v2[:n]
                x_mean = sum(x) / n
                y_mean = sum(y) / n
                cov = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y)) / n
                x_std = (sum((xi - x_mean) ** 2 for xi in x) / n) ** 0.5
                y_std = (sum((yi - y_mean) ** 2 for yi in y) / n) ** 0.5
                corr = cov / max(0.001, x_std * y_std)
                matrix[m1][m2] = round(corr, 3)
        return {"metrics": metrics, "correlations": matrix}

    def get_feature_usage(self) -> dict:
        total = sum(self._feature_usage.values())
        return {"total_interactions": total, "features": [{"name": k, "count": v, "percentage": round(v / max(1, total) * 100, 1)} for k, v in sorted(self._feature_usage.items(), key=lambda x: x[1], reverse=True)]}

    def get_comparative_report(self, metric: str, period1: str = "7d", period2: str = "7d") -> dict:
        d1 = {"7d": 7, "30d": 30}.get(period1, 7)
        d2 = {"7d": 7, "30d": 30}.get(period2, 7)
        data = self._metric_history.get(metric, [])
        v1 = [d["value"] for d in data[:d1]]
        v2 = [d["value"] for d in data[d1:d1 + d2]]
        avg1 = sum(v1) / max(1, len(v1))
        avg2 = sum(v2) / max(1, len(v2))
        change = ((avg1 - avg2) / max(0.001, avg2)) * 100
        return {"metric": metric, "period1": {"label": period1, "avg": round(avg1, 2), "count": len(v1)}, "period2": {"label": period2, "avg": round(avg2, 2), "count": len(v2)}, "change_percent": round(change, 1), "direction": "improvement" if change > 0 else "decline"}

    def get_predictive_insights(self) -> list[dict]:
        insights = []
        hr_data = self._metric_history.get("heart_rate", [])
        if len(hr_data) >= 7:
            recent = [d["value"] for d in hr_data[:7]]
            avg = sum(recent) / len(recent)
            if avg > 80:
                insights.append({"type": "warning", "metric": "heart_rate", "message": f"Average heart rate ({avg:.0f} bpm) is elevated. Consider stress management."})
            elif avg < 55:
                insights.append({"type": "info", "metric": "heart_rate", "message": f"Excellent resting heart rate ({avg:.0f} bpm). Great cardiovascular fitness!"})
        sleep_data = self._metric_history.get("sleep_hours", [])
        if len(sleep_data) >= 7:
            avg_sleep = sum(d["value"] for d in sleep_data[:7]) / 7
            if avg_sleep < 7:
                insights.append({"type": "warning", "metric": "sleep", "message": f"Average sleep ({avg_sleep:.1f}h) is below recommended 7-9 hours."})
            elif avg_sleep >= 8:
                insights.append({"type": "positive", "metric": "sleep", "message": f"Great sleep average ({avg_sleep:.1f}h). Keep it up!"})
        steps_data = self._metric_history.get("steps", [])
        if len(steps_data) >= 7:
            avg_steps = sum(d["value"] for d in steps_data[:7]) / 7
            if avg_steps < 5000:
                insights.append({"type": "warning", "metric": "activity", "message": f"Average steps ({avg_steps:.0f}) is below 5,000. Try to walk more."})
            elif avg_steps >= 10000:
                insights.append({"type": "positive", "metric": "activity", "message": f"Excellent activity level ({avg_steps:.0f} steps/day)!"})
        weight_data = self._metric_history.get("weight", [])
        if len(weight_data) >= 14:
            recent_avg = sum(d["value"] for d in weight_data[:7]) / 7
            older_avg = sum(d["value"] for d in weight_data[7:14]) / 7
            diff = recent_avg - older_avg
            if diff < -0.5:
                insights.append({"type": "positive", "metric": "weight", "message": f"Great progress! You've lost {abs(diff):.1f} kg this week."})
            elif diff > 0.5:
                insights.append({"type": "info", "metric": "weight", "message": f"Weight increased by {diff:.1f} kg. Monitor your nutrition."})
        if not insights:
            insights.append({"type": "info", "metric": "general", "message": "Keep logging your health data for personalized insights!"})
        return insights

    def get_health_report(self, period: str = "30d") -> dict:
        dashboard = self.get_dashboard_summary(period)
        correlations = self.get_correlation_matrix()
        insights = self.get_predictive_insights()
        usage = self.get_feature_usage()
        return {"report_title": f"Health Report ({period})", "generated_at": time.strftime("%Y-%m-%d %H:%M"), "dashboard": dashboard, "correlations": correlations, "insights": insights, "feature_usage": usage}


analytics_dashboard_service = AnalyticsDashboardService()
