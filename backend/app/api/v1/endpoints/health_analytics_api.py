"""Health Analytics API"""
from fastapi import APIRouter
from app.services.health_analytics import health_analytics_service

router = APIRouter()

@router.get("/weekly")
async def get_weekly_summary():
    """Get comprehensive weekly health summary."""
    return health_analytics_service.get_weekly_summary()

@router.get("/monthly")
async def get_monthly_report():
    """Get monthly health report."""
    return health_analytics_service.get_monthly_report()

@router.get("/dashboard")
async def get_dashboard():
    """Get unified health dashboard with all key metrics."""
    return health_analytics_service.get_health_dashboard()

@router.get("/correlation")
async def get_correlation(metric_a: str, metric_b: str):
    """Analyze correlation between two metrics."""
    return health_analytics_service.get_metric_correlation(metric_a, metric_b)

@router.get("/anomalies")
async def get_anomalies():
    """Detect anomalies across health metrics."""
    return {"anomalies": health_analytics_service.get_anomaly_detection()}
