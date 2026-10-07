from datetime import date
from pydantic import BaseModel, EmailStr, Field, field_validator

class RecipientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Recipient name is required")
        return value

class JobCreate(BaseModel):
    event_name: str = Field(min_length=2, max_length=180)
    course_name: str = Field(min_length=2, max_length=180)
    issuer_name: str = Field(min_length=2, max_length=180)
    issue_date: date
    recipients: list[RecipientCreate] = Field(min_length=1, max_length=5000)

    @field_validator("event_name", "course_name", "issuer_name")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("recipients")
    @classmethod
    def unique_emails(cls, value):
        emails = [str(item.email).lower() for item in value]
        if len(emails) != len(set(emails)):
            raise ValueError("Duplicate recipient emails are not allowed")
        return value

class RecipientOut(BaseModel):
    id: int
    name: str
    email: str
    status: str
    error_message: str | None = None

class JobOut(BaseModel):
    id: int
    status: str
    total: int
    completed: int
    failed: int
    progress: float
    recipients: list[RecipientOut]
