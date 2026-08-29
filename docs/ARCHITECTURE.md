# AdapFit — Detailed Architecture

## System Overview

AdapFit follows a **three-tier architecture** with clear separation:

1. **Presentation Layer** (React Native / Expo)
2. **Application Layer** (FastAPI / Python)
3. **Data Layer** (PostgreSQL / In-Memory Store)

### Request Lifecycle

```
Mobile App
    ↓ HTTPS (JSON)
Nginx Reverse Proxy (rate limiting, SSL termination)
    ↓
FastAPI Application
    ↓
Middleware Pipeline:
  1. CORS validation
  2. Request ID injection
  3. Rate limiting (SlowAPI)
  4. Security headers
    ↓
Route Handler:
  1. Pydantic validation (input)
  2. Auth dependency (JWT verification)
  3. Service call (business logic)
  4. Storage operation (persistence)
  5. Response model (output)
    ↓
Response (JSON)
```

---

## Data Models

### User Model

```python
class User:
    id: str                    # UUID
    email: str                 # Unique, indexed
    name: str | None
    password_hash: str         # PBKDF2-SHA256
    role: str                  # "user" | "admin"
    fitness_level: str         # "beginner" | "intermediate" | "advanced"
    primary_goal: str          # "general_fitness" | "weight_loss" | etc.
    created_at: float          # Unix timestamp
    failed_login_attempts: int # Account lockout counter
    locked_until: float | None # Lockout expiry timestamp
```

### Health Data Record

```python
class HealthRecord:
    id: str                    # UUID
    user_id: str               # Foreign key
    measurement_type: str      # "heart_rate" | "steps" | "sleep" | etc.
    value: float               # Numeric value
    source: str                # "manual" | "wearable" | "health_connect" | "camera"
    confidence: str            # "high" | "medium" | "low"
    timestamp: float           # When measured
    privacy_level: str         # "private" | "shared" | "emergency_only"
    metadata: dict             # Additional context
```

### Family Connection

```python
class FamilyConnection:
    id: str                    # UUID
    user_a: str                # Inviter
    user_b: str                # Invitee
    relationship: str          # "parent" | "child" | "spouse" | etc.
    status: str                # "active" | "paused" | "revoked"
    permissions_by_a: dict     # What B can see of A's data
    permissions_by_b: dict     # What A can see of B's data
    created_at: float
    paused_at: float | None
    revoked_at: float | None
```

### Permission Categories (20+)

```python
DEFAULT_PERMISSIONS = {
    # Category-level
    "view_activity": False,
    "view_workouts": False,
    "view_sleep": False,
    "view_recovery": False,
    "view_location": False,
    "view_vitals": False,
    "view_medications": False,
    "view_emergency": False,
    "view_nutrition": False,
    "view_mood": False,
    "send_alerts": True,
    "view_summary": False,
    # Data-type-level
    "heart_rate": False,
    "hrv": False,
    "steps": False,
    "blood_pressure": False,
    "sleep_data": False,
    "weight": False,
    "medications": False,
    "location": False,
    "mood_data": False,
    "nutrition_data": False,
    "emergency_info": False,
    "stress": False,
    "activity": False,
    "workouts": False,
    "recovery": False,
}
```

---

## Security Boundaries

### Authentication Architecture

```
┌─────────────────────────────────────────────┐
│              AUTH FLOW                       │
├─────────────────────────────────────────────┤
│                                             │
│  Register:                                  │
│    email + password                         │
│    → validate password strength             │
│    → hash with PBKDF2-SHA256 (310k iter)    │
│    → store in database                      │
│    → return JWT pair                        │
│                                             │
│  Login:                                     │
│    email + password                         │
│    → check account lockout (5 attempts)     │
│    → timing-safe password verification      │
│    → on failure: increment attempts         │
│    → on success: reset attempts, issue JWT  │
│    → audit log event                        │
│                                             │
│  API Request:                               │
│    Bearer token in Authorization header     │
│    → decode JWT (HS256)                     │
│    → extract user_id                        │
│    → inject into request context            │
│                                             │
│  Token Refresh:                             │
│    refresh_token                            │
│    → validate not expired                   │
│    → delete old refresh token               │
│    → issue new pair                         │
│                                             │
└─────────────────────────────────────────────┘
```

