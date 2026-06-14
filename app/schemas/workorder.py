from pydantic import BaseModel, ConfigDict, Field
import uuid as _uuid
from datetime import datetime


class PrintJobBase(BaseModel):
    uuid: _uuid.UUID = Field(default_factory=_uuid.uuid4)
    customer_uuid: _uuid.UUID
    shop_uuid: _uuid.UUID
    properties: dict


class PrintJobCreate(PrintJobBase):
    pass


class PrintJobRead(PrintJobBase):
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
