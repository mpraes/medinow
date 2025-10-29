"""
Pydantic schemas for FastAPI request and response validation.

This module defines all data models used in the API with comprehensive
type hints and validation rules for Python 3.13+.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, EmailStr, field_validator


# ============================================================================
# Chat Endpoints
# ============================================================================


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    session_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique identifier for the conversation session (e.g., WhatsApp ID)",
        examples=["whatsapp:+5511999999999"],
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="User message text",
        examples=["Olá, gostaria de agendar uma consulta"],
    )

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """Validate session_id is not empty after stripping."""
        if not v.strip():
            raise ValueError("session_id cannot be empty or whitespace only")
        return v.strip()

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate message is not empty after stripping."""
        if not v.strip():
            raise ValueError("message cannot be empty or whitespace only")
        return v.strip()


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    session_id: str = Field(
        ...,
        description="Session identifier for this conversation",
    )
    response: str = Field(
        ...,
        description="Bot's response message",
        examples=["Olá! Como posso ajudá-lo a agendar uma consulta?"],
    )
    timestamp: datetime = Field(
        ...,
        description="Timestamp of the response",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "whatsapp:+5511999999999",
                    "response": "Olá! Como posso ajudá-lo a agendar uma consulta?",
                    "timestamp": "2025-10-28T15:30:00",
                }
            ]
        }
    }


# ============================================================================
# Calendar Event Management
# ============================================================================


class CalendarEventRequest(BaseModel):
    """Request model for creating a calendar event."""

    calendar_id: str = Field(
        default="primary",
        description="Google Calendar ID ('primary' for main calendar)",
        examples=["primary"],
    )
    start_datetime: str = Field(
        ...,
        description="Event start datetime in ISO format (YYYY-MM-DDTHH:MM:SS)",
        examples=["2025-10-28T14:00:00"],
    )
    timezone: str = Field(
        default="America/Sao_Paulo",
        description="Timezone for the event",
        examples=["America/Sao_Paulo", "America/New_York"],
    )
    event_duration_hour: int = Field(
        default=0,
        ge=0,
        le=23,
        description="Event duration in hours",
    )
    event_duration_minutes: int = Field(
        default=30,
        ge=0,
        le=59,
        description="Event duration in minutes",
    )
    summary: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Event title/summary",
        examples=["Consulta médica - Dr. Silva"],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=8192,
        description="Event description (optional)",
        examples=["Consulta de rotina com o paciente João"],
    )
    location: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Event location (optional)",
        examples=["Clínica Saúde, Rua Principal 123, Porto Feliz"],
    )
    attendees: Optional[list[str]] = Field(
        default=None,
        description="List of attendee email addresses",
        examples=[["patient@example.com", "doctor@clinic.com"]],
    )

    @field_validator("start_datetime")
    @classmethod
    def validate_datetime_format(cls, v: str) -> str:
        """Validate datetime is in correct ISO format."""
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError(
                "start_datetime must be in ISO format: YYYY-MM-DDTHH:MM:SS"
            )
        return v

    @field_validator("attendees")
    @classmethod
    def validate_attendees(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Validate attendee emails are valid."""
        if v is None:
            return v

        # Basic email validation
        for email in v:
            if "@" not in email or "." not in email.split("@")[1]:
                raise ValueError(f"Invalid email address: {email}")

        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "calendar_id": "primary",
                    "start_datetime": "2025-10-28T14:00:00",
                    "timezone": "America/Sao_Paulo",
                    "event_duration_hour": 1,
                    "event_duration_minutes": 0,
                    "summary": "Consulta médica - Dr. Silva",
                    "description": "Consulta de rotina",
                    "location": "Clínica Saúde, Porto Feliz",
                    "attendees": ["patient@example.com"],
                }
            ]
        }
    }


class CalendarEventResponse(BaseModel):
    """Response model for calendar event operations."""

    event_id: str = Field(
        ...,
        description="Google Calendar event ID",
    )
    summary: str = Field(
        ...,
        description="Event title",
    )
    start_time: str = Field(
        ...,
        description="Event start time in ISO format",
    )
    end_time: str = Field(
        ...,
        description="Event end time in ISO format",
    )
    status: str = Field(
        ...,
        description="Event status (confirmed, tentative, cancelled)",
        examples=["confirmed"],
    )
    message: str = Field(
        ...,
        description="Success or error message",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "event_id": "abc123def456",
                    "summary": "Consulta médica - Dr. Silva",
                    "start_time": "2025-10-28T14:00:00",
                    "end_time": "2025-10-28T15:00:00",
                    "status": "confirmed",
                    "message": "Appointment booked successfully",
                }
            ]
        }
    }


# ============================================================================
# Available Slots
# ============================================================================


class AvailableSlotsRequest(BaseModel):
    """Request model for querying available appointment slots."""

    start_date: str = Field(
        ...,
        description="Start date for availability search (YYYY-MM-DD)",
        examples=["2025-10-28"],
    )
    end_date: str = Field(
        ...,
        description="End date for availability search (YYYY-MM-DD)",
        examples=["2025-10-30"],
    )
    calendar_id: str = Field(
        default="primary",
        description="Google Calendar ID",
    )
    slot_duration_minutes: int = Field(
        default=30,
        ge=15,
        le=480,
        description="Desired slot duration in minutes",
    )

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date is in correct format."""
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("Date must be in ISO format: YYYY-MM-DD")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "start_date": "2025-10-28",
                    "end_date": "2025-10-30",
                    "calendar_id": "primary",
                    "slot_duration_minutes": 30,
                }
            ]
        }
    }


class TimeSlot(BaseModel):
    """Model for a single time slot."""

    start: str = Field(
        ...,
        description="Slot start time in ISO format",
    )
    end: str = Field(
        ...,
        description="Slot end time in ISO format",
    )
    available: bool = Field(
        default=True,
        description="Whether this slot is available for booking",
    )


class AvailableSlotsResponse(BaseModel):
    """Response model for available slots query."""

    slots: list[TimeSlot] = Field(
        ...,
        description="List of available time slots",
    )
    count: int = Field(
        ...,
        ge=0,
        description="Total number of available slots",
    )
    start_date: str = Field(
        ...,
        description="Start date of search range",
    )
    end_date: str = Field(
        ...,
        description="End date of search range",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "slots": [
                        {
                            "start": "2025-10-28T09:00:00",
                            "end": "2025-10-28T09:30:00",
                            "available": True,
                        },
                        {
                            "start": "2025-10-28T09:30:00",
                            "end": "2025-10-28T10:00:00",
                            "available": True,
                        },
                    ],
                    "count": 2,
                    "start_date": "2025-10-28",
                    "end_date": "2025-10-28",
                }
            ]
        }
    }


# ============================================================================
# Health Check
# ============================================================================


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(
        ...,
        description="Overall API status",
        examples=["healthy", "degraded", "unhealthy"],
    )
    timestamp: datetime = Field(
        ...,
        description="Health check timestamp",
    )
    services: dict[str, bool] = Field(
        ...,
        description="Status of individual services",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "timestamp": "2025-10-28T15:30:00",
                    "services": {
                        "conversation": True,
                        "calendar": True,
                    },
                }
            ]
        }
    }
