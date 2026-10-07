import os
os.environ["DATABASE_URL"] = "sqlite:///./test_certificates.db"

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
client = TestClient(app)

def test_create_generation_job():
    response = client.post("/api/jobs", json={
        "event_name":"Test Event","course_name":"Python","issuer_name":"Test Org",
        "issue_date":"2026-10-07",
        "recipients":[{"name":"Alice Example","email":"alice@example.com"}]
    })
    assert response.status_code == 202
    assert "job_id" in response.json()

def test_input_validation():
    response = client.post("/api/jobs", json={
        "event_name":"Test","course_name":"Python","issuer_name":"Org",
        "issue_date":"2026-10-07",
        "recipients":[
            {"name":"Alice","email":"same@example.com"},
            {"name":"Bob","email":"same@example.com"}
        ]
    })
    assert response.status_code == 422

def test_job_status_and_progress():
    response = client.post("/api/jobs", json={
        "event_name":"Test","course_name":"Python","issuer_name":"Org",
        "issue_date":"2026-10-07",
        "recipients":[{"name":"Alice","email":"alice2@example.com"}]
    })
    job_id = response.json()["job_id"]
    import time
    for _ in range(20):
        status = client.get(f"/api/jobs/{job_id}")
        assert status.status_code == 200
        if status.json()["progress"] == 100:
            break
        time.sleep(.05)
    assert status.json()["total"] == 1

def test_certificate_generation_and_retrieval():
    response = client.post("/api/jobs", json={
        "event_name":"Test","course_name":"Python","issuer_name":"Org",
        "issue_date":"2026-10-07",
        "recipients":[{"name":"PDF User","email":"pdf@example.com"}]
    })
    job_id = response.json()["job_id"]
    import time
    recipient_id = None
    for _ in range(30):
        data = client.get(f"/api/jobs/{job_id}").json()
        if data["progress"] == 100:
            recipient_id = data["recipients"][0]["id"]
            break
        time.sleep(.05)
    assert recipient_id
    pdf = client.get(f"/api/jobs/{job_id}/certificates/{recipient_id}")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"].startswith("application/pdf")

def test_individual_failure_does_not_cancel_job(monkeypatch):
    from app.services import jobs
    original = jobs.generate_certificate
    calls = {"n": 0}
    def flaky(job, recipient):
        calls["n"] += 1
        if recipient.name == "Bad User":
            raise RuntimeError("simulated generation failure")
        return original(job, recipient)
    monkeypatch.setattr(jobs, "generate_certificate", flaky)
    response = client.post("/api/jobs", json={
        "event_name":"Test","course_name":"Python","issuer_name":"Org",
        "issue_date":"2026-10-07",
        "recipients":[
            {"name":"Bad User","email":"bad@example.com"},
            {"name":"Good User","email":"good@example.com"}
        ]
    })
    job_id = response.json()["job_id"]
    import time
    for _ in range(40):
        data = client.get(f"/api/jobs/{job_id}").json()
        if data["progress"] == 100:
            break
        time.sleep(.05)
    assert data["failed"] == 1
    assert data["completed"] == 1
    assert data["status"] == "completed_with_errors"
