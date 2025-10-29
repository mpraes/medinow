"""
Test script for Groq API connectivity and response.
This script tests if we can connect to the Groq API and get a valid response.
"""

import os
import sys
from dotenv import load_dotenv
import requests
import json

# Load environment variables from .env file
load_dotenv()

# Get the Groq API key from environment
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    print("❌ Error: GROQ_API_KEY not found in environment variables.")
    print("Make sure you have a valid .env file with the GROQ_API_KEY defined.")
    sys.exit(1)

# Groq API endpoint
api_url = "https://api.groq.com/openai/v1/chat/completions"

# Set up headers with API key
headers = {
    "Authorization": f"Bearer {groq_api_key}",
    "Content-Type": "application/json"
}

# Test prompt for the LLM
data = {
    "model": "llama-3.1-8b-instant",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, please respond with a simple 'Hello, I am working!' message to test connectivity."}
    ],
    "temperature": 0
}

print("Testing connection to Groq API...")
print(f"Using model: llama-3.1-8b-instant")

try:
    # Make the request to Groq API
    response = requests.post(api_url, headers=headers, json=data, timeout=30)

    # Check if request was successful
    if response.status_code == 200:
        result = response.json()

        # Print the response for inspection
        print("\n✅ Success! Received response from Groq API:")
        if "choices" in result and len(result["choices"]) > 0:
            message_content = result["choices"][0]["message"]["content"]
            print(f"\nLLM Response: {message_content}")
            print("\nFull API Response:")
            print(json.dumps(result, indent=2))
        else:
            print("❌ Warning: Response format unexpected.")
            print("Response content:")
            print(json.dumps(result, indent=2))
    else:
        print(f"❌ Error: Received status code {response.status_code}")
        print("Response content:")
        print(response.text)

except Exception as e:
    print(f"❌ Error connecting to Groq API: {str(e)}")
    print("This could indicate network issues, invalid API key, or service unavailability.")

print("\nTest completed.")