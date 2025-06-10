from datetime import datetime

from pydantic import BaseModel


class Challenge(BaseModel):
    id: str
    salt: str
    expires_at: datetime
