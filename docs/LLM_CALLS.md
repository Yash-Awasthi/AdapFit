# Language model calls

Every place the server sends text or an image to a language model. There are
no others: `grep -rn "generateContent\|chat/completions\|gemini_endpoint(" backend/app`
finds exactly these.

Providers: Google Gemini (`GEMINI_API_KEY`, model `gemini-3.6-flash` in
`backend/app/core/gemini.py`) and Groq (`GROQ_API_KEY`, model `GROQ_MODEL`,
default `openai/gpt-oss-120b`). Both have free tiers; production needs at least
one key (`startup_checks.py`). Without a key, or without the user's AI consent,
every call below takes its fallback and nothing leaves the server.

Rules shared by all calls:

- **Consent and quota.** No call runs unless the account has granted the `ai`
  purpose (and `health_data`) and has calls left today, checked with
  `llm_quota.ai_call_allowed()`. The websocket chat
  has no request context and checks the account explicitly.
- **Input triage.** Chat, websocket chat and the misinformation check run the
  user's text through `safety_policy.triage()` first. Chest pain, stroke signs,
  severe bleeding, overdose or self-harm get a fixed reply with 112 / 108 /
  Tele-MANAS 14416, and no model is called.
- **System rules.** Chat prompts end with `SAFETY_RULES`: wellness coach, never
  diagnose, never start, stop or change a medicine, compare with the user's own
  baseline, name the kind of professional and how soon.
- **Output screen.** Free-text model output goes through
  `safety_policy.screen_reply()`, which drops any sentence that tells the user
  they have a condition or to change a medicine, and adds "For anything about a
  diagnosis or your medicines, please ask your doctor."
- **What is sent.** The user's message, recent chat turns, and a context block
  of their own numbers (recovery score, HRV, sleep, soreness, ACWR once it
  exists, recent RPE). Names and emails are not sent. Photos only for photo
  meal logging.

| # | Where | Purpose | Model and limits | Filter | Fallback |
|---|---|---|---|---|---|
| 1 | `endpoints/chat.py` `POST /chat` | Coach chat | Gemini, then Groq; 1,024 / 300 output tokens | triage, SAFETY_RULES, screen_reply | Knowledge-base passages with sources, else rule-based reply |
| 2 | `endpoints/ws_chat.py` `/ws/{user_id}` | Streaming coach chat | Gemini, then Groq; 1,024 output tokens | triage, SAFETY_RULES (BASE_SYSTEM), screen_reply | Knowledge-base passages |
| 3 | `endpoints/misinformation_api.py` | Checks a health claim the user pastes | Gemini, then Groq, JSON verdict | triage, SAFETY_RULES, screen_reply on the explanation, sources kept only if on the trusted list | "Unverified" verdict |
| 4 | `services/recommendation_engine.py` | Writes today's workout as JSON | Gemini, JSON mode, temperature 0.3, 10 s timeout | Told never to state a score it was not given; rationale through screen_reply; schema-validated | Rule-based routine from the exercise library |
| 5 | `services/nlp_pipeline.py` `parse_goals_from_text` | Turns a typed goal into fields | Gemini, JSON mode, temperature 0.2 | Output is enum fields, not advice | Keyword parser |
| 6 | `services/nlp_pipeline.py` weekly summary | Two-sentence weekly summary | Gemini, 800 output tokens | screen_reply | Rule-based sentence from measured scores |
| 7 | `services/food_vision.py` via `POST /diet/photo-log` | Foods and macros from a meal photo | Gemini vision, 30 s timeout | Output parsed as numbers only | Refused (502): no zero-calorie meal is logged |

Developer override: `POST /chat` accepts `llm_override` (provider, key, model,
base URL) for the in-app developer tools. It is ignored when `ENVIRONMENT` is
`production`, so the server never calls a URL or key a caller supplies there.

## Cost

Each chat turn sends roughly 1,500 to 2,500 input tokens (system rules, the
context block, up to 600 tokens of knowledge-base text, 10 prior turns) and
returns at most 1,024. A workout generation is about 400 in and 800 out. A
meal photo is one image plus about 150 tokens. Both providers' free tiers cover
testing and a closed beta; at scale the bill is set by the provider's price
per million tokens at the time. Each account may make `LLM_DAILY_CALLS` model
calls a day (default 60, `backend/app/core/llm_quota.py`); after that every
call site uses its fallback and the chat says so. That caps the worst case at
about 60 × 3,500 tokens per active user per day.

## Known limits

- `screen_reply` is English pattern matching. A reply in Hindi or another
  language passes through unscreened; the system rules still apply.
- The food photo "confidence" per item is a fixed label (0.85), not a
  probability the model reported.
