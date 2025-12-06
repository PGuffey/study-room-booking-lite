import logging
import os
from typing import Optional

from huggingface_hub import InferenceClient
from .storage import FileStore

store = FileStore()
ROOMS = store.load_rooms()

ROOMS_SUMMARY = "; ".join(
    f"Room {r['name']} (id={r['id']}, capacity {r['capacity']}, {r['location']})"
    for r in ROOMS
)

log = logging.getLogger(__name__)

_client: Optional[InferenceClient] = None


def _get_client() -> InferenceClient:
    """
    Lazily create an InferenceClient using env vars.
    This reads HF_API_KEY / HF_MODEL_ID at call time so it works
    even if .env is loaded after import.
    """
    log.info("HF_API_KEY debug: %r", os.getenv("HF_API_KEY"))
    log.info("HF_MODEL_ID debug: %r", os.getenv("HF_MODEL_ID"))

    api_key = os.getenv("HF_API_KEY", "").strip().strip('"').strip("'")
    model_id = os.getenv("HF_MODEL_ID", "google/gemma-2-2b-it").strip().strip('"').strip("'")

    if not api_key:
        raise RuntimeError("HF_API_KEY not configured")

    global _client
    if _client is None:
        log.info("Initializing HF InferenceClient with model %s", model_id)
        _client = InferenceClient(model=model_id, token=api_key)
    return _client



SYSTEM_PROMPT = (
    "You are the AI assistant for a web app called 'Study Room Booking Lite'. "
    "The app lets students browse rooms, search availability, and book or cancel rooms.\n\n"
    f"Here are the study rooms the campus offers: {ROOMS_SUMMARY}.\n\n"
    "You do NOT have live availability data, only this room list. "
    "Suggest rooms based on capacity and location, but do not claim you know if a room is actually free.\n"
    "Be friendly, helpful, and concise (1–4 sentences)."
)


def chat_with_ai(message: str) -> str:
    client = _get_client()

    completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        max_tokens=200,
    )

    reply = completion.choices[0].message.content.strip()
    log.info("AI reply: %s", reply)
    return reply
