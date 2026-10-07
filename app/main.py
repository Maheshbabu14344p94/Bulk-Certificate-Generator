from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine
from .models import Job, Recipient
from .schemas import JobCreate, JobOut, RecipientOut
from .services.jobs import process_job


# ---------------------------------------------------------
# Database
# ---------------------------------------------------------

Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

# Project root:
# Bulk-Certificate-Generator/
BASE_DIR = Path(__file__).resolve().parent.parent

# Static folder:
# Bulk-Certificate-Generator/static/
STATIC_DIR = BASE_DIR / "static"

# Generated certificates:
# Bulk-Certificate-Generator/generated/
GENERATED_DIR = BASE_DIR / "generated"

# Make sure the generated directory exists
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------

app = FastAPI(
    title="Bulk Certificate Generator",
    version="1.0.0",
    description=(
        "Bulk certificate generation API with validation, "
        "background processing, progress tracking and PDF retrieval."
    ),
)


# ---------------------------------------------------------
# Static files
# ---------------------------------------------------------

# THIS IS THE IMPORTANT FIX.
#
# It makes:
#
# /static/app.css
# /static/app.js
#
# available to the browser.

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Database dependency
# ---------------------------------------------------------

def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ---------------------------------------------------------
# Dashboard
# ---------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def dashboard():
    """
    Serve the frontend dashboard.
    """

    index_file = STATIC_DIR / "index.html"

    if not index_file.exists():
        raise HTTPException(
            status_code=500,
            detail="Frontend index.html was not found.",
        )

    return index_file.read_text(encoding="utf-8")


# ---------------------------------------------------------
# Create bulk generation job
# ---------------------------------------------------------

@app.post(
    "/api/jobs",
    response_model=dict,
    status_code=202,
)
def create_job(
    payload: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create one bulk generation job.

    All recipients belong to the same job.
    Certificate generation happens in the background.
    """

    job = Job(
        event_name=payload.event_name,
        course_name=payload.course_name,
        issuer_name=payload.issuer_name,
        issue_date=payload.issue_date.isoformat(),
        total=len(payload.recipients),
        status="queued",
    )

    db.add(job)
    db.flush()

    # Add recipients to the job
    for item in payload.recipients:
        recipient = Recipient(
            job_id=job.id,
            name=item.name,
            email=str(item.email),
        )

        db.add(recipient)

    db.commit()

    # Process the complete bulk job in the background.
    background_tasks.add_task(
        process_job,
        job.id,
        SessionLocal,
    )

    return {
        "job_id": job.id,
        "status": job.status,
    }


# ---------------------------------------------------------
# Get job status / progress
# ---------------------------------------------------------

@app.get(
    "/api/jobs/{job_id}",
    response_model=JobOut,
)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Return current job status and recipient-level progress.
    """

    job = db.get(Job, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    processed = job.completed + job.failed

    progress = (
        round((processed / job.total) * 100, 2)
        if job.total
        else 0
    )

    return {
        "id": job.id,
        "status": job.status,
        "total": job.total,
        "completed": job.completed,
        "failed": job.failed,
        "progress": progress,
        "recipients": [
            RecipientOut(
                id=recipient.id,
                name=recipient.name,
                email=recipient.email,
                status=recipient.status,
                error_message=recipient.error_message,
            )
            for recipient in job.recipients
        ],
    }


# ---------------------------------------------------------
# List generated certificates
# ---------------------------------------------------------

@app.get(
    "/api/jobs/{job_id}/certificates"
)
def list_certificates(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Return certificate availability for every recipient.
    """

    job = db.get(Job, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return {
        "job_id": job_id,
        "certificates": [
            {
                "recipient_id": recipient.id,
                "name": recipient.name,
                "status": recipient.status,
                "download_url": (
                    f"/api/jobs/{job_id}/certificates/{recipient.id}"
                    if recipient.status == "completed"
                    else None
                ),
            }
            for recipient in job.recipients
        ],
    }


# ---------------------------------------------------------
# Download individual certificate
# ---------------------------------------------------------

@app.get(
    "/api/jobs/{job_id}/certificates/{recipient_id}"
)
def download_certificate(
    job_id: int,
    recipient_id: int,
    db: Session = Depends(get_db),
):
    """
    Download a generated PDF certificate.
    """

    recipient = (
        db.query(Recipient)
        .filter(
            Recipient.id == recipient_id,
            Recipient.job_id == job_id,
        )
        .first()
    )

    if not recipient:
        raise HTTPException(
            status_code=404,
            detail="Recipient not found",
        )

    if recipient.status != "completed" or not recipient.file_path:
        raise HTTPException(
            status_code=409,
            detail="Certificate is not available",
        )

    path = Path(recipient.file_path)

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Generated certificate file is missing",
        )

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=path.name,
    )