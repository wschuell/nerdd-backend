from datetime import datetime
from typing import Optional

from pydantic import BaseModel

__all__ = ["Job"]


class Job(BaseModel):
    id: str
    job_type: str
    source_id: str
    params: dict
    created_at: datetime = datetime.now()
    status: str
    num_entries_total: Optional[int] = None
