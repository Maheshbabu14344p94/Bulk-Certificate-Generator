from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from .database import Base

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    event_name = Column(String(180), nullable=False)
    course_name = Column(String(180), nullable=False)
    issuer_name = Column(String(180), nullable=False)
    issue_date = Column(String(20), nullable=False)
    status = Column(String(40), default="queued", nullable=False)
    total = Column(Integer, default=0, nullable=False)
    completed = Column(Integer, default=0, nullable=False)
    failed = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    recipients = relationship("Recipient", back_populates="job", cascade="all, delete-orphan")

class Recipient(Base):
    __tablename__ = "recipients"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    name = Column(String(120), nullable=False)
    email = Column(String(320), nullable=False)
    status = Column(String(30), default="queued", nullable=False)
    file_path = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    job = relationship("Job", back_populates="recipients")
