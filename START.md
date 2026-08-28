# AdapFit — How to Run

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

Backend reads from `backend/app/core/config.py`. Optional:

```
GEMINI_API_KEY=your_key_here    # For AI features (works without it via fallbacks)
GROQ_API_KEY=your_key_here      # For LLM streaming
```

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
    ↕ In-memory storage (suppliable with PostgreSQL)
```

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
