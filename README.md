# Practical Task – Mini Notes REST API + Webhook Ingest

Dear candidate for Python and Automation Intern in DTSE,

Thank you for your time and interest in our position.
This small practical exercise is designed to reflect a typical intern-level backend task that you would encounter working with in our team: building a small REST API and a simple integration (webhook) endpoint.

---

## Goal
Build a small REST API for managing **notes**, and add **one webhook endpoint** that can create a note from an incoming request (simulating an automation tool such as n8n / Power Automate).

We care most about **clean, understandable code**, correct API behavior, and a README that lets us run it quickly.

---

## Tech Requirements (minimal)
- **Python 3.10+**
- Framework: **FastAPI** (preferred) or Flask
- Persistence:
  - **Required:** In-memory storage (list/dict) is totally fine
  - **Bonus:** SQLite or PostgreSQL (optional)

> You can keep everything simple. Bonus items are *not* required.

---

## Data Model (simple)
A **Note** should contain at least:
- `id` (int or UUID)
- `title` (string, required)
- `content` (string, optional)
- `tags` (list of strings, optional)
- `created_at` (timestamp)

---

## Required API Endpoints

### 1) Create a note
`POST /notes`

Request body:
```json
{ "title": "Buy milk", "content": "2L", "tags": ["shopping"] }
```

Response (example):
```json
{ "id": 1, "title": "Buy milk", "content": "2L", "tags": ["shopping"], "created_at": "2026-02-16T12:34:56Z" }
```

Expected behavior:
- Validate required fields (title required)
- Return **201 Created** on success

---

### 2) List notes
`GET /notes`

Support these optional query parameters:
- `q` – search in `title` and `content` (case-insensitive)
- `tag` – filter notes that contain a given tag

Examples:
- `GET /notes?q=milk`
- `GET /notes?tag=shopping`

---

### 3) Get a single note
`GET /notes/{id}`

- Return **404 Not Found** if the note does not exist.

---

### 4) Delete a note
`DELETE /notes/{id}`

- If deleted successfully, return **204 No Content** (or 200 is acceptable)
- If not found, return **404 Not Found**

---

## Required Webhook

### 5) Create a note via webhook
`POST /webhooks/note`

Request body:
```json
{
  "source": "n8n",
  "message": "Reminder: submit timesheet",
  "tags": ["admin"]
}
```

Required behavior:
- Create a new note from the webhook payload:
  - `title` = first 40 characters of `message` (or the whole message if shorter)
  - `content` = full `message`
  - `tags` = provided tags
  - (optional) append a tag like `source:n8n` based on `source`
- Return the created note (or at minimum `{ "id": ... }`)

Validation:
- `message` is required

### Optional security (bonus)
Support a shared secret header:
- Header: `X-Webhook-Token`
- Compare against env var `WEBHOOK_TOKEN`
- If missing or wrong → **401 Unauthorized**

---

## Error Handling & Validation (bonus)
- `title` required for `POST /notes`, max length e.g. 100
- `message` required for `POST /webhooks/note`
- Use meaningful HTTP status codes:
  - 201, 200, 204
  - 401 (if webhook token is implemented)
  - 404 for missing note
  - 422 (or similar) for validation errors

---

## Tests (minimum)
Please include **at least 2 automated tests** (pytest recommended):
1. Create note → retrieve it
2. Webhook call → creates a note → appears in `GET /notes`

---

## Deliverables
Please submit **either**:
- A link to a Git repository (preferred), **or**
- A ZIP archive containing the project

Your submission should include:
- Source code
- `README.md` (this file) updated with your exact run instructions
- Tests

Bonus items are welcome but not required.

---

## Bonus Ideas (optional)
Pick any (or none):
- Add `PUT /notes/{id}` to update a note
- Add pagination: `GET /notes?limit=&offset=`
- Persist notes in SQLite or PostgreSQL
- Store a simple webhook event log (e.g., last 20 payloads in memory)
- Add idempotency: if header `Idempotency-Key` repeats, do not create a duplicate note

---

## How to Run (example)
> Replace the commands below with what matches your project structure.

### Create and activate virtual environment
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run the API (FastAPI example)
```bash
uvicorn app.main:app --reload --port 8000
```

API docs (FastAPI):
- http://localhost:8000/docs

---

## Example curl commands

### Create a note
```bash
curl -X POST http://localhost:8000/notes \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy milk","content":"2L","tags":["shopping"]}'
```

### List notes
```bash
curl http://localhost:8000/notes
```

### Search notes
```bash
curl "http://localhost:8000/notes?q=milk"
```

### Filter by tag
```bash
curl "http://localhost:8000/notes?tag=shopping"
```

### Create note via webhook
```bash
curl -X POST http://localhost:8000/webhooks/note \
  -H "Content-Type: application/json" \
  -d '{"source":"n8n","message":"Reminder: submit timesheet","tags":["admin"]}'
```

### Webhook with token (if implemented)
```bash
curl -X POST http://localhost:8000/webhooks/note \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Token: your-token" \
  -d '{"source":"n8n","message":"Reminder: submit timesheet","tags":["admin"]}'
```

---

## What we evaluate
- Correctness of endpoints and status codes
- Code readability and structure
- Input validation and basic error handling
- Ability to run the solution easily from README
- Tests (even a couple are enough)

Good luck — we’re looking forward to reviewing your solution!
