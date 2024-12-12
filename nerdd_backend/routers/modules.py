from fastapi import APIRouter, HTTPException, Request

from ..data import RecordNotFoundError
from ..models import ModulePublic, ModuleShort

__all__ = ["modules_router"]

modules_router = APIRouter(prefix="/modules")


@modules_router.get("", include_in_schema=False)
@modules_router.get("/")
async def get_modules(request: Request):
    app = request.app
    repository = app.state.repository

    modules = await repository.get_all_modules()
    return [
        ModuleShort(**module.model_dump(), module_url=f"{request.base_url}{module.id}")
        for module in modules
    ]


@modules_router.get("/{module_id}")
async def get_module(module_id: str, request: Request):
    app = request.app
    repository = app.state.repository

    try:
        module = await repository.get_module_by_id(module_id)
    except RecordNotFoundError:
        raise HTTPException(status_code=404, detail="Module not found")

    return ModulePublic(**module.model_dump(), module_url=request.url.path)
