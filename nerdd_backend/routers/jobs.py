import math
from time import time
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, Body, HTTPException, Request
from nerdd_link import JobMessage
from pydantic import BaseModel

from ..data import Job, RecordNotFoundError

__all__ = ["jobs_router", "CreateJobRequest"]

jobs_router = APIRouter(prefix="/jobs")


class JobPublic(Job):
    job_url: str
    results_url: str
    num_entries_processed: int
    num_pages_processed: int
    num_pages_total: Optional[int]


async def augment_job(job: Job, request: Request) -> JobPublic:
    app = request.app
    repository = app.state.repository
    page_size = app.state.config.page_size

    num_entries_processed = await repository.get_num_processed_entries_by_job_id(job.id)

    # The number of processed pages is only valid if the computation has not finished yet. We adapt
    # this number in the if statement below.
    num_pages_processed = num_entries_processed // page_size
    if job.num_entries_total is not None:
        num_pages_total = math.ceil(job.num_entries_total / page_size)

        if job.num_entries_total == num_entries_processed:
            num_pages_processed = num_pages_total
    else:
        num_pages_total = None

    return JobPublic(
        **job.model_dump(),
        job_url=f"{request.base_url}jobs/{job.id}",
        results_url=f"{request.base_url}jobs/{job.id}/results",
        num_entries_processed=num_entries_processed,
        num_pages_processed=num_pages_processed,
        num_pages_total=num_pages_total,
    )


class CreateJobRequest(BaseModel):
    job_type: str
    source_id: str
    params: Dict[str, Any]


@jobs_router.post("", include_in_schema=False)
@jobs_router.post("/")
async def create_job(request: Request, request_data: CreateJobRequest = Body()):
    job_type = request_data.job_type
    source_id = request_data.source_id
    params = request_data.params

    app = request.app
    repository = app.state.repository
    channel = app.state.channel

    job_id = uuid4()

    # check if module exists
    module = await repository.get_module_by_id(job_type)
    if module is None:
        all_modules = await repository.get_all_modules()
        valid_options = [module.id for module in all_modules]
        raise HTTPException(
            status_code=404,
            detail=f"Module {job_type} not found. Valid options are: {', '.join(valid_options)}",
        )

    # check if source exists
    try:
        await repository.get_source_by_id(source_id)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail="Source not found") from e

    result = Job(
        id=str(job_id),
        job_type=job_type,
        source_id=source_id,
        params=params,
        status="created",
    )
    # TODO: necessary?
    await repository.upsert_job(result)

    # send job to kafka
    await channel.jobs_topic().send(
        JobMessage(
            id=str(job_id),
            job_type=job_type,
            source_id=source_id,
            params=params,
            timestamp=int(time()),
        )
    )

    # return the response
    return await augment_job(result, request)


@jobs_router.delete("/{job_id}")
async def delete_job(job_id: str, request: Request):
    app = request.app
    repository = app.state.repository

    try:
        await repository.get_job_by_id(job_id)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail="Job not found") from e

    await repository.delete_job_by_id(job_id)
    return {"message": "Job deleted"}


@jobs_router.get("/{job_id}")
async def get_job(job_id: str, request: Request):
    app = request.app
    repository = app.state.repository

    try:
        job = await repository.get_job_by_id(job_id)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail="Job not found") from e

    return await augment_job(job, request)
