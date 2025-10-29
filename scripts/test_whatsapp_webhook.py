#!/usr/bin/env python
"""
Test script for WhatsApp webhook integration.

This script simulates Twilio webhooks to test the WhatsApp integration
without requiring an actual Twilio account. It sends mock webhook requests
to the local API endpoint and validates the TwiML responses.
"""

import argparse
import requests
import sys
import os
import hmac
import hashlib
import base64
from urllib.parse import urlencode
from xml.etree import ElementTree

# Add parent directory to path to import from backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.integrations.twilio.webhook_handler import TwilioWebhookHandler

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def generate_twilio_signature(auth_token, url, params):
    """
    Generate a Twilio signature for a webhook request.

    Args:
        auth_token: Twilio auth token
        url: Full webhook URL
        params: Dictionary of form parameters

    Returns:
        str: Base64-encoded HMAC-SHA1 signature
    """
    # Sort the parameters
    sorted_params = sorted(params.items())

    # Concatenate URL and parameters
    data = url
    for k, v in sorted_params:
        data += k + v

    # Compute HMAC-SHA1 signature
    hmac_obj = hmac.new(
        auth_token.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha1
    )

    # Return Base64 encoded signature
    return base64.b64encode(hmac_obj.digest()).decode('utf-8')

def parse_twiml_response(xml_response):
    """
    Parse a TwiML response.

    Args:
        xml_response: TwiML XML string

    Returns:
        str: Extracted message text
    """
    try:
        root = ElementTree.fromstring(xml_response)
        message_elem = root.find(".//Message")
        if message_elem is not None and message_elem.text:
            return message_elem.text
        else:
            # Try the Body element
            body_elem = root.find(".//Body")
            if body_elem is not None and body_elem.text:
                return body_elem.text

        return "No message content found"
    except Exception as e:
        return f"Error parsing TwiML: {e}"

def test_whatsapp_webhook(base_url, auth_token=None):
    """
    Test the WhatsApp webhook endpoint.

    Args:
        base_url: Base API URL
        auth_token: Optional Twilio auth token for signature validation
    """
    print_section("WHATSAPP WEBHOOK TEST")

    webhook_url = f"{base_url}/api/webhook/whatsapp"
    print(f"Testing webhook endpoint: {webhook_url}")

    # Test parameters
    messages = [
        {
            "description": "Initial greeting",
            "body": "Olá",
            "from_number": "whatsapp:+5511999999999",
            "to_number": "whatsapp:+14155238886"
        },
        {
            "description": "Appointment request",
            "body": "Quero agendar uma consulta",
            "from_number": "whatsapp:+5511999999999",
            "to_number": "whatsapp:+14155238886"
        },
        {
            "description": "Date specification",
            "body": "amanhã",
            "from_number": "whatsapp:+5511999999999",
            "to_number": "whatsapp:+14155238886"
        },
        {
            "description": "With media",
            "body": "Aqui está meu documento",
            "from_number": "whatsapp:+5511999999999",
            "to_number": "whatsapp:+14155238886",
            "media": True
        }
    ]

    all_passed = True

    for i, msg_config in enumerate(messages):
        print_section(f"TEST {i+1}: {msg_config['description']}")

        # Prepare form data
        form_data = {
            "From": msg_config["from_number"],
            "To": msg_config["to_number"],
            "Body": msg_config["body"],
            "MessageSid": f"SM{i}123456789abcdef",
            "AccountSid": "AC123456789abcdef",
            "SmsMessageSid": f"SM{i}123456789abcdef",
        }

        # Add media if specified
        if msg_config.get("media", False):
            form_data["NumMedia"] = "1"
            form_data["MediaUrl0"] = "https://example.com/image.jpg"
            form_data["MediaContentType0"] = "image/jpeg"
        else:
            form_data["NumMedia"] = "0"

        # Generate Twilio signature if auth token is provided
        headers = {}
        if auth_token:
            signature = generate_twilio_signature(auth_token, webhook_url, form_data)
            headers["X-Twilio-Signature"] = signature

        # Send webhook request
        print(f"Sending message: '{msg_config['body']}'")

        try:
            response = requests.post(webhook_url, data=form_data, headers=headers)

            # Print status code
            print(f"Status code: {response.status_code}")

            # Check if response was successful
            if response.status_code == 200:
                print("✓ Webhook request successful")

                # Parse TwiML response
                content_type = response.headers.get("Content-Type", "")
                if "xml" in content_type.lower():
                    print("✓ Response is XML/TwiML format")

                    # Extract message from TwiML
                    message_text = parse_twiml_response(response.text)
                    print(f"Response message: {message_text}")

                    if message_text and len(message_text) > 0:
                        print("✓ TwiML contains a message")
                    else:
                        print("✗ TwiML does not contain a message")
                        all_passed = False
                else:
                    print(f"✗ Response is not XML/TwiML format: {content_type}")
                    print(f"Response content: {response.text[:200]}...")
                    all_passed = False
            else:
                print(f"✗ Webhook request failed with status {response.status_code}")
                print(f"Response content: {response.text[:200]}...")
                all_passed = False

        except Exception as e:
            print(f"✗ Error testing webhook: {e}")
            all_passed = False

    # Print final summary
    print_section("TEST SUMMARY")
    if all_passed:
        print("✅ All WhatsApp webhook tests PASSED")
    else:
        print("❌ Some WhatsApp webhook tests FAILED")

    return all_passed

