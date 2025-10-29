"""
FastAPI application for Medinow chatbot with Composio Calendar integration.

This module provides REST endpoints for chatbot conversations and calendar operations.
Implements modern Python 3.13+ patterns with async support and comprehensive error handling.
"""

import logging
import traceback
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, Union

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import uvicorn
from twilio.twiml.messaging_response import MessagingResponse

from backend.api.schemas import (
    ChatRequest,
    ChatResponse,
    CalendarEventRequest,
    CalendarEventResponse,
    AvailableSlotsRequest,
    AvailableSlotsResponse,
    HealthResponse,
)
# Import calendar service implementation
from backend.api.services.simple_composio_calendar_service import SimpleComposioCalendarService
from backend.agents.conversation import ConversationManager
from backend.integrations.twilio.webhook_handler import TwilioWebhookHandler, format_whatsapp_message
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fastapi_app")

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    global calendar_service
    # Startup
    logger.info("Starting Medinow FastAPI application...")

    # Initialize calendar service
    try:
        logger.info("Initializing SimpleComposioCalendarService...")
        calendar_service = SimpleComposioCalendarService()
        logger.info("✅ Calendar service initialized successfully")
    except Exception as e:
        logger.error(f"⚠️ Calendar service initialization failed: {e}")
        logger.error("Calendar features will be unavailable")

    yield

    # Shutdown
    logger.info("Shutting down Medinow FastAPI application...")


# Initialize FastAPI app
app = FastAPI(
    title="Medinow API",
    description="Medical appointment booking chatbot with WhatsApp integration and Google Calendar",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
conversation_manager = ConversationManager()
calendar_service: Optional[SimpleComposioCalendarService] = None
twilio_webhook_handler = TwilioWebhookHandler(auth_token=os.getenv('TWILIO_AUTH_TOKEN'))


# Improved error handling for the API
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed error messages."""
    errors = []
    for error in exc.errors():
        error_detail = {
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"],
        }
        errors.append(error_detail)

    logger.warning(f"Validation error: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error in request",
            "errors": errors
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors with detailed logging."""
    error_id = datetime.utcnow().isoformat()
    logger.error(f"Unhandled exception [{error_id}]: {str(exc)}")
    logger.error(traceback.format_exc())

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "error": str(exc),
            "error_id": error_id,
            "help": "Please check server logs for more information"
        },
    )


@app.get("/", response_model=dict[str, str])
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "message": "Medinow API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint to verify API status.

    Returns:
        HealthResponse: Current API status and service availability
    """
    calendar_available = calendar_service is not None and calendar_service.is_available()

    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        services={
            "conversation": True,
            "calendar": calendar_available,
        },
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint for conversational interactions.

    Handles user messages, maintains conversation state, and integrates with
    calendar functionality when needed.

    Args:
        request: ChatRequest with session_id and message

    Returns:
        ChatResponse: Bot response with optional calendar data

    Raises:
        HTTPException: If session_id or message is invalid
    """
    if not request.session_id or not request.session_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id is required and cannot be empty",
        )

    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="message is required and cannot be empty",
        )

    try:
        # Process message through conversation manager
        response_text = await conversation_manager.handle_incoming_message(
            session_id=request.session_id,
            message_text=request.message,
        )

        # Build response
        return ChatResponse(
            session_id=request.session_id,
            response=response_text,
            timestamp=datetime.utcnow(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}",
        )


@app.post("/api/calendar/available-slots", response_model=AvailableSlotsResponse)
async def get_available_slots(request: AvailableSlotsRequest) -> AvailableSlotsResponse:
    """
    Retrieve available appointment slots from Google Calendar.

    Args:
        request: AvailableSlotsRequest with date range and optional filters

    Returns:
        AvailableSlotsResponse: List of available time slots

    Raises:
        HTTPException: If calendar service is unavailable or request is invalid
    """
    if calendar_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Calendar service is not available",
        )

    try:
        slots = await calendar_service.get_available_slots(
            start_date=request.start_date,
            end_date=request.end_date,
            calendar_id=request.calendar_id,
        )

        return AvailableSlotsResponse(
            slots=slots,
            count=len(slots),
            start_date=request.start_date,
            end_date=request.end_date,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving available slots: {str(e)}",
        )


