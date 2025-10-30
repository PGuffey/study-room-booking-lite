from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import List
from emailer import write_confirmation
from storage import FileStore

app = FastAPI(title="Study Room Booking – Lite")

# ---------- persistence ----------
store = FileStore()                 # data directory is ../data by default
ROOMS = store.load_rooms()          # static seed or file content
BOOKINGS = store.load_bookings()    # list[dict] with datetime objects

def _next_id() -> int:
    if not BOOKINGS:
        return 1
    return max(b["id"] for b in BOOKINGS) + 1

# ---------- rules ----------
MAX_HOURS_PER_DAY = 2
CANCEL_CUTOFF_MIN = 30

# ---------- models ----------
class BookingCreate(BaseModel):
    user_id: int
    room_id: int
    start: datetime
    end: datetime
    group_size: int = Field(ge=1)

class BookingOut(BaseModel):
    id: int
    user_id: int
    room_id: int
    start: datetime
    end: datetime
    group_size: int

# ---------- routes ----------
@app.get("/")
def root():
    return {
        "ok": True,
        "service": app.title,
        "docs": "/docs",
        "endpoints": ["/rooms", "/search", "/bookings", "/users/{user_id}/bookings"]
    }

@app.get("/rooms")
def list_rooms():
    return ROOMS

@app.get("/search")
def search_rooms(date: str, start: str, end: str):
    start_dt = _parse_dt(date, start)
    end_dt = _parse_dt(date, end)
    _ensure_valid(start_dt, end_dt)
    available = []
    for r in ROOMS:
        if not _has_overlap(r["id"], start_dt, end_dt):
            available.append(r)
    return available

@app.post("/bookings", response_model=BookingOut, status_code=201)
def create_booking(payload: BookingCreate):
    # basic checks
    room = _get_room(payload.room_id)
    _ensure_valid(payload.start, payload.end)
    if payload.group_size > room["capacity"]:
        raise HTTPException(422, detail="group_size exceeds room capacity")
    if _has_overlap(payload.room_id, payload.start, payload.end):
        raise HTTPException(409, detail="room already booked for that window")
    if _exceeds_daily_hours(payload.user_id, payload.start, payload.end):
        raise HTTPException(422, detail="daily booking hours limit exceeded")

    booking = {
        "id": _next_id(),
        "user_id": payload.user_id,
        "room_id": payload.room_id,
        "start": payload.start,
        "end": payload.end,
        "group_size": payload.group_size,
    }
    BOOKINGS.append(booking)
    store.save_bookings(BOOKINGS)  # persist to JSON

    # side-effect (ok to be sync for class project)
    write_confirmation(to_email=f"user{payload.user_id}@example.edu",
                       booking_id=booking["id"])
    return booking

@app.get("/users/{user_id}/bookings", response_model=List[BookingOut])
def my_bookings(user_id: int):
    return [b for b in BOOKINGS if b["user_id"] == user_id]

@app.delete("/bookings/{booking_id}", status_code=204)
def cancel_booking(booking_id: int):
    idx = next((i for i, b in enumerate(BOOKINGS) if b["id"] == booking_id), None)
    if idx is None:
        raise HTTPException(404, detail="booking not found")
    b = BOOKINGS[idx]
    now = datetime.now(b["start"].tzinfo)
    if (b["start"] - now) < timedelta(minutes=CANCEL_CUTOFF_MIN):
        raise HTTPException(422, detail="cannot cancel within 30 minutes of start")
    BOOKINGS.pop(idx)
    store.save_bookings(BOOKINGS)  # persist deletion

# ---------- helpers ----------
def _parse_dt(date_str: str, hm: str) -> datetime:
    # expects YYYY-MM-DD and HH:MM
    try:
        return datetime.fromisoformat(f"{date_str}T{hm}")
    except Exception:
        raise HTTPException(400, detail="use YYYY-MM-DD for date and HH:MM for time")

def _ensure_valid(start: datetime, end: datetime):
    if end <= start:
        raise HTTPException(400, detail="end must be after start")

def _get_room(room_id: int) -> dict:
    r = next((r for r in ROOMS if r["id"] == room_id), None)
    if not r:
        raise HTTPException(404, detail="room not found")
    return r

def _has_overlap(room_id: int, start: datetime, end: datetime) -> bool:
    for b in BOOKINGS:
        if b["room_id"] != room_id:
            continue
        if b["start"] < end and b["end"] > start:
            return True
    return False

def _exceeds_daily_hours(user_id: int, start: datetime, end: datetime) -> bool:
    day0 = start.replace(hour=0, minute=0, second=0, microsecond=0)
    day1 = day0 + timedelta(days=1)
    total = 0.0
    for b in BOOKINGS:
        if b["user_id"] != user_id:
            continue
        if not (b["start"] >= day0 and b["end"] <= day1):
            continue
        total += (b["end"] - b["start"]).total_seconds() / 3600
    total += (end - start).total_seconds() / 3600
    return total > MAX_HOURS_PER_DAY + 1e-9
