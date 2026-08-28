# AdapFit

**AI-Powered Adaptive Fitness & Recovery Engine**

AdapFit listens to your body's biometrics — HRV, sleep, subjective wellness, and training load — then generates personalized workouts that adapt in real-time. Built with scientific recovery algorithms, PyTorch neural networks, and an AI fitness coach.

![Tests](https://img.shields.io/badge/tests-45%20passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.12+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)
![React Native](https://img.shields.io/badge/React%20Native-0.79-purple)

---

## Features

### Recovery Engine
- **HRV Z-Score**: Rolling 28-day RMSSD baseline normalization
- **Hooper-Mackinnon Matrix**: Soreness, fatigue, stress, muscle region scoring
- **Foster's Session-RPE**: Internal load calculation (TL = Duration x RPE)
- **ACWR**: Exponentially weighted Acute:Chronic Workload Ratio with deload alerts
- **4-Tier State Machine**: OPTIMAL → MODERATE → REDUCED → DEPLETED

### AI Workout Generation
- **Gemini 2.0 Flash**: LLM-powered adaptive workout creation
- **Soreness Exclusion**: Automatic muscle group avoidance
- **Equipment Matching**: Filter by available equipment
- **Rule-Based Fallback**: Deterministic scientific fallback when LLM unavailable

### ML Analytics
- **PyTorch ReadinessNet**: Neural network for readiness prediction
- **HRV Forecasting**: Linear regression 7-day trend prediction
- **Anomaly Detection**: Z-score outlier flagging
- **Injury Risk Scoring**: Multi-factor risk assessment
- **Online Learning**: Feedback loop for continuous model improvement

### NLP Pipeline
- **Sentiment Analysis**: HuggingFace DistilBERT + keyword fallback
- **Goal Parsing**: LLM + rule-based fitness goal extraction
- **Pain Detection**: Automatic pain flagging in workout feedback
- **Muscle Extraction**: Free-text muscle group identification

### AI Fitness Coach
- **Context-Aware Chat**: Uses recovery data, ACWR, readiness state
- **Gemini LLM**: Natural language fitness coaching
- **Pain Detection**: NLP side-effects on chat messages
- **Rule-Based Fallback**: Deterministic advice for common questions

### Mental Health Module
- **Mood Tracking**: Mood, energy, anxiety with tags
- **Trend Analysis**: 7-day rolling averages, improving/stable/declining
- **Breathing Exercises**: Box, 4-7-8, Coherent, Energizing, Pre-Workout

### Mobile App (React Native + Expo)
- **6 Tabs**: Recovery, Workout, Coach, Wellness, Trends, Profile
- **Health Connect**: Android health data integration
- **Dark Theme**: Consistent slate/indigo design system
- **Real-time Chat**: AI coach conversation interface

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **API** | FastAPI + Pydantic v2 + slowapi |
| **ML** | PyTorch, XGBoost, scikit-learn |
| **NLP** | HuggingFace Transformers, Gemini API |
| **Vector Search** | Qdrant in-memory + sentence-transformers |
| **Database** | Supabase PostgreSQL (optional) + in-memory fallback |
| **Mobile** | React Native 0.79 + Expo SDK 53 + NativeWind |
| **State** | Zustand |
| **Health Data** | react-native-health-connect |

---

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Dashboard: http://localhost:8000/dashboard
API docs: http://localhost:8000/docs

### Mobile

```bash
cd mobile
npm install
npx expo start
```

Scan QR code with Expo Go on Android.

### Run Tests

```bash
cd backend
python -m pytest tests/ -v
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/users` | Create user profile |
| GET | `/api/v1/users/{id}` | Get user profile |
| PATCH | `/api/v1/users/{id}` | Update user |
| POST | `/api/v1/recovery-logs` | Log recovery data |
| POST | `/api/v1/workouts` | Generate workout |
| PATCH | `/api/v1/workouts/{id}` | Complete workout |
| GET | `/api/v1/exercises` | List exercises (paginated) |
| POST | `/api/v1/exercises/search` | Semantic search |
| POST | `/api/v1/chat` | AI coach chat |
| POST | `/api/v1/mental-health` | Log mood |
| GET | `/api/v1/mental-health` | Mood trends |
| GET | `/api/v1/mental-health/breathing-exercises` | Breathing exercises |
| GET | `/api/v1/trends/acwr` | ACWR analysis |
| GET | `/api/v1/trends/hrv` | HRV trends |
| GET | `/api/v1/trends/ml-insights` | ML predictions |
| WS | `/ws/{user_id}` | Real-time notifications |

---

## Environment Variables

```bash
# AI (optional — app works without these via rule-based fallbacks)
GEMINI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here

# Database (optional — falls back to in-memory storage)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

---

## Architecture

```
Mobile (Expo) ←→ FastAPI Backend ←→ Storage Engine
                      ↓
              ┌───────┼───────┐
              ↓       ↓       ↓
         Recovery   ML/NLP   Exercise
         Engine     Engine   Service
              ↓       ↓       ↓
         Core Engine (Rust/Python)
```

---

## License

Internal Hackathon Project — 007-Synapse