@app.post("/api/calendar/book", response_model=CalendarEventResponse)
async def book_appointment(request: CalendarEventRequest) -> CalendarEventResponse:
    """
    Book a new appointment in Google Calendar.

    Creates a calendar event with the provided details including attendees,
    description, and location.

    Args:
        request: CalendarEventRequest with event details

    Returns:
        CalendarEventResponse: Created event details with confirmation

    Raises:
        HTTPException: If calendar service is unavailable or booking fails
    """
    if calendar_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Calendar service is not available",
        )

    try:
        event = await calendar_service.create_event(
            calendar_id=request.calendar_id,
            start_datetime=request.start_datetime,
            timezone=request.timezone,
            duration_hours=request.event_duration_hour,
            duration_minutes=request.event_duration_minutes,
            summary=request.summary,
            description=request.description,
            location=request.location,
            attendees=request.attendees,
        )

        return CalendarEventResponse(
            event_id=event.get("id", ""),
            summary=event.get("summary", ""),
            start_time=event.get("start", {}).get("dateTime", ""),
            end_time=event.get("end", {}).get("dateTime", ""),
            status="confirmed",
            message="Appointment booked successfully",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error booking appointment: {str(e)}",
        )


@app.post("/api/test/chat")
async def test_chat_endpoint(request: dict):
    """
    Endpoint de teste para simular conversas do WhatsApp sem Twilio.
    
    Body esperado:
    {
        "phone": "+5515991367797",
        "message": "Olá"
    }
    """
    try:
        phone = request.get('phone', '+5515991367797')
        message = request.get('message', '')
        
        if not message:
            return {"error": "Message is required"}
        
        # Simular session_id baseado no telefone
        session_id = phone.replace('+', '').replace(' ', '')
        
        # Processar mensagem
        response_text = await conversation_manager.handle_incoming_message(
            session_id=session_id,
            message_text=message,
        )
        
        return {
            "session_id": session_id,
            "user_message": message,
            "bot_response": response_text,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in test chat: {e}")
        return {"error": str(e)}


@app.post("/api/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    WhatsApp webhook endpoint for Twilio integration.

    Receives incoming WhatsApp messages from Twilio, processes them through
    the conversation manager, and returns TwiML-formatted responses.

    Args:
        request: FastAPI Request object with Twilio webhook data

    Returns:
        TwiML XML response for WhatsApp

    Raises:
        HTTPException: If webhook validation fails or message processing errors occur
    """
    try:
        logger.info("Received WhatsApp webhook request")
        
        # Get form data directly from request
        form_data = await request.form()
        logger.info(f"Raw form data keys: {list(form_data.keys())}")
        
        # Extract message data
        from_number = str(form_data.get('From', ''))
        to_number = str(form_data.get('To', ''))
        message_body = str(form_data.get('Body', ''))
        message_sid = str(form_data.get('MessageSid', ''))
        
        logger.info(f"Extracted - From: {from_number}, To: {to_number}, Body: {message_body}, SID: {message_sid}")
        
        # Validate required fields
        if not from_number or not message_body:
            logger.warning("Missing required fields in webhook data")
            error_response = MessagingResponse()
            error_response.message("Erro ao processar mensagem.")
            from fastapi.responses import Response
            return Response(
                content=str(error_response),
                media_type="application/xml",
                status_code=200
            )

        # Get session ID from phone number (remove whatsapp: prefix and +)
        session_id = from_number.replace('whatsapp:', '').replace('+', '')

        # Process message through conversation manager
        response_text = await conversation_manager.handle_incoming_message(
            session_id=session_id,
            message_text=message_body,
        )

        logger.info(f"Generated response: {response_text}")

        # Create TwiML response
        twiml = MessagingResponse()
        twiml.message(response_text)
        
        twiml_content = str(twiml)
        logger.info(f"Generated TwiML response: {twiml_content}")
        logger.info(f"Sent WhatsApp response to {from_number}")

        # Return TwiML response with correct content type
        from fastapi.responses import Response
        return Response(
            content=twiml_content,
            media_type="application/xml",
            status_code=200
        )

    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}", exc_info=True)
        # Return error response in TwiML format
        error_twiml = MessagingResponse()
        error_twiml.message(
            "Desculpe, ocorreu um erro ao processar sua mensagem. "
            "Por favor, tente novamente em alguns instantes."
        )
        from fastapi.responses import Response
        return Response(
            content=str(error_twiml),
            media_type="application/xml",
            status_code=200
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "error": str(exc),
        },
    )


def create_twiml_response(message: str) -> str:
    """
    Create a TwiML response for WhatsApp messages.
    
    Args:
        message: The message text to send back
        
    Returns:
        TwiML XML string
    """
    response = MessagingResponse()
    response.message(message)
    return str(response)


def create_twiml_error_response(error_message: str = "Erro no processamento da mensagem") -> str:
    """
    Create a TwiML error response.
    
    Args:
        error_message: Error message to send back
        
    Returns:
        TwiML XML string
    """
    response = MessagingResponse()
    response.message(error_message)
    return str(response)


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = True):
    """
    Run the FastAPI server using uvicorn.

    Args:
        host: Server host address
        port: Server port
        reload: Enable auto-reload for development
    """
    uvicorn.run(
        "backend.api.fastapi_app:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    run_server()
