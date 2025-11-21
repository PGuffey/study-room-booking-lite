# app/main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from pathlib import Path
import uuid
import json
import datetime as dt
from typing import NoReturn, Optional, Any, Dict, List as _List, cast
from pydantic import BaseModel as _BaseModel
from .emailer import write_confirmation
from .storage import FileStore

app = FastAPI(
    title="Study Room Booking – Lite",
    description="Local-only, file-backed demo API with structured errors and developer CLI.",
    version="0.3.0",
)

# --- Web frontend directory ---
WEB_DIR = Path(__file__).resolve().parent.parent / "web"
if WEB_DIR.exists():
    # If you later add CSS/JS files (app.js, styles.css), they can be served from /static/...
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


@app.get("/", include_in_schema=False)
def serve_index():
    idx = WEB_DIR / "index.html"
    if idx.exists():
        return FileResponse(str(idx))
    # Fallback if index.html is missing
    return {
        "ok": True,
        "docs": "/docs",
    }


# CORS for local dev / future Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- meta routes ----------
@app.get("/api", tags=["meta"], summary="Service metadata")
def root():
    return {
        "ok": True,
        "service": app.title,
        "version": app.version,
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": ["/rooms", "/search", "/bookings", "/users/{user_id}/bookings"],
    }


@app.get("/health", tags=["meta"], summary="Health check")
def health():
    return {"status": "ok"}


# ---------- persistence ----------
store = FileStore()  # ../data by default
ROOMS = store.load_rooms()
BOOKINGS = store.load_bookings()


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


# ---- OpenAPI helper models (for documenting error responses) ----
class ErrorBody(_BaseModel):
    code: str
    message: str
    hint: Optional[str] = None
    extras: Optional[Dict[str, Any]] = None
    status: int
    path: str
    method: str
    request_id: Optional[str] = None
    ts: str
    validation_errors: Optional[_List[Dict[str, Any]]] = None


class ErrorEnvelope(_BaseModel):
    error: ErrorBody


# ---------- error logging / request-id ----------
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
ERROR_LOG_PATH = DATA_DIR / "errors.ndjson"  # newline-delimited JSON


def _append_error_to_log(payload: dict) -> None:
    try:
        with ERROR_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        # Silent fail: we never want logging to crash the API
        pass


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.request_id = uuid.uuid4().hex
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response


app.add_middleware(RequestIdMiddleware)


def _error_payload(
    request: Request,
    status: int,
    detail: dict[str, Any] | str,
) -> dict[str, Any]:
    # detail can be str or dict; normalize to dict
    if isinstance(detail, str):
        detail_dict: dict[str, Any] = {"code": "HTTP_ERROR", "message": detail}
    else:
        detail_dict = detail

    payload: dict[str, Any] = {
        "error": {
            **detail_dict,
            "status": status,
            "path": request.url.path,
            "method": request.method,
            "request_id": getattr(request.state, "request_id", None),
            "ts": dt.datetime.now().isoformat(),
        }
    }
    return payload


def err(
    code: str,
    message: str,
    *,
    hint: str | None = None,
    extras: dict | None = None,
    status: int = 400,
) -> NoReturn:
    detail: dict[str, Any] = {"code": code, "message": message}
    if hint:
        detail["hint"] = hint
    if extras:
        detail["extras"] = extras
    raise HTTPException(status, detail=detail)


