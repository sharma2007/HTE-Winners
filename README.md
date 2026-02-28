# DoomLearn (hackathon MVP)

Mobile-first edtech app that replaces doomscrolling with “doom learning”. This repo contains:

- `apps/mobile`: React Native (Expo + TypeScript) client
- `backend/api`: FastAPI API (Postgres + S3-compatible storage)
- `backend/worker`: Celery worker (Redis) for async processing + reel generation

## Local dev quickstart

1) Start infra:

```bash
docker compose up -d
```

Notes:
- **FFmpeg** is required on your machine for mock reel generation (the worker creates a vertical MP4 via `ffmpeg`).
- Keep `VECTOR_DIM=384` (matches the initial migration).

2) Backend API:

```bash
cd backend/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../../.env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

3) Worker:

```bash
cd backend/worker
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../../.env.example .env
celery -A worker.celery_app worker --loglevel=INFO
```

4) Mobile:

```bash
cd apps/mobile
npm install
# Optional (recommended): set these in your shell before running Expo:
# export EXPO_PUBLIC_API_BASE_URL="http://localhost:8000"
# export EXPO_PUBLIC_GOOGLE_CLIENT_ID="..."
npx expo start
```

## MVP demo flow

- Login (Google OAuth in production; `AUTH_MOCK=1` for local dev)
- Create course → create topics/subtopics
- Upload PDF → Process upload → Open feed → scroll reels → answer micro-quizzes → check progress

## API smoke test (optional)

With `AUTH_MOCK=1`, you can get a JWT and call the API:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/google \
  -H "Content-Type: application/json" \
  -d '{"id_token":"dev"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s http://localhost:8000/courses -H "Authorization: Bearer $TOKEN"
```
