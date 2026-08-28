"""
AdapFit Apache Spark (PySpark) Batch Analytics Processor
Nightly baselines, weekly trends, monthly analytics.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import math

try:
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F
    _HAS_SPARK = True
except ImportError:
    _HAS_SPARK = False


class SparkAnalytics:
    """
    Batch analytics using Apache Spark for large-scale data processing.
    Falls back to pure Python when PySpark unavailable.
    """
    
    def __init__(self):
        self.spark = None
        if _HAS_SPARK:
            try:
                self.spark = SparkSession.builder \
                    .master("local[*]") \
                    .appName("AdapFit Analytics") \
                    .config("spark.ui.enabled", "false") \
                    .config("spark.sql.shuffle.partitions", "2") \
                    .getOrCreate()
            except Exception:
                self.spark = None
    
    def compute_rolling_baselines(self, recovery_logs: List[Dict]) -> Dict[str, float]:
        """Compute 28-day rolling baselines for a user."""
        if not recovery_logs:
            return {
                "hrv_mean_rmssd": 50.0,
                "hrv_std_rmssd": 10.0,
                "rhr_baseline": 65.0,
                "sleep_target_hours": 8.0,
                "avg_recovery_score": 70.0,
            }
        
        hrvs = [r.get("hrv_rmssd", 50.0) for r in recovery_logs[-28:] if r.get("hrv_rmssd")]
        rhrs = [r.get("resting_heart_rate", 65) for r in recovery_logs[-28:] if r.get("resting_heart_rate")]
        sleeps = [r.get("sleep_duration_hours", 7.5) for r in recovery_logs[-28:] if r.get("sleep_duration_hours")]
        scores = [r.get("recovery_score", 70) for r in recovery_logs[-28:]]
        
        if self.spark:
            return self._compute_with_spark(hrvs, rhrs, sleeps, scores)
        
        return self._compute_pure_python(hrvs, rhrs, sleeps, scores)
    
    def _compute_pure_python(self, hrvs, rhrs, sleeps, scores):
        def mean(lst): return sum(lst) / len(lst) if lst else 50.0
        def std(lst):
            if len(lst) < 2: return 10.0
            m = mean(lst)
            return math.sqrt(sum((x - m) ** 2 for x in lst) / len(lst))
        
        return {
            "hrv_mean_rmssd": round(mean(hrvs), 1),
            "hrv_std_rmssd": round(std(hrvs), 1) if std(hrvs) > 0.1 else 10.0,
            "rhr_baseline": round(mean(rhrs), 1),
            "sleep_target_hours": round(mean(sleeps), 1) if sleeps else 8.0,
            "avg_recovery_score": round(mean(scores), 1),
        }
    
    def _compute_with_spark(self, hrvs, rhrs, sleeps, scores):
        try:
            hrv_df = self.spark.createDataFrame([(v,) for v in hrvs], ["value"])
            result = hrv_df.select(
                F.mean("value").alias("hrv_mean"),
                F.stddev("value").alias("hrv_std"),
            ).collect()[0]
            
            rhr_df = self.spark.createDataFrame([(v,) for v in rhrs], ["value"])
            rhr_mean = rhr_df.select(F.mean("value")).collect()[0][0] or 65.0
            
            return {
                "hrv_mean_rmssd": round(float(result["hrv_mean"] or 50.0), 1),
                "hrv_std_rmssd": round(float(result["hrv_std"] or 10.0), 1),
                "rhr_baseline": round(float(rhr_mean), 1),
                "sleep_target_hours": round(sum(sleeps) / len(sleeps), 1) if sleeps else 8.0,
                "avg_recovery_score": round(sum(scores) / len(scores), 1) if scores else 70.0,
            }
        except Exception:
            return self._compute_pure_python(hrvs, rhrs, sleeps, scores)
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "pyspark_available": _HAS_SPARK,
            "spark_session_active": self.spark is not None,
        }


spark_analytics = SparkAnalytics()
