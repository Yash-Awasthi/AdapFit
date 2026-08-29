"""
Health Savings Account (HSA/FSA) API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/health-savings", tags=["Health Savings Account"])


class CreateAccountRequest(BaseModel):
    user_id: str
    account_type: str
    provider: str = ""
    plan_year: Optional[int] = None


class ContributeRequest(BaseModel):
    user_id: str
    amount: float
    source: str = "payroll"
    notes: str = ""


class ExpenseRequest(BaseModel):
    user_id: str
    amount: float
    category: str
    description: str
    provider_name: str = ""
    date: Optional[str] = None
    receipt_url: Optional[str] = None


@router.post("/account/create")
async def create_account(req: CreateAccountRequest):
    from app.services.health_savings import health_savings
    return health_savings.create_account(req.user_id, req.account_type, req.provider, req.plan_year)


@router.post("/contribute")
async def contribute(req: ContributeRequest):
    from app.services.health_savings import health_savings
    return health_savings.contribute(req.user_id, req.amount, req.source, req.notes)


@router.post("/expense")
async def record_expense(req: ExpenseRequest):
    from app.services.health_savings import health_savings
    return health_savings.expense(req.user_id, req.amount, req.category, req.description, req.provider_name, req.date, req.receipt_url)


@router.get("/summary/{user_id}")
async def get_summary(user_id: str):
    from app.services.health_savings import health_savings
    return health_savings.get_account_summary(user_id)


@router.get("/transactions/{user_id}")
async def get_transactions(user_id: str, limit: int = 50, type: Optional[str] = None):
    from app.services.health_savings import health_savings
    return health_savings.get_transaction_history(user_id, limit, type)


@router.get("/eligibility/{category}")
async def check_eligibility(category: str):
    from app.services.health_savings import health_savings
    return health_savings.check_eligibility(category)


@router.get("/categories")
async def get_categories():
    from app.services.health_savings import health_savings
    return health_savings.get_eligible_categories()


@router.get("/account-types")
async def get_account_types():
    from app.services.health_savings import health_savings
    return health_savings.get_account_types()
