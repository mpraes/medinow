from enum import Enum, auto
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """
    Conversation states for the Medinow chatbot.

    Covers all flows: booking, querying, rescheduling, and cancelling appointments.
    """
    # Core states
    IDLE = auto()
    GREETING = auto()

    # Booking flow states
    COLLECTING_DATE = auto()
    COLLECTING_TIME = auto()
    SHOWING_AVAILABLE_SLOTS = auto()
    COLLECTING_PATIENT_INFO = auto()
    CONFIRMING_APPOINTMENT = auto()
    BOOKING_APPOINTMENT = auto()

    # Query flow states
    IDENTIFYING_USER = auto()
    SHOWING_USER_APPOINTMENTS = auto()

    # Cancellation flow states
    SELECTING_APPOINTMENT_TO_CANCEL = auto()
    CONFIRMING_CANCELLATION = auto()
    CANCELLING_APPOINTMENT = auto()

    # Rescheduling flow states
    SELECTING_APPOINTMENT_TO_RESCHEDULE = auto()
    COLLECTING_NEW_DATE = auto()
    COLLECTING_NEW_TIME = auto()
    SHOWING_RESCHEDULE_SLOTS = auto()
    CONFIRMING_RESCHEDULE = auto()
    RESCHEDULING_APPOINTMENT = auto()

    # Special states
    OFF_TOPIC = auto()


class ConversationStateMachine:
    """
    State machine for managing conversation flow with context preservation.

    Implements context stack for handling topic changes without losing conversation state.
    """

    def __init__(self):
        self.state = ConversationState.IDLE
        self.appointment_data: Dict[str, Any] = {}
        self.available_slots: List[Dict[str, Any]] = []
        self.selected_slot: Optional[Dict[str, Any]] = None
        self.context_stack: List[Dict[str, Any]] = []  # Stack for saved contexts
        self.user_appointments: List[Dict[str, Any]] = []  # User's appointments for query/cancel/reschedule

    def transition_to(self, new_state):
        print(f"Transitioning from {self.state.name} to {new_state.name}")
        self.state = new_state

    def get_state(self):
        return self.state
    
    def set_appointment_data(self, key: str, value: Any):
        """Store appointment information as it's collected."""
        self.appointment_data[key] = value
        
    def get_appointment_data(self, key: str) -> Any:
        """Retrieve stored appointment information."""
        return self.appointment_data.get(key)
    
    def clear_appointment_data(self):
        """Clear all appointment data for a new booking."""
        self.appointment_data = {}
        self.available_slots = []
        self.selected_slot = None
    
    def set_available_slots(self, slots):
        """Store available time slots."""
        self.available_slots = slots
    
    def get_available_slots(self):
        """Get stored available slots."""
        return self.available_slots
    
    def set_selected_slot(self, slot):
        """Set the user's selected time slot."""
        self.selected_slot = slot
    
    def get_selected_slot(self):
        """Get the user's selected slot."""
        return self.selected_slot
    
    def is_appointment_complete(self) -> bool:
        """Check if we have all required appointment information."""
        required_fields = ['date', 'time', 'patient_name', 'patient_email']
        return all(key in self.appointment_data for key in required_fields)

    def save_context(self):
        """
        Save current conversation context when user changes topic.

        Stores the current state, appointment data, and other context
        to allow returning to the conversation later.
        """
        context = {
            'state': self.state,
            'appointment_data': self.appointment_data.copy(),
            'available_slots': self.available_slots.copy(),
            'selected_slot': self.selected_slot,
            'user_appointments': self.user_appointments.copy(),
            'timestamp': datetime.now().isoformat()
        }
        self.context_stack.append(context)
        logger.info(f"Saved context, stack depth: {len(self.context_stack)}")

    def restore_context(self) -> bool:
        """
        Restore previous conversation context.

        Returns to the saved conversation state after handling off-topic messages.

        Returns:
            bool: True if context was restored, False if no saved context
        """
        if self.context_stack:
            context = self.context_stack.pop()
            self.state = context['state']
            self.appointment_data = context['appointment_data']
            self.available_slots = context['available_slots']
            self.selected_slot = context['selected_slot']
            self.user_appointments = context['user_appointments']
            logger.info(f"Restored context to state {self.state.name}")
            return True
        return False

    def has_saved_context(self) -> bool:
        """Check if there is saved context available."""
        return len(self.context_stack) > 0

    def set_user_appointments(self, appointments: List[Dict[str, Any]]):
        """Store user's appointments for query/cancel/reschedule operations."""
        self.user_appointments = appointments

    def get_user_appointments(self) -> List[Dict[str, Any]]:
        """Get stored user appointments."""
        return self.user_appointments

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize state machine to dictionary for persistence.

        Returns:
            Dict: Serializable state machine data
        """
        return {
            'state': self.state.name,
            'appointment_data': self.appointment_data,
            'available_slots': self.available_slots,
            'selected_slot': self.selected_slot,
            'context_stack': self.context_stack,
            'user_appointments': self.user_appointments,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationStateMachine':
        """
        Deserialize state machine from dictionary.

        Args:
            data: Dictionary with state machine data

        Returns:
            ConversationStateMachine: Restored state machine instance
        """
        machine = cls()
        machine.state = ConversationState[data.get('state', 'IDLE')]
        machine.appointment_data = data.get('appointment_data', {})
        machine.available_slots = data.get('available_slots', [])
        machine.selected_slot = data.get('selected_slot')
        machine.context_stack = data.get('context_stack', [])
        machine.user_appointments = data.get('user_appointments', [])
        return machine
