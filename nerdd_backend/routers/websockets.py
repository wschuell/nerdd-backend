from fastapi import APIRouter, HTTPException, Query, WebSocket

from ..settings import PAGE_SIZE
from .jobs import get_job

__all__ = ["get_job_ws", "get_results_ws", "websockets_router"]

websockets_router = APIRouter(prefix="/websocket")


@websockets_router.websocket("/jobs/{job_id}")
@websockets_router.websocket("/jobs/{job_id}/")
async def get_job_ws(websocket: WebSocket, job_id: str):
    app = websocket.app
    repository = app.state.repository

    await websocket.accept()

    job = await get_job(job_id, websocket)
    await websocket.send_json(job)

    cursor = await repository.get_job_changes(job_id)
    async for _ in cursor:
        job = await get_job(job_id, websocket)
        await websocket.send_json(job)


@websockets_router.websocket("/jobs/{job_id}/results")
@websockets_router.websocket("/jobs/{job_id}/results/")
async def get_results_ws(websocket: WebSocket, job_id: str, page: int = Query()):
    app = websocket.app
    repository = app.state.repository

    await websocket.accept()

    job = await repository.get_job_by_id(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # num_entries might not be available, yet
    # we assume it to be positive infinity in that case
    num_entries = job.get("num_entries_total", float("inf"))

    page_zero_based = page - 1

    # check if page is clearly out of range
    if page_zero_based < 0 or page_zero_based * PAGE_SIZE >= num_entries:
        raise HTTPException(status_code=404, detail="Page out of range")

    first_mol_id = page_zero_based * PAGE_SIZE
    last_mol_id = min(first_mol_id + PAGE_SIZE, num_entries) - 1

    cursor = await repository.get_result_changes(job_id, first_mol_id, last_mol_id)
    async for result in cursor:
        await websocket.send_json(result)
