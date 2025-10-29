#!/usr/bin/env python3

import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from crewai import Agent, Crew, Task, LLM
import json

from composio import Composio
from composio_crewai import CrewAIProvider

# Coletando a API Key do Groq
groq_api_key = os.getenv('GROQ_API_KEY')

# Coletando API do Composio
composio_api_key = os.getenv('COMPOSIO_API_KEY')

# Get the user ID that was used in authentication
user_id = os.getenv('COMPOSIO_USER_ID', "b752b3b0-754c-4425-9043-098eaf516540")  # Use the authenticated user ID

# Check if GROQ_API_KEY is set
if not groq_api_key:
    print("ERROR: GROQ_API_KEY environment variable is not set")
    print("Please set it in your .env file or environment")
    exit(1)

# Print which API key we're using
print(f"Using GROQ API key: {groq_api_key[:4]}...{groq_api_key[-4:] if len(groq_api_key) > 8 else ''}")

# Configure LLM using CrewAI's LLM class for Groq (correct format)
llm = LLM(
    model="groq/llama-3.1-8b-instant",
    temperature=0
)

# Ferramenta do Composio
composio = Composio(provider=CrewAIProvider(), api_key=composio_api_key or "")

# Trazer a ferramenta específica do Composio usando o user_id autenticado
tools = composio.tools.get(user_id=user_id, toolkits=["GOOGLECALENDAR"])

# Configure the agent to use Groq LLM
crewai_agent = Agent(
    role="Google Calendar Scheduler",
    goal="You take action on Google Calendar to create, update and delete Events using the provided tools",
    backstory=(
        "You are an event manager with access to Google Calendar tools via Composio. "
        "You MUST use the GOOGLECALENDAR_CREATE_EVENT tool to actually create events. "
        "Never generate code - always use the tools directly to perform actions on Google Calendar."
    ),
    verbose=True,
    tools=tools,
    llm=llm,  # Use the LLM instance
    allow_delegation=False
)

# Function to collect user input for event details
def get_event_details():
    print("\n=== Google Calendar Event Creator ===")
    
    # Required parameters
    calendar_id = input("Calendar ID (press Enter for 'primary'): ") or "primary"
    
    # Date and time inputs
    date_input = input("Event date (YYYY-MM-DD): ")
    time_input = input("Event start time (HH:MM): ")
    start_datetime = f"{date_input}T{time_input}:00"
    
    timezone = input("Timezone (press Enter for 'America/Sao_Paulo'): ") or "America/Sao_Paulo"
    
    # Duration
    event_duration_hour = int(input("Event duration hours: ") or "1")
    event_duration_minutes = int(input("Event duration minutes (press Enter for 30): ") or "30")
    
    # Event details
    summary = input("Event title/summary: ")
    description = input("Event description (optional): ")
    location = input("Event location (optional): ")
    
    # Attendees
    attendees = []
    while True:
        email = input("Add attendee email (leave empty to finish adding): ")
        if not email:
            break
        attendees.append(email)
    
    # Prepare event parameters
    event_params = {
        "calendar_id": calendar_id,
        "start_datetime": start_datetime,
        "timezone": timezone,
        "event_duration_hour": event_duration_hour,
        "event_duration_minutes": event_duration_minutes,
        "summary": summary,
    }
    
    # Add optional parameters if provided
    if description:
        event_params["description"] = description
    if location:
        event_params["location"] = location
    if attendees:
        event_params["attendees"] = attendees
    
    return json.dumps(event_params, indent=2)

# Get event parameters from user
event_json = get_event_details()
print(f"\nEvent parameters:\n{event_json}")

# Create the task with user input
task = Task(
    description=(
        f"""You MUST use the GOOGLECALENDAR_CREATE_EVENT tool to actually create an event in Google Calendar.
        
        IMPORTANT: The attendees parameter must be a list of EMAIL STRINGS, not objects with email keys.
        
        Do NOT generate code or provide instructions. Use the tool directly with these exact parameters:
        {event_json}
        
        Call the GOOGLECALENDAR_CREATE_EVENT tool now to create this event and return the actual confirmation details from Google Calendar.
        """
    ),
    agent=crewai_agent,
    expected_output='A successfully created, updated, or deleted event in Google Calendar with confirmation details'
)

# Create a crew with the agent and task
crew = Crew(
    agents=[crewai_agent],
    tasks=[task],
    verbose=True
)

# Run the crew to execute the task
result = crew.kickoff()

print("\n=== Result ===\n")
print(result)