"""Analytics Dashboard API — Trends, correlations, insights"""
from fastapi import APIRouter
from typing import Optional
from app.services.analytics_dashboard import analytics_dashboard_service

router = APIRouter()


@router.get("/summary")
async def get_dashboard_summary(period: str = "30d"):
    return analytics_dashboard_service.get_dashboard_summary(period)


@router.get("/trend/{metric}")
async def get_trend(metric: str, period: str = "30d"):
    return analytics_dashboard_service.get_trend_data(metric, period)


@router.get("/correlations")
async def get_correlations():
    return analytics_dashboard_service.get_correlation_matrix()


@router.get("/usage")
async def get_feature_usage():
    return analytics_dashboard_service.get_feature_usage()


@router.get("/compare")
async def compare_periods(metric: str, period1: str = "7d", period2: str = "7d"):
    return analytics_dashboard_service.get_comparative_report(metric, period1, period2)


@router.get("/insights")
async def get_insights():
    return {"insights": analytics_dashboard_service.get_predictive_insights()}


@router.get("/report")
async def get_health_report(period: str = "30d"):
    return analytics_dashboard_service.get_health_report(period)
