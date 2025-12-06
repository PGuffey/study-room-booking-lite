# Usage & Testing Guide

This guide contains **all instructions**, including:

- Running the API
- Running via Docker
- Using the CLI
- AI Assistant
- Curl examples
- Error codes
- Troubleshooting

---

# 1) Run the API (Local Development)

`bash
uvicorn app.main:app --reload
`

Visit:

- Frontend UI → http://127.0.0.1:8000/
- Health Check → http://127.0.0.1:8000/health
- Swagger → http://127.0.0.1:8000/docs
- ReDoc → http://127.0.0.1:8000/redoc
- Metadata → http://127.0.0.1:8000/api

---

# 2) AI Assistant Usage

The AI assistant uses a **HuggingFace Inference API model**.

### Endpoint

`bash
curl -X POST http://127.0.0.1:8000/ai/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What room is good for 6 people?\"}"
`

### Example Response

`json
{"reply": "Room E, located in Library L3, is a great option for a group of 6..."}
`

### Requirements

Your `.env` must include:

`HF_API_KEY=hf_xxxxxx
HF_MODEL_ID=google/gemma-2-2b-it`

### Frontend AI Panel

The web interface includes an **AI Assistant** box for natural-language queries.

---

# 3) CLI Reference (Typer CLI)

Run:

`bash
python cli.py <command>
`

Or if installed:

`bash
study-cli <command>
`

### Commands

| Command                                  | Description          |
| ---------------------------------------- | -------------------- |
| `rooms`                                  | List all study rooms |
| `search <date> <start> <end>`            | Search availability  |
| `book <uid> <room> <start> <end> [-g N]` | Create booking       |
| `mine <uid>`                             | Show user bookings   |
| `cancel <booking_id>`                    | Cancel booking       |
| `ai-chat "<message>"`                    | Talk to AI assistant |

### Examples

`bash
study-cli rooms
study-cli search 2025-11-23 13:00 14:00
study-cli book 1 2 2025-11-23T13:00:00 2025-11-23T14:00:00 -g 3
study-cli mine 1
study-cli cancel 5

study-cli ai-chat "Suggest a room for 4 near the library"
`

### CLI Exit Codes

- `0` success
- `1` API error
- `2` cannot connect to API

---

# 4) Docker Usage

### Build the image

`bash
docker compose build
`

### Run containers

`bash
docker compose up
`

### Visit the app

> http://localhost:8000/

### Run CLI from inside the container

`bash
docker compose exec api python cli.py rooms
docker compose exec api python cli.py ai-chat "Which room fits 8 people?"
`

### Check environment variables inside container

`bash
docker compose exec api printenv | grep HF_
`

---

# 5) Curl Examples

`bash
curl http://127.0.0.1:8000/rooms

curl "http://127.0.0.1:8000/search?date=2025-11-23&start=13:00&end=14:00"

curl -X POST http://127.0.0.1:8000/bookings \
 -H "Content-Type: application/json" \
 -d "{\"user_id\":1,\"room_id\":2,\"start\":\"2025-11-23T13:00:00\",\"end\":\"2025-11-23T14:00:00\",\"group_size\":3}"

curl http://127.0.0.1:8000/users/1/bookings

curl -X DELETE http://127.0.0.1:8000/bookings/5
`

---

# 6) Error Codes (Quick Reference)

| Code                | HTTP | Meaning                              |
| ------------------- | ---- | ------------------------------------ |
| BAD_DATETIME_FORMAT | 400  | Wrong date/time format               |
| END_NOT_AFTER_START | 400  | End must be later than start         |
| ROOM_NOT_FOUND      | 404  | Room ID does not exist               |
| BOOKING_NOT_FOUND   | 404  | Booking ID does not exist            |
| OVERLAP_CONFLICT    | 409  | Time window already booked           |
| CAPACITY_EXCEEDED   | 422  | Group size > room capacity           |
| DAILY_CAP_EXCEEDED  | 422  | More than 2 hrs/day booked           |
| CANCEL_CUTOFF       | 422  | Too late to cancel                   |
| VALIDATION_ERROR    | 422  | Pydantic validation failure          |
| GENAI_UNAVAILABLE   | 503  | AI not configured (missing env vars) |
| GENAI_FAILED        | 502  | HuggingFace error                    |
| INTERNAL_ERROR      | 500  | Unexpected server failure            |

All errors include:

- `status`
- `path`
- `method`
- `request_id`
- Timestamp

Logged at: `data/errors.ndjson`

---

# 7) Troubleshooting

- **API unreachable** → run `uvicorn` or `docker compose up`
- **AI disabled** → check `.env` for `HF_API_KEY`
- **409 OVERLAP_CONFLICT** → choose a different time
- **422 DAILY_CAP_EXCEEDED** → user exceeded limit
- **422 CANCEL_CUTOFF** → cancellation too close to start
- **Docker not updating** → rebuild with `docker compose build --no-cache`

---
