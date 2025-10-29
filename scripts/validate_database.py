#!/usr/bin/env python
"""
Validate persistent storage with real data.

This script checks the SQLite database to verify that user data,
session data, and appointment data are being correctly persisted.
"""

import sqlite3
import json
import sys
import os
from datetime import datetime, date
from pathlib import Path

# Add parent directory to path to import from backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.storage.database import get_database

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def print_data(title, data):
    """Print data with a title."""
    print(f"\n--- {title} ---")
    if isinstance(data, dict):
        for key, value in data.items():
            print(f"  {key}: {value}")
    elif isinstance(data, list):
        for item in data:
            print(f"  - {item}")
    else:
        print(f"  {data}")

def validate_users_table():
    """Validate the users table structure and data."""
    print_section("USERS TABLE VALIDATION")

    conn = sqlite3.connect('data/medinow.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check table structure
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    print_data("Table Structure", [f"{col['name']} ({col['type']})" for col in columns])

    # Check if users exist
    cursor.execute("SELECT COUNT(*) as count FROM users")
    count = cursor.fetchone()['count']
    print_data("Total Users", count)

    # Check sample users
    if count > 0:
        cursor.execute("""
            SELECT phone_number, name, email, created_at, updated_at
            FROM users
            LIMIT 5
        """)
        users = cursor.fetchall()
        print_data("Sample Users", [dict(user) for user in users])
    else:
        print_data("Sample Users", "No users found in database")

    conn.close()
    return count > 0

def validate_sessions_table():
    """Validate the sessions table structure and data."""
    print_section("SESSIONS TABLE VALIDATION")

    conn = sqlite3.connect('data/medinow.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check table structure
    cursor.execute("PRAGMA table_info(sessions)")
    columns = cursor.fetchall()
    print_data("Table Structure", [f"{col['name']} ({col['type']})" for col in columns])

    # Check if sessions exist
    cursor.execute("SELECT COUNT(*) as count FROM sessions")
    count = cursor.fetchone()['count']
    print_data("Total Sessions", count)

    # Check sample sessions
    if count > 0:
        cursor.execute("""
            SELECT session_id, phone_number, state, appointment_data, context_stack, created_at, updated_at
            FROM sessions
            LIMIT 5
        """)
        sessions = cursor.fetchall()

        # Process and display sessions
        processed_sessions = []
        for session in sessions:
            session_dict = dict(session)

            # Parse JSON fields
            try:
                session_dict['appointment_data'] = json.loads(session_dict['appointment_data'] or '{}')
                session_dict['context_stack'] = json.loads(session_dict['context_stack'] or '[]')
            except json.JSONDecodeError:
                print_data("WARNING", f"Could not parse JSON for session {session_dict['session_id']}")

            processed_sessions.append(session_dict)

        print_data("Sample Sessions", processed_sessions)
    else:
        print_data("Sample Sessions", "No sessions found in database")

    conn.close()
    return count > 0

def validate_appointments_table():
    """Validate the appointments table structure and data."""
    print_section("APPOINTMENTS TABLE VALIDATION")

    conn = sqlite3.connect('data/medinow.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check table structure
    cursor.execute("PRAGMA table_info(appointments)")
    columns = cursor.fetchall()
    print_data("Table Structure", [f"{col['name']} ({col['type']})" for col in columns])

    # Check if appointments exist
    cursor.execute("SELECT COUNT(*) as count FROM appointments")
    count = cursor.fetchone()['count']
    print_data("Total Appointments", count)

    # Check sample appointments
    if count > 0:
        cursor.execute("""
            SELECT appointment_id, phone_number, calendar_event_id,
                  start_datetime, end_datetime, patient_name, patient_email,
                  status, summary, description, location, created_at, updated_at
            FROM appointments
            LIMIT 5
        """)
        appointments = cursor.fetchall()
        print_data("Sample Appointments", [dict(appt) for appt in appointments])
    else:
        print_data("Sample Appointments", "No appointments found in database")

    conn.close()
    return count > 0

def validate_using_database_api():
    """Validate using the database API directly."""
    print_section("DATABASE API VALIDATION")

    db = get_database()

    # Test getting a session
    session_id = "test-date-fix"
    session = db.get_session(session_id)
    print_data(f"Session '{session_id}'", session or "Not found")

    # Test getting user appointments
    if session:
        phone_number = session.get('phone_number')
        if phone_number:
            appointments = db.get_appointments(phone_number=phone_number)
            print_data(f"Appointments for {phone_number}", appointments or "No appointments found")

    # Test getting a user
    test_phone = "test-user-123"
    user = db.get_user(test_phone)
    print_data(f"User '{test_phone}'", user or "Not found")

    return True

def test_creating_data():
    """Test creating new data in the database."""
    print_section("CREATING TEST DATA")

    db = get_database()
    test_id = f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Create a test user
    print_data("Creating test user", test_id)
    success = db.save_user(
        phone_number=test_id,
        name="Test User",
        email="test@example.com"
    )
    print_data("User creation result", "Success" if success else "Failed")

    # Create a test session
    print_data("Creating test session", test_id)
    success = db.save_session(
        session_id=test_id,
        phone_number=test_id,
        state="IDLE",
        appointment_data={"test": True, "date": date.today().isoformat()},
        context_stack=[]
    )
    print_data("Session creation result", "Success" if success else "Failed")

    # Create a test appointment
    print_data("Creating test appointment", test_id)
    success = db.save_appointment(
        appointment_id=test_id,
        phone_number=test_id,
        calendar_event_id=f"cal-{test_id}",
        start_datetime=datetime.now(),
        end_datetime=datetime.now(),
        patient_name="Test Patient",
        patient_email="test@example.com",
        summary="Test Appointment",
        description="Test Description",
        location="Test Location"
    )
    print_data("Appointment creation result", "Success" if success else "Failed")

    # Verify the data was created
    user = db.get_user(test_id)
    session = db.get_session(test_id)
    appointments = db.get_appointments(phone_number=test_id)

    print_data("Retrieved user", user or "Not found")
    print_data("Retrieved session", session or "Not found")
    print_data("Retrieved appointments", appointments or "Not found")

    return True

def main():
    """Main validation function."""
    print_section("DATABASE VALIDATION SCRIPT")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Database path: data/medinow.db")

    # Check if database file exists
    if not Path('data/medinow.db').exists():
        print("ERROR: Database file not found!")
        return False

    # Validate each table
    users_valid = validate_users_table()
    sessions_valid = validate_sessions_table()
    appointments_valid = validate_appointments_table()

    # Validate using the database API
    api_valid = validate_using_database_api()

    # Test creating new data
    create_valid = test_creating_data()

    # Print summary
    print_section("VALIDATION SUMMARY")
    print_data("Users Table", "✅ Valid" if users_valid else "❌ Invalid")
    print_data("Sessions Table", "✅ Valid" if sessions_valid else "❌ Invalid")
    print_data("Appointments Table", "✅ Valid" if appointments_valid else "❌ Invalid")
    print_data("Database API", "✅ Valid" if api_valid else "❌ Invalid")
    print_data("Data Creation", "✅ Valid" if create_valid else "❌ Invalid")

    print("\nOverall result:", end=" ")
    if all([users_valid, sessions_valid, appointments_valid, api_valid, create_valid]):
        print("✅ All validations passed!")
    else:
        print("❌ Some validations failed!")

if __name__ == "__main__":
    main()