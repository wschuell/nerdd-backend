from fastapi import APIRouter, HTTPException, Request

from ..data import RethinkDbRepository
from ..settings import PAGE_SIZE
from .jobs import get_job

__all__ = ["results_router"]

results_router = APIRouter(prefix="")


@results_router.get("/jobs/{job_id}/results")
async def get_results(
    job_id: str, page: int = 1, return_incomplete: bool = False, request: Request = None
):
    app = request.app
    repository: RethinkDbRepository = app.state.repository

    job = await repository.get_job_by_id(job_id)
    page_zero_based = page - 1

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # num_entries might not be available, yet
    # we assume it to be positive infinity in that case
    num_entries = job.get("num_entries_total", float("inf"))

    # check if page is clearly out of range
    if page_zero_based < 0 or page_zero_based * PAGE_SIZE >= num_entries:
        raise HTTPException(status_code=404, detail="Page out of range")

    first_mol_id = page_zero_based * PAGE_SIZE
    last_mol_id = min(first_mol_id + PAGE_SIZE, num_entries) - 1
    results = await repository.get_results_by_job_id(job_id, first_mol_id, last_mol_id)
    is_incomplete = len(results) < last_mol_id - first_mol_id + 1

    # if return_incomplete is not set, then we need to have all results on that page
    if not return_incomplete and is_incomplete:
        raise HTTPException(status_code=202, detail="Results not yet available")

    job_type = job["job_type"]

    def page_url(p):
        # page in url is 1-based
        return f"{request.base_url}{job_type}/jobs/{job_id}/results?page={p+1}"

    job = await get_job(job_id, request)

    pagination = dict(
        page=page,  # 1-based!
        page_size=PAGE_SIZE,
        is_incomplete=is_incomplete,
        first_mol_id_on_page=first_mol_id,
        last_mol_id_on_page=last_mol_id,
        previous_url=page_url(page_zero_based - 1) if page_zero_based > 0 else None,
        next_url=(page_url(page_zero_based + 1) if last_mol_id < num_entries - 1 else None),
    )

    return dict(data=results, pagination=pagination, job=job)
