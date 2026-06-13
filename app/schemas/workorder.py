from datetime import datetime

from pydantic import BaseModel, ConfigDict

import uuid as _uuid


class PrintJobBase(BaseModel):
    customer_uuid: _uuid.UUID
    shop_uuid: _uuid.UUID


class PrintJobCreate(PrintJobBase):
    pass


class PrintJobRead(PrintJobBase):
    uuid: _uuid.UUID
    shop_uuid: _uuid.UUID

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
