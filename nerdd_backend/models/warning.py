from typing import Optional

from pydantic import BaseModel

__all__ = ["NerddWarning"]


class NerddWarning(BaseModel):
    id: str
    rank: Optional[int] = None
    name: Optional[str] = None
    visible: Optional[str] = None
