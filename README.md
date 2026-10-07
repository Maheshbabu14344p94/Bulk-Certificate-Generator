# Bulk Certificate Generator

A production-minded FastAPI backend for submitting bulk certificate generation jobs, validating recipients, processing certificates independently, tracking progress, and downloading generated PDFs.

## Stack

- Python 3.11+
- FastAPI
- SQLAlchemy
- SQLite by default / PostgreSQL-ready
- ReportLab for PDF certificates
- Pytest + HTTPX for tests
- HTML/CSS/JavaScript dashboard

## Architecture

The client submits one bulk generation request. The API validates the request, creates a job and recipient records in a relational database, then processes the job in the background.

Each recipient is processed independently. If one certificate fails, other valid recipients continue. The database stores per-recipient status and the aggregate job progress.

For a production deployment, the in-process background task can be replaced with Celery/RQ + Redis without changing the API contract.

## Setup

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Open:

- Dashboard: http://127.0.0.1:8000
- Swagger API docs: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## API

### Create a generation job

`POST /api/jobs`

Example:

```json
{
  "event_name": "Frontend Development Bootcamp",
  "course_name": "Advanced React",
  "issuer_name": "Fermor Academy",
  "issue_date": "2026-10-07",
  "recipients": [
    {"name": "Mahesh Babu", "email": "mahesh@example.com"},
    {"name": "Ananya Rao", "email": "ananya@example.com"}
  ]
}
```

The API returns a job ID immediately. Processing continues in the background.

### Check status

`GET /api/jobs/{job_id}`

Returns totals, completed/failed counts, progress percentage, and individual recipient statuses.

### Retrieve a certificate

`GET /api/jobs/{job_id}/certificates/{recipient_id}`

Successful recipients return the generated PDF.

### List certificates

`GET /api/jobs/{job_id}/certificates`

## Validation and failure handling

- Recipient names must be non-empty and limited to 120 characters.
- Emails must be valid.
- Duplicate emails in the same job are rejected.
- A single generation failure is recorded against that recipient and does not cancel the remaining recipients.
- A job can finish as `completed` or `completed_with_errors`.

## Design decisions

### Why background processing?

Bulk generation can involve expensive PDF rendering. Returning the job ID immediately avoids holding the client connection open for a large batch and provides a natural progress endpoint.

### Why relational storage?

Jobs, recipients, and generated files have clear relationships and transactional state transitions. SQLAlchemy keeps the data layer portable between SQLite and PostgreSQL.

### Why one template?

The assignment explicitly requires one predefined certificate template. The template is intentionally kept simple and reusable instead of introducing a template editor.

## Tests

Run:

```bash
pytest -q
```

The suite covers:

- Creating a generation job
- Input validation
- Certificate generation
- Job status/progress
- Individual certificate failure isolation
- Certificate retrieval

## Project structure

```text
app/
  main.py
  database.py
  models.py
  schemas.py
  services/
    certificate.py
    jobs.py
tests/
  test_api.py
static/
  index.html
  app.css
  app.js
```
