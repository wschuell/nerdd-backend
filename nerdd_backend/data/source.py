from datetime import datetime
from typing import Optional

from pydantic import BaseModel

__all__ = ["Source"]


class Source(BaseModel):
    id: str
    format: Optional[str] = None
    filename: str
    created_at: datetime = datetime.now()
