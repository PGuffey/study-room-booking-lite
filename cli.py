# cli.py
import os, sys, json
import typer
import httpx

app = typer.Typer(add_completion=False)

def resolve_api(api_opt: str | None) -> str:
    # precedence: --api flag > STUDY_API env > default localhost
    return api_opt or os.environ.get("STUDY_API") or "http://127.0.0.1:8000"

def pretty(obj) -> str:
    try:
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        return str(obj)

def handle_response(r: httpx.Response, expect: set[int]) -> int:
    req_id = r.headers.get("X-Request-ID")
    if r.status_code in expect:
        try:
            data = r.json()
            typer.echo(pretty(data))
        except Exception:
            typer.echo(r.text or f"{r.status_code} {r.reason_phrase}")
        if req_id:
            typer.secho(f"(request_id: {req_id})", dim=True)
        return 0
    else:
        # Try structured error payload from API
        try:
            data = r.json()
            err = data.get("error") if isinstance(data, dict) else None
            if isinstance(err, dict):
                code = err.get("code", "HTTP_ERROR")
                msg = err.get("message", r.reason_phrase)
                hint = err.get("hint")
                status = err.get("status", r.status_code)
                typer.secho(f"[{status}] {code}: {msg}", fg=typer.colors.RED, bold=True)
                if hint:
                    typer.secho(f"Hint: {hint}", fg=typer.colors.YELLOW)
                ve = err.get("validation_errors")
                if ve:
                    typer.echo("Validation errors:")
                    for e in ve:
                        loc = ".".join(str(x) for x in e.get("loc", []))
                        typer.echo(f"  • {loc}: {e.get('msg')} ({e.get('type')})")
            else:
                # Fallback to raw
                typer.secho(r.text or f"{r.status_code} {r.reason_phrase}", fg=typer.colors.RED)
        except Exception:
            typer.secho(r.text or f"{r.status_code} {r.reason_phrase}", fg=typer.colors.RED)
        if req_id:
            typer.secho(f"(request_id: {req_id})", dim=True)
        return 1

@app.command()
def rooms(
    api: str = typer.Option(None, "--api", help="Base API URL (or set STUDY_API env var)")
):
    """List available rooms."""
    base = resolve_api(api)
    try:
        r = httpx.get(f"{base}/rooms", timeout=5)
        sys.exit(handle_response(r, {200}))
    except httpx.RequestError as e:
        typer.secho(f"Cannot reach API at {base} ({e.__class__.__name__}): {e}", fg=typer.colors.RED)
        sys.exit(2)

@app.command()
def search(
    date: str = typer.Argument(..., help="YYYY-MM-DD"),
    start: str = typer.Argument(..., help="HH:MM  (24h)"),
    end: str = typer.Argument(..., help="HH:MM  (24h)"),
    api: str = typer.Option(None, "--api", help="Base API URL (or set STUDY_API env var)")
):
    """Search for rooms available in a time window."""
    base = resolve_api(api)
    try:
        r = httpx.get(f"{base}/search", params={"date": date, "start": start, "end": end}, timeout=5)
        sys.exit(handle_response(r, {200}))
    except httpx.RequestError as e:
        typer.secho(f"Cannot reach API at {base} ({e.__class__.__name__}): {e}", fg=typer.colors.RED)
        sys.exit(2)

@app.command()
def book(
    user_id: int,
    room_id: int,
    start_iso: str = typer.Argument(..., help="ISO datetime e.g. 2025-11-02T13:00:00"),
    end_iso: str   = typer.Argument(..., help="ISO datetime e.g. 2025-11-02T14:00:00"),
    group_size: int = typer.Option(1, "--group-size", "-g"),
    api: str = typer.Option(None, "--api", help="Base API URL (or set STUDY_API env var)")
):
    """Create a booking."""
    base = resolve_api(api)
    payload = {"user_id": user_id, "room_id": room_id, "start": start_iso, "end": end_iso, "group_size": group_size}
    try:
        r = httpx.post(f"{base}/bookings", json=payload, timeout=5)
        sys.exit(handle_response(r, {200, 201}))
    except httpx.RequestError as e:
        typer.secho(f"Cannot reach API at {base} ({e.__class__.__name__}): {e}", fg=typer.colors.RED)
        sys.exit(2)

@app.command()
def mine(
    user_id: int,
    api: str = typer.Option(None, "--api", help="Base API URL (or set STUDY_API env var)")
):
    """List bookings for a user."""
    base = resolve_api(api)
    try:
        r = httpx.get(f"{base}/users/{user_id}/bookings", timeout=5)
        sys.exit(handle_response(r, {200}))
    except httpx.RequestError as e:
        typer.secho(f"Cannot reach API at {base} ({e.__class__.__name__}): {e}", fg=typer.colors.RED)
        sys.exit(2)

@app.command()
def cancel(
    booking_id: int,
    api: str = typer.Option(None, "--api", help="Base API URL (or set STUDY_API env var)")
):
    """Cancel a booking by ID."""
    base = resolve_api(api)
    try:
        r = httpx.delete(f"{base}/bookings/{booking_id}", timeout=5)
        if r.status_code == 204:
            typer.echo("OK")
            req_id = r.headers.get("X-Request-ID")
            if req_id:
                typer.secho(f"(request_id: {req_id})", dim=True)
            sys.exit(0)
        sys.exit(handle_response(r, {204}))
    except httpx.RequestError as e:
        typer.secho(f"Cannot reach API at {base} ({e.__class__.__name__}): {e}", fg=typer.colors.RED)
        sys.exit(2)

if __name__ == "__main__":
    app()
