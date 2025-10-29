"""
Test script for Phase 1 Core Functionality.

Verifies that all Phase 1 components are working correctly.
"""

import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.storage.database import get_database
from backend.agents.state_machine import ConversationStateMachine, ConversationState
from backend.agents.conversation import ConversationManager


def test_database():
    """Test database operations."""
    print("\n=== Testing Database Operations ===")

    db = get_database()

    # Test user save and retrieve
    print("Testing user operations...")
    phone = "+5511999999999"
    db.save_user(phone, "João Silva", "joao@example.com")
    user = db.get_user(phone)
    assert user is not None, "User should be saved"
    assert user['name'] == "João Silva", "User name should match"
    print("✅ User operations working")

    # Test session save and retrieve
    print("Testing session operations...")
    session_id = "test_session_123"
    db.save_session(
        session_id=session_id,
        phone_number=phone,
        state="GREETING",
        appointment_data={"date": "2025-10-30"},
        context_stack=[]
    )
    session = db.get_session(session_id)
    assert session is not None, "Session should be saved"
    assert session['state'] == "GREETING", "Session state should match"
    print("✅ Session operations working")

    # Test appointment save and retrieve
    print("Testing appointment operations...")
    db.save_appointment(
        appointment_id="apt_123",
        phone_number=phone,
        calendar_event_id="cal_event_123",
        start_datetime="2025-10-30T14:00:00",
        end_datetime="2025-10-30T14:30:00",
        patient_name="João Silva",
        patient_email="joao@example.com"
    )
    appointments = db.get_appointments(phone_number=phone)
    assert len(appointments) > 0, "Should have appointments"
    print("✅ Appointment operations working")

    # Cleanup
    db.delete_session(session_id)
    print("✅ Database tests passed!")


def test_state_machine():
    """Test state machine with context preservation."""
    print("\n=== Testing State Machine ===")

    machine = ConversationStateMachine()

    # Test initial state
    assert machine.state == ConversationState.IDLE, "Should start in IDLE"
    print("✅ Initial state correct")

    # Test state transition
    machine.transition_to(ConversationState.GREETING)
    assert machine.state == ConversationState.GREETING, "Should transition to GREETING"
    print("✅ State transition working")

    # Test appointment data
    machine.set_appointment_data('date', '2025-10-30')
    assert machine.get_appointment_data('date') == '2025-10-30', "Should store data"
    print("✅ Appointment data storage working")

    # Test context preservation
    machine.transition_to(ConversationState.COLLECTING_DATE)
    machine.set_appointment_data('time', '14:00')
    machine.save_context()
    assert machine.has_saved_context(), "Should have saved context"
    print("✅ Context save working")

    # Change state
    machine.transition_to(ConversationState.OFF_TOPIC)
    machine.clear_appointment_data()

    # Restore context
    restored = machine.restore_context()
    assert restored, "Should restore context"
    assert machine.state == ConversationState.COLLECTING_DATE, "Should restore state"
    assert machine.get_appointment_data('time') == '14:00', "Should restore data"
    print("✅ Context restoration working")

    # Test serialization
    machine_dict = machine.to_dict()
    assert 'state' in machine_dict, "Should serialize state"
    restored_machine = ConversationStateMachine.from_dict(machine_dict)
    assert restored_machine.state == machine.state, "Should deserialize correctly"
    print("✅ Serialization working")

    print("✅ State machine tests passed!")


async def test_conversation_manager():
    """Test conversation manager with persistence."""
    print("\n=== Testing Conversation Manager ===")

    manager = ConversationManager(enable_persistence=True)

    # Test session creation
    session_id = "test_conv_session"
    phone = "+5511888888888"
    state_machine = manager.get_or_create_session(session_id, phone)
    assert state_machine is not None, "Should create session"
    print("✅ Session creation working")

    # Test message handling
    response = await manager.handle_incoming_message(session_id, "Olá")
    assert response is not None, "Should get response"
    assert len(response) > 0, "Response should not be empty"
    print(f"✅ Message handling working: {response[:50]}...")

    # Test session persistence
    manager.save_session(session_id, phone, state_machine)
    print("✅ Session persistence working")

    # Test session restoration
    manager.sessions.clear()  # Clear memory cache
    restored_machine = manager.get_or_create_session(session_id, phone)
    assert restored_machine.state == state_machine.state, "Should restore from DB"
    print("✅ Session restoration working")

    # Cleanup
    manager.clear_session(session_id)
    print("✅ Conversation manager tests passed!")


def test_imports():
    """Test that all new modules can be imported."""
    print("\n=== Testing Imports ===")

    try:
        from backend.integrations.twilio.webhook_handler import TwilioWebhookHandler
        print("✅ TwilioWebhookHandler imported")

        from backend.storage.database import Database, get_database
        print("✅ Database imported")

        from backend.agents.state_machine import ConversationState, ConversationStateMachine
        print("✅ State machine imported")

        from backend.agents.conversation import ConversationManager
        print("✅ ConversationManager imported")

        print("✅ All imports successful!")

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

    return True


async def run_all_tests():
    """Run all Phase 1 tests."""
    print("=" * 60)
    print("MEDINOW PHASE 1 - COMPONENT TESTS")
    print("=" * 60)

    try:
        # Test imports first
        if not test_imports():
            print("\n❌ Import tests failed. Aborting.")
            return

        # Test database
        test_database()

        # Test state machine
        test_state_machine()

        # Test conversation manager
        await test_conversation_manager()

        print("\n" + "=" * 60)
        print("🎉 ALL PHASE 1 TESTS PASSED!")
        print("=" * 60)

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())
