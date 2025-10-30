# Usage & Testing Guide

This file provides **detailed usage instructions, commands, error codes, and examples**.

---

## 1) Run the API

```bash
uvicorn app.main:app --reload
```

Visit: `/`, `/docs`, `/redoc`.

---

## 2) CLI Reference (Typer)

**Commands**:

- `rooms` → list room catalog
- `search <date> <start> <end>` → find available rooms
- `book <user_id> <room_id> <start_iso> <end_iso> [-g N]` → create booking
- `mine <user_id>` → list bookings
- `cancel <booking_id>` → cancel booking

**Global option:** `--api <base_url>` (or env `STUDY_API`)

**Examples**:

```bash
study-cli rooms
study-cli search 2025-11-02 13:00 14:00
study-cli book 210 2 2025-11-02T13:00:00 2025-11-02T14:00:00 -g 3
study-cli mine 210
study-cli cancel 3
```

---

## 3) Exit Codes

- `0` → success
- `1` → API responded with error (validation, overlap, etc.)
- `2` → cannot connect (API not running)

---

## 4) Troubleshooting

- **“Cannot reach API”** → make sure Uvicorn is running on port 8000.
- **409 OVERLAP_CONFLICT** → choose different time/room.
- **422 CAPACITY_EXCEEDED** → reduce group size.
- **422 DAILY_CAP_EXCEEDED** → user exceeded 2h/day.
- **422 CANCEL_CUTOFF** → too close to start time.
- **400 BAD_DATETIME_FORMAT** → fix input format.

---

## 5) Curl Equivalents

```bash
curl http://127.0.0.1:8000/rooms
curl "http://127.0.0.1:8000/search?date=2025-11-02&start=13:00&end=14:00"

curl -X POST http://127.0.0.1:8000/bookings \
  -H "Content-Type: application/json" \
  -d {"user_id":210,"room_id":2,"start":"2025-11-02T13:00:00","end":"2025-11-02T14:00:00","group_size":3}

curl http://127.0.0.1:8000/users/210/bookings
curl -X DELETE http://127.0.0.1:8000/bookings/3
```

---

## 6) Error Codes (Quick Reference)

| Code                | HTTP | Meaning                       |
| ------------------- | ---- | ----------------------------- |
| BAD_DATETIME_FORMAT | 400  | Wrong date/time format        |
| END_NOT_AFTER_START | 400  | End must be later than start  |
| ROOM_NOT_FOUND      | 404  | Room ID not found             |
| BOOKING_NOT_FOUND   | 404  | Booking ID not found          |
| OVERLAP_CONFLICT    | 409  | Time slot already booked      |
| CAPACITY_EXCEEDED   | 422  | Group size > room capacity    |
| DAILY_CAP_EXCEEDED  | 422  | User exceeded daily max (2h)  |
| CANCEL_CUTOFF       | 422  | Too close to start to cancel  |
| VALIDATION_ERROR    | 422  | Request validation failed     |
| INTERNAL_ERROR      | 500  | Generic fallback server error |

All errors include: `path`, `method`, `request_id`, `ts`; also logged in `data/errors.ndjson`.

---

## 7) Roadmap / Future Issues

- **Issue 3 (current):** Docs polish, `/` + `/health`, CORS, README.
- **Issue 4 (next):** Admin stats (`/admin/stats`, `study-cli stats`).
- **Issue 5:** Frontend MVP (static `index.html` at `/`).
- **Issue 6:** Frontend polish (CORS tweaks, UI, screenshots).
- **Nice-to-haves:** Users registry (`users.json`), named users in bookings, admin room management.
