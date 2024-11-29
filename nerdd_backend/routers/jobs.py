import math
from time import time
from typing import Any, Dict
from uuid import uuid4

from fastapi import APIRouter, Body, HTTPException, Request
from nerdd_link import JobMessage
from pydantic import BaseModel

__all__ = ["jobs_router"]

jobs_router = APIRouter(prefix="/jobs")


async def augment_job(job, page_size, request: Request):
    app = request.app
    repository = app.state.repository

    num_entries_processed = await repository.get_num_processed_entries_by_job_id(
        job["id"]
    )
    job["num_entries_processed"] = num_entries_processed

    # TODO
    job["num_pages_processed"] = num_entries_processed // page_size
    if "num_entries_total" in job:
        job["num_pages_total"] = math.ceil(job["num_entries_total"] / page_size)

    job["job_url"] = f"{request.base_url}jobs/{job['id']}"
    job["results_url"] = f"{request.base_url}jobs/{job['id']}/results"

    return job


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
        valid_options = [module["id"] for module in all_modules]
        raise HTTPException(
            status_code=404,
            detail=f"Module {job_type} not found. Valid options are: {', '.join(valid_options)}",
        )

    # check if source exists
    source = await repository.get_source_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    result = dict(
        id=str(job_id),
        job_type=job_type,
        source_id=source_id,
        params=params,
        timestamp=int(time()),
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
    return await augment_job(result, PAGE_SIZE, request)


@jobs_router.delete("/{job_id}")
async def delete_job(job_id: str, request: Request):
    app = request.app
    repository = app.state.repository

    job = await repository.get_job_by_id(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    await repository.delete_job_by_id(job_id)
    return {"message": "Job deleted"}


@jobs_router.get("/{job_id}")
async def get_job(job_id: str, request: Request):
    app = request.app
    repository = app.state.repository

    job = await repository.get_job_by_id(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return await augment_job(job, PAGE_SIZE, request)
