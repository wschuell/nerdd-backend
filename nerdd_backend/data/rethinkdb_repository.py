import hashlib
import json
from typing import Any, AsyncIterable, Dict, List, Optional

from rethinkdb import RethinkDB
from rethinkdb.errors import ReqlOpFailedError

from .exceptions import RecordNotFoundError
from .job import Job
from .module import Module
from .repository import Repository
from .result import Result
from .source import Source

__all__ = ["RethinkDbRepository"]


def hash_object(obj: Dict[str, Any]) -> str:
    obj_str = json.dumps(obj, sort_keys=True)
    return hashlib.sha256(obj_str.encode("utf-8")).hexdigest()


class RethinkDbRepository(Repository):
    def __init__(self, host: str, port: int, database_name: str) -> None:
        self.r = RethinkDB()
        self.r.set_loop_type("asyncio")

        self.host = host
        self.port = port
        self.database_name = database_name

    #
    # INITIALIZATION
    #
    async def initialize(self) -> None:
        self.connection = await self.r.connect(self.host, self.port)

        # create database
        try:
            await self.r.db_create(self.database_name).run(self.connection)
        except ReqlOpFailedError:
            pass

        # create tables
        await self.create_module_table()
        await self.create_sources_table()
        await self.create_jobs_table()
        await self.create_results_table()

    #
    # MODULES
    #
    async def get_module_changes(self) -> AsyncIterable[Module]:
        return (
            await self.r.db(self.database_name)
            .table("modules")
            .changes(include_initial=True)
            .run(self.connection)
        )

    async def get_all_modules(self) -> List[Module]:
        cursor = (
            await self.r.db(self.database_name).table("modules").run(self.connection)
        )
        return [Module(**item) async for item in cursor]

    async def get_module_by_id(self, module_id: str) -> Module:
        result = (
            await self.r.db(self.database_name)
            .table("modules")
            .get(module_id)
            .run(self.connection)
        )

        if result is None:
            raise RecordNotFoundError(Module, module_id)

        return Module(**result)

    async def create_module_table(self) -> None:
        try:
            await (
                self.r.db(self.database_name)
                .table_create("modules")
                .run(self.connection)
            )
        except ReqlOpFailedError:
            pass

    async def get_most_recent_version(self, module_name: str) -> Module:
        result = (
            await self.r.db(self.database_name)
            .table("modules")
            .get(module_name)
            .run(self.connection)
        )

        if result is None:
            raise RecordNotFoundError(Module, module_name)

        return Module(**result)

    async def upsert_module(self, module: Module) -> None:
        # insert the module (or update if it matches an existing name-version combo)
        await (
            self.r.db(self.database_name)
            .table("modules")
            .insert(module.model_dump(), conflict="update")
            .run(self.connection)
        )

    #
    # JOBS
    #
    async def create_jobs_table(self) -> None:
        try:
            await (
                self.r.db(self.database_name)
                .table_create("jobs", primary_key="id")
                .run(self.connection)
            )
        except ReqlOpFailedError:
            pass

    async def upsert_job(self, job: Job) -> None:
        await (
            self.r.db(self.database_name)
            .table("jobs")
            .insert(job.model_dump(), conflict="update")
            .run(self.connection)
        )

    async def get_job_by_id(self, job_id: str) -> Job:
        result = (
            await self.r.db(self.database_name)
            .table("jobs")
            .get(job_id)
            .run(self.connection)
        )

        if result is None:
            raise RecordNotFoundError(Job, job_id)

        return Job(**result)

    async def delete_job_by_id(self, job_id: str) -> None:
        await (
            self.r.db(self.database_name)
            .table("jobs")
            .get(job_id)
            .delete()
            .run(self.connection)
        )

    #
    # SOURCES
    #
    async def create_sources_table(self) -> None:
        try:
            await (
                self.r.db(self.database_name)
                .table_create("sources", primary_key="id")
                .run(self.connection)
            )
        except ReqlOpFailedError:
            pass

    async def upsert_source(self, source: Source) -> None:
        await (
            self.r.db(self.database_name)
            .table("sources")
            .insert(source.model_dump(), conflict="update")
            .run(self.connection)
        )

    async def get_source_by_id(self, source_id: str) -> Source:
        result = (
            await self.r.db(self.database_name)
            .table("sources")
            .get(source_id)
            .run(self.connection)
        )

        if result is None:
            raise RecordNotFoundError(Source, source_id)

        return Source(**result)

    async def delete_source_by_id(self, source_id: str) -> None:
        await (
            self.r.db(self.database_name)
            .table("sources")
            .get(source_id)
            .delete()
            .run(self.connection)
        )

    #
    # RESULTS
    #
    async def create_results_table(self) -> None:
        try:
            await (
                self.r.db(self.database_name)
                .table_create("results", primary_key="id")
                .run(self.connection)
            )
        except ReqlOpFailedError:
            pass

    async def get_all_results_by_job_id(self, job_id: str) -> List[Result]:
        cursor = (
            await self.r.db(self.database_name)
            .table("results")
            .filter(self.r.row["job_id"] == job_id)
            .run(self.connection)
        )
        return [Result(**item) async for item in cursor]

    async def get_num_processed_entries_by_job_id(self, job_id: str) -> int:
        return (
            await self.r.db(self.database_name)
            .table("results")
            .filter(self.r.row["job_id"] == job_id)
            .pluck("mol_id")
            .distinct()
            .count()
            .run(self.connection)
        )

    async def get_results_by_job_id(
        self,
        job_id: str,
        start_mol_id: Optional[int] = None,
        end_mol_id: Optional[int] = None,
    ) -> List[Result]:
        cursor = (
            await self.r.db(self.database_name)
            .table("results")
            .filter(
                (self.r.row["job_id"] == job_id)
                & (self.r.row["mol_id"] >= start_mol_id)
                & (self.r.row["mol_id"] <= end_mol_id)
            )
            .order_by("mol_id")
            .run(self.connection)
        )

        if cursor is None:
            raise RecordNotFoundError(Result, job_id)

        return [Result(**item) async for item in cursor]

    async def upsert_result(self, result: Result) -> None:
        await (
            self.r.db(self.database_name)
            .table("results")
            .insert(result.model_dump(), conflict="update")
            .run(self.connection)
        )

    async def get_job_changes(self, job_id: str) -> AsyncIterable[Job]:
        return (
            await self.r.db(self.database_name)
            .table("results")
            .filter(self.r.row["job_id"] == job_id)
            .pluck("mol_id")
            .changes(include_initial=False)
            .run(self.connection)
        )

    async def get_result_changes(
        self,
        job_id: str,
        start_mol_id: Optional[int] = None,
        end_mol_id: Optional[int] = None,
    ) -> AsyncIterable[Result]:
        return (
            await self.r.db(self.database_name)
            .table("results")
            .filter(
                (self.r.row["job_id"] == job_id)
                & (self.r.row["mol_id"] >= start_mol_id)
                & (self.r.row["mol_id"] <= end_mol_id)
            )
            .changes(include_initial=False)
            .run(self.connection)
        )
