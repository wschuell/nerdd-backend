from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from .job import JobPublic

__all__ = ["Result", "Pagination", "ResultSet"]


class Result(BaseModel):
    id: str
    job_id: str
    mol_id: int

    model_config = ConfigDict(extra="allow")


class Pagination(BaseModel):
    page: int  # 1-based!
    page_size: int
    is_incomplete: bool
    first_mol_id_on_page: int
    last_mol_id_on_page: int
    previous_url: Optional[str]
    next_url: Optional[str]


class ResultSet(BaseModel):
    data: List[Result]
    job: JobPublic
    pagination: Pagination
