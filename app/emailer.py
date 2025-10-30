from pathlib import Path
from datetime import datetime
OUTBOX = Path("outbox")
OUTBOX.mkdir(exist_ok=True)
def write_confirmation(to_email: str, booking_id: int):
    (OUTBOX / f"booking_{booking_id}.txt").write_text(
        f"To: {to_email} Subject: Booking Confirmation #{booking_id}"
    )