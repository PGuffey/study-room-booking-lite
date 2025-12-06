# Study Room Booking – Lite

This project was built as part of a university course.  
The goal wasn’t to create a massive application — the focus was **simplicity**,  
but with enough technical variety to demonstrate a _wide breadth_ of tools, patterns,  
and real-world development practices.

At its core, this is a **file-based room booking application**.  
Nothing fancy — no databases, no microservices — just JSON files, clean API design,  
and a straightforward FastAPI backend that’s easy to understand and easy to build on.

Even though the app itself stays intentionally simple, the project uses a surprising  
amount of modern tooling to show competence across the stack:

### Technologies & Tools Used

- **FastAPI** – backend framework
- **Python 3.11+** – main language
- **Vanilla HTML + JS frontend** – lightweight, fetch-based UI
- **Typer CLI** – developer command-line interface
- **HuggingFace Inference API** – small AI assistant for room suggestions
- **JSON file persistence** – no database required
- **Docker & Docker Compose** – containerized runtime
- **GitHub Actions CI** – automated linting, typing, tests, import checks
- **ruff** – formatting + linting
- **mypy** – static type checking
- **pytest** – smoke testing

The entire point was to build something that:

- works end-to-end
- is easy to test
- is easy to read
- demonstrates real tooling used in modern development
- and is small enough that you can understand the whole codebase in an hour

---

# Quick Start (Local)

`bash
pip install -r requirements.txt
uvicorn app.main:app --reload
`

Frontend: http://127.0.0.1:8000/  
Docs: http://127.0.0.1:8000/docs

---

# Run with Docker

Found at:

> https://hub.docker.com/repository/docker/pkguffey1/study-room-booking-lite/general

`bash
docker compose build
docker compose up
`

Visit the app at:

> http://localhost:8000/

---

# Full Usage Guide

For **complete instructions**, including:

- CLI usage
- AI assistant
- Docker commands
- Curl examples
- Troubleshooting

👉 **See the full usage guide here:**  
👉 **[usage.md](usage.md)**

---

# License

MIT – purely educational project.
