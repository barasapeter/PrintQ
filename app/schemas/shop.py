from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator
import uuid as _uuid


class ShopBase(BaseModel):
    vendor_uuid: _uuid.UUID
    name: str
    location: str
    phone_contact: str
    properties: dict

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        return " ".join(v.strip().split()).title()


class ShopCreate(ShopBase):
    pass


class ShopRead(ShopBase):
    uuid: _uuid.UUID
    name: str
    location: str

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
