"""
Health Savings Account (HSA/FSA) — Expense tracking, receipt management, eligible expenses
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
import hashlib


class HealthSavingsService:
    ACCOUNT_TYPES = {
        "hsa": {
            "name": "Health Savings Account (HSA)",
            "2024_limit_individual": 4150,
            "2024_limit_family": 8300,
            "2025_limit_individual": 4300,
            "2025_limit_family": 8550,
            "rollover": True,
            "employer_contribution": True,
            "investment_options": True,
        },
        "fsa": {
            "name": "Flexible Spending Account (FSA)",
            "2024_limit": 3200,
            "2025_limit": 3300,
            "rollover": False,
            "use_it_or_lose_it": True,
            "employer_contribution": False,
            "investment_options": False,
        },
        "limited_purpose_fsa": {
            "name": "Limited Purpose FSA",
            "2024_limit": 3200,
            "2025_limit": 3300,
            "eligible_only": ["dental", "vision"],
            "rollover": False,
        },
    }

    ELIGIBLE_EXPENSES = {
        "medical": ["doctor_visits", "hospital_stays", "surgery", "diagnostics", "lab_work", "urgent_care"],
        "dental": ["cleanings", "fillings", "crowns", "orthodontics", "oral_surgery"],
        "vision": ["eye_exams", "glasses", "contact_lens", "laser_eye_surgery"],
        "prescriptions": ["medications", "insulin", "medical_devices", "first_aid_supplies"],
        "mental_health": ["therapy", "counseling", "psychiatry", "substance_abuse_treatment"],
        "wellness": ["smoking_cessation", "weight_loss_programs", "acupuncture", "chiropractic"],
        "insurance": ["premiums", "deductibles", "copays", "coinsurance"],
    }

    EXPENSE_CATEGORIES = [
        "Doctor Visit", "Specialist Visit", "Emergency Room", "Hospital Stay",
        "Prescription Medication", "Over-the-Counter (w/ Rx)", "Dental - Preventive",
        "Dental - Major", "Vision - Exam", "Vision - Glasses/Contacts",
        "Lab Work", "Imaging (X-ray/MRI)", "Physical Therapy", "Mental Health",
        "Medical Equipment", "Durable Medical Equipment", "Copay", "Deductible",
        "Insurance Premium", "Acupuncture", "Chiropractic", "Massage Therapy",
        "Smoking Cessation", "Weight Loss Program",
    ]

    def __init__(self):
        self.accounts: Dict[str, dict] = {}
        self.transactions: Dict[str, List[dict]] = {}
        self.receipts: Dict[str, dict] = {}
        self.recurring: Dict[str, List[dict]] = {}

    def create_account(self, user_id: str, account_type: str, provider: str = "", plan_year: int = None) -> dict:
        config = self.ACCOUNT_TYPES.get(account_type)
        if not config:
            return {"error": f"Unknown account type: {account_type}"}
        
        year = plan_year or datetime.now().year
        if account_type == "hsa":
            limit = config.get(f"{year}_limit_individual", config["2024_limit_individual"])
        else:
            limit = config.get(f"{year}_limit", config.get("2024_limit", 3200))
        
        account = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": account_type,
            "type_name": config["name"],
            "provider": provider,
            "plan_year": year,
            "contribution_limit": limit,
            "balance": 0,
            "total_contributions": 0,
            "total_expenses": 0,
            "status": "active",
            "created_at": datetime.now().isoformat(),
        }
        self.accounts[user_id] = account
        self.transactions[user_id] = []
        return account

    def contribute(self, user_id: str, amount: float, source: str = "payroll", notes: str = "") -> dict:
        account = self.accounts.get(user_id)
        if not account:
            return {"error": "No account found"}
        
        new_total = account["total_contributions"] + amount
        if new_total > account["contribution_limit"]:
            return {"error": f"Would exceed contribution limit of ${account['contribution_limit']:,.2f}", "current_total": account["total_contributions"], "remaining": account["contribution_limit"] - account["total_contributions"]}
        
        account["total_contributions"] = new_total
        account["balance"] += amount
        
        transaction = {
            "id": str(uuid.uuid4()),
            "type": "contribution",
            "amount": amount,
            "source": source,
            "notes": notes,
            "balance_after": account["balance"],
            "timestamp": datetime.now().isoformat(),
        }
        self.transactions.setdefault(user_id, []).append(transaction)
        return transaction

    def expense(self, user_id: str, amount: float, category: str, description: str, provider_name: str = "", date: str = None, receipt_url: str = None) -> dict:
        account = self.accounts.get(user_id)
        if not account:
            return {"error": "No account found"}
        
        if amount > account["balance"]:
            return {"error": f"Insufficient balance. Available: ${account['balance']:,.2f}", "balance": account["balance"]}
        
        account["balance"] -= amount
        account["total_expenses"] += amount
        
        transaction = {
            "id": str(uuid.uuid4()),
            "type": "expense",
            "amount": amount,
            "category": category,
            "description": description,
            "provider_name": provider_name,
            "date": date or datetime.now().isoformat(),
            "receipt_url": receipt_url,
            "eligible": True,
            "tax_year": datetime.now().year,
            "balance_after": account["balance"],
            "timestamp": datetime.now().isoformat(),
        }
        self.transactions.setdefault(user_id, []).append(transaction)
        
        if receipt_url:
            self.receipts[transaction["id"]] = {
                "transaction_id": transaction["id"],
                "url": receipt_url,
                "uploaded_at": datetime.now().isoformat(),
            }
        
        return transaction

    def get_account_summary(self, user_id: str) -> dict:
        account = self.accounts.get(user_id)
        if not account:
            return {"error": "No account found"}
        
        transactions = self.transactions.get(user_id, [])
        year_transactions = [t for t in transactions if t.get("timestamp", "").startswith(str(datetime.now().year))]
        
        contributions = sum(t["amount"] for t in year_transactions if t["type"] == "contribution")
        expenses = sum(t["amount"] for t in year_transactions if t["type"] == "expense")
        
        category_breakdown = {}
        for t in year_transactions:
            if t["type"] == "expense":
                cat = t.get("category", "Other")
                category_breakdown[cat] = category_breakdown.get(cat, 0) + t["amount"]
        
        remaining = account["contribution_limit"] - contributions
        
        return {
            "account": account,
            "summary": {
                "contributions_this_year": round(contributions, 2),
                "expenses_this_year": round(expenses, 2),
                "current_balance": round(account["balance"], 2),
                "contribution_limit": account["contribution_limit"],
                "remaining_to_contribute": round(max(remaining, 0), 2),
                "utilization_rate": round(expenses / max(contributions, 1) * 100, 1),
            },
            "category_breakdown": dict(sorted(category_breakdown.items(), key=lambda x: x[1], reverse=True)),
            "recent_transactions": transactions[-10:],
        }

    def get_transaction_history(self, user_id: str, limit: int = 50, transaction_type: str = None) -> List[dict]:
        transactions = self.transactions.get(user_id, [])
        if transaction_type:
            transactions = [t for t in transactions if t["type"] == transaction_type]
        return transactions[-limit:]

    def check_eligibility(self, category: str) -> dict:
        for cat, items in self.ELIGIBLE_EXPENSES.items():
            if category.lower().replace(" ", "_") in items or cat == category.lower().replace(" ", "_"):
                return {"eligible": True, "category": cat, "description": category}
        return {"eligible": False, "category": category, "note": "Consult your plan documents for eligibility"}

    def get_eligible_categories(self) -> dict:
        return self.ELIGIBLE_EXPENSES

    def get_account_types(self) -> dict:
        return self.ACCOUNT_TYPES


health_savings = HealthSavingsService()
