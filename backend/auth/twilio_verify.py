"""
Twilio Verify Service Adapter (SIH 26180)
Integrates with Twilio Verify v2 API to send and verify SMS one-time passwords.
Never generates, stores, or handles raw verification codes in local memory or database.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger("smart_farming.auth.twilio")


class TwilioVerifyClient:
    """
    Encapsulates Twilio Verify v2 API interaction.
    Gracefully handles missing credentials during unit testing or offline edge operation.
    """

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        service_sid: Optional[str] = None,
    ):
        self.account_sid = account_sid or os.environ.get("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.environ.get("TWILIO_AUTH_TOKEN")
        self.service_sid = service_sid or os.environ.get("TWILIO_VERIFY_SERVICE_SID")
        self._client = None

    @property
    def is_configured(self) -> bool:
        """Returns True if all required Twilio Verify credentials exist."""
        return bool(self.account_sid and self.auth_token and self.service_sid)

    def _get_client(self):
        if not self.is_configured:
            raise RuntimeError(
                "Twilio Verify is not fully configured. Ensure TWILIO_ACCOUNT_SID, "
                "TWILIO_AUTH_TOKEN, and TWILIO_VERIFY_SERVICE_SID are set in the environment."
            )
        if self._client is None:
            try:
                from twilio.rest import Client
                self._client = Client(self.account_sid, self.auth_token)
            except Exception as exc:
                logger.error("Failed to initialize Twilio REST Client: %s", exc)
                raise RuntimeError("Failed to initialize Twilio client") from exc
        return self._client

    def send_verification(self, phone: str) -> bool:
        """
        Requests Twilio Verify to send an SMS verification code to the given E.164 phone.
        Returns True if verification state was created with status 'pending'.
        """
        client = self._get_client()
        try:
            verification = (
                client.verify.v2.services(self.service_sid)
                .verifications.create(to=phone, channel="sms")
            )
            return verification.status == "pending"
        except Exception as exc:
            logger.error("Twilio Verify send error for %s: %s", phone[:6] + "****", exc)
            raise

    def check_verification(self, phone: str, code: str) -> bool:
        """
        Validates the user-submitted code against Twilio Verify.
        Returns True ONLY if status is 'approved'.
        """
        client = self._get_client()
        try:
            check = (
                client.verify.v2.services(self.service_sid)
                .verification_checks.create(to=phone, code=code)
            )
            return check.status == "approved"
        except Exception as exc:
            logger.error("Twilio Verify check error for %s: %s", phone[:6] + "****", exc)
            return False


# Global default client instance
_default_twilio_client: Optional[TwilioVerifyClient] = None


def get_twilio_client() -> TwilioVerifyClient:
    """Returns the application-wide Twilio Verify client."""
    global _default_twilio_client
    if _default_twilio_client is None:
        _default_twilio_client = TwilioVerifyClient()
    return _default_twilio_client


def set_twilio_client(client: Optional[TwilioVerifyClient]) -> None:
    """Sets the application-wide Twilio Verify client (used for tests/mocking)."""
    global _default_twilio_client
    _default_twilio_client = client
