from fastapi import APIRouter, HTTPException, Request

__all__ = ["modules_router"]

modules_router = APIRouter(prefix="/modules")


@modules_router.get("", include_in_schema=False)
@modules_router.get("/")
async def get_modules(request: Request):
    app = request.app
    repository = app.state.repository

    modules = await repository.get_all_modules()
    return modules


@modules_router.get("/{module_id}")
async def get_module(module_id: str, request: Request):
    app = request.app
    repository = app.state.repository

    module = await repository.get_module_by_id(module_id)

    if module is None:
        raise HTTPException(status_code=404, detail="Module not found")

    return module
