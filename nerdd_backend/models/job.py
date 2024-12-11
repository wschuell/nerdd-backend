from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel

__all__ = ["Job", "JobCreate", "JobPublic"]


class Job(BaseModel):
    id: str
    job_type: str
    source_id: str
    params: dict
    created_at: datetime = datetime.now()
    status: str
    num_entries_total: Optional[int] = None
    num_checkpoints_total: Optional[int] = None
    

class JobCreate(BaseModel):
    job_type: str
    source_id: str
    params: Dict[str, Any]


class JobPublic(Job):
    num_entries_processed: int
    num_pages_total: Optional[int]
    num_pages_processed: int
    page_size: int
    job_url: str
    results_url: str
