# test_fastapi_init.py
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

print("\n=== Simulating FastAPI initialization ===")
from backend.api.services.simple_composio_calendar_service import SimpleComposioCalendarService

# Initialize the service
calendar_service = None
try:
    calendar_service = SimpleComposioCalendarService()
    print(f"Direct initialization: Service available = {calendar_service.is_available()}")
except Exception as e:
    print(f"Error initializing directly: {type(e).__name__}: {str(e)}")

# Simulate startup event
try:
    async def startup_simulation():
        global calendar_service
        try:
            if calendar_service is None:
                calendar_service = SimpleComposioCalendarService()
            print(f"Startup event: Service available = {calendar_service.is_available()}")
        except Exception as e:
            print(f"Error in startup event: {type(e).__name__}:{str(e)}")

    # Run the async function
    import asyncio
    asyncio.run(startup_simulation())
except Exception as e:
    print(f"Error running startup simulation: {type(e).__name__}: {str(e)}")

# Check health (similar to health endpoint)
try:
    calendar_available = calendar_service is not None and calendar_service.is_available()
    print(f"Health check simulation: calendar_available = {calendar_available}")
except Exception as e:
    print(f"Error in health check: {type(e).__name__}: {str(e)}")