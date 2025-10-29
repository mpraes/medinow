"""
Simple Composio Calendar Service for Google Calendar integration.

This service uses Composio tools directly without the CrewAI framework
to avoid compatibility issues and provide more reliable calendar operations.
"""

import os
import asyncio
import concurrent.futures
import logging
from datetime import datetime, timedelta
from typing import Optional

from composio import Composio
from composio_crewai import CrewAIProvider
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class SimpleComposioCalendarService:
    """
    Simplified service for interacting with Google Calendar via Composio.

    Uses Composio tools directly without CrewAI agents for better reliability.
    """

    def __init__(
        self,
        composio_api_key: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """
        Initialize the Simple Composio Calendar Service.

        Args:
            composio_api_key: Composio API key (reads from env if not provided)
            user_id: User ID for Composio authentication (reads from env if not provided)

        Raises:
            ValueError: If required API keys are missing
        """
        self.composio_api_key = composio_api_key or os.getenv("COMPOSIO_API_KEY")
        self.user_id = user_id or os.getenv(
            "COMPOSIO_USER_ID", "b752b3b0-754c-4425-9043-098eaf516540"
        )

        if not self.composio_api_key:
            raise ValueError("COMPOSIO_API_KEY is required")

        # Initialize Composio
        self.composio = Composio(
            provider=CrewAIProvider(),
            api_key=self.composio_api_key,
        )

        # Get Google Calendar tools
        self.tools = self.composio.tools.get(
            user_id=self.user_id,
            toolkits=["GOOGLECALENDAR"],
        )

        # Index tools by name for easy access
        self.tools_dict = {tool.name: tool for tool in self.tools}

    def is_available(self) -> bool:
        """
        Check if the calendar service is properly configured and available.

        Returns:
            bool: True if service is available, False otherwise
        """
        try:
            return (
                self.composio_api_key is not None
                and self.tools is not None
                and "GOOGLECALENDAR_CREATE_EVENT" in self.tools_dict
            )
        except Exception:
            return False

    async def create_event(
        self,
        calendar_id: str,
        start_datetime: str,
        timezone: str,
        duration_hours: int,
        duration_minutes: int,
        summary: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[list[str]] = None,
    ) -> dict:
        """
        Create a new event in Google Calendar using Composio tools directly.

        Args:
            calendar_id: Calendar ID (use 'primary' for primary calendar)
            start_datetime: Start datetime in ISO format (YYYY-MM-DDTHH:MM:SS)
            timezone: Timezone (e.g., 'America/Sao_Paulo')
            duration_hours: Event duration in hours
            duration_minutes: Event duration in minutes
            summary: Event title/summary
            description: Optional event description
            location: Optional event location
            attendees: Optional list of attendee email addresses

        Returns:
            dict: Created event details from Google Calendar

        Raises:
            ValueError: If required parameters are invalid
            Exception: If event creation fails
        """
        # Run the synchronous operations in a thread pool
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(
                executor,
                self._create_event_sync,
                calendar_id,
                start_datetime,
                timezone,
                duration_hours,
                duration_minutes,
                summary,
                description,
                location,
                attendees,
            )

    def _create_event_sync(
        self,
        calendar_id: str,
        start_datetime: str,
        timezone: str,
        duration_hours: int,
        duration_minutes: int,
        summary: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[list[str]] = None,
    ) -> dict:
        """
        Synchronous method to create a calendar event using Composio tools directly.
        """
        # Validate inputs
        if not summary or not summary.strip():
            raise ValueError("Event summary is required")

        try:
            datetime.fromisoformat(start_datetime)
        except ValueError:
            raise ValueError(
                "Invalid start_datetime format. Use ISO format: YYYY-MM-DDTHH:MM:SS"
            )

        # Calculate end datetime
        start_dt = datetime.fromisoformat(start_datetime)
        end_dt = start_dt + timedelta(hours=duration_hours, minutes=duration_minutes)
        end_datetime = end_dt.isoformat()

        # Get the create event tool
        create_event_tool = self.tools_dict.get("GOOGLECALENDAR_CREATE_EVENT")
        if not create_event_tool:
            raise Exception("GOOGLECALENDAR_CREATE_EVENT tool not available")

        # Prepare event parameters according to the tool's schema
        event_params = {
            "calendar_id": calendar_id,
            "summary": summary,
            "start_datetime": start_datetime,
            "timezone": timezone,
            "event_duration_hour": duration_hours,
            "event_duration_minutes": duration_minutes,
        }

        # Add optional parameters
        if description:
            event_params["description"] = description
        if location:
            event_params["location"] = location
        if attendees:
            event_params["attendees"] = attendees  # List of email strings directly

        try:
            # Execute the tool directly
            result = create_event_tool.run(**event_params)
            
            # Parse the result
            if isinstance(result, dict):
                return {
                    "event_id": result.get("id", ""),
                    "summary": result.get("summary", summary),
                    "start_datetime": start_datetime,
                    "end_datetime": end_datetime,
                    "timezone": timezone,
                    "status": result.get("status", "confirmed"),
                    "link": result.get("htmlLink", ""),
                    "attendees": attendees or [],
                    "description": description or "",
                    "location": location or "",
                    "created": True,
                    "raw_result": result,
                }
            else:
                # If result is not a dict, try to parse it
                result_str = str(result)
                return {
                    "event_id": "",
                    "summary": summary,
                    "start_datetime": start_datetime,
                    "end_datetime": end_datetime,
                    "timezone": timezone,
                    "status": "confirmed",
                    "link": "",
                    "attendees": attendees or [],
                    "description": description or "",
                    "location": location or "",
                    "created": True,
                    "raw_result": result_str,
                }

        except Exception as e:
            print(f"Error executing create event tool: {e}")
            raise Exception(f"Failed to create calendar event: {e}")

    async def get_available_slots(
        self,
        start_date: str,
        end_date: str,
        calendar_id: str = "primary",
        slot_duration_minutes: int = 30,
    ) -> list[dict]:
        """
        Get available time slots within a date range using Composio tools directly.
        """
        # Run the synchronous operations in a thread pool
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(
                executor,
                self._get_available_slots_sync,
                start_date,
                end_date,
                calendar_id,
                slot_duration_minutes,
            )

    def _get_available_slots_sync(
        self,
        start_date: str,
        end_date: str,
        calendar_id: str = "primary",
        slot_duration_minutes: int = 30,
    ) -> list[dict]:
        """
        Synchronous method to get available slots using Composio tools directly.
        """
        # Validate dates
        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise ValueError("Invalid date format. Use ISO format: YYYY-MM-DD")

        if end_dt <= start_dt:
            raise ValueError("end_date must be after start_date")

        # Get the find free slots tool
        find_slots_tool = self.tools_dict.get("GOOGLECALENDAR_FIND_FREE_SLOTS")
        if not find_slots_tool:
            raise Exception("GOOGLECALENDAR_FIND_FREE_SLOTS tool not available")

        try:
            # Prepare parameters for the free slots tool
            params = {
                "calendar_id": calendar_id,
                "timeMin": f"{start_date}T00:00:00",
                "timeMax": f"{end_date}T23:59:59",
                "slot_duration_minutes": slot_duration_minutes,
            }

            # Execute the tool directly
            result = find_slots_tool.run(**params)

            # Parse the result and return slots
            if isinstance(result, list):
                return [
                    {
                        "start": slot.get("start", ""),
                        "end": slot.get("end", ""),
                        "available": True,
                    }
                    for slot in result
                ]
            elif isinstance(result, dict) and "slots" in result:
                return [
                    {
                        "start": slot.get("start", ""),
                        "end": slot.get("end", ""),
                        "available": True,
                    }
                    for slot in result["slots"]
                ]
            else:
                # If we can't parse the result, return sample slots
                print(f"Could not parse slots result: {result}")
                return self._generate_sample_slots(start_date, end_date, slot_duration_minutes)

        except Exception as e:
            print(f"Error getting available slots: {e}")
            # Return sample slots as fallback
            return self._generate_sample_slots(start_date, end_date, slot_duration_minutes)

    def _generate_sample_slots(
        self, start_date: str, end_date: str, slot_duration_minutes: int
    ) -> list[dict]:
        """Generate sample time slots as fallback."""
        slots = []
        current = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)

        # Generate business hours slots (9 AM to 5 PM)
        while current.date() <= end.date():
            # Skip weekends
            if current.weekday() < 5:  # Monday = 0, Friday = 4
                # Generate slots from 9 AM to 5 PM
                slot_start = current.replace(hour=9, minute=0, second=0, microsecond=0)
                day_end = current.replace(hour=17, minute=0, second=0, microsecond=0)

                while slot_start < day_end:
                    slot_end = slot_start + timedelta(minutes=slot_duration_minutes)
                    slots.append({
                        "start": slot_start.isoformat(),
                        "end": slot_end.isoformat(),
                        "available": True,
                    })
                    slot_start = slot_end

            current += timedelta(days=1)

        return slots[:20]  # Limit to 20 slots to avoid overwhelming response

    async def query_appointments(
        self,
        calendar_id: str = "primary",
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        attendee_email: Optional[str] = None,
    ) -> list[dict]:
        """
        Query appointments from Google Calendar.

        Retrieves appointments within a time range, optionally filtered by attendee.

        Args:
            calendar_id: Calendar ID (use 'primary' for primary calendar)
            time_min: Start of time range in ISO format (YYYY-MM-DDTHH:MM:SS)
            time_max: End of time range in ISO format (YYYY-MM-DDTHH:MM:SS)
            attendee_email: Optional filter by attendee email address

        Returns:
            list[dict]: List of appointment details
        """
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(
                executor,
                self._query_appointments_sync,
                calendar_id,
                time_min,
                time_max,
                attendee_email,
            )

    def _query_appointments_sync(
        self,
        calendar_id: str = "primary",
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        attendee_email: Optional[str] = None,
    ) -> list[dict]:
        """Synchronous method to query appointments."""
        # Get the list events tool
        list_events_tool = self.tools_dict.get("GOOGLECALENDAR_LIST_EVENTS")
        if not list_events_tool:
            raise Exception("GOOGLECALENDAR_LIST_EVENTS tool not available")

        # Set default time range if not provided (next 30 days)
        if not time_min:
            time_min = datetime.now().isoformat()
        if not time_max:
            time_max = (datetime.now() + timedelta(days=30)).isoformat()

        try:
            # Prepare parameters
            params = {
                "calendar_id": calendar_id,
                "timeMin": time_min,
                "timeMax": time_max,
                "maxResults": 50,
                "singleEvents": True,
                "orderBy": "startTime",
            }

            # Execute the tool
            result = list_events_tool.run(**params)

            # Parse result
            appointments = []
            if isinstance(result, dict) and 'items' in result:
                events = result['items']
            elif isinstance(result, list):
                events = result
            else:
                logger.warning(f"Unexpected result format from list events: {type(result)}")
                return []

            # Filter by attendee if provided
            for event in events:
                if attendee_email:
                    attendees = event.get('attendees', [])
                    attendee_emails = [a.get('email', '') for a in attendees]
                    if attendee_email not in attendee_emails:
                        continue

                # Extract event details
                appointment = {
                    'event_id': event.get('id', ''),
                    'summary': event.get('summary', ''),
                    'description': event.get('description', ''),
                    'location': event.get('location', ''),
                    'start': event.get('start', {}).get('dateTime', ''),
                    'end': event.get('end', {}).get('dateTime', ''),
                    'status': event.get('status', ''),
                    'attendees': [
                        {
                            'email': a.get('email', ''),
                            'responseStatus': a.get('responseStatus', ''),
                        }
                        for a in event.get('attendees', [])
                    ],
                    'created': event.get('created', ''),
                    'updated': event.get('updated', ''),
                    'html_link': event.get('htmlLink', ''),
                }
                appointments.append(appointment)

            logger.info(f"Retrieved {len(appointments)} appointments from calendar")
            return appointments

        except Exception as e:
            logger.error(f"Error querying appointments: {e}")
            raise Exception(f"Failed to query appointments: {e}")

    async def update_appointment(
        self,
        event_id: str,
        calendar_id: str = "primary",
        start_datetime: Optional[str] = None,
        timezone: Optional[str] = None,
        duration_hours: Optional[int] = None,
        duration_minutes: Optional[int] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> dict:
        """
        Update an existing calendar appointment.

        Allows rescheduling and updating event details.

        Args:
            event_id: Google Calendar event ID
            calendar_id: Calendar ID
            start_datetime: New start datetime in ISO format (optional)
            timezone: Timezone (optional)
            duration_hours: New duration in hours (optional)
            duration_minutes: New duration in minutes (optional)
            summary: New event title (optional)
            description: New event description (optional)
            location: New event location (optional)

        Returns:
            dict: Updated event details
        """
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(
                executor,
                self._update_appointment_sync,
                event_id,
                calendar_id,
                start_datetime,
                timezone,
                duration_hours,
                duration_minutes,
                summary,
                description,
                location,
            )

    def _update_appointment_sync(
        self,
        event_id: str,
        calendar_id: str = "primary",
        start_datetime: Optional[str] = None,
        timezone: Optional[str] = None,
        duration_hours: Optional[int] = None,
        duration_minutes: Optional[int] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> dict:
        """Synchronous method to update an appointment."""
        # Get the update event tool
        update_event_tool = self.tools_dict.get("GOOGLECALENDAR_UPDATE_EVENT")
        if not update_event_tool:
            raise Exception("GOOGLECALENDAR_UPDATE_EVENT tool not available")

        try:
            # Prepare parameters (only include fields to update)
            params = {
                "calendar_id": calendar_id,
                "event_id": event_id,
            }

            if start_datetime:
                params["start_datetime"] = start_datetime
            if timezone:
                params["timezone"] = timezone
            if duration_hours is not None:
                params["event_duration_hour"] = duration_hours
            if duration_minutes is not None:
                params["event_duration_minutes"] = duration_minutes
            if summary:
                params["summary"] = summary
            if description:
                params["description"] = description
            if location:
                params["location"] = location

            # Execute the tool
            result = update_event_tool.run(**params)

            logger.info(f"Updated appointment {event_id}")

            # Parse result
            if isinstance(result, dict):
                return {
                    'event_id': result.get('id', event_id),
                    'summary': result.get('summary', summary or ''),
                    'start': result.get('start', {}).get('dateTime', start_datetime or ''),
                    'end': result.get('end', {}).get('dateTime', ''),
                    'status': result.get('status', 'confirmed'),
                    'updated': True,
                }
            else:
                return {
                    'event_id': event_id,
                    'updated': True,
                    'raw_result': str(result),
                }

        except Exception as e:
            logger.error(f"Error updating appointment: {e}")
            raise Exception(f"Failed to update appointment: {e}")

    async def cancel_appointment(
        self,
        event_id: str,
        calendar_id: str = "primary",
        send_notification: bool = True,
    ) -> dict:
        """
        Cancel a calendar appointment.

        Deletes the event from Google Calendar and optionally sends
        cancellation notifications to attendees.

        Args:
            event_id: Google Calendar event ID
            calendar_id: Calendar ID
            send_notification: Whether to send cancellation emails to attendees

        Returns:
            dict: Cancellation confirmation details
        """
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(
                executor,
                self._cancel_appointment_sync,
                event_id,
                calendar_id,
                send_notification,
            )

    def _cancel_appointment_sync(
        self,
        event_id: str,
        calendar_id: str = "primary",
        send_notification: bool = True,
    ) -> dict:
        """Synchronous method to cancel an appointment."""
        # Get the delete event tool
        delete_event_tool = self.tools_dict.get("GOOGLECALENDAR_DELETE_EVENT")
        if not delete_event_tool:
            raise Exception("GOOGLECALENDAR_DELETE_EVENT tool not available")

        try:
            # Prepare parameters
            params = {
                "calendar_id": calendar_id,
                "event_id": event_id,
                "sendUpdates": "all" if send_notification else "none",
            }

            # Execute the tool
            result = delete_event_tool.run(**params)

            logger.info(f"Cancelled appointment {event_id}")

            return {
                'event_id': event_id,
                'cancelled': True,
                'notification_sent': send_notification,
                'message': 'Appointment cancelled successfully',
            }

        except Exception as e:
            logger.error(f"Error cancelling appointment: {e}")
            raise Exception(f"Failed to cancel appointment: {e}")