import re
import asyncio
from datetime import datetime, timedelta, date
from typing import Optional, Tuple, List
from backend.agents.state_machine import ConversationState
from backend.api.services.simple_composio_calendar_service import SimpleComposioCalendarService

# Initialize calendar service
calendar_service = SimpleComposioCalendarService()

def extract_date_from_message(message: str) -> Optional[date]:
    """Extract date from user message using various patterns."""
    message_lower = message.lower()
    
    # Today/tomorrow patterns
    if "hoje" in message_lower:
        return date.today()
    elif "amanhã" in message_lower or "amanha" in message_lower:
        return date.today() + timedelta(days=1)
    
    # Specific date patterns (dd/mm, dd-mm, dd de mm)
    date_patterns = [
        r'(\d{1,2})[/-](\d{1,2})',  # 15/10 or 15-10
        r'(\d{1,2})\s+de\s+(\d{1,2})',  # 15 de 10
        r'dia\s+(\d{1,2})',  # dia 15
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, message_lower)
        if match:
            try:
                day = int(match.group(1))
                if len(match.groups()) > 1:
                    month = int(match.group(2))
                else:
                    month = date.today().month
                
                # Assume current year if not specified
                year = date.today().year
                
                # Handle month rollover
                if month < date.today().month:
                    year += 1
                
                return date(year, month, day)
            except ValueError:
                continue
    
    return None

def extract_time_from_message(message: str) -> Optional[str]:
    """Extract time from user message."""
    # Time patterns: 14:00, 14h, 14:30, 2 da tarde, etc.
    time_patterns = [
        r'(\d{1,2}):(\d{2})',  # 14:30
        r'(\d{1,2})h(\d{2})',  # 14h30
        r'(\d{1,2})h',  # 14h
        r'(\d{1,2})\s+(?:da\s+)?(?:manhã|manha)',  # 9 da manhã
        r'(\d{1,2})\s+(?:da\s+)?tarde',  # 2 da tarde
        r'(\d{1,2})\s+(?:da\s+)?noite',  # 8 da noite
    ]
    
    message_lower = message.lower()
    
    for pattern in time_patterns:
        match = re.search(pattern, message_lower)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if len(match.groups()) > 1 else 0
            
            # Handle period indicators
            if "tarde" in message_lower and hour < 12:
                hour += 12
            elif "noite" in message_lower and hour < 12:
                hour += 12
            
            return f"{hour:02d}:{minute:02d}"
    
    return None

