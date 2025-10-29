from composio import Composio
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

# Get the API key and auth config ID from environment variables
composio_api_key = os.getenv('COMPOSIO_API_KEY')
googlecalendar_auth_config_id = os.getenv('GOOGLE_CALENDAR_AUTH_KEY')  # Auth config ID from Composio dashboard
user_id = str(uuid.uuid4())  # Generate a unique user ID

# Check if API key is available
if not composio_api_key:
    raise ValueError("COMPOSIO_API_KEY not found in environment variables")

# Initialize Composio with API key
composio = Composio(api_key=composio_api_key)

def authenticate_toolkit(user_id: str, auth_config_id: str):
    """
    Authenticate the Google Calendar toolkit for a specific user
    """
    try:
        print(f"Starting authentication for user: {user_id}")
        print(f"Using auth config ID: {auth_config_id}")
        
        # Initiate the connection
        connection_request = composio.connected_accounts.initiate(
            user_id=user_id,
            auth_config_id=auth_config_id,
        )
        
        print(f"Visit this URL to authenticate Google Calendar: {connection_request.redirect_url}")
        print("Please complete the authentication in your browser...")
        
        # Wait for the auth flow to be completed
        connection_request.wait_for_connection(timeout=120)  # Increased timeout to 2 minutes
        
        print("Authentication completed successfully!")
        return connection_request.id
        
    except Exception as e:
        print(f"Error during authentication: {e}")
        return None

def main():
    """
    Main function to run the authentication flow
    """
    if not composio_api_key:
        print("Error: COMPOSIO_API_KEY not found in environment variables")
        return
        
    if not googlecalendar_auth_config_id:
        print("Error: GOOGLE_CALENDAR_AUTH_KEY not found in environment variables")
        return
    
    print("=== Google Calendar Authentication ===")
    print(f"API Key: {composio_api_key[:10]}...")
    print(f"Auth Config ID: {googlecalendar_auth_config_id}")
    print(f"User ID: {user_id}")
    
    # Authenticate the toolkit
    connection_id = authenticate_toolkit(user_id, googlecalendar_auth_config_id)
    
    if connection_id:
        print(f"Connection ID: {connection_id}")
        
        # Verify the connection status
        try:
            connected_account = composio.connected_accounts.get(connection_id)
            print(f"Connected account details: {connected_account}")
            print("✅ Google Calendar authentication successful!")
        except Exception as e:
            print(f"Error verifying connection: {e}")
    else:
        print("❌ Authentication failed")

if __name__ == "__main__":
    main()
