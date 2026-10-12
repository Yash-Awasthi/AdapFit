# Handoff: Windows side

Open work for the whole project is in `todo.md`; this file is only what needs
the Windows machine.

1. Update and apply the pending migrations (012 to 014). `backend/.env` must
   hold `DATABASE_URL` and the same `DATA_ENCRYPTION_KEYS` the database was
   written with; a different key makes startup refuse to load sealed rows.
   ```powershell
   git checkout master
   git pull
   cd backend
   python -m scripts.apply_migrations --list
   python -m scripts.apply_migrations
   python -m scripts.verify_postgres
   python -m pytest tests -q -p no:warnings
   ```
2. Install and type-check the app:
   ```powershell
   cd ..\mobile
   npm ci
   npx tsc --noEmit
   node scripts/audit-gate.mjs
   npx expo start
   ```
3. On a device or emulator, walk the core loop and confirm:
   - Check-in with the pain toggle on gives a REST decision and a mobility
     session.
   - A sore area (for example legs) is left out of that day's plan.
   - Finishing a workout records it once, with the RPE from the completion
     screen.
   - The rest timer uses each exercise's prescribed rest.
   - A workout finished offline and synced later shows on the day it was done.
