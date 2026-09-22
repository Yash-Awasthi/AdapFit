# AdapFit — How to Run

## Database (PostgreSQL)

The app runs against Postgres. Without `DATABASE_URL` set it falls back to an
in-memory store that writes to `backend/app/data/`, which is fine for a quick
look but loses concurrency and query power.

```bash
# One-off, if Postgres is not installed:
winget install --id PostgreSQL.PostgreSQL.17 --exact

# Create the role and database (as the postgres superuser):
psql -U postgres -h 127.0.0.1 -c "CREATE ROLE adapfit LOGIN PASSWORD '<pick-one>'"
psql -U postgres -h 127.0.0.1 -c "CREATE DATABASE adapfit OWNER adapfit"
```

Put the connection string in `backend/.env`:

```
DATABASE_URL=postgresql://adapfit:<password>@127.0.0.1:5432/adapfit
```

Then apply the schema:

```bash
cd backend
python -m scripts.apply_migrations          # apply what is pending
python -m scripts.apply_migrations --list   # show status, change nothing
```

pgvector is optional. Without it the schema still applies and semantic
exercise search falls back to an in-memory index.

To check the whole loop against the database — register, log check-ins, read a
decision, then re-read it all in a fresh process:

```bash
python -m scripts.verify_postgres
```

## Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Dashboard**: http://localhost:8000/dashboard

## Mobile (React Native / Expo)

```bash
cd mobile
npm install
npx expo start
```

Scan the QR code with Expo Go or press `a` for Android emulator.

## Environment Variables

Backend reads from `backend/app/core/config.py`. `.env` is gitignored.

```
DATABASE_URL=postgresql://...   # Postgres; in-memory fallback without it
JWT_SECRET_KEY=...              # Required in production; random per run otherwise
GEMINI_API_KEY=your_key_here    # For AI features (works without it via fallbacks)
GROQ_API_KEY=your_key_here      # For LLM streaming
ADAPFIT_DATA_DIR=...            # Where the file-backed store writes
AUTH_DISABLED=true              # Local convenience; ignored when ENVIRONMENT=production
```

`AUTH_DISABLED` switches off JWT validation for local work. It is ignored in
production, but note that it also switches off the identity binding that ties
every request to its caller — so with it on, the app behaves as a single-user
one. Turn it off to exercise multi-user behaviour.

Air quality, UV and pollen come from Open-Meteo, which needs no key or account.

## What's Running

| Service | URL | Status |
|---------|-----|--------|
| Backend API | http://localhost:8000 | ✅ 78 routes, 290+ endpoints |
| API Docs | http://localhost:8000/docs | ✅ Auto-generated |
| Health Check | http://localhost:8000/health | ✅ All services healthy |
| Mobile App | Expo DevTools | Runs on `npx expo start` |

## Architecture

```
Mobile (React Native/Expo)
    ↕ HTTP + WebSocket
Backend (FastAPI/Python)
    ↕ PostgreSQL (in-memory + file fallback when DATABASE_URL is unset)
```

Every request is bound to its authenticated user before routing, so a handler
never sees another account's id. See `backend/app/middleware/identity.py`.

## Key Features Working End-to-End

### Backend (all verified)
- ✅ Exercise library with search/filter (800+ exercises)
- ✅ AI chat coach with intent classification
- ✅ Recovery engine (HRV Z-score, Hooper-Mackinnon, ACWR)
- ✅ Workout generation with adaptive scaling
- ✅ Health conditions tracker (40+ conditions)
- ✅ Medication tracker with exercise interactions
- ✅ Diet logging with macro tracking
- ✅ Meditation library (8 guided sessions)
- ✅ Daily wellness check-in
- ✅ Personal best tracker
- ✅ GPS route tracking
- ✅ Social workout rooms (WebSocket)
- ✅ Sensor hub (WebSocket)
- ✅ Cycle tracking with phase-aware recommendations
- ✅ Working hours personalization
- ✅ Injury risk prediction
- ✅ AI meal planner
- ✅ QR code workout sharing
- ✅ Achievement badge system (25 badges)
- ✅ Body composition photo comparison
- ✅ HRV trend charts
- ✅ Workout comparison
- ✅ Breathing exercises
- ✅ Health advisor with web search

### Mobile (15 screens)
- ✅ Recovery dashboard (HRV trends, streaks)
- ✅ Workout generator + active workout
- ✅ Exercise library browser
- ✅ AI chat coach
- ✅ Health conditions dashboard (new)
- ✅ Diet tracker with macro chart (new)
- ✅ Meditation player (new)
- ✅ Sleep tracker
- ✅ Nutrition logging
- ✅ Trends/analytics
- ✅ Stats dashboard
- ✅ Social feed + challenges
- ✅ Periodization planner
- ✅ Profile with heatmap
- ✅ Settings
