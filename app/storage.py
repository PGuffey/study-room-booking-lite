# app/storage.py
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any, Iterable
from datetime import datetime
import json
import tempfile
import os


class FileStore:
    """
    Simple JSON-backed storage for rooms and bookings.
    - Rooms are static (read at startup) from ../data/rooms.json
    - Bookings are read on startup and saved on every mutation.
    - Datetimes in bookings are serialized as ISO 8601 strings.
    """

    def __init__(self, data_dir: Path | None = None):
        # Default to project_root/data (this file is app/storage.py)
        self.data_dir = data_dir or (Path(__file__).resolve().parent.parent / "data")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.rooms_path = self.data_dir / "rooms.json"
        self.bookings_path = self.data_dir / "bookings.json"

        # Ensure files exist
        if not self.rooms_path.exists():
            # Minimal seed only if missing; you already have a filled rooms.json
            default_rooms = [
                {"id": 1, "name": "Room A", "capacity": 4, "location": "Library L1"},
                {"id": 2, "name": "Room B", "capacity": 6, "location": "Library L2"},
                {
                    "id": 3,
                    "name": "Room C",
                    "capacity": 8,
                    "location": "Engineering 2F",
                },
            ]
            self._atomic_write_json(self.rooms_path, default_rooms)

        if not self.bookings_path.exists():
            self._atomic_write_text(self.bookings_path, "[]")

    # -------------------- Public API --------------------

    def load_rooms(self) -> List[Dict[str, Any]]:
        """Read rooms.json and return a validated list of room dicts."""
        data = self._read_json(self.rooms_path, default=[])
        rooms: List[Dict[str, Any]] = []
        seen_ids: set[int] = set()

        for i, r in enumerate(data):
            try:
                room = self._normalize_room(r)
            except ValueError as ex:
                print(f"[storage] Skipping invalid room at index {i}: {ex}")
                continue
            if room["id"] in seen_ids:
                print(
                    f"[storage] Duplicate room id {room['id']} ignored (keeping first)."
                )
                continue
            seen_ids.add(room["id"])
            rooms.append(room)

        # Keep a stable order by id
        rooms.sort(key=lambda x: x["id"])
        return rooms

    def save_rooms(self, rooms: Iterable[Dict[str, Any]]) -> None:
        """
        Save rooms back to rooms.json.
        (You’re not calling this yet, but it’s ready for future admin endpoints.)
        """
        normalized = [self._normalize_room(r) for r in rooms]
        self._atomic_write_json(self.rooms_path, normalized)

    def load_bookings(self) -> List[Dict[str, Any]]:
        """Read bookings.json and return a list where start/end are datetimes."""
        data = self._read_json(self.bookings_path, default=[])
        bookings: List[Dict[str, Any]] = []
        for i, b in enumerate(data):
            try:
                nb = self._normalize_booking_on_load(b)
                bookings.append(nb)
            except ValueError as ex:
                print(f"[storage] Skipping invalid booking at index {i}: {ex}")
        # Sort by id for stability (not strictly required)
        bookings.sort(key=lambda x: x.get("id", 0))
        return bookings

    def save_bookings(self, bookings: List[Dict[str, Any]]) -> None:
        """Write bookings to bookings.json (datetimes -> ISO 8601 strings)."""
        serializable: List[Dict[str, Any]] = []
        for b in bookings:
            serializable.append(self._serialize_booking_for_save(b))
        self._atomic_write_json(self.bookings_path, serializable)

    # -------------------- Normalizers / Validators --------------------

    @staticmethod
    def _normalize_room(r: Dict[str, Any]) -> Dict[str, Any]:
        """Validate/normalize a room dict."""
        if not isinstance(r, dict):
            raise ValueError("room entry must be an object")

        try:
            rid = int(r["id"])
        except Exception:
            raise ValueError("room.id must be an integer")

        name = str(r.get("name", "")).strip()
        loc = str(r.get("location", "")).strip()
        try:
            cap = int(r["capacity"])
        except Exception:
            raise ValueError("room.capacity must be an integer")

        if rid <= 0:
            raise ValueError("room.id must be positive")
        if not name:
            raise ValueError("room.name is required")
        if cap < 1:
            raise ValueError("room.capacity must be >= 1")
        if not loc:
            raise ValueError("room.location is required")

        return {"id": rid, "name": name, "capacity": cap, "location": loc}

    @staticmethod
    def _normalize_booking_on_load(b: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ISO datetime strings and validate required fields when loading."""
        if not isinstance(b, dict):
            raise ValueError("booking entry must be an object")

        # id is optional historically, but we prefer it
        bid = b.get("id")
        if bid is not None:
            try:
                bid = int(bid)
            except Exception:
                raise ValueError("booking.id must be an integer if present")

        # required fields
        try:
            user_id = int(b["user_id"])
            room_id = int(b["room_id"])
            start_s = b["start"]
            end_s = b["end"]
            group_size = int(b["group_size"])
        except KeyError as ex:
            raise ValueError(f"missing field {ex.args[0]!r}")
        except Exception:
            raise ValueError("invalid types in booking")

        try:
            start_dt = datetime.fromisoformat(str(start_s))
            end_dt = datetime.fromisoformat(str(end_s))
        except Exception:
            raise ValueError("start/end must be ISO 8601 strings")

        if end_dt <= start_dt:
            raise ValueError("end must be after start")
        if group_size < 1:
            raise ValueError("group_size must be >= 1")

        out = {
            "id": bid if bid is not None else 0,
            "user_id": user_id,
            "room_id": room_id,
            "start": start_dt,
            "end": end_dt,
            "group_size": group_size,
        }
        return out

    @staticmethod
    def _serialize_booking_for_save(b: Dict[str, Any]) -> Dict[str, Any]:
        """Convert datetimes to ISO strings before saving."""
        start = b.get("start")
        end = b.get("end")
        if isinstance(start, datetime):
            start = start.isoformat()
        if isinstance(end, datetime):
            end = end.isoformat()

        try:
            bid = int(b.get("id", 0))
        except Exception:
            bid = 0

        return {
            "id": bid,
            "user_id": int(b["user_id"]),
            "room_id": int(b["room_id"]),
            "start": start,
            "end": end,
            "group_size": int(b["group_size"]),
        }

    # -------------------- File helpers --------------------

    def _read_json(self, path: Path, default: Any) -> Any:
        try:
            text = path.read_text(encoding="utf-8")
            return json.loads(text)
        except FileNotFoundError:
            return default
        except json.JSONDecodeError as ex:
            print(f"[storage] JSON parse error in {path.name}: {ex}")
            return default

    def _atomic_write_json(self, path: Path, obj: Any) -> None:
        data = json.dumps(obj, indent=2)
        self._atomic_write_text(path, data)

    @staticmethod
    def _atomic_write_text(path: Path, data: str) -> None:
        """
        Write to a temporary file in the same directory, then replace.
        Works on Windows + POSIX.
        """
        dir_ = path.parent
        dir_.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=dir_, delete=False
        ) as tf:
            tmp_name = tf.name
            tf.write(data)
            tf.flush()
            os.fsync(tf.fileno())
        # Replace atomically
        os.replace(tmp_name, path)
