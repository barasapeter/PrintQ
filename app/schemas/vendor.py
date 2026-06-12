from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr
import uuid as _uuid


class VendorBase(BaseModel):
    name: str
    username: str
    email_address: EmailStr
    password: str


class VendorCreate(VendorBase):
    pass


class VendorRead(VendorBase):
    uuid: _uuid.UUID
    username: str
    email_address: EmailStr

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
