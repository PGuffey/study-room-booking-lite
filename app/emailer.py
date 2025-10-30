# app/emailer.py
from pathlib import Path
from datetime import datetime

# Always write into ../data/outbox relative to this file
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTBOX = DATA_DIR / "outbox"
OUTBOX.mkdir(parents=True, exist_ok=True)

def write_confirmation(to_email: str, booking_id: int):
    path = OUTBOX / f"booking_{booking_id}.txt"
    content = (
        f"To: {to_email}\n"
        f"Subject: Booking Confirmation #{booking_id}\n\n"
        f"Your booking #{booking_id} has been recorded at {datetime.now().isoformat()}"
    )
    path.write_text(content, encoding="utf-8")
    print(f"[EMAIL] Wrote confirmation to {path}")
