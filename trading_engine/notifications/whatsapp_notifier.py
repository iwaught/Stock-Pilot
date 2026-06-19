"""
WhatsApp notification module using Twilio API.
Sends trading signals to a configured WhatsApp number.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def send_whatsapp_message(message: str, to: str = None, from_: str = None) -> bool:
    """
    Send a WhatsApp message via Twilio.

    Args:
        message: Text body to send.
        to: Destination WhatsApp number (e.g. 'whatsapp:+56912345678').
            Falls back to WHATSAPP_TO env variable.
        from_: Twilio sender number (e.g. 'whatsapp:+14155238886').
            Falls back to TWILIO_WHATSAPP_FROM env variable.

    Returns:
        True if the message was sent successfully, False otherwise.
    """
    try:
        from twilio.rest import Client
    except ImportError:
        logger.error("Twilio package is not installed. Run: pip install twilio")
        return False

    import trading_engine.config as cfg

    account_sid = cfg.TWILIO_ACCOUNT_SID
    auth_token = cfg.TWILIO_AUTH_TOKEN
    from_number = from_ or cfg.TWILIO_WHATSAPP_FROM
    to_number = to or cfg.WHATSAPP_TO

    if not all([account_sid, auth_token, from_number, to_number]):
        logger.error(
            "Twilio credentials not configured. "
            "Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, "
            "TWILIO_WHATSAPP_FROM, and WHATSAPP_TO in your .env file."
        )
        return False

    try:
        client = Client(account_sid, auth_token)
        msg = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number,
        )
        logger.info("WhatsApp message sent. SID: %s", msg.sid)
        return True
    except Exception as exc:
        logger.error("Failed to send WhatsApp message: %s", exc)
        return False


def check_whatsapp_configured() -> dict:
    """Return status dict indicating whether WhatsApp is properly configured."""
    import trading_engine.config as cfg

    configured = bool(
        cfg.TWILIO_ACCOUNT_SID
        and cfg.TWILIO_AUTH_TOKEN
        and cfg.TWILIO_WHATSAPP_FROM
        and cfg.WHATSAPP_TO
    )
    return {
        "configured": configured,
        "from": cfg.TWILIO_WHATSAPP_FROM if configured else None,
        "to": cfg.WHATSAPP_TO if configured else None,
    }