### User Data Isolation

Every endpoint that reads or writes user data must:

1. Extract `user_id` from JWT via `require_user` dependency
2. Scope all database queries to that `user_id`
3. Never accept `user_id` from request body

```python
# CORRECT
@router.get("/data")
async def get_data(user: dict = Depends(require_user)):
    return store.get_user_data(user["id"])

# WRONG - user_id from body = spoofable
@router.get("/data")
async def get_data(user_id: str):
    return store.get_user_data(user_id)
```

### Family Network Security

```
Invite Flow:
  1. User A sends invite (generates cryptographic token)
  2. User B receives invite (token required to accept)
  3. User B accepts (token verified; empty string does NOT bypass)
  4. Connection created with ALL permissions False (default-deny)
  5. Users explicitly grant permissions per data type

Permission Enforcement:
  - check_permission(conn_id, viewer_id, permission)
  - Resolves aliases (bpm → heart_rate)
  - Default: denied
  - Must be explicitly granted by data owner
  - Audit logged on every grant/deny
```

### Emergency SOS Security

```
Per-User Isolation:
  - _active_alerts: Dict[str, SOSAlert]  # keyed by user_id
  - Each user has independent active alert
  - One user's SOS does not block another's

Ownership Verification:
  - confirm_sos(alert_id, user_id)
  - cancel_sos(alert_id, user_id)
  - Both verify: alert belongs to requesting user
  - Cross-user operations rejected with "Not authorized"
```

---

## Intelligence Layer

### Recovery Engine V2

Cross-domain recovery scoring combining 6 health domains:

| Domain | Weight | Data Sources |
|--------|--------|-------------|
| Sleep | 25% | Duration, quality, deep sleep %, consistency |
| HRV | 20% | RMSSD, LF/HF ratio |
| Training Load | 20% | ACWR, session RPE, days since rest |
| Subjective | 15% | Fatigue level, mood, stress |
| Nutrition | 10% | Hydration, calories, protein |
| Heart Rate | 10% | Resting HR, trend direction |

**Score Calculation:**
```
domain_score = f(domain_data)  # 0-100
weighted_score = domain_score × domain_weight
overall = Σ(weighted_scores) / Σ(available_weights)
```

**Cross-Domain Insights:**
- Sleep + Training Load → injury risk correlation
- HRV + Subjective → accumulated fatigue detection
- Training Load + HRV → overtraining detection
- Nutrition + Training → recovery adequacy
- Sleep + Heart Rate → illness onset detection

### Health Action Engine

Natural language intent routing:

```
User: "I need help with sleep"
    ↓
Word-boundary matching (prevents "rest" → "interest")
    ↓
Intent: "sleep" (confidence: 0.3)
    ↓
Module: sleep-tracker
Screen: sleep-tracker
API: /api/v1/sleep/analysis
```

### Personalization Pipeline

```
Observations → Patterns → Insights → Recommendations → Actions

Example:
  Observation: sleep_hours=5.5, steps=3000, stress=high
  Pattern: declining sleep trend over 3 days
  Insight: Sleep debt accumulating
  Recommendation: "Prioritize 8+ hours tonight"
  Action: Sleep reminder at 10 PM
```

---

## API Design Principles

### RESTful Conventions

| Pattern | Example | Method |
|---------|---------|--------|
| List resources | `/api/v1/users` | GET |
| Get single | `/api/v1/users/{id}` | GET |
| Create | `/api/v1/users` | POST |
| Update | `/api/v1/users/{id}` | PATCH |
| Delete | `/api/v1/users/{id}` | DELETE |
| Action | `/api/v1/recovery/v2/calculate` | POST |
| Query | `/api/v1/sleep/analysis?user_id=x&days=7` | GET |

### Response Envelope

```json
{
  "status": "success",
  "data": { ... },
  "meta": {
    "timestamp": "2026-08-29T10:30:00Z",
    "user_id": "abc123"
  }
}
```

### Error Response

```json
{
  "detail": "Not authenticated",
  "status_code": 401
}
```

---

## Mobile Architecture

### Screen Hierarchy

