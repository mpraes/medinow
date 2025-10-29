"""
WhatsApp webhook handler for Twilio integration.

Handles incoming WhatsApp messages from Twilio, validates webhook requests,
and formats responses in TwiML format for WhatsApp compatibility.
"""

import logging
from typing import Optional
from fastapi import Request, HTTPException, status
from twilio.twiml.messaging_response import MessagingResponse
import hmac
import hashlib

logger = logging.getLogger(__name__)


class TwilioWebhookHandler:
    """
    Handler for Twilio WhatsApp webhook requests.

    Provides validation, message extraction, and TwiML response formatting
    for WhatsApp Business API integration via Twilio.
    """

    def __init__(self, auth_token: Optional[str] = None):
        """
        Initialize the webhook handler.

        Args:
            auth_token: Twilio auth token for request signature validation
        """
        self.auth_token = auth_token

    def validate_webhook_signature(
        self,
        url: str,
        post_data: dict,
        signature: str
    ) -> bool:
        """
        Validate that the webhook request comes from Twilio.

        Validates the X-Twilio-Signature header to ensure the request
        is authentic and hasn't been tampered with.

        Args:
            url: Full webhook URL including scheme, host, and path
            post_data: Dictionary of POST parameters
            signature: X-Twilio-Signature header value

        Returns:
            bool: True if signature is valid, False otherwise
        """
        if not self.auth_token:
            logger.warning("No auth token configured, skipping signature validation")
            return True

        # Concatenate URL and sorted parameters
        data = url
        for key in sorted(post_data.keys()):
            data += key + post_data[key]

        # Compute HMAC-SHA1 signature
        computed_signature = hmac.new(
            self.auth_token.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha1
        ).digest()

        # Base64 encode the result
        import base64
        computed_signature_b64 = base64.b64encode(computed_signature).decode('utf-8')

        return hmac.compare_digest(computed_signature_b64, signature)

    async def extract_message_data(self, request: Request) -> dict:
        """
        Extract message data from Twilio webhook request.

        Args:
            request: FastAPI Request object

        Returns:
            dict: Extracted message data including sender, body, and metadata

        Raises:
            HTTPException: If required fields are missing
        """
        try:
            form_data = await request.form()

            # Extract required fields
            from_number = form_data.get('From', '')
            to_number = form_data.get('To', '')
            message_body = form_data.get('Body', '')
            message_sid = form_data.get('MessageSid', '')

            # Validate required fields
            if not from_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing 'From' field in webhook data"
                )

            if not message_body:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing 'Body' field in webhook data"
                )

            # Extract optional media URLs
            num_media = int(form_data.get('NumMedia', '0'))
            media_urls = []
            for i in range(num_media):
                media_url = form_data.get(f'MediaUrl{i}')
                if media_url:
                    media_urls.append(media_url)

            message_data = {
                'from': from_number,
                'to': to_number,
                'body': message_body,
                'message_sid': message_sid,
                'media_urls': media_urls,
                'profile_name': form_data.get('ProfileName', ''),
                'account_sid': form_data.get('AccountSid', ''),
                'timestamp': form_data.get('SmsMessageSid', ''),
            }

            logger.info(f"Received WhatsApp message from {from_number}: {message_body[:50]}...")

            return message_data

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error extracting message data: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse webhook data: {str(e)}"
            )

    def create_twiml_response(self, message: str) -> str:
        """
        Create a TwiML response for WhatsApp.

        Formats the bot's response in TwiML format that Twilio expects
        for WhatsApp Business API messages.

        Args:
            message: Bot response message text

        Returns:
            str: TwiML-formatted XML response
        """
        response = MessagingResponse()
        response.message(message)

        logger.debug(f"Created TwiML response: {message[:50]}...")

        return str(response)

    def create_twiml_response_with_media(
        self,
        message: str,
        media_url: Optional[str] = None
    ) -> str:
        """
        Create a TwiML response with optional media attachment.

        Args:
            message: Bot response message text
            media_url: Optional URL to media file (image, document, etc.)

        Returns:
            str: TwiML-formatted XML response
        """
        response = MessagingResponse()
        msg = response.message(message)

        if media_url:
            msg.media(media_url)
            logger.debug(f"Added media to TwiML response: {media_url}")

        return str(response)

    def get_session_id_from_phone(self, phone_number: str) -> str:
        """
        Extract or format session ID from phone number.

        Converts WhatsApp phone number format to a clean session ID.
        Example: 'whatsapp:+5511999999999' -> '5511999999999'

        Args:
            phone_number: Phone number in Twilio format

        Returns:
            str: Clean session ID
        """
        # Remove 'whatsapp:' prefix if present
        session_id = phone_number.replace('whatsapp:', '')
        # Remove '+' if present
        session_id = session_id.replace('+', '')
        # Remove any spaces or special characters
        session_id = ''.join(c for c in session_id if c.isalnum())

        return session_id


def format_whatsapp_message(text: str) -> str:
    """
    Format message text for WhatsApp display.

    Converts markdown-style formatting to WhatsApp-compatible format.

    Args:
        text: Message text with markdown formatting

    Returns:
        str: WhatsApp-formatted message
    """
    # WhatsApp supports basic markdown:
    # *bold*, _italic_, ~strikethrough~, ```code```

    # Convert markdown **bold** to WhatsApp *bold*
    text = text.replace('**', '*')

    # Remove markdown headers (not supported in WhatsApp)
    lines = text.split('\n')
    formatted_lines = []
    for line in lines:
        # Remove # headers
        if line.strip().startswith('#'):
            line = line.lstrip('#').strip()
            line = f"*{line}*"  # Make headers bold instead
        formatted_lines.append(line)

    return '\n'.join(formatted_lines)
