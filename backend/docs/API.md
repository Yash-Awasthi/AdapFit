# AdapFit API Documentation

## Overview
AdapFit is an AI-powered adaptive fitness and health platform with 462+ API endpoints across 24+ services.

**Base URL:** `http://localhost:8000/api/v1`  
**Version:** 2.0.0  
**Format:** JSON

---

## Authentication

### JWT Token Auth
```bash
# Register
POST /api/v1/auth/register
{ "email": "user@example.com", "username": "john", "password": "Secure123!" }

# Login
POST /api/v1/auth/login
{ "email": "user@example.com", "password": "Secure123!" }
# Returns: { "tokens": { "access_token": "...", "refresh_token": "..." } }

# Use token in headers
Authorization: Bearer <access_token>
```

### API Key Auth
```bash
# Create API key (admin only)
POST /api/v1/auth/keys
{ "name": "my-app", "tier": "pro" }

# Use API key
X-API-Key: af_...
```

### Rate Limits
| Tier | Requests/min |
|------|-------------|
| Free | 100 |
| Pro | 1,000 |
| Enterprise | 10,000 |

---

## Service Groups

### Health & Biometrics
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/camera/bpm/start` | POST | Start BPM measurement from camera |
| `/camera/bpm/frame` | POST | Process camera frame for rPPG |
| `/camera/bpm/result` | GET | Get BPM measurement result |
| `/camera/fatigue/detect` | POST | Detect fatigue from face |
| `/stress/assess` | POST | Multi-factor stress assessment |
| `/stress/breathing` | GET | List breathing exercises |
| `/sleep/log` | POST | Log sleep session |
| `/sleep/score` | GET | Get sleep score |
| `/body-health/bp/log` | POST | Log blood pressure |
| `/body-health/hydration/log` | POST | Log water intake |

### Fitness
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/workout-engine/exercises` | GET | List 102 exercises |
| `/workout-engine/plans` | GET | List workout plans |
| `/workout-engine/session/start` | POST | Start workout session |
| `/workout-engine/session/{id}/log` | POST | Log set (reps/weight) |
| `/workout-engine/session/{id}/complete` | POST | Complete workout |
| `/workout-engine/history` | GET | Workout history |
| `/workout-engine/prs` | GET | Personal records |

### Nutrition
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/nutrition/search` | GET | Search 110+ foods |
| `/nutrition/meal` | POST | Log meal |
| `/nutrition/daily` | GET | Daily summary |
| `/nutrition/targets` | GET | Calculate macro targets |
| `/nutrition/water` | POST | Log water intake |

### Mental Health
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/mental-health/mood` | POST | Log mood entry |
| `/mental-health/mood/trend` | GET | Mood trend analysis |
| `/mental-health/phq9` | GET | PHQ-9 depression screening |
| `/mental-health/gad7` | GET | GAD-7 anxiety screening |
| `/mental-health/journal` | GET | Journal entries |
| `/mental-health/thought-record` | POST | CBT thought record |

### AI & Personalization
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ai-coach/daily-insight` | GET | Daily health insight |
| `/ai-coach/ask` | POST | Ask health question |
| `/ai-coach/weekly-report` | GET | Weekly health report |
| `/personalize/recommendations` | GET | Personalized recommendations |

### Content
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/content/feed` | GET | Health content feed |
| `/content/trending` | GET | Trending content |
| `/content/search` | GET | Search content |

### Social & Community
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/community/challenges` | GET | Active challenges |
| `/community/leaderboard` | GET | Community leaderboard |
| `/community/feed` | GET | Activity feed |

### Enterprise
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/medication/add` | POST | Add medication |
| `/medication/today` | GET | Today's schedule |
| `/emergency/sos` | POST | Trigger SOS alert |
| `/emergency/contacts` | GET | Emergency contacts |
| `/export/formats` | GET | Available export formats |
| `/notifications/send` | POST | Send notification |
| `/rewards/status` | GET | Rewards status |

### Health Summary
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/summary` | GET | Unified health dashboard |

### Admin
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/stats` | GET | System statistics |
| `/admin/users` | GET | User management |
| `/admin/analytics` | GET | Feature analytics |

---

## Error Codes
| Code | Description |
|------|-------------|
| 400 | Bad Request — Invalid input |
| 401 | Unauthorized — Invalid/missing token |
| 403 | Forbidden — Insufficient permissions |
| 404 | Not Found — Resource doesn't exist |
| 429 | Too Many Requests — Rate limit exceeded |
| 500 | Internal Server Error |

## WebSocket Endpoints
| Endpoint | Description |
|----------|-------------|
| `/ws/bpm/{user_id}` | Real-time BPM streaming |
| `/ws/{user_id}` | Push notifications |
