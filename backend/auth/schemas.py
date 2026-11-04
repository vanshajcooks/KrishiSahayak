"""
Authentication Data Models and Schemas (SIH 26180)
Strict Pydantic models for phone verification, registration, and farmer profile responses.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
import re


# E.164 phone regex (e.g. +919876543210)
E164_REGEX = re.compile(r"^\+[1-9]\d{7,14}$")


def normalize_phone_number(raw_phone: str) -> str:
    """
    Normalizes input phone number to E.164 format.
    Specifically supports Indian standard numbers (10 digits starting with 6-9, with or without leading 0, 91, or +91).
    Rejects malformed or invalid strings.
    """
    if not raw_phone or not isinstance(raw_phone, str):
        raise ValueError("Phone number is required")

    # Strip whitespace, hyphens, parentheses
    cleaned = re.sub(r"[\s\-\(\)\.]", "", raw_phone)

    # If already starts with '+', validate directly against E.164
    if cleaned.startswith("+"):
        if not E164_REGEX.match(cleaned):
            raise ValueError("Invalid international E.164 phone number format")
        # If it's an Indian number starting with +91, ensure exactly 10 digits follow
        if cleaned.startswith("+91"):
            digits = cleaned[3:]
            if len(digits) != 10 or not digits[0] in "6789":
                raise ValueError("Invalid Indian mobile number; must be 10 digits starting with 6-9")
        return cleaned

    # Check for Indian standard numbers
    # Case 1: 10 digits starting with 6-9
    if re.match(r"^[6-9]\d{9}$", cleaned):
        return f"+91{cleaned}"

    # Case 2: 11 digits starting with 0 followed by 6-9
    if re.match(r"^0[6-9]\d{9}$", cleaned):
        return f"+91{cleaned[1:]}"

    # Case 3: 12 digits starting with 91 followed by 6-9
    if re.match(r"^91[6-9]\d{9}$", cleaned):
        return f"+{cleaned}"

    # If non-standard or foreign without '+', reject
    raise ValueError(
        "Invalid phone number. Please provide a valid 10-digit Indian mobile number or full E.164 format (+91XXXXXXXXXX)"
    )


class OTPSendRequest(BaseModel):
    phone: str = Field(..., description="Farmer mobile number (10 digits or E.164 format)")

    @field_validator("phone")
    @classmethod
    def validate_and_normalize_phone(cls, v: str) -> str:
        return normalize_phone_number(v)


class OTPSendResponse(BaseModel):
    status: str = Field(default="pending")
    message: str = Field(default="Verification code sent if phone number is eligible.")


class OTPVerifyRequest(BaseModel):
    phone: str = Field(..., description="Farmer mobile number")
    code: str = Field(..., min_length=4, max_length=10, description="Verification code received via SMS")

    @field_validator("phone")
    @classmethod
    def validate_and_normalize_phone(cls, v: str) -> str:
        return normalize_phone_number(v)

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        code_cleaned = v.strip()
        if not code_cleaned.isdigit():
            raise ValueError("Verification code must contain only digits")
        return code_cleaned


class FarmerProfile(BaseModel):
    uuid: str
    name: str
    phone: str
    preferred_language: str
    state: Optional[str] = None
    district: Optional[str] = None
    village: Optional[str] = None
    created_at: str
    last_login_at: Optional[str] = None
    is_active: bool


class FieldSummary(BaseModel):
    uuid: str
    name: str
    crop_type: str
    soil_type: Optional[str] = None
    area_acres: Optional[float] = None
    sensor_count: int = 0


class AuthMeResponse(BaseModel):
    farmer: FarmerProfile
    fields: List[FieldSummary] = Field(default_factory=list)
    active_sensor_count: int = 0


class OTPVerifyResponse(BaseModel):
    is_registered: bool
    message: str
    farmer: Optional[FarmerProfile] = None
    registration_token: Optional[str] = None


class FarmerRegisterRequest(BaseModel):
    registration_token: str = Field(..., description="Short-lived token received from successful OTP verification")
    name: str = Field(..., min_length=2, max_length=100, description="Farmer full name")
    preferred_language: str = Field(default="en", max_length=10, description="Preferred app language ('en', 'hi')")
    state: Optional[str] = Field(default=None, max_length=100)
    district: Optional[str] = Field(default=None, max_length=100)
    village: Optional[str] = Field(default=None, max_length=100)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if len(stripped) < 2:
            raise ValueError("Farmer name must be at least 2 characters")
        return stripped


class AuthMessageResponse(BaseModel):
    status: str = Field(default="success")
    message: str