def test_webhook_handler():
    """Test the TwilioWebhookHandler class directly."""
    print_section("WEBHOOK HANDLER UNIT TEST")

    # Create a webhook handler
    handler = TwilioWebhookHandler(auth_token="test_token")

    # Test signature validation
    print("Testing signature validation...")
    url = "https://example.com/webhook"
    params = {"Body": "Hello", "From": "+123456789"}
    signature = generate_twilio_signature("test_token", url, params)

    is_valid = handler.validate_webhook_signature(url, params, signature)
    print(f"Signature validation result: {is_valid}")

    if is_valid:
        print("✓ Signature validation passed")
    else:
        print("✗ Signature validation failed")

    # Test message formatting
    print("\nTesting WhatsApp message formatting...")
    message = """
    # Header

    This is a **bold** text with some _italic_ formatting.

    ## Subheader

    1. Item one
    2. Item two
    """

    from backend.integrations.twilio.webhook_handler import format_whatsapp_message
    formatted = format_whatsapp_message(message)

    print(f"Original message:\n{message}")
    print(f"Formatted message:\n{formatted}")

    # Test TwiML creation
    print("\nTesting TwiML response creation...")
    twiml = handler.create_twiml_response("Hello, world!")
    print(f"TwiML response:\n{twiml}")

    # Test TwiML with media
    print("\nTesting TwiML response with media...")
    twiml_media = handler.create_twiml_response_with_media(
        "Check this image",
        "https://example.com/image.jpg"
    )
    print(f"TwiML with media response:\n{twiml_media}")

    # Test phone number normalization
    print("\nTesting phone number normalization...")
    phone_numbers = [
        "whatsapp:+5511999999999",
        "+5511999999999",
        "5511999999999"
    ]

    for phone in phone_numbers:
        session_id = handler.get_session_id_from_phone(phone)
        print(f"Phone: {phone} -> Session ID: {session_id}")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Test WhatsApp webhook integration")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base API URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--auth-token",
        help="Twilio auth token for signature validation"
    )
    parser.add_argument(
        "--handler-only",
        action="store_true",
        help="Test only the webhook handler, not the API endpoint"
    )

    args = parser.parse_args()

    print_section("WHATSAPP WEBHOOK INTEGRATION TEST")
    print(f"Base URL: {args.url}")
    print(f"Auth Token: {'Provided' if args.auth_token else 'Not provided'}")

    # Run tests
    if args.handler_only:
        # Test only the webhook handler
        test_webhook_handler()
    else:
        # Test both handler and API endpoint
        test_webhook_handler()
        test_whatsapp_webhook(args.url, args.auth_token)

if __name__ == "__main__":
    main()