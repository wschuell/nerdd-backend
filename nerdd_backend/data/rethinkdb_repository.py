import hashlib
import json

from rethinkdb import RethinkDB
from rethinkdb.errors import ReqlOpFailedError

from .exceptions import RecordNotFoundError
from .job import Job
from .module import Module
from .repository import Repository
from .result import Result
from .source import Source

__all__ = ["RethinkDbRepository"]


def hash_object(obj):
    obj_str = json.dumps(obj, sort_keys=True)
    return hashlib.sha256(obj_str.encode("utf-8")).hexdigest()


class RethinkDbRepository(Repository):
    def __init__(self, host, port, database_name):
        self.r = RethinkDB()
        self.r.set_loop_type("asyncio")

        self.host = host
        self.port = port
        self.database_name = database_name

    #
    # INITIALIZATION
    #
    async def initialize(self):
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
    async def get_module_changes(self):
        return (
            await self.r.db(self.database_name)
            .table("modules")
            .changes(include_initial=True)
            .run(self.connection)
        )

    async def get_all_modules(self):
        cursor = (
            await self.r.db(self.database_name).table("modules").run(self.connection)
        )
        return [item async for item in cursor]

    async def get_module_by_id(self, module_id):
        result = (
            await self.r.db(self.database_name)
            .table("modules")
            .get(module_id)
            .run(self.connection)
        )

        if result is None:
            raise RecordNotFoundError(Module, module_id)

        return result

    async def create_module_table(self):
        try:
            await (
                self.r.db(self.database_name)
                .table_create("modules")
                .run(self.connection)
            )
        except ReqlOpFailedError:
            pass

    async def get_most_recent_version(self, module_name):
        result = (
            await self.r.db(self.database_name)
            .table("modules")
            .get(module_name)
            .run(self.connection)
        )

        if result is None:
            raise RecordNotFoundError(Module, module_name)

        return result

    async def upsert_module(self, module):
        # insert the module (or update if it matches an existing name-version combo)
        await (
            self.r.db(self.database_name)
            .table("modules")
            .insert(module, conflict="update")
            .run(self.connection)
        )

    #
    # JOBS
    #
    async def create_jobs_table(self):
        try:
            await (
                self.r.db(self.database_name)
                .table_create("jobs", primary_key="id")
                .run(self.connection)
            )
        except ReqlOpFailedError:
            pass

    async def upsert_job(self, job):
        await (
            self.r.db(self.database_name)
            .table("jobs")
            .insert(job, conflict="update")
            .run(self.connection)
        )

    async def get_job_by_id(self, job_id):
        result = (
            await self.r.db(self.database_name)
            .table("jobs")
            .get(job_id)
            .run(self.connection)
        )

        if result is None:
            raise RecordNotFoundError(Job, job_id)

        return result

    async def delete_job_by_id(self, job_id):
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
    async def create_sources_table(self):
        try:
            await (
                self.r.db(self.database_name)
                .table_create("sources", primary_key="id")
                .run(self.connection)
            )
        except ReqlOpFailedError:
            pass

    async def upsert_source(self, source):
        await (
            self.r.db(self.database_name)
            .table("sources")
            .insert(source, conflict="update")
            .run(self.connection)
        )

    async def get_source_by_id(self, source_id):
        result = (
            await self.r.db(self.database_name)
            .table("sources")
            .get(source_id)
            .run(self.connection)
        )

        if result is None:
            raise RecordNotFoundError(Source, source_id)

        return result

    async def delete_source_by_id(self, source_id):
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
    async def create_results_table(self):
        try:
            await (
                self.r.db(self.database_name)
                .table_create("results", primary_key="id")
                .run(self.connection)
            )
        except ReqlOpFailedError:
            pass

    async def get_all_results_by_job_id(self, job_id):
        return (
            await self.r.db(self.database_name)
            .table("results")
            .filter(self.r.row["job_id"] == job_id)
            .run(self.connection)
        )

    async def get_num_processed_entries_by_job_id(self, job_id):
        return (
            await self.r.db(self.database_name)
            .table("results")
            .filter(self.r.row["job_id"] == job_id)
            .pluck("mol_id")
            .distinct()
            .count()
            .run(self.connection)
        )

    async def get_results_by_job_id(self, job_id, start_mol_id, end_mol_id):
        result = (
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

        if result is None:
            raise RecordNotFoundError(Result, job_id)

        return result

    async def upsert_result(self, result):
        await (
            self.r.db(self.database_name)
            .table("results")
            .insert(result, conflict="update")
            .run(self.connection)
        )

    async def get_job_changes(self, job_id):
        return (
            await self.r.db(self.database_name)
            .table("results")
            .filter(self.r.row["job_id"] == job_id)
            .pluck("mol_id")
            .changes(include_initial=False)
            .run(self.connection)
        )

    async def get_result_changes(self, job_id, start_mol_id, end_mol_id):
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
