from datetime import datetime
from typing import Optional

from pydantic import BaseModel

__all__ = ["Job"]


class Job(BaseModel):
    id: Optional[str] = None
    job_type: str
    source_id: str
    params: dict
    created_at: datetime
    status: str
