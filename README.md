# Study Room Booking – Lite

A **local-only, file-backed FastAPI demo** for managing study room bookings.  
Features include JSON persistence, structured errors, and a developer CLI.

---

## Quickstart

### 1) Create & activate venv

`powershell
python -m venv venv
venv\Scripts\Activate.ps1
`

### 2) Install dependencies

`bash
pip install -r requirements.txt
`

### 3) Run the API

`bash
uvicorn app.main:app --reload
`

Visit:

- Root metadata → [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Swagger UI → [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc → [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Developer CLI

The CLI provides a simple interface to the API:  
`bash
python cli.py rooms
`

Once installed in editable mode:  
`bash
pip install -e .
study-cli rooms
`

---

## Data & Persistence

All runtime data lives in `data/`:

- `rooms.json` — seed catalog (tracked)
- `bookings.json` — bookings (tracked)
- `errors.ndjson` — error log (tracked)
- `outbox/` — mock “email” confirmations (ignored by git, `.gitkeep` kept)

---

## Health & Docs

- `GET /` → `{ service, version, docs, redoc }`
- `GET /health` → `{ "status": "ok" }`

Swagger UI and ReDoc are always available for API reference.

---

## Documentation

For full usage, commands, curl examples, and error codes → see [USAGE.md](USAGE.md).
