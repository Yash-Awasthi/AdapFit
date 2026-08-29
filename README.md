# 🏋️ AdapFit — AI-Powered Adaptive Fitness & Recovery Engine

> **An intelligent health companion that answers: "What should I do today, and why?"**

[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-teal.svg)](https://fastapi.tiangolo.com)
[![React Native](https://img.shields.io/badge/React%20Native-0.83-purple.svg)](https://reactnative.dev)
[![Tests](https://img.shields.io/badge/Tests-228+-brightgreen.svg)](#testing)

**AdapFit** is a full-stack health platform that aggregates data from wearables, manual entry, and health platforms into a unified intelligence layer — providing cross-domain recovery scoring, contextual health recommendations, medication safety, emergency SOS, and AI-powered coaching.

Not a dashboard of raw numbers. Every screen answers: *What should I do today, and why?*

---

## ✨ Highlights

| Domain | Features |
|--------|----------|
| 🧠 **AI Health Coach** | Intent-classified chat with RAG knowledge retrieval |
| 💪 **Smart Workouts** | Auto-generated plans based on recovery, goals, and periodization |
| 😴 **Sleep Analysis** | Smart alarm, stage breakdown, sleep debt tracking |
| 🫀 **Recovery Engine** | 6-domain scoring (sleep, HRV, load, subjective, nutrition, heart rate) |
| 🥗 **Nutrition** | Meal logging, macro tracking, AI meal planning |
| 🧘 **Mental Health** | Mood tracking, breathing exercises, meditation library |
| ⚠️ **Emergency SOS** | One-tap emergency alerts with medical ID |
| 👨‍👩‍👧 **Family Network** | Shared health dashboards with granular permissions |
| 📊 **ML Pipeline** | Fatigue forecasting, trend correlation, anomaly detection |
| 🎮 **Gamification** | 25 achievement badges, 7 categories, XP system |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  MOBILE APP                          │
│  React Native · Expo SDK 55 · TypeScript · Zustand  │
├─────────────────────────────────────────────────────┤
│                 REST API (HTTPS)                     │
├─────────────────────────────────────────────────────┤
│                 FASTAPI BACKEND                      │
│  203 routers · 166 services · 228+ tests            │
├─────────────────────────────────────────────────────┤
│              DATA & INTELLIGENCE LAYER               │
│  Health Store · ML Engine · Recovery V2 · NLP        │
├─────────────────────────────────────────────────────┤
│  PostgreSQL (or in-memory) · Redis · Docker          │
└─────────────────────────────────────────────────────┘
```

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

### Docker (Full Stack)

```bash
docker-compose up -d
# Backend: http://localhost:8000
# PostgreSQL: localhost:5432
# Redis: localhost:6379
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET_KEY` | Yes | random (dev) | JWT signing secret |
| `DATABASE_URL` | No | in-memory | PostgreSQL connection string |
| `GEMINI_API_KEY` | No | — | Google Gemini for AI coach |
| `GROQ_API_KEY` | No | — | Groq Llama for AI fallback |
| `RATE_LIMITING_ENABLED` | No | `false` | Enable slowapi rate limiting |

---

## 🧪 Testing

```bash
cd backend
python -m pytest tests/ -v
# 228/228 tests pass
```

---

## 📊 Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/auth/login` | Authenticate (JWT) |
| `POST` | `/api/v1/recovery/v2/calculate` | Recovery score |
| `POST` | `/api/v1/chat` | AI health coach |
| `POST` | `/api/v1/workouts` | Generate workout |
| `GET` | `/api/v1/sleep/analysis` | Sleep analysis |
| `GET` | `/api/v1/achievements-v2` | Badge system |
| `POST` | `/api/v1/nl-workout` | Natural language workout logging |

Full interactive docs: `http://localhost:8000/docs`

---

## 🔒 Security

- **PBKDF2-SHA256** password hashing (310k iterations)
- **JWT** with refresh token rotation
- **Account lockout** after 5 failed attempts
- **Rate limiting** per-IP on all endpoints
- **Pydantic v2** validation on every API boundary
- **User isolation** — all data scoped to authenticated user

---

## 📂 Project Structure

```
ZFIT/
├── backend/
│   ├── app/
│   │   ├── main.py             # Entry point, router registration
│   │   ├── core/               # Auth, config, storage, metrics
│   │   ├── api/v1/endpoints/   # 203 endpoint modules
│   │   ├── services/           # 166 business logic modules
│   │   └── middleware/         # Security, validation, compression
│   └── tests/                  # 228+ tests
├── mobile/
│   ├── app/                    # File-based routing (expo-router)
│   └── src/                    # Components, stores, theme
├── docker-compose.yml
└── README.md
```

---

## 🎯 What Makes AdapFit Different

1. **In-memory by default** — zero-config startup. Set `DATABASE_URL` for persistence.
2. **Rule-based fallbacks** — works 100% offline without LLM keys. AI enhances when available.
3. **API-first** — every feature has a REST endpoint. Mobile is just one consumer.
4. **Modular services** — 166 independent modules; each can be extended or replaced.
5. **Recovery-first** — every recommendation is grounded in your current recovery state.

---

## 🗺️ Roadmap

- [ ] Wearable BLE sync (Health Connect integration)
- [ ] Real-time WebSocket updates
- [ ] Camera-based vitals (rPPG heart rate)
- [ ] Push notifications (EAS Build)
- [ ] Payment/subscription (Stripe)
- [ ] HIPAA compliance pathway

---

## 🤝 Contributing

Contributions welcome! Open an issue or PR.

---

## 📄 License

Proprietary — All rights reserved.

---

*Built with ❤️ by the AdapFit team.*
