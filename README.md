# 🏋️ AdapFit — AI-Powered Adaptive Fitness & Recovery Engine

> **An intelligent health companion that answers: "What should I do today, and why?"**

[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-teal.svg)](https://fastapi.tiangolo.com)
[![React Native](https://img.shields.io/badge/React%20Native-0.83+-purple.svg)](https://reactnative.dev)
[![Expo](https://img.shields.io/badge/Expo-SDK%2055-black.svg)](https://expo.dev)
[![Tests](https://img.shields.io/badge/Tests-228+-brightgreen.svg)](#testing)
[![Endpoints](https://img.shields.io/badge/API-290+-endpoints-orange.svg)](#api-overview)

**AdapFit** is a full-stack health platform that aggregates data from wearables, manual entry, and health platforms into a unified intelligence layer — providing cross-domain recovery scoring, contextual health recommendations, medication safety, emergency SOS, AI-powered coaching, and a self-evolving personalization engine.

Not a dashboard of raw numbers. Every screen answers: *What should I do today, and why?*

🌐 **[Landing Page](web/index.html)** · 📖 **[API Docs](http://localhost:8000/docs)** · 🏗️ **[Architecture](docs/ARCHITECTURE.md)** · 🚀 **[Deployment Guide](docs/DEPLOYMENT.md)**

---

## ✨ Highlights

| Domain | Features |
|--------|----------|
| 🧠 **AI Health Coach** | Intent-classified chat with RAG knowledge retrieval, conversational memory, and multi-turn context |
| 💪 **Smart Workouts** | Auto-generated plans based on recovery, goals, ACWR, and periodization |
| 😴 **Sleep Analysis** | Smart alarm, stage breakdown, sleep debt tracking, chronotype analysis, sleep architecture scoring |
| 🫀 **Recovery Engine** | 6-domain scoring (HRV Z-score, Hooper-Mackinnon, sleep, subjective, ACWR, nutrition) |
| 🥗 **Nutrition** | Meal logging, macro tracking, AI meal planning, precision nutrition, food scanner, recipe generation |
| 🧘 **Mental Health** | Mood tracking, breathing exercises, meditation library, stress engine, digital wellbeing |
| ⚠️ **Emergency SOS** | One-tap emergency alerts with medical ID, first aid guidance, hospital finder |
| 👨‍👩‍👧 **Family Network** | Shared health dashboards with granular permissions, family mode |
| 📊 **ML Pipeline** | XGBoost/LightGBM ensemble, PyTorch neural nets, fatigue forecasting, trend correlation, anomaly detection |
| 🎮 **Gamification** | 25 achievement badges, 7 categories, XP system, streaks, fitness challenges, social workout rooms |
| 🩺 **Clinical Health** | 40+ chronic conditions, medication tracker with exercise interactions, diabetes management, cardiac rehab |
| 🔬 **Biosignal Processing** | ECG interpretation, rPPG heart rate, BVP signal processing, voice biomarkers |
| 🧬 **Precision Health** | Genomics insights, nutrigenomics, personalized medicine, longevity tracking, microbiome health |
| 📱 **Camera Vitals** | Real-time heart rate via rPPG (remote photoplethysmography), posture analysis, form checking |
| 🏠 **Health Ecosystem** | Telemedicine, hospital at home, preventive screening, health passport, government schemes |
| 🔒 **Enterprise Security** | JWT + refresh rotation, PBKDF2-SHA256, CSP headers, input sanitization, rate limiting, IP blocking |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MOBILE APP                            │
│  React Native · Expo SDK 55 · TypeScript · Zustand      │
│  60+ screens · Offline-first SQLite · BLE sensors        │
├─────────────────────────────────────────────────────────┤
│                   REST API (HTTPS) + WebSocket           │
├─────────────────────────────────────────────────────────┤
│                   FASTAPI BACKEND                        │
│  290+ endpoints · 300+ services · 228+ tests            │
├─────────────────────────────────────────────────────────┤
│              DATA & INTELLIGENCE LAYER                   │
│  Recovery engine (personal baseline) · Daily decision   │
│  NLP sentiment · Preference learning · LLM (Groq/Gemini)│
│  RAG Knowledge System · Vector Store · Health Validation │
├─────────────────────────────────────────────────────────┤
│  Rust Core Engine (PyO3, optional) · PostgreSQL · Docker │
└─────────────────────────────────────────────────────────┘
```

### Daily decision

A check-in is scored against the user's own baseline (HRV z-score, sleep,
soreness, fatigue, stress, and training load once 28 days of sessions exist).
`daily_decision.decide()` turns the signals into TRAIN, REDUCE, RECOVER or
REST with the reasons; a language model may only reword that decision.

---

## 🚀 Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# → http://localhost:8000/docs (Swagger UI)
```

### Mobile

```bash
cd mobile
npm install
npx expo start
# → Scan QR code with Expo Go
```

### Docker

```bash
docker compose up --build
# API on http://localhost:8010, on Postgres; see docs/DEPLOYMENT.md
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET_KEY` | Yes (prod) | random (dev) | JWT signing secret |
| `DATABASE_URL` | No | in-memory | PostgreSQL connection string |
| `SUPABASE_URL` | No | — | Supabase project URL |
| `SUPABASE_KEY` | No | — | Supabase anon/service key |
| `GEMINI_API_KEY` | No | — | Google Gemini for AI coach & phrasing |
| `GROQ_API_KEY` | No | — | Groq Llama for AI fallback |
| `ENVIRONMENT` | No | `development` | `production` enables fail-fast checks |
| `AUTH_DISABLED` | No | `false` | Skip JWT validation in dev |
| `RATE_LIMITING_ENABLED` | No | `false` | Enable slowapi rate limiting |
| `RATE_LIMIT_PER_MINUTE` | No | `100` | Requests per minute per IP |

---

## 🧩 Feature Deep Dive

### 🫀 Recovery Engine (Multi-Domain Scoring)

The recovery score is computed from six physiological domains using validated sports science models:

| Domain | Method | Weight |
|--------|--------|--------|
| **HRV** | Z-score vs personal 28-day baseline | 40% (with HRV) |
| **Sleep** | Duration + efficiency vs target | 35% (with HRV) / 55% (without) |
| **Subjective** | Soreness, fatigue, stress, muscle groups | 25% (with HRV) / 45% (without) |
| **ACWR** | Acute:Chronic Workload Ratio penalty | Penalty overlay |
| **Training Load** | TRIMP-based session load | Feeds ACWR |
| **Nutrition** | Macro adherence, hydration | Contextual |

```
Recovery Score → Readiness State:
  ≥ 85  → OPTIMAL   → Full progressive overload permitted
  ≥ 65  → MODERATE  → Standard training, RPE 7-8
  ≥ 45  → REDUCED   → Scaled-back volume (-40%), mobility focus
  < 45  → DEPLETED  → Active recovery only, rest or gentle mobility
```

Key endpoints:
- `POST /api/v1/recovery-v2/calculate` — Full recovery calculation
- `GET /api/v1/recovery` — Recovery history
- `GET /api/v1/recovery-logs` — Raw recovery logs
- `GET /api/v1/hrv-trends` — HRV trend analysis

### 💪 Adaptive Workout Generation

Workouts are generated based on your current recovery state, not a static plan:

1. **Recovery assessment** determines readiness state
2. **Exercise selection** uses RAG knowledge + personal preference vector
3. **Volume/intensity scaling** adapts to ACWR and fatigue forecast
4. **Substitution engine** swaps exercises based on pain flags and equipment
5. **Warmup/cooldown** tailored to the day's focus muscles

Readiness states map to training directives:
- **OPTIMAL** → Full progressive overload, RPE 8-9
- **MODERATE** → Standard training, RPE 7-8
- **REDUCED** → Reduced volume, mobility focus
- **DEPLETED** → Active recovery or complete rest

Key endpoints:
- `POST /api/v1/workout-engine` — Generate adaptive workout
- `POST /api/v1/nl-workout` — Natural language workout logging ("3 sets of squats at 100kg")
- `POST /api/v1/exercise-subs` — Smart exercise substitution
- `POST /api/v1/workouts/adaptive` — Adaptive workout with auto-scaling
- `GET /api/v1/planner` — AI workout planner

### 🧠 AI Health Coach

Multi-layered AI coaching system:

- **Intent classification** — Routes user messages to appropriate handlers
- **RAG knowledge retrieval** — Evidence-based fitness science from curated knowledge base (40+ entries across recovery science, exercise science, nutrition, injury prevention, mental health)
- **Conversational memory** — Tracks conversation context across sessions
- **Weekly summary generation** — LLM-powered or rule-based progress reports
- **Goal parsing** — Converts free-text goals into structured targets

The AI coach operates with a **safety-first architecture**: rule-based constraints are applied before any LLM output, ensuring recommendations are physiologically plausible.

Key endpoints:
- `POST /api/v1/chat` — AI health coach chat
- `POST /api/v1/fitness-chat` — RAG-enhanced fitness chatbot
- `GET /api/v1/memory` — Conversational memory
- `GET /api/v1/ai-coach` — AI coach v1
- `GET /api/v1/ai-coach-v2` — AI coach v2

### 📊 ML Analytics Engine

Enterprise-grade machine learning with graceful fallbacks:

| Component | Technology | Fallback |
|-----------|------------|----------|
| Readiness Prediction | PyTorch neural network | Rule-based scoring |
| Performance Prediction | XGBoost gradient boosting | Weighted heuristic |
| HRV Forecasting | Linear regression with R² | Trend direction |
| Anomaly Detection | Z-score outlier detection | — |
| Injury Risk | Multi-factor risk scoring | — |
| Fatigue Forecasting | Cumulative fatigue model | — |
| Trend Correlation | Pearson correlation analysis | — |

The ML engine extracts 14+ features from recovery and workout history:
- 7-day HRV values, sleep durations, recovery scores
- ACWR, RPE, workout frequency
- Sleep debt, 7-day averages

Key endpoints:
- `GET /api/v1/trends` — ML-powered trend analysis
- `GET /api/v1/anomaly` — Health anomaly detection
- `GET /api/v1/predictions` — Health predictions
- `GET /api/v1/injury-risk-v2` — Injury risk detection

### 😴 Sleep Analysis

Comprehensive sleep intelligence:

- **Sleep staging** — Deep, light, REM classification
- **Sleep architecture** — Cycle analysis and quality scoring
- **Sleep debt tracking** — Cumulative deficit vs target
- **Chronotype analysis** — Morningness-eveningness profiling
- **Smart alarm** — Optimal wake time based on sleep cycles
- **Sleep audio analysis** — Environmental sound monitoring
- **Circadian rhythm** — Alignment tracking with training schedule

Key endpoints:
- `GET /api/v1/sleep-analysis` — Comprehensive sleep analysis
- `GET /api/v1/sleep-tracking` — Sleep tracking data
- `GET /api/v1/chronotype` — Chronotype analysis
- `GET /api/v1/sleep-audio` — Sleep audio analysis
- `GET /api/v1/circadian` — Circadian rhythm tracking

### 🥗 Nutrition & Diet

Full nutrition intelligence platform:

- **Meal logging** with macro tracking (protein, carbs, fats, calories)
- **AI meal planning** — Personalized plans based on goals and recovery
- **Precision nutrition** — Phase-aware recommendations
- **Food scanner** — Camera-based meal photo recognition
- **Recipe generation** — AI-powered recipe creation
- **Macro tracking** — Daily/weekly/monthly trend analysis
- **Hydration tracking** — Water intake logging with reminders
- **Nutrigenomics** — Genetic nutrition insights
- **Cycling fueling planner** — Activity-specific nutrition timing

Key endpoints:
- `GET /api/v1/nutrition` — Nutrition data
- `GET /api/v1/nutrition-tracking` — Nutrition tracking
- `GET /api/v1/meal-plan` — AI meal planning
- `GET /api/v1/food-scanner` — Food photo recognition
- `GET /api/v1/recipes` — AI recipe generation
- `GET /api/v1/precision-nutrition` — Precision nutrition
- `GET /api/v1/nutrigenomics` — Nutrigenomics insights
- `GET /api/v1/hydration` — Hydration tracking

### 🧘 Mental Health & Wellness

Holistic mental wellness support:

- **Mood tracking** — Daily mood logging with trend analysis
- **Breathing exercises** — Guided breathing with pacer
- **Meditation library** — 8+ guided meditation sessions
- **Stress engine** — Multi-factor stress assessment
- **Digital wellbeing** — Screen time awareness
- **Digital detox** — Addiction recovery tools
- **Cognitive training** — Brain exercise programs
- **Peer support** — Community mental health support

Key endpoints:
- `GET /api/v1/mental-health` — Mental health tracking
- `GET /api/v1/breathing` — Breathing exercises
- `GET /api/v1/breathing-analysis` — Breathing analysis
- `GET /api/v1/meditation` — Meditation library
- `GET /api/v1/stress` — Stress management
- `GET /api/v1/wellbeing` — Digital wellbeing
- `GET /api/v1/digital-detox` — Digital detox
- `GET /api/v1/cognitive` — Cognitive training
- `GET /api/v1/peer-support` — Peer support

### 🩺 Clinical Health & Medical

Enterprise-grade health management:

- **40+ chronic conditions** — Diabetes, hypertension, asthma, arthritis, and more
- **Medication tracker** — Medication reminders with exercise interaction checker
- **Drug interaction engine** — Checks medication-exercise interactions
- **Blood pressure monitoring** — Trend tracking and alerts
- **ECG interpretation** — Heart rhythm analysis
- **Cardiac rehab** — Post-cardiac event recovery programs
- **Stroke rehab** — Neurological recovery tracking
- **Diabetes management** — CGM integration, glucose tracking
- **Pregnancy tracking** — Trimester-aware recommendations
- **Fertility tracking** — Cycle-aware fitness guidance
- **Preventive screening** — Health risk assessments

Key endpoints:
- `GET /api/v1/health-conditions` — Health conditions tracker
- `GET /api/v1/medication` — Medication reminders
- `GET /api/v1/medication-tracker` — Medication tracking
- `GET /api/v1/drug-interactions` — Drug interaction checker
- `GET /api/v1/blood-pressure` — Blood pressure tracking
- `GET /api/v1/ecg` — ECG interpretation
- `GET /api/v1/cardiac-rehab` — Cardiac rehabilitation
- `GET /api/v1/stroke-rehab` — Stroke rehabilitation
- `GET /api/v1/diabetes` — Diabetes management
- `GET /api/v1/pregnancy` — Pregnancy tracking
- `GET /api/v1/fertility` — Fertility tracking
- `GET /api/v1/screening` — Preventive screening

### 📱 Camera Vitals & Computer Vision

Real-time health monitoring through your phone camera:

- **rPPG heart rate** — Estimate BPM from face video using remote photoplethysmography
- **rPPG signal processing** — BVP signal extraction and filtering
- **Posture analysis** — Real-time posture assessment via MediaPipe
- **Form checking** — Exercise form analysis with joint angle calculation
- **Pose estimation** — 33-landmark MediaPipe pose detection
- **Drowsiness detection** — Fatigue monitoring from facial landmarks

Key endpoints:
- `GET /api/v1/camera` — Camera vitals (rPPG)
- `GET /api/v1/rppg` — Remote photoplethysmography
- `GET /api/v1/pose` — Pose estimation & form check
- `GET /api/v1/posture` — Posture analysis
- `GET /api/v1/drowsiness` — Drowsiness detection

### 🔬 Biosignal Processing

Advanced biometric signal analysis:

- **ECG interpretation** — Heart rhythm classification
- **HRV analysis** — Time-domain, frequency-domain, and non-linear metrics
- **HRV artifact correction** — Automatic outlier removal
- **HRV biofeedback** — Guided breathing for HRV improvement
- **BVP signal processing** — Blood volume pulse analysis
- **Voice biomarkers** — Health indicators from voice patterns
- **Biosignal analysis** — Multi-signal fusion

Key endpoints:
- `GET /api/v1/biosignal` — Biosignal analysis
- `GET /api/v1/voice-biomarker` — Voice biomarker analysis
- `GET /api/v1/hrv-trends` — HRV trend analysis

### 🧬 Precision & Genomic Health

Personalized health at the genetic level:

- **Genomics insights** — Genetic predisposition analysis
- **Nutrigenomics** — Gene-nutrient interaction guidance
- **Personalized medicine** — Treatment customization
- **Longevity tracking** — Biomarkers for aging
- **Microbiome health** — Gut health monitoring

Key endpoints:
- `GET /api/v1/genomics` — Genomics insights
- `GET /api/v1/nutrigenomics` — Nutrigenomics
- `GET /api/v1/personalized-medicine` — Personalized medicine
- `GET /api/v1/longevity` — Longevity tracking
- `GET /api/v1/microbiome` — Microbiome health

### 🏠 Health Ecosystem

Connected health services:

- **Telemedicine** — Virtual health consultations
- **Hospital finder** — Locate nearby healthcare facilities
- **Hospital at home** — Remote patient monitoring programs
- **Healthcare providers** — Provider directory
- **Health passport** — Portable health records
- **Government schemes** — Health program discovery
- **Clinical trials** — Trial matching and information
- **Insurance** — Health insurance management

Key endpoints:
- `GET /api/v1/telemedicine` — Telemedicine
- `GET /api/v1/hospitals` — Hospital finder
- `GET /api/v1/hospital-at-home` — Hospital at home
- `GET /api/v1/providers` — Healthcare providers
- `GET /api/v1/passport` — Health passport
- `GET /api/v1/government-schemes` — Government schemes
- `GET /api/v1/clinical-trials` — Clinical trials
- `GET /api/v1/insurance` — Insurance management

### 🎮 Gamification & Social

Engagement and community features:

- **25 achievement badges** across 7 categories
- **XP system** with level progression
- **Streaks** with recovery-aware rules (Rest Day ≠ streak break)
- **Social workout rooms** — Multiplayer sessions via WebSocket
- **Community forums** — Health and fitness discussions
- **Team challenges** — Corporate wellness, friend groups
- **Activity feed** — Social health updates
- **QR code sharing** — Workout and progress sharing

Key endpoints:
- `GET /api/v1/achievements-v3` — Fitness gamification
- `GET /api/v1/streaks` — Streak tracking
- `GET /api/v1/rooms` — Workout rooms (WebSocket)
- `GET /api/v1/forums` — Community forums
- `GET /api/v1/community-v2` — Community v2
- `GET /api/v1/challenges` — Fitness challenges
- `GET /api/v1/activity-feed` — Activity feed
- `GET /api/v1/qr-share` — QR code sharing

### 🩸 Wearable & Sensor Integration

Deep hardware integration:

- **HealthKit bridge** — Apple Health data sync
- **Health Connect** — Android Health Connect v2
- **BLE heart rate** — Real-time HR streaming during workouts
- **Samsung Health** — Galaxy Watch integration
- **Fitbit** — Fitbit Web API bridge
- **Garmin** — Garmin data import and analysis
- **Oura Ring** — Oura sleep and readiness data
- **Smart ring parser** — Generic ring data support
- **Apple Health parser** — XML health export parsing
- **FitDown parser** — FitDown data format
- **Strava import** — Workout import from Strava
- **Sensor hub** — Real-time multi-device BLE streaming
- **GPS tracking** — Route, pace, elevation for outdoor workouts

Key endpoints:
- `GET /api/v1/healthkit` — HealthKit bridge
- `GET /api/v1/wearable` — Wearable import
- `GET /api/v1/wearable-rt` — Wearable real-time
- `GET /api/v1/device-sync` — Device sync
- `GET /api/v1/ble-sensors` — BLE sensor integration
- `GET /api/v1/sensors` — Sensor hub (WebSocket)
- `GET /api/v1/gps` — GPS tracking

### 🚨 Emergency & Safety

Critical safety features:

- **Emergency SOS** — One-tap emergency alerts
- **Medical ID** — Emergency medical information
- **First aid** — AI-guided first aid instructions
- **Health risk engine** — Multi-factor risk assessment
- **Illness detection** — Early warning system
- **Injury risk prediction** — ACWR + HRV + sleep-based risk scoring

Key endpoints:
- `GET /api/v1/emergency` — Emergency SOS
- `GET /api/v1/medical-id` — Medical ID
- `GET /api/v1/first-aid` — First aid guidance
- `GET /api/v1/risk` — Health risk assessment
- `GET /api/v1/illness` — Illness detection
- `GET /api/v1/injury-risk-v2` — Injury risk detection

### 🔒 Security & Privacy

Enterprise-grade security:

- **PBKDF2-SHA256** password hashing (310,000 iterations)
- **JWT** with access + refresh token rotation (30-day refresh)
- **Account lockout** after 5 failed attempts (15-minute lockout)
- **Rate limiting** per-IP on all endpoints (slowapi)
- **CSP headers** — Content Security Policy on all responses
- **Input sanitization** — XSS, SQL injection, and suspicious pattern detection
- **IP blocking** — Abuse prevention
- **API key management** — Tiered access for external integrations
- **Audit logging** — Security event tracking
- **E2E encryption** — End-to-end data encryption
- **Privacy dashboard** — User data control
- **Security headers** — X-Frame-Options, HSTS, X-XSS-Protection
- **Circuit breaker** — Resilient external API calls
- **Request deduplication** — Idempotency support
- **Pydantic v2** validation on every API boundary
- **User isolation** — All data scoped to authenticated user
- **Data confidence scoring** — Source trust + range validation + cross-field consistency

Key endpoints:
- `GET /api/v1/security` — Security dashboard
- `GET /api/v1/encryption` — E2E encryption
- `GET /api/v1/privacy` — Privacy dashboard
- `GET /api/v1/rate-limit` — Rate limiting

### 🌐 Internationalization

Multi-language support:

- **English** (en) — Full translation
- **Spanish** (es) — Full translation
- **French** (fr) — Full translation
- **i18n API** — Language switching at runtime

Key endpoint:
- `GET /api/v1/i18n` — Internationalization

### ♿ Accessibility

Inclusive design:

- **WCAG 2.1 AA** compliance
- **VoiceOver/TalkBack** support
- **Dynamic font scaling**
- **High contrast mode**
- **Reduced motion** support
- **Haptic feedback** — Tactile responses for key actions

Key endpoint:
- `GET /api/v1/accessibility` — Accessibility settings

---

## 📱 Mobile App (60+ Screens)

### Tab Navigation

| Tab | Description |
|-----|-------------|
| 🏠 **Home** | Today's decision, recovery dashboard, quick actions |
| 🏋️ **Train** | Workout generation, active workout, exercise library |
| 🎬 **Watch** | Health content feed, video cards, meditation player |
| 💬 **Coach** | AI health coach chat, intent classification, memory |
| 📋 **More** | Full feature catalog (55+ screens) |

### Key Mobile Features

- **Recovery dashboard** — HRV trends, streaks, readiness gauge
- **Active workout** — Real-time timer, set logging, RPE input
- **Exercise browser** — 800+ exercises with muscle group filtering
- **Sleep tracker** — Duration, quality, stages, smart alarm
- **Nutrition logging** — Meals, macros, hydration, recipes
- **Meditation player** — Guided sessions with audio
- **Health conditions** — 40+ conditions dashboard
- **Mental health** — Mood, breathing, stress tracking
- **Periodization planner** — Training phase management
- **Stats dashboard** — Progress photos, body composition, personal bests
- **Trends analytics** — Historical data visualization
- **Social feed** — Community updates, challenges
- **Settings** — Profile, preferences, theme, accessibility
- **Onboarding** — 5-step wizard (goals, experience, equipment, schedule, injuries)

### Mobile Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | React Native 0.83 + Expo SDK 55 |
| Routing | expo-router (file-based) |
| State | Zustand 5.0 |
| Data Fetching | TanStack Query 5.x |
| Styling | NativeWind (Tailwind CSS) |
| Charts | react-native-circular-progress, SVG |
| Animations | React Native Reanimated 4.x |
| Gestures | React Native Gesture Handler |
| Offline | expo-sqlite (WAL mode, sync queue) |
| BLE | react-native-ble-plx |
| Camera | expo-camera |
| Voice | expo-speech |
| Notifications | expo-notifications |
| Validation | Zod 4.5 |

---

## 🔌 API Overview

### Core Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/auth/login` | Authenticate (JWT) |
| `POST` | `/api/v1/auth/register` | Register new user |
| `POST` | `/api/v1/recovery-v2/calculate` | Full recovery calculation |
| `POST` | `/api/v1/chat` | AI health coach |
| `POST` | `/api/v1/fitness-chat` | RAG-enhanced fitness chat |
| `POST` | `/api/v1/workout-engine` | Generate adaptive workout |
| `POST` | `/api/v1/nl-workout` | Natural language workout logging |
| `GET` | `/api/v1/sleep-analysis` | Sleep analysis |
| `GET` | `/api/v1/achievements-v3` | Badge system |
| `GET` | `/api/v1/trends` | ML-powered trend analysis |
| `GET` | `/api/v1/health-conditions` | Health conditions |
| `POST` | `/api/v1/meal-plan` | AI meal planning |
| `GET` | `/api/v1/camera` | Camera heart rate |
| `WS` | `/ws/bpm/{user_id}` | Real-time BPM WebSocket |
| `WS` | `/ws/{user_id}` | General WebSocket |

Full interactive docs: `http://localhost:8000/docs`

### WebSocket Endpoints

| Path | Description |
|------|-------------|
| `/ws/bpm/{user_id}` | Real-time camera heart rate |
| `/ws/{user_id}` | General real-time updates |
| `/api/v1/rooms/{room_id}` | Social workout rooms |
| `/api/v1/sensors` | Multi-device sensor streaming |
| `/api/v1/challenges` | Challenge WebSocket |

---

## 🧪 Testing

```bash
cd backend
python -m pytest tests/ -v
# 228/228 tests pass
```

### Test Coverage

| Category | Tests |
|----------|-------|
| Recovery Engine | 15+ tests |
| Workout Generation | 20+ tests |
| ML/NLP/Agents | 25+ tests |
| Authentication | 10+ tests |
| Health Services | 50+ tests |
| Integration | 30+ tests |
| Edge Cases | 78+ tests |

---

## 🗂️ Project Structure

```
ZFIT/
├── backend/
│   ├── app/
│   │   ├── main.py                    # Entry point, router registration
│   │   ├── core/                      # Auth, config, storage, validation, security
│   │   │   ├── auth.py                # JWT, PBKDF2, account lockout, API keys
│   │   │   ├── config.py              # Pydantic settings
│   │   │   ├── storage.py             # In-memory + PostgreSQL storage
│   │   │   ├── health_validation.py   # Physiological plausibility ranges
│   │   │   ├── registry.py            # Auto-discover endpoint routers
│   │   │   ├── circuit_breaker.py     # Resilient external API calls
│   │   │   ├── encryption.py          # E2E encryption
│   │   │   └── daily_decision.py      # 4-state training decision engine
│   │   ├── api/v1/endpoints/          # 290+ endpoint modules (auto-discovered)
│   │   ├── services/                  # 300+ business logic modules
│   │   │   ├── agent/evolution_engine.py # Preference learning
│   │   │   ├── ml_engine.py           # Trends, forecasts, anomalies
│   │   │   ├── nlp_pipeline.py        # Sentiment, goal parsing
│   │   │   ├── rag_knowledge.py       # Fitness science knowledge base
│   │   │   └── ...                    # 290+ service modules
│   │   └── middleware/                # Security, validation, compression
│   ├── core_engine/                   # Rust PyO3 extension (optional)
│   │   ├── Cargo.toml
│   │   └── src/                       # Rust source for fast computation
│   ├── tests/                         # 228+ tests
│   └── docs/                          # API docs, schema
├── mobile/
│   ├── app/                           # File-based routing (expo-router)
│   │   ├── (tabs)/                    # 60+ tab screens
│   │   ├── login.tsx, register.tsx    # Auth screens
│   │   ├── onboarding*.tsx           # Onboarding wizard
│   │   └── workout-*.tsx             # Active workout flow
│   └── src/
│       ├── components/                # 25+ reusable components
│       ├── stores/                    # Zustand state management
│       ├── services/                  # API client, auth, sync, theme
│       ├── hooks/                     # Custom React hooks
│       ├── db/                        # SQLite schema, sync queue
│       ├── i18n/                      # Internationalization (en, es, fr)
│       ├── accessibility/             # Accessibility utilities
│       ├── theme/                     # Design tokens
│       └── utils/                     # Performance, accessibility helpers
├── web/                               # Landing page + admin dashboard
├── docker-compose.yml                 # Local stack: API and Postgres
├── Dockerfile                         # The one API image
└── render.yaml                        # Free staging on Render
```

---

## 🎯 What Makes AdapFit Different

1. **Decision, not dashboard** — Every screen answers "What should I do today?" instead of dumping raw numbers.

2. **Recovery-first architecture** — Every recommendation is grounded in your current physiological state, not a static plan.

3. **Rule-based safety + LLM enhancement** — Deterministic metrics make the decision; LLM only explains it. The AI never picks the workout — it just phrases it.

4. **Self-evolving personalization** — The system learns from every accepted/rejected workout, pain flag, and feedback signal. Preferences evolve over time via the Evolution Engine.

5. **In-memory by default** — Zero-config startup. Set `DATABASE_URL` for persistence.

6. **Rust-powered core** — Optional PyO3 extension delivers 10-100x faster computation for HRV, recovery, and ACWR calculations. Falls back to pure Python seamlessly.

7. **API-first** — Every feature has a REST endpoint. Mobile is just one consumer.

8. **Modular services** — 300+ independent modules; each can be extended or replaced.

9. **Offline-first mobile** — SQLite with WAL mode and sync queue for seamless offline operation.

10. **Comprehensive health coverage** — From fitness to clinical health, from genomics to telemedicine, from emergency SOS to hospital finder.

---

## 🗺️ Roadmap

- [ ] Wearable BLE sync (Health Connect integration)
- [ ] Real-time WebSocket updates for live coaching
- [ ] Camera-based vitals (rPPG heart rate) — production hardening
- [ ] Push notifications (EAS Build)
- [ ] Payment/subscription (Stripe)
- [ ] HIPAA compliance pathway
- [ ] Federated learning for privacy-preserving ML
- [ ] AR fitness overlay (pose guidance in camera view)
- [ ] Voice-first coaching (TTS + real-time cues)
- [ ] Digital twin simulation

---

## 📚 Documentation

- **[Architecture Overview](docs/ARCHITECTURE.md)** — System design and component relationships
- **[Deployment Guide](docs/DEPLOYMENT.md)** — Production deployment instructions
- **[API Reference](backend/docs/API.md)** — Detailed API documentation
- **[Database Schema](backend/docs/schema.sql)** — PostgreSQL schema
- **[Contributing Guide](CONTRIBUTING.md)** — Development guidelines
- **[How to Run](START.md)** — Quick start instructions

---

## 🤝 Contributing

Contributions welcome! Open an issue or PR.

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

---

## 📄 License

Proprietary — All rights reserved.

---

*Built with ❤️ by the AdapFit team.*