```
app/_layout.tsx (Root Stack)
├── (tabs)/_layout.tsx (Tab Navigator)
│   ├── index.tsx (Home)
│   ├── dashboard.tsx (Dashboard)
│   ├── workout.tsx (Workout)
│   ├── health-hub.tsx (Health)
│   ├── chat.tsx (AI Coach)
│   ├── content-feed.tsx (Content)
│   └── trends.tsx (Trends)
├── login.tsx (Auth)
├── register.tsx (Auth)
├── onboarding.tsx (Onboarding)
├── recovery-dashboard.tsx (Recovery V2)
├── camera-heart-rate.tsx (rPPG)
├── form-checker.tsx (Pose Estimation)
├── workout-active.tsx (Active Workout)
├── workout-complete.tsx (Post-Workout)
└── workout-detail.tsx (Workout Details)
```

### State Management

```
Zustand Stores:
├── userStore.ts      → userId, profile, auth state
├── workoutStore.ts   → active workout, history
├── healthStore.ts    → vitals, trends
└── settingsStore.ts  → preferences, theme

Persistence:
  AsyncStorage (React Native)
  → Token storage
  → User preferences
  → Offline queue
```

### Theme System

```typescript
// Dark mode
background: '#0F172A'
surface: '#1E293B'
text: '#F8FAFC'

// Light mode
background: '#F3F1EC'
surface: '#FBFAF7'
text: '#25291F'

// Accent colors
indigo: '#6366F1'  (default)
emerald: '#059669'
rose: '#E11D48'
amber: '#D97706'
cyan: '#0891B2'
```

---

## Deployment Architecture

### Docker Stack

```
┌─────────────────────────────────────┐
│           Nginx (80/443)            │
│   SSL termination, rate limiting    │
│   Static file serving               │
├─────────────────────────────────────┤
│         FastAPI (8000)              │
│   uvicorn, auto-scaling             │
│   Health check: /health             │
├──────────┬──────────────────────────┤
│ Postgres │        Redis             │
│ (5432)   │        (6379)            │
│ 16-alpine│     7-alpine             │
└──────────┴──────────────────────────┘
```

### Railway Deployment

```yaml
# railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 10
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

### Environment Progression

| Environment | Database | AI | Cache | Purpose |
|-------------|----------|-----|-------|---------|
| Development | In-memory | Rule-based | In-memory LRU | Local dev |
| Staging | Supabase free | Gemini free tier | Redis Cloud free | Testing |
| Production | Supabase Pro | Gemini + Groq | Redis Pro | Live users |

---

## Testing Strategy

### Backend

| Level | Tool | Coverage |
|-------|------|----------|
| Unit tests | pytest | Service logic |
| Integration | pytest-asyncio | API endpoints |
| Security | Manual review | Auth, isolation, permissions |
| Load | locust (planned) | Performance |

### Mobile

| Level | Tool | Coverage |
|-------|------|----------|
| Type check | tsc --noEmit | All TypeScript |
| E2E | Detox (configured) | Critical paths |
| Manual | Expo Go | Visual QA |

### Security Audit Checklist

- [x] JWT secret crashes in production if not set
- [x] Password hashing with sufficient iterations
- [x] Timing-safe comparisons for auth
- [x] Account lockout after failed attempts
- [x] User data isolation on all endpoints
- [x] Permission enforcement on family data
- [x] SOS ownership verification
- [x] Invite token verification (no bypass)
- [x] Input validation via Pydantic
- [x] CORS hardening for production
- [x] No hardcoded secrets in source
- [x] Audit logging for sensitive operations

---

## Monitoring & Observability

### Structured Logging

```python
import structlog
logger = structlog.get_logger()

logger.info("recovery_calculated",
    user_id=user["id"],
    score=result.overall_score,
    confidence=result.confidence,
    domains=len(result.domains)
)
```

### Health Check

```json
GET /health
{
  "status": "healthy",
  "version": "2.0.0",
  "services": {
    "database": "connected",
    "cache": "connected",
    "ai": "available"
  }
}
```

### Metrics (Prometheus)

- Request count by endpoint
- Response time percentiles
- Error rate by status code
- Active user count
- Recovery score distribution
- AI model usage

---

*Last updated: August 29, 2026*
