# test_both_approaches.py
import os
from dotenv import load_dotenv
load_dotenv()

print("=== Environment Variables ===")
print(f"COMPOSIO_API_KEY: {'✓ Set' if 
os.getenv('COMPOSIO_API_KEY') else '❌ Missing'}")
print(f"GROQ_API_KEY: {'✓ Set' if os.getenv('GROQ_API_KEY') else 
'❌ Missing'}")
print(f"COMPOSIO_USER_ID: {'✓ Set' if 
os.getenv('COMPOSIO_USER_ID') else '❌ Missing'}")

print("\n=== Testing create_events_gmail.py approach ===")
try:
    from composio import Composio
    from composio_crewai import CrewAIProvider
    from crewai import Agent, LLM

    # Get the API keys from environment variables
    composio_api_key = os.getenv('COMPOSIO_API_KEY')
    groq_api_key = os.getenv('GROQ_API_KEY')
    user_id = os.getenv('COMPOSIO_USER_ID')

    # Configure LLM
    llm = LLM(
        model="groq/llama-3.1-8b-instant",
        temperature=0
    )

    # Initialize Composio
    composio = Composio(provider=CrewAIProvider(), api_key=composio_api_key)

    # Get tools
    tools = composio.tools.get(user_id=user_id, toolkits=["GOOGLECALENDAR"])

    print("Script approach works! Tools retrieved successfully.")
except Exception as e:
    print(f"Script approach failed: {type(e).__name__}: {str(e)}")

print("\n=== Testing FastAPI service approach ===")
try:
    from backend.api.services.simple_composio_calendar_service import SimpleComposioCalendarService
    service = SimpleComposioCalendarService()
    print(f"Service initialized successfully: {service.is_available()}")
except Exception as e:
    print(f"Service initialization failed: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()