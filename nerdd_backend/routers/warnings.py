from fastapi import APIRouter, HTTPException, Request

from ..data import RecordNotFoundError
from ..models import NerddWarning

__all__ = ["warnings_router"]

warnings_router = APIRouter(prefix="/warnings")


@warnings_router.get("", include_in_schema=False)
@warnings_router.get("/")
async def get_warnings(request: Request):
    app = request.app
    repository = app.state.repository

    warnings = await repository.get_all_warnings()
    return [
        # NerddWarning(
        #     **warning.model_dump(), warning_url=f"{request.base_url}{warning.id}"
        # )
        warning
        for warning in warnings
        if warning.visible
    ]
