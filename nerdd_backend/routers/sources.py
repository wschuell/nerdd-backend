import asyncio
import json
import os
from io import BytesIO
from typing import List, Optional
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, HTTPException, Request, UploadFile

from ..data import RethinkDbRepository, Source
from ..settings import MEDIA_ROOT

sources_router = APIRouter(prefix="/sources")


async def put_multiple_sources(
    inputs: List[str],
    sources: List[str],
    files: List[UploadFile],
    repository: RethinkDbRepository,
):
    all_sources = []

    # create source from inputs list
    if len(inputs) > 0:

        async def _put_input(input: str):
            file_stream = BytesIO(input.encode("utf-8"))
            file = UploadFile(file_stream)
            return await put_source(file=file)

        sources_from_inputs = await asyncio.gather(
            *[_put_input(input) for input in inputs]
        )
        all_sources += sources_from_inputs

    for source_id in sources:
        source = await repository.get_source_by_id(source_id)
        if source is not None:
            all_sources.append(source)

    # create one json file referencing all sources
    sources_from_files = await asyncio.gather(
        *[put_source(file=file) for file in files]
    )
    all_sources += sources_from_files

    # create a merged file with all sources
    file_stream = BytesIO(json.dumps(all_sources).encode("utf-8"))
    file = UploadFile(file_stream, filename="input.json")
    result_source = await put_source(file=file, format="json")

    return result_source


@sources_router.put("", include_in_schema=False)
@sources_router.put("/")
async def put_source(request: Request, file: UploadFile, format: Optional[str] = None):
    app = request.app
    repository: RethinkDbRepository = app.state.repository

    # create uuid
    uuid = uuid4()

    # create path to new file
    path = os.path.join(MEDIA_ROOT, "sources", str(uuid))
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # store file
    async with aiofiles.open(path, "wb") as out_file:
        while content := await file.read(1024):  # async read chunk
            await out_file.write(content)  # async write chunk

    # create media object
    source = Source(
        id=str(uuid),
        format=format,
        filename=file.filename,
    )
    await repository.upsert_source(source)

    return source


@sources_router.get("/{uuid}")
async def get_source(request: Request, uuid: str):
    app = request.app
    repository: RethinkDbRepository = app.state.repository

    source = await repository.get_source_by_id(uuid)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    return source


@sources_router.delete("/{uuid}")
async def delete_source(request: Request, uuid: str):
    app = request.app
    repository: RethinkDbRepository = app.state.repository

    source = await repository.get_source_by_id(uuid)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    # delete file from disk
    path = os.path.join(MEDIA_ROOT, "sources", str(uuid))
    os.remove(path)

    # delete source from database
    await repository.delete_source_by_id(uuid)
