# 📚 Study Room Booking – Lite

A **local-only, file-backed FastAPI demo** providing:

- Study room browsing

- Availability search

- Booking creation

- My bookings view

- Cancel booking

- Inline error messages with structured FastAPI error envelopes

- A simple built-in **web frontend** (no framework)

- A developer **CLI**

- Persistent JSON storage

- CI: ruff, mypy, pytest, import validation

This is a lightweight learning project demonstrating API design, error modeling, frontend consumption via `fetch()`, and safer patterns for file-backed persistence.

---

# 🚀 Quick Start

### 1) Install dependencies

```bash

pip install -r requirements.txt

```

---

### 2) Run the API + Frontend

```bash

uvicorn app.main:app --reload

```

Visit:

- **Frontend UI** → http://127.0.0.1:8000/

- **API metadata** → http://127.0.0.1:8000/api

- **Swagger docs** → http://127.0.0.1:8000/docs

- **ReDoc** → http://127.0.0.1:8000/redoc

---

# 🖥️ Frontend UI (MVP)

A pure **vanilla HTML + JS** frontend lives in:

```

web/index.html

```

It is automatically served at:

```

GET /

```

### The UI supports:

✔ Load Rooms

✔ Search availability

✔ Create booking

✔ View my bookings

✔ Cancel booking

✔ Inline structured error display (`error.code`, `error.message`, `error.hint`)

✔ Mobile-friendly via Tailwind CDN

✔ Uses `fetch()` to call all API endpoints

---

# 🧪 Running Tests

This project includes CI-verified smoke tests.

Run locally:

```bash

pytest -q

```

Tests confirm:

- API imports cleanly

- `/health` responds with `{ "status": "ok" }`

- `/api` exposes service metadata

---

# 🛠️ Developer CLI

A simple Typer-powered CLI is included:

```bash

python cli.py rooms

python cli.py search 2025-11-02 13:00 14:00

python cli.py book 1 2 2025-11-02T13:00:00 2025-11-02T14:00:00

python cli.py mine 1

python cli.py cancel 5

```

Once installed in editable mode:

```bash

pip install -e .

study-cli rooms

```

The CLI is validated in CI to ensure no regressions.

---

# 📦 Data & Persistence

All runtime JSON storage lives in `data/`.

- `rooms.json` — static room catalog

- `bookings.json` — saved on every booking / cancel

- `errors.ndjson` — structured error envelope logs

- `data/outbox/` — mock outbound emails (`booking_123.txt`)

This project uses **atomic writes** to avoid partial corruption.

---

# 🔧 CI / CD Pipeline

Your GitHub Actions workflow (`ci.yml`) runs:

- ✔ **ruff check** (lint)

- ✔ **ruff format --check**

- ✔ **mypy** (type checking)

- ✔ **pytest**

- ✔ Import FastAPI app

- ✔ Import CLI

- ✔ Multi-Python matrix (3.11 + 3.12)

A merged PR means all validations passed.

---

# 🌐 API Overview

### `/api`

Returns metadata:

```json
{
	"ok": true,

	"service": "Study Room Booking – Lite",

	"version": "0.3.0",

	"endpoints": ["/rooms", "/search", "/bookings", "/users/{user_id}/bookings"]
}
```

### `/rooms`

### `/search?date=YYYY-MM-DD&start=HH:MM&end=HH:MM`

### `POST /bookings`

### `/users/{user_id}/bookings`

### `DELETE /bookings/{booking_id}`

All errors follow a structured envelope:

```json
{
	"error": {
		"code": "OVERLAP_CONFLICT",

		"message": "room already booked for that window",

		"hint": "Pick a different time or room.",

		"status": 409,

		"path": "/bookings",

		"method": "POST",

		"ts": "2025-11-21T10:31:02.512Z"
	}
}
```

---
