"""
Conversation manager with persistent storage integration.

Manages conversation sessions with automatic state persistence and restoration.
"""

import asyncio
import logging
from typing import Dict
from backend.agents.state_machine import ConversationStateMachine, ConversationState
from backend.agents.message_handlers import handle_message
from backend.storage.database import get_database

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Manages conversation sessions with persistent storage.

    Provides session management with automatic state saving and restoration
    from SQLite database.
    """

    def __init__(self, enable_persistence: bool = True):
        """
        Initialize conversation manager.

        Args:
            enable_persistence: Enable persistent storage (default: True)
        """
        self.sessions: Dict[str, ConversationStateMachine] = {}
        self.enable_persistence = enable_persistence
        self.db = get_database() if enable_persistence else None

    def get_or_create_session(self, session_id: str, phone_number: str) -> ConversationStateMachine:
        """
        Get existing session or create new one.

        Attempts to restore session from database if not in memory.

        Args:
            session_id: Unique session identifier
            phone_number: User's phone number

        Returns:
            ConversationStateMachine: Session state machine
        """
        # Check memory cache first
        if session_id in self.sessions:
            return self.sessions[session_id]

        # Try to restore from database
        if self.enable_persistence and self.db:
            try:
                session_data = self.db.get_session(session_id)
                if session_data:
                    # Restore state machine from database
                    state_machine = ConversationStateMachine()
                    state_machine.state = ConversationState[session_data['state']]
                    state_machine.appointment_data = session_data['appointment_data']
                    state_machine.context_stack = session_data['context_stack']

                    self.sessions[session_id] = state_machine
                    logger.info(f"Restored session {session_id} from database")
                    return state_machine
            except Exception as e:
                logger.error(f"Error restoring session from database: {e}")

        # Create new session
        state_machine = ConversationStateMachine()
        self.sessions[session_id] = state_machine
        logger.info(f"Created new session {session_id}")

        return state_machine

    def save_session(self, session_id: str, phone_number: str, state_machine: ConversationStateMachine):
        """
        Save session state to persistent storage.

        Args:
            session_id: Unique session identifier
            phone_number: User's phone number
            state_machine: Current state machine to save
        """
        if not self.enable_persistence or not self.db:
            return

        try:
            self.db.save_session(
                session_id=session_id,
                phone_number=phone_number,
                state=state_machine.state.name,
                appointment_data=state_machine.appointment_data,
                context_stack=state_machine.context_stack
            )
            logger.debug(f"Saved session {session_id} to database")
        except Exception as e:
            logger.error(f"Error saving session to database: {e}")

    async def handle_incoming_message(self, session_id: str, message_text: str) -> str:
        """
        Handle incoming message asynchronously with persistence.

        Args:
            session_id: Unique session identifier (phone number)
            message_text: User's message text

        Returns:
            str: Bot's response message
        """
        # Extract phone number from session_id
        phone_number = session_id

        # Get or create session
        state_machine = self.get_or_create_session(session_id, phone_number)

        # Process message
        response = await handle_message(state_machine, message_text, phone_number)

        # Save session state after processing
        self.save_session(session_id, phone_number, state_machine)

        return response

    def clear_session(self, session_id: str):
        """
        Clear session from memory and database.

        Args:
            session_id: Unique session identifier
        """
        # Remove from memory
        if session_id in self.sessions:
            del self.sessions[session_id]

        # Remove from database
        if self.enable_persistence and self.db:
            try:
                self.db.delete_session(session_id)
                logger.info(f"Cleared session {session_id}")
            except Exception as e:
                logger.error(f"Error clearing session: {e}")