@app.exception_handler(HTTPException)
async def http_exc_handler(request: Request, exc: HTTPException):
    payload = _error_payload(request, exc.status_code, exc.detail)
    _append_error_to_log(payload)  # <- write to data/errors.ndjson
    return JSONResponse(payload, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def pydantic_exc_handler(request: Request, exc: RequestValidationError):
    detail = {
        "code": "VALIDATION_ERROR",
        "message": "Request validation failed",
        "validation_errors": exc.errors(),
        "hint": "Check field names and types; see 'validation_errors'.",
    }
    payload = _error_payload(request, 422, detail)
    _append_error_to_log(payload)
    return JSONResponse(payload, status_code=422)


@app.exception_handler(Exception)
async def unhandled_exc_handler(request: Request, exc: Exception):
    # Last-resort catcher: don’t leak stack traces to clients
    detail = {
        "code": "INTERNAL_ERROR",
        "message": "Unexpected server error",
        "hint": "Try again or contact the developer.",
    }
    payload = _error_payload(request, 500, detail)
    # Include a non-sensitive summary for the log
    payload["error"]["extras"] = {"exception_type": exc.__class__.__name__}
    _append_error_to_log(payload)
    return JSONResponse(payload, status_code=500)


# ---------- routes ----------
@app.get(
    "/rooms",
    tags=["rooms"],
    summary="List all rooms",
    description="Returns the room catalog loaded from `data/rooms.json`.",
)
def list_rooms():
    return ROOMS


@app.get(
    "/search",
    tags=["rooms"],
    summary="Search available rooms",
    description=(
        "Returns rooms **without any booking overlap** in the given window.\n\n"
        "**Date/time format**:\n"
        "- `date`: `YYYY-MM-DD`\n"
        "- `start`/`end`: `HH:MM` (24h)\n"
    ),
    responses={
        200: {"description": "List of available rooms"},
        400: {
            "description": "Bad date/time or `end <= start`",
            "model": ErrorEnvelope,
        },
    },
)
def search_rooms(date: str, start: str, end: str):
    start_dt = _parse_dt(date, start)
    end_dt = _parse_dt(date, end)
    _ensure_valid(start_dt, end_dt)
    available = []
    for r in ROOMS:
        if not _has_overlap(r["id"], start_dt, end_dt):
            available.append(r)
    return available


@app.post(
    "/bookings",
    tags=["bookings"],
    summary="Create a booking",
    response_model=BookingOut,
    status_code=201,
    responses={
        201: {"description": "Created"},
        400: {
            "description": "`end` not after `start` or bad payload",
            "model": ErrorEnvelope,
        },
        404: {"description": "Room not found", "model": ErrorEnvelope},
        409: {"description": "Room overlap conflict", "model": ErrorEnvelope},
        422: {
            "description": "Capacity exceeded / Daily cap / Validation error",
            "model": ErrorEnvelope,
        },
    },
)
def create_booking(payload: BookingCreate):
    room = _get_room(payload.room_id)
    _ensure_valid(payload.start, payload.end)
    if payload.group_size > room["capacity"]:
        err(
            "CAPACITY_EXCEEDED",
            "group_size exceeds room capacity",
            hint=f"Room capacity is {room['capacity']}.",
            extras={"room_capacity": room["capacity"]},
            status=422,
        )
    if _has_overlap(payload.room_id, payload.start, payload.end):
        err(
            "OVERLAP_CONFLICT",
            "room already booked for that window",
            hint="Pick a different time or room.",
            extras={"room_id": payload.room_id},
            status=409,
        )
    if _exceeds_daily_hours(payload.user_id, payload.start, payload.end):
        err(
            "DAILY_CAP_EXCEEDED",
            "daily booking hours limit exceeded",
            hint=f"Max per day is {MAX_HOURS_PER_DAY} hours.",
            extras={"max_hours_per_day": MAX_HOURS_PER_DAY},
            status=422,
        )

    booking = {
        "id": _next_id(),
        "user_id": payload.user_id,
        "room_id": payload.room_id,
        "start": payload.start,
        "end": payload.end,
        "group_size": payload.group_size,
    }
    BOOKINGS.append(booking)
    store.save_bookings(BOOKINGS)

    write_confirmation(
        to_email=f"user{payload.user_id}@example.edu",
        booking_id=cast(int, booking["id"]),
    )

    return booking


@app.get(
    "/users/{user_id}/bookings",
    tags=["bookings"],
    summary="List bookings for a user",
    description="Returns all bookings made by the given `user_id`.",
    responses={
        200: {"description": "List of bookings (possibly empty)"},
    },
)
def my_bookings(user_id: int):
    return [b for b in BOOKINGS if b["user_id"] == user_id]


@app.delete(
    "/bookings/{booking_id}",
    tags=["bookings"],
    summary="Cancel a booking",
    status_code=204,
    responses={
        204: {"description": "Cancelled"},
        404: {"description": "Booking not found", "model": ErrorEnvelope},
        422: {
            "description": "Too late to cancel (cutoff window)",
            "model": ErrorEnvelope,
        },
    },
)
def cancel_booking(booking_id: int):
    idx = next((i for i, b in enumerate(BOOKINGS) if b["id"] == booking_id), None)
    if idx is None:
        err(
            "BOOKING_NOT_FOUND",
            "booking not found",
            extras={"booking_id": booking_id},
            status=404,
        )
    b = BOOKINGS[idx]
    now = datetime.now(b["start"].tzinfo)
    if (b["start"] - now) < timedelta(minutes=CANCEL_CUTOFF_MIN):
        err(
            "CANCEL_CUTOFF",
            "cannot cancel within 30 minutes of start",
            hint=f"Cutoff is {CANCEL_CUTOFF_MIN} minutes.",
            extras={"cutoff_minutes": CANCEL_CUTOFF_MIN},
            status=422,
        )
    BOOKINGS.pop(idx)
    store.save_bookings(BOOKINGS)


# ---------- helpers ----------
def _parse_dt(date_str: str, hm: str) -> datetime:
    try:
        return datetime.fromisoformat(f"{date_str}T{hm}")
    except Exception:
        err(
            "BAD_DATETIME_FORMAT",
            "use YYYY-MM-DD for date and HH:MM for time",
            hint="Example: /search?date=2025-11-16&start=13:00&end=14:00",
            status=400,
        )


def _ensure_valid(start: datetime, end: datetime):
    if end <= start:
        err(
            "END_NOT_AFTER_START",
            "end must be after start",
            hint="Ensure end time is later than start time.",
            status=400,
        )


def _get_room(room_id: int) -> dict[str, Any]:
    r = next((r for r in ROOMS if r["id"] == room_id), None)
    if r is None:
        err("ROOM_NOT_FOUND", "room not found", extras={"room_id": room_id}, status=404)
    return cast(dict[str, Any], r)


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
