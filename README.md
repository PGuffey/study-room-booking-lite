# Study Room Booking — Sprint 1

## Overview

Minimal FastAPI service that supports:

- `GET /rooms` – list static rooms
- `GET /search?date=YYYY-MM-DD&start=HH:MM&end=HH:MM` – find available rooms
- `POST /bookings` – reserve a room
- `GET /users/{id}/bookings` – list bookings
- `DELETE /bookings/{id}` – cancel if >30 min before start

**Rules enforced:**

- Max 2 hours/day per user
- Group size ≤ room capacity

**“Email confirmations”** are text files saved in `./outbox/`.

---

## Quick Start

```bash
pip install fastapi uvicorn pydantic
uvicorn app.main:app --reload
```

Then visit:  
`http://127.0.0.1:8000/docs`

---

## Example Calls

```bash
GET  /rooms
GET  /search?date=2025-10-07&start=10:00&end=11:00
POST /bookings {"user_id":1,"room_id":1,"start":"2025-10-07T10:00:00","end":"2025-10-07T11:00:00","group_size":2}
GET  /users/1/bookings
DELETE /bookings/1
```

---

## Notes

- All data is **in-memory**; restarting clears bookings.
- No database or email service yet.
- Keep inputs in ISO format (`YYYY-MM-DD` and `HH:MM`).
- Outbox files appear in `/outbox` folder.

---

## Next Steps

- Add JSON persistence (Sprint 2)
- Optional React front-end to visualize bookings
- Add basic automated tests (`pytest`)
