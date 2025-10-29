"""
Tests for FastAPI application endpoints.

This module contains comprehensive tests for the Medinow FastAPI
implementation including chat, calendar, and health endpoints.
"""

import pytest
from datetime import datetime
from httpx import AsyncClient, ASGITransport

from backend.api.fastapi_app import app


@pytest.fixture
def sample_chat_request():
    """Sample chat request data."""
    return {
        "session_id": "test-session-123",
        "message": "Olá, gostaria de agendar uma consulta",
    }


@pytest.fixture
def sample_calendar_request():
    """Sample calendar event request data."""
    return {
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


@pytest.fixture
def sample_slots_request():
    """Sample available slots request data."""
    return {
        "start_date": "2025-10-28",
        "end_date": "2025-10-30",
        "calendar_id": "primary",
        "slot_duration_minutes": 30,
    }


# ============================================================================
# Health Check Tests
# ============================================================================


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint returns API information."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Medinow API"
        assert data["version"] == "0.1.0"
        assert "docs" in data
        assert "health" in data


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data
        assert isinstance(data["services"], dict)
        assert "conversation" in data["services"]
        assert "calendar" in data["services"]


# ============================================================================
# Chat Endpoint Tests
# ============================================================================


@pytest.mark.asyncio
async def test_chat_endpoint_success(sample_chat_request):
    """Test chat endpoint with valid request."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/chat", json=sample_chat_request)
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "response" in data
        assert "timestamp" in data
        assert data["session_id"] == sample_chat_request["session_id"]
        assert isinstance(data["response"], str)
        assert len(data["response"]) > 0


@pytest.mark.asyncio
async def test_chat_endpoint_missing_session_id():
    """Test chat endpoint with missing session_id."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            json={"message": "Hello"}
        )
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_chat_endpoint_empty_session_id():
    """Test chat endpoint with empty session_id."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            json={"session_id": "", "message": "Hello"}
        )
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_chat_endpoint_missing_message():
    """Test chat endpoint with missing message."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            json={"session_id": "test-session"}
        )
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_chat_endpoint_empty_message():
    """Test chat endpoint with empty message."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            json={"session_id": "test-session", "message": ""}
        )
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_chat_endpoint_whitespace_only():
    """Test chat endpoint with whitespace-only message."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            json={"session_id": "test-session", "message": "   "}
        )
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_chat_endpoint_multiple_sessions():
    """Test chat endpoint maintains separate session contexts."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Session 1
        response1 = await client.post(
            "/api/chat",
            json={"session_id": "session-1", "message": "Hello"}
        )
        assert response1.status_code == 200

        # Session 2
        response2 = await client.post(
            "/api/chat",
            json={"session_id": "session-2", "message": "Hi"}
        )
        assert response2.status_code == 200

        # Verify sessions are different
        data1 = response1.json()
        data2 = response2.json()
        assert data1["session_id"] != data2["session_id"]


# ============================================================================
# Calendar Slots Tests
# ============================================================================


@pytest.mark.asyncio
async def test_available_slots_endpoint_structure(sample_slots_request):
    """Test available slots endpoint response structure."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/calendar/available-slots",
            json=sample_slots_request
        )

        # Note: This test assumes calendar service might not be available
        # In that case, we expect 503, otherwise 200
        if response.status_code == 200:
            data = response.json()
            assert "slots" in data
            assert "count" in data
            assert "start_date" in data
            assert "end_date" in data
            assert isinstance(data["slots"], list)
            assert data["count"] == len(data["slots"])
        elif response.status_code == 503:
            # Service unavailable is acceptable if calendar not configured
            assert "detail" in response.json()


@pytest.mark.asyncio
async def test_available_slots_invalid_date_format():
    """Test available slots with invalid date format."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/calendar/available-slots",
            json={
                "start_date": "invalid-date",
                "end_date": "2025-10-30",
                "calendar_id": "primary"
            }
        )
        assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_available_slots_end_before_start():
    """Test available slots with end date before start date."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/calendar/available-slots",
            json={
                "start_date": "2025-10-30",
                "end_date": "2025-10-28",
                "calendar_id": "primary"
            }
        )
        # Should return error (400 or 503 if service unavailable)
        assert response.status_code in [400, 503]


