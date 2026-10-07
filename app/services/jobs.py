from pathlib import Path
from sqlalchemy.orm import Session
from ..models import Job, Recipient
from .certificate import generate_certificate

def process_job(job_id: int, session_factory):
    db: Session = session_factory()
    try:
        job = db.get(Job, job_id)
        if not job:
            return
        job.status = "processing"
        db.commit()

        for recipient in job.recipients:
            try:
                recipient.status = "processing"
                db.commit()
                # A deliberately isolated operation: one failure only affects this recipient.
                path = generate_certificate(job, recipient)
                recipient.file_path = str(path)
                recipient.status = "completed"
                job.completed += 1
            except Exception as exc:
                recipient.status = "failed"
                recipient.error_message = str(exc)[:500]
                job.failed += 1
            finally:
                db.commit()

        job.status = "completed" if job.failed == 0 else "completed_with_errors"
        db.commit()
    finally:
        db.close()
