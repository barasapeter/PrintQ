from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
import uuid as _uuid

import re


USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,30}$")


class VendorBase(BaseModel):
    name: str
    username: str
    email_address: EmailStr

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        return " ".join(v.strip().split()).title()

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        cleaned = v.strip().replace(" ", "").lower()
        if not USERNAME_PATTERN.match(cleaned):
            raise ValueError(
                "Username must be 3-30 characters and contain only letters, numbers and underscores"
            )
        return cleaned

    @field_validator("email_address")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class VendorCreate(VendorBase):
    password_hash: str


class VendorRead(VendorBase):
    uuid: _uuid.UUID
    username: str
    email_address: EmailStr

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VendorLogin(BaseModel):
    email_address: EmailStr
    password: str