def extract_patient_info(message: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract patient name and email from message."""
    # Simple email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, message)
    email = email_match.group(0) if email_match else None
    
    # Extract name (simple approach - assume anything before email or first words)
    name = None
    if email:
        # Remove email from message and clean up
        name_text = re.sub(email_pattern, '', message).strip()
        # Remove common prefixes
        name_text = re.sub(r'^(meu nome é|me chamo|sou|eu sou)\s+', '', name_text, flags=re.IGNORECASE)
        name_text = name_text.replace(',', '').strip()
        if name_text:
            name = name_text
    else:
        # Try to extract name without email
        name_match = re.search(r'(?:meu nome é|me chamo|sou|eu sou)\s+([a-zA-ZÀ-ÿ\s]+)', message, re.IGNORECASE)
        if name_match:
            name = name_match.group(1).strip()
    
    return name, email

async def get_available_slots(appointment_date: date) -> List[dict]:
    """Get available slots for a given date."""
    try:
        # Format date for API
        start_date = appointment_date.strftime("%Y-%m-%d")
        end_date = start_date  # Same day
        
        # Get available slots from calendar service
        slots_response = await calendar_service.get_available_slots(
            start_date=start_date,
            end_date=end_date,
            calendar_id="primary",
            slot_duration_minutes=30
        )
        
        return slots_response if isinstance(slots_response, list) else []
    except Exception as e:
        print(f"Error getting available slots: {e}")
        # Return some default slots if service fails
        return [
            {"start": f"{appointment_date}T09:00:00", "end": f"{appointment_date}T09:30:00", "available": True},
            {"start": f"{appointment_date}T10:00:00", "end": f"{appointment_date}T10:30:00", "available": True},
            {"start": f"{appointment_date}T14:00:00", "end": f"{appointment_date}T14:30:00", "available": True},
            {"start": f"{appointment_date}T15:00:00", "end": f"{appointment_date}T15:30:00", "available": True},
        ]

def format_available_slots(slots: List[dict]) -> str:
    """Format available slots for display to user."""
    if not slots:
        return "Desculpe, não há horários disponíveis para esta data."
    
    formatted_slots = []
    for i, slot in enumerate(slots[:6], 1):  # Limit to 6 slots
        start_time = slot['start'].split('T')[1][:5]  # Extract HH:MM
        formatted_slots.append(f"{i}. {start_time}")
    
    return "Horários disponíveis:\n" + "\n".join(formatted_slots) + "\n\nDigite o número do horário desejado."

async def handle_message(state_machine, message_text, phone_number: str = None):
    """
    Handles incoming messages based on the conversation state.

    Args:
        state_machine: Conversation state machine
        message_text: User's message text
        phone_number: User's phone number (optional, for user identification)

    Returns:
        str: Bot's response message
    """
    current_state = state_machine.get_state()

    if current_state == ConversationState.IDLE:
        state_machine.transition_to(ConversationState.GREETING)
        return "Olá! 👋 Sou o assistente de agendamento da Clínica MediNow. Como posso ajudá-lo hoje?"

    elif current_state == ConversationState.GREETING:
        if any(word in message_text.lower() for word in ["agendar", "consulta", "agendamento", "marcar"]):
            state_machine.clear_appointment_data()
            state_machine.transition_to(ConversationState.COLLECTING_DATE)
            return "Perfeito! Vou ajudá-lo a agendar uma consulta. 📅\n\nQual data você prefere? Você pode dizer algo como 'hoje', 'amanhã' ou uma data específica como '15/11'."
        else:
            return "Posso ajudá-lo a agendar uma consulta médica. Digite 'agendar consulta' para começar!"

    elif current_state == ConversationState.COLLECTING_DATE:
        appointment_date = extract_date_from_message(message_text)
        if appointment_date:
            # Check if date is not in the past
            if appointment_date < date.today():
                return "⚠️ Não posso agendar para datas passadas. Por favor, escolha uma data futura."
            
            state_machine.set_appointment_data('date', appointment_date)
            
            # Get available slots for this date
            slots = await get_available_slots(appointment_date)
            state_machine.set_available_slots(slots)
            
            if slots:
                state_machine.transition_to(ConversationState.SHOWING_AVAILABLE_SLOTS)
                date_formatted = appointment_date.strftime("%d/%m/%Y")
                slots_text = format_available_slots(slots)
                return f"Ótimo! Para o dia {date_formatted}:\n\n{slots_text}"
            else:
                return f"😕 Infelizmente não há horários disponíveis para {appointment_date.strftime('%d/%m/%Y')}. Poderia escolher outra data?"
        else:
            return "Não consegui identificar a data. Poderia informar novamente? Use formatos como 'hoje', 'amanhã' ou '15/11'."

    elif current_state == ConversationState.SHOWING_AVAILABLE_SLOTS:
        # User should select a slot number
        try:
            slot_number = int(message_text.strip())
            available_slots = state_machine.get_available_slots()
            
            if 1 <= slot_number <= len(available_slots):
                selected_slot = available_slots[slot_number - 1]
                state_machine.set_selected_slot(selected_slot)
                
                # Extract time from slot
                start_time = selected_slot['start'].split('T')[1][:5]
                state_machine.set_appointment_data('time', start_time)
                
                state_machine.transition_to(ConversationState.COLLECTING_PATIENT_INFO)
                return f"✅ Horário {start_time} selecionado!\n\nAgora preciso de suas informações:\nPor favor, me informe seu nome completo e email."
            else:
                return f"Por favor, escolha um número entre 1 e {len(available_slots)}."
        except ValueError:
            return "Por favor, digite apenas o número do horário desejado."

    elif current_state == ConversationState.COLLECTING_PATIENT_INFO:
        name, email = extract_patient_info(message_text)
        
        if name and email:
            state_machine.set_appointment_data('patient_name', name)
            state_machine.set_appointment_data('patient_email', email)
            
            # Show confirmation
            appointment_date = state_machine.get_appointment_data('date')
            appointment_time = state_machine.get_appointment_data('time')
            
            state_machine.transition_to(ConversationState.CONFIRMING_APPOINTMENT)
            
            confirmation_text = f"""
📋 **Confirmação do Agendamento**

👤 **Paciente:** {name}
📧 **Email:** {email}
📅 **Data:** {appointment_date.strftime('%d/%m/%Y')}
🕒 **Horário:** {appointment_time}
🏥 **Local:** Clínica MediNow

Confirma o agendamento? Digite 'SIM' para confirmar ou 'NÃO' para cancelar.
            """
            return confirmation_text
        else:
            missing = []
            if not name:
                missing.append("nome")
            if not email:
                missing.append("email")
            
            return f"Preciso do seu {' e '.join(missing)}. Por favor, informe seu nome completo e email válido."

    elif current_state == ConversationState.CONFIRMING_APPOINTMENT:
        if any(word in message_text.lower() for word in ["sim", "confirma", "confirmar", "ok"]):
            state_machine.transition_to(ConversationState.BOOKING_APPOINTMENT)
            
            # Book the appointment
            try:
                appointment_date = state_machine.get_appointment_data('date')
                appointment_time = state_machine.get_appointment_data('time')
                patient_name = state_machine.get_appointment_data('patient_name')
                patient_email = state_machine.get_appointment_data('patient_email')
                
                # Format datetime for calendar
                start_datetime = f"{appointment_date}T{appointment_time}:00"
                
                # Create calendar event
                result = await calendar_service.create_event(
                    calendar_id="primary",
                    start_datetime=start_datetime,
                    timezone="America/Sao_Paulo",
                    duration_hours=0,
                    duration_minutes=30,
                    summary=f"Consulta médica - {patient_name}",
                    description=f"Consulta agendada via WhatsApp para {patient_name}",
                    location="Clínica MediNow",
                    attendees=[patient_email]
                )
                
                state_machine.transition_to(ConversationState.IDLE)
                state_machine.clear_appointment_data()
                
                return f"""
🎉 **Agendamento Confirmado com Sucesso!**

Sua consulta foi agendada para:
📅 {appointment_date.strftime('%d/%m/%Y')} às {appointment_time}

📧 Você receberá um convite por email com todos os detalhes.

Até breve na Clínica MediNow! 🏥✨
                """
                
            except Exception as e:
                print(f"Error booking appointment: {e}")
                state_machine.transition_to(ConversationState.IDLE)
                return "😓 Ocorreu um erro ao confirmar seu agendamento. Por favor, tente novamente ou entre em contato diretamente com a clínica."
        
        elif any(word in message_text.lower() for word in ["não", "nao", "cancelar", "cancel"]):
            state_machine.transition_to(ConversationState.IDLE)
            state_machine.clear_appointment_data()
            return "❌ Agendamento cancelado. Se precisar de algo mais, é só me chamar!"
        else:
            return "Por favor, responda 'SIM' para confirmar ou 'NÃO' para cancelar o agendamento."

    return "Desculpe, não entendi. Digite 'agendar consulta' para começar um novo agendamento."
