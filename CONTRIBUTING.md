# Contributing to ZFIT

AdapFit — AI-Powered Fitness That Adapts To You.

## Quick Start

```bash
# Clone and setup
git clone https://github.com/Yash-Awasthi/ZFIT.git
cd ZFIT/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Start dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.10+ |
| Framework | FastAPI | 0.100+ |
| Database | PostgreSQL | 15+ |
| ORM | SQLAlchemy | 2.0+ |
| Migrations | Alembic | 1.10+ |
| Testing | pytest | 7.0+ |
| Linting | ruff | 0.1.0+ |
| Type Checking | mypy | 1.0+ |

## Project Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/   # FastAPI route handlers
│   ├── core/               # Config, security, database
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   └── services/           # Business logic (pure functions)
├── tests/
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
└── alembic/                # Database migrations
```

## Development Guidelines

### Service Development

ZFIT services are **pure functions** — no database, no async, just math.

```python
# Good: Pure function
def calculate_hrv_score(rmssd_values: list[float]) -> float:
    """Calculate HRV score from RMSSD values."""
    if not rmssd_values:
        return 0.0
    mean_rmssd = sum(rmssd_values) / len(rmssd_values)
    return min(100.0, mean_rmssd * 2)

# Bad: Service with side effects
async def get_hrv_score(db: Session, user_id: int) -> float:
    data = await db.query(...)
    return calculate_hrv_score(data)
```

### Adding a New Service

1. Create `backend/app/services/your_service.py`
2. Implement as pure functions with type hints
3. Add `backend/tests/test_your_service.py`
4. Add API endpoints in `backend/app/api/v1/endpoints/`
5. Register endpoints in `backend/app/core/registry.py`

### Code Style

```python
# Follow ruff defaults
# - Line length: 88
# - Quote style: double quotes
# - Import sorting: isort compatible

# Type hints are required
def process_data(values: list[float], threshold: float = 0.5) -> dict[str, Any]:
    ...

# Docstrings for public functions
def analyze_heart_rate(samples: list[int]) -> HeartRateAnalysis:
    """Analyze heart rate data and return metrics.
    
    Args:
        samples: List of heart rate values in BPM
        
    Returns:
        HeartRateAnalysis with resting_hr, max_hr, zones
    """
```

### Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_cardiovascular.py -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html

# Run only unit tests
python -m pytest tests/unit/ -v
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "add_your_table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Pull Request Checklist

- [ ] Tests pass (`python -m pytest tests/ -v`)
- [ ] Type hints on all public functions
- [ ] Docstrings for new services
- [ ] No database calls in service functions
- [ ] Migration if schema changed
- [ ] README updated if new feature

## Commit Messages

```
feat: add HRV biofeedback training service
fix: correct sleep stage calculation for REM
docs: update API documentation for /predictions
test: add edge cases for anomaly detection
refactor: extract common validation helpers
```
