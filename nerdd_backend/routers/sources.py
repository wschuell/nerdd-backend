import asyncio
import json
import os
from io import BytesIO
from typing import List, Optional
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, HTTPException, Request, UploadFile
from fastapi.encoders import jsonable_encoder

from ..data import RecordNotFoundError, Repository
from ..models import Source, SourcePublic

__all__ = ["sources_router", "put_multiple_sources"]

sources_router = APIRouter(prefix="/sources")


@sources_router.put("", include_in_schema=False)
@sources_router.put("/")
async def put_source(file: UploadFile, format: Optional[str] = None, request: Request = None):
    app = request.app
    repository: Repository = app.state.repository
    media_root = app.state.config.media_root

    # create uuid
    uuid = uuid4()

    # create path to new file
    # TODO: use FileSystem
    path = os.path.join(media_root, "sources", str(uuid))
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
    await repository.create_source(source)

    return SourcePublic(**source.model_dump())


@sources_router.get("/{uuid}")
async def get_source(uuid: str, request: Request):
    app = request.app
    repository: Repository = app.state.repository
    try:
        source = await repository.get_source_by_id(uuid)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail="Source not found") from e

    return SourcePublic(**source.model_dump())


@sources_router.delete("/{uuid}")
async def delete_source(uuid: str, request: Request):
    app = request.app
    repository: Repository = app.state.repository
    media_root = app.state.config.media_root

    try:
        await repository.get_source_by_id(uuid)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail="Source not found") from e

    # delete file from disk
    # TODO: use FileSystem
    path = os.path.join(media_root, "sources", str(uuid))
    os.remove(path)

    # delete source from database
    await repository.delete_source_by_id(uuid)

    return {"message": "Source deleted successfully"}


async def put_multiple_sources(
    inputs: List[str],
    sources: List[str],
    files: List[UploadFile],
    request: Request,
):
    app = request.app
    repository: Repository = app.state.repository

    all_sources = []

    # create source from inputs list
    if len(inputs) > 0:

        async def _put_input(input: str):
            file_stream = BytesIO(input.encode("utf-8"))
            file = UploadFile(file_stream)
            return await put_source(file=file, request=request)

        sources_from_inputs = await asyncio.gather(*[_put_input(input) for input in inputs])
        all_sources += sources_from_inputs

    for source_id in sources:
        source = await repository.get_source_by_id(source_id)
        if source is not None:
            all_sources.append(source)

    # create one json file referencing all sources
    sources_from_files = await asyncio.gather(*[put_source(request, file=file) for file in files])
    all_sources += sources_from_files

    all_sources_objects = [source.model_dump() for source in all_sources]

    # create a merged file with all sources
    file_stream = BytesIO(json.dumps(jsonable_encoder(all_sources_objects)).encode("utf-8"))
    file = UploadFile(file_stream, filename="input.json")
    result_source = await put_source(file=file, format="json", request=request)

    return result_source