# ============================================================================
# Calendar Booking Tests
# ============================================================================


@pytest.mark.asyncio
async def test_book_appointment_endpoint_structure(sample_calendar_request):
    """Test book appointment endpoint response structure."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/calendar/book",
            json=sample_calendar_request
        )

        # Note: This test assumes calendar service might not be available
        if response.status_code == 200:
            data = response.json()
            assert "event_id" in data
            assert "summary" in data
            assert "start_time" in data
            assert "end_time" in data
            assert "status" in data
            assert "message" in data
        elif response.status_code == 503:
            # Service unavailable is acceptable if calendar not configured
            assert "detail" in response.json()


@pytest.mark.asyncio
async def test_book_appointment_invalid_datetime():
    """Test booking with invalid datetime format."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/calendar/book",
            json={
                "calendar_id": "primary",
                "start_datetime": "invalid-datetime",
                "timezone": "America/Sao_Paulo",
                "event_duration_hour": 1,
                "event_duration_minutes": 0,
                "summary": "Test Event"
            }
        )
        assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_book_appointment_missing_summary():
    """Test booking without summary."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/calendar/book",
            json={
                "calendar_id": "primary",
                "start_datetime": "2025-10-28T14:00:00",
                "timezone": "America/Sao_Paulo",
                "event_duration_hour": 1,
                "event_duration_minutes": 0,
            }
        )
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_book_appointment_invalid_attendee_email():
    """Test booking with invalid attendee email."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/calendar/book",
            json={
                "calendar_id": "primary",
                "start_datetime": "2025-10-28T14:00:00",
                "timezone": "America/Sao_Paulo",
                "event_duration_hour": 1,
                "event_duration_minutes": 0,
                "summary": "Test Event",
                "attendees": ["invalid-email"]
            }
        )
        assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_book_appointment_with_optional_fields():
    """Test booking with all optional fields."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/calendar/book",
            json={
                "calendar_id": "primary",
                "start_datetime": "2025-10-28T14:00:00",
                "timezone": "America/Sao_Paulo",
                "event_duration_hour": 1,
                "event_duration_minutes": 30,
                "summary": "Complete Test Event",
                "description": "This is a test description",
                "location": "Test Location",
                "attendees": ["test@example.com", "test2@example.com"]
            }
        )
        # Should either succeed or fail due to service unavailability
        assert response.status_code in [200, 503]


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.asyncio
async def test_invalid_endpoint():
    """Test accessing non-existent endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/nonexistent")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_method_not_allowed():
    """Test using wrong HTTP method."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/chat")  # Should be POST
        assert response.status_code == 405


@pytest.mark.asyncio
async def test_invalid_json():
    """Test sending invalid JSON."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_full_booking_flow():
    """
    Test complete booking flow: health check -> chat -> get slots -> book.

    This is an integration test that exercises the full API workflow.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        health = await client.get("/api/health")
        assert health.status_code == 200

        # 2. Chat interaction
        chat = await client.post(
            "/api/chat",
            json={
                "session_id": "integration-test",
                "message": "Gostaria de agendar uma consulta"
            }
        )
        assert chat.status_code == 200

        # 3. Get available slots (may fail if calendar not configured)
        slots = await client.post(
            "/api/calendar/available-slots",
            json={
                "start_date": "2025-10-28",
                "end_date": "2025-10-30",
                "calendar_id": "primary"
            }
        )
        # Either succeeds or service unavailable
        assert slots.status_code in [200, 503]

        # 4. If slots available, try booking (may fail if calendar not configured)
        if slots.status_code == 200:
            booking = await client.post(
                "/api/calendar/book",
                json={
                    "calendar_id": "primary",
                    "start_datetime": "2025-10-28T14:00:00",
                    "timezone": "America/Sao_Paulo",
                    "event_duration_hour": 1,
                    "event_duration_minutes": 0,
                    "summary": "Integration Test Appointment",
                    "attendees": ["test@example.com"]
                }
            )
            assert booking.status_code in [200, 503]
