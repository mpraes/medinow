"""
SQLite database layer for persistent storage.

Provides storage for conversation sessions, user data, and appointments
using SQLite for MVP simplicity and easy maintenance.
"""

import sqlite3
import json
import logging
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles date and datetime objects."""

    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


class Database:
    """
    SQLite database manager for persistent storage.

    Handles storage of sessions, users, and appointments with thread-safe operations.
    """

    def __init__(self, db_path: str = "data/medinow.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._local = threading.local()

        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        self._initialize_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    def _initialize_schema(self):
        """Create database tables if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                phone_number TEXT PRIMARY KEY,
                name TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                phone_number TEXT,
                state TEXT NOT NULL,
                appointment_data TEXT,
                context_stack TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (phone_number) REFERENCES users(phone_number)
            )
        """)

        # Appointments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                appointment_id TEXT PRIMARY KEY,
                phone_number TEXT NOT NULL,
                calendar_event_id TEXT UNIQUE,
                start_datetime TEXT NOT NULL,
                end_datetime TEXT NOT NULL,
                patient_name TEXT,
                patient_email TEXT,
                status TEXT DEFAULT 'confirmed',
                summary TEXT,
                description TEXT,
                location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (phone_number) REFERENCES users(phone_number)
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_phone
            ON sessions(phone_number)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_appointments_phone
            ON appointments(phone_number)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_appointments_calendar
            ON appointments(calendar_event_id)
        """)

        conn.commit()
        logger.info("Database schema initialized successfully")

    def save_user(
        self,
        phone_number: str,
        name: Optional[str] = None,
        email: Optional[str] = None
    ) -> bool:
        """
        Save or update user information.

        Args:
            phone_number: User's phone number (unique identifier)
            name: User's name
            email: User's email address

        Returns:
            bool: True if successful
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO users (phone_number, name, email)
                VALUES (?, ?, ?)
                ON CONFLICT(phone_number) DO UPDATE SET
                    name = COALESCE(?, name),
                    email = COALESCE(?, email),
                    updated_at = CURRENT_TIMESTAMP
            """, (phone_number, name, email, name, email))

            conn.commit()
            logger.info(f"Saved user data for {phone_number}")
            return True

        except Exception as e:
            logger.error(f"Error saving user: {e}")
            return False

    def get_user(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user information.

        Args:
            phone_number: User's phone number

        Returns:
            Optional[Dict]: User data or None if not found
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT phone_number, name, email, created_at, updated_at
                FROM users
                WHERE phone_number = ?
            """, (phone_number,))

            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

        except Exception as e:
            logger.error(f"Error retrieving user: {e}")
            return None

    def save_session(
        self,
        session_id: str,
        phone_number: str,
        state: str,
        appointment_data: Dict[str, Any],
        context_stack: List[Dict[str, Any]]
    ) -> bool:
        """
        Save conversation session state.

        Args:
            session_id: Unique session identifier
            phone_number: User's phone number
            state: Current conversation state
            appointment_data: Dictionary of appointment data
            context_stack: Stack of saved contexts

        Returns:
            bool: True if successful
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Serialize complex data to JSON with custom encoder for dates
            appointment_data_json = json.dumps(appointment_data, cls=DateTimeEncoder)
            context_stack_json = json.dumps(context_stack, cls=DateTimeEncoder)

            cursor.execute("""
                INSERT INTO sessions (session_id, phone_number, state,
                                     appointment_data, context_stack)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    state = ?,
                    appointment_data = ?,
                    context_stack = ?,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                session_id, phone_number, state,
                appointment_data_json, context_stack_json,
                state, appointment_data_json, context_stack_json
            ))

            conn.commit()
            logger.debug(f"Saved session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving session: {e}")
            return False

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve conversation session state.

        Args:
            session_id: Unique session identifier

        Returns:
            Optional[Dict]: Session data or None if not found
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT session_id, phone_number, state,
                       appointment_data, context_stack,
                       created_at, updated_at
                FROM sessions
                WHERE session_id = ?
            """, (session_id,))

            row = cursor.fetchone()
            if row:
                session_dict = dict(row)
                # Deserialize JSON fields
                session_dict['appointment_data'] = json.loads(
                    session_dict['appointment_data'] or '{}'
                )
                session_dict['context_stack'] = json.loads(
                    session_dict['context_stack'] or '[]'
                )
                return session_dict
            return None

        except Exception as e:
            logger.error(f"Error retrieving session: {e}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a conversation session.

        Args:
            session_id: Unique session identifier

        Returns:
            bool: True if successful
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()

            logger.info(f"Deleted session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False

    def save_appointment(
        self,
        appointment_id: str,
        phone_number: str,
        calendar_event_id: str,
        start_datetime: str or datetime or date,
        end_datetime: str or datetime or date,
        patient_name: Optional[str] = None,
        patient_email: Optional[str] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        status: str = "confirmed"
    ) -> bool:
        """
        Save appointment information.

        Args:
            appointment_id: Unique appointment identifier
            phone_number: User's phone number
            calendar_event_id: Google Calendar event ID
            start_datetime: Appointment start time (string or datetime)
            end_datetime: Appointment end time (string or datetime)
            patient_name: Patient's name
            patient_email: Patient's email
            summary: Appointment summary
            description: Appointment description
            location: Appointment location
            status: Appointment status

        Returns:
            bool: True if successful
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Convert datetime/date objects to ISO strings if needed
            if isinstance(start_datetime, (datetime, date)):
                start_datetime = start_datetime.isoformat()

            if isinstance(end_datetime, (datetime, date)):
                end_datetime = end_datetime.isoformat()

            cursor.execute("""
                INSERT INTO appointments (
                    appointment_id, phone_number, calendar_event_id,
                    start_datetime, end_datetime, patient_name, patient_email,
                    summary, description, location, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(appointment_id) DO UPDATE SET
                    start_datetime = ?,
                    end_datetime = ?,
                    status = ?,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                appointment_id, phone_number, calendar_event_id,
                start_datetime, end_datetime, patient_name, patient_email,
                summary, description, location, status,
                start_datetime, end_datetime, status
            ))

            conn.commit()
            logger.info(f"Saved appointment {appointment_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving appointment: {e}")
            return False

    def get_appointments(
        self,
        phone_number: Optional[str] = None,
        calendar_event_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve appointments with optional filters.

        Args:
            phone_number: Filter by phone number
            calendar_event_id: Filter by calendar event ID
            status: Filter by status

        Returns:
            List[Dict]: List of appointments
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                SELECT appointment_id, phone_number, calendar_event_id,
                       start_datetime, end_datetime, patient_name, patient_email,
                       summary, description, location, status,
                       created_at, updated_at
                FROM appointments
                WHERE 1=1
            """
            params = []

            if phone_number:
                query += " AND phone_number = ?"
                params.append(phone_number)

            if calendar_event_id:
                query += " AND calendar_event_id = ?"
                params.append(calendar_event_id)

            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY start_datetime DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error retrieving appointments: {e}")
            return []

    def update_appointment_status(
        self,
        appointment_id: str,
        status: str
    ) -> bool:
        """
        Update appointment status.

        Args:
            appointment_id: Unique appointment identifier
            status: New status (confirmed, cancelled, rescheduled)

        Returns:
            bool: True if successful
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE appointments
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE appointment_id = ?
            """, (status, appointment_id))

            conn.commit()
            logger.info(f"Updated appointment {appointment_id} status to {status}")
            return True

        except Exception as e:
            logger.error(f"Error updating appointment status: {e}")
            return False

    def close(self):
        """Close database connection."""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            logger.info("Database connection closed")


# Global database instance
_db_instance: Optional[Database] = None


def get_database() -> Database:
    """
    Get or create global database instance.

    Returns:
        Database: Singleton database instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
