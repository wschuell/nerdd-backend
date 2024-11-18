import math
from time import time
from typing import Any, Dict
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request

from ..data import repository
from ..kafka import get_kafka_producer
from ..settings import PAGE_SIZE

__all__ = ["jobs_router"]

jobs_router = APIRouter(prefix="/jobs")


async def augment_job(job, page_size, request: Request):
    num_entries_processed = await repository.get_num_processed_entries_by_job_id(job["id"])
    job["num_entries_processed"] = num_entries_processed

    # TODO
    job["num_pages_processed"] = num_entries_processed // page_size
    if "num_entries_total" in job:
        job["num_pages_total"] = math.ceil(job["num_entries_total"] / page_size)

    job["job_url"] = f"{request.base_url}jobs/{job['id']}"
    job["results_url"] = f"{request.base_url}jobs/{job['id']}/results"

    return job


@jobs_router.post("", include_in_schema=False)
@jobs_router.post("/")
async def create_job(job_type: str, source_id: str, params: Dict[str, Any], request: Request):
    job_id = uuid4()

    # check if module exists
    module = await repository.get_module_by_id(job_type)
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found")

    result = dict(
        id=str(job_id),
        job_type=job_type,
        source_id=source_id,
        params=params,
        timestamp=int(time()),
    )
    await repository.upsert_job(result)

    # send job to kafka
    action = dict(
        id=str(job_id),
        job_type=job_type,
        source_id=source_id,
        action_type="create",
        params=params,
        timestamp=int(time()),
    )
    producer = await get_kafka_producer()
    await producer.send_and_wait("jobs", action)

    # return the response
    return await augment_job(result, PAGE_SIZE, request)


@jobs_router.delete("/{job_id}")
async def delete_job(job_id: str):
    job = await repository.get_job_by_id(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    await repository.delete_job_by_id(job_id)
    return {"message": "Job deleted"}


@jobs_router.get("/{job_id}")
async def get_job(job_id: str, request: Request):
    job = await repository.get_job_by_id(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return await augment_job(job, PAGE_SIZE, request)
