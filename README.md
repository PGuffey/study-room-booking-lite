# Study Room Booking – Sprint 1

## Run

uvicorn app.main:app --reload

## Example Calls

GET /rooms
GET /search?date=2025-10-07&start=10:00&end=11:00
POST /bookings {"user_id":1,"room_id":
1,"start":"2025-10-08T10:00:00","end":"2025-10-08T11:00:00","group_size":2}
GET /users/1/bookings
DELETE /bookings/1

## Notes

- In‑memory storage. Restart clears data.
- "Email" is a text file in ./outbox.
- Inputs must use ISO format: YYYY‑MM‑DD and HH:MM.
