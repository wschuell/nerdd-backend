import hashlib
import json
import logging
from typing import Any, AsyncIterable, Dict, List, Optional, Tuple

from rethinkdb import RethinkDB
from rethinkdb.errors import ReqlOpFailedError

from ..models import Job, JobInternal, JobUpdate, Module, Result, Source
from ..util import CompressedSet
from .exceptions import RecordAlreadyExistsError, RecordNotFoundError
from .repository import Repository

__all__ = ["RethinkDbRepository"]

logger = logging.getLogger(__name__)


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
        except ReqlOpFailedError as e:
            if not str(e).startswith("Database `nerdd` already exists"):
                logger.exception("Failed to create database", exc_info=e)

        # use the same database for all queries
        self.connection.use(self.database_name)

        # create tables
        await self.create_warning_table()
        await self.create_module_table()
        await self.create_sources_table()
        await self.create_jobs_table()
        await self.create_results_table()

        # create an index on job_id in results table
        try:
            await self.r.table("results").index_create("job_id").run(self.connection)

            # wait for index to be ready
            await self.r.table("results").index_wait("job_id").run(self.connection)
        except ReqlOpFailedError as e:
            if not str(e).startswith("Index `job_id` already exists"):
                logger.exception("Failed to create index", exc_info=e)

    #
    # WARNINGS
    #
    async def create_warning_table(self) -> None:
        try:
            await self.r.table_create("warnings", primary_key="id").run(self.connection)
        except ReqlOpFailedError:
            pass

    async def create_warning(self, warning: NerddWarning) -> NerddWarning:
        result = await (
            self.r.table("warnings")
            .insert(warning.model_dump(), conflict="error", return_changes=True)
            .run(self.connection)
        )

        if len(result["changes"]) == 0:
            raise RecordAlreadyExistsError(NerddWarning, warning.id)

        return NerddWarning(**result["changes"][0]["new_val"])

    async def get_all_warnings(self) -> List[NerddWarning]:
        cursor = await self.r.table("warnings").run(self.connection)
        return [NerddWarning(**item) async for item in cursor]

    #
    # MODULES
    #
    async def get_module_changes(
        self,
    ) -> AsyncIterable[Tuple[Optional[Module], Optional[Module]]]:
        cursor = (
            await self.r.table("modules")
            .changes(include_initial=True)
            .run(self.connection)
        )

        async for change in cursor:
            if "old_val" not in change or change["old_val"] is None:
                old_module = None
            else:
                old_module = Module(**change["old_val"])

            if "new_val" not in change or change["new_val"] is None:
                new_module = None
            else:
                new_module = Module(**change["new_val"])

            yield old_module, new_module

    async def get_all_modules(self) -> List[Module]:
        cursor = await self.r.table("modules").run(self.connection)
        return [Module(**item) async for item in cursor]

    async def get_module_by_id(self, module_id: str) -> Module:
        result = await self.r.table("modules").get(module_id).run(self.connection)

        if result is None:
            raise RecordNotFoundError(Module, module_id)

        return Module(**result)

    async def create_module_table(self) -> None:
        try:
            await self.r.table_create("modules", primary_key="id").run(self.connection)
        except ReqlOpFailedError:
            pass

    # async def get_most_recent_version(self, module_name: str) -> Module:
    #     result = (
    #         await self.r
    #         .table("modules")
    #         .get(module_name)
    #         .run(self.connection)
    #     )

    #     if result is None:
    #         raise RecordNotFoundError(Module, module_name)

    #     return Module(**result)

    async def create_module(self, module: Module) -> Module:
        result = await (
            self.r.table("modules")
            .insert(module.model_dump(), conflict="error", return_changes=True)
            .run(self.connection)
        )

        if len(result["changes"]) == 0:
            raise RecordAlreadyExistsError(Module, module.id)

        return Module(**result["changes"][0]["new_val"])

    async def update_module(self, module: Module) -> Module:
        result = await (
            self.r.table("modules")
            .get(module.id)
            .update(module.model_dump(), return_changes=True)
            .run(self.connection)
        )

        if result["skipped"] == 1:
            raise RecordNotFoundError(Module, module.id)

        return module

    #
    # JOBS
    #
    async def get_job_changes(
        self, job_id: str
    ) -> AsyncIterable[Tuple[Optional[JobInternal], Optional[JobInternal]]]:
        cursor = (
            await self.r.table("jobs")
            .get(job_id)
            .changes(include_initial=False)
            .run(self.connection)
        )

        async for change in cursor:
            if change["old_val"] is None:
                old_job = None
            else:
                old_job = JobInternal(**change["old_val"])

            if change["new_val"] is None:
                new_job = None
            else:
                new_job = JobInternal(**change["new_val"])

            yield old_job, new_job

    async def create_jobs_table(self) -> None:
        try:
            await self.r.table_create("jobs", primary_key="id").run(self.connection)
        except ReqlOpFailedError:
            pass

    async def create_job(self, job: Job) -> JobInternal:
        job = JobInternal(**job.model_dump())
        result = await (
            self.r.table("jobs")
            .insert(job.model_dump(), conflict="error", return_changes=True)
            .run(self.connection)
        )
        return JobInternal(**result["changes"][0]["new_val"])

    async def update_job(self, job_update: JobUpdate) -> JobInternal:
        # all fields (except entries_processed) can be updated in a single query
        # --> prepare an object with all fields that should be updated
        update_set = {}
        if job_update.status is not None:
            update_set["status"] = job_update.status
        if job_update.num_entries_total is not None:
            update_set["num_entries_total"] = job_update.num_entries_total
        if job_update.num_checkpoints_total is not None:
            update_set["num_checkpoints_total"] = job_update.num_checkpoints_total
        if job_update.new_checkpoints_processed is not None:
            update_set["checkpoints_processed"] = self.r.row[
                "checkpoints_processed"
            ].set_union(job_update.new_checkpoints_processed)
        if job_update.new_output_formats is not None:
            update_set["output_formats"] = self.r.row["output_formats"].set_union(
                job_update.new_output_formats
            )

        if job_update.entries_processed is None:
            changes = (
                await self.r.table("jobs")
                .get(job_update.id)
                .update(update_set, return_changes=True)
                .run(self.connection)
            )
        else:
            # The field entries_processed is tricky: we need to update the slightly complex data
            # structure containing the processed entries in a way that is atomic.
            while True:
                # get old value
                old_job = (
                    await self.r.table("jobs")
                    .get(job_update.id)
                    .pluck("entries_processed")
                    .run(self.connection)
                )
                old_intervals = old_job["entries_processed"]

                # update the old value
                compressed_set = CompressedSet(intervals=old_intervals)
                for entry in job_update.entries_processed:
                    compressed_set.add(entry)
                new_intervals = compressed_set.to_intervals()

                if old_intervals == new_intervals:
                    changes = {"unchanged": 1}
                    break

                # this is the important part: before updating we check if the value has changed
                # * if yes: start over
                # * if no: update the value
                changes = (
                    await self.r.table("jobs")
                    .get(job_update.id)
                    .update(
                        lambda record: self.r.branch(
                            record["entries_processed"] == old_intervals,
                            # update:
                            {**update_set, "entries_processed": new_intervals},
                            # do not update:
                            {},
                        ),
                        return_changes=True,
                    )
                    .run(self.connection)
                )

                if changes["replaced"] > 0:
                    break

        if changes["unchanged"] == 1:
            return None

        if len(changes["changes"]) == 0:
            raise RecordNotFoundError(Job, job_update.id)

        return JobInternal(**changes["changes"][0]["new_val"])

    async def get_job_by_id(self, job_id: str) -> JobInternal:
        result = await self.r.table("jobs").get(job_id).run(self.connection)

        if result is None:
            raise RecordNotFoundError(Job, job_id)

        return JobInternal(**result)

    async def delete_job_by_id(self, job_id: str) -> None:
        await self.r.table("jobs").get(job_id).delete().run(self.connection)

    #
    # SOURCES
    #
    async def create_sources_table(self) -> None:
        try:
            await self.r.table_create("sources", primary_key="id").run(self.connection)
        except ReqlOpFailedError:
            pass

    async def create_source(self, source: Source) -> Source:
        result = await (
            self.r.table("sources")
            .insert(source.model_dump(), conflict="error", return_changes=True)
            .run(self.connection)
        )

        if len(result["changes"]) == 0:
            raise RecordNotFoundError(Source, source.id)

        return Source(**result["changes"][0]["new_val"])

    async def get_source_by_id(self, source_id: str) -> Source:
        result = await self.r.table("sources").get(source_id).run(self.connection)

        if result is None:
            raise RecordNotFoundError(Source, source_id)

        return Source(**result)

    async def delete_source_by_id(self, source_id: str) -> None:
        await self.r.table("sources").get(source_id).delete().run(self.connection)

    #
    # RESULTS
    #
    async def create_results_table(self) -> None:
        try:
            await self.r.table_create("results", primary_key="id").run(self.connection)
        except ReqlOpFailedError:
            pass

    async def get_all_results_by_job_id(self, job_id: str) -> List[Result]:
        cursor = (
            await self.r.table("results")
            .get_all(job_id, index="job_id")
            .run(self.connection)
        )
        return [Result(**item) async for item in cursor]

    async def get_num_processed_entries_by_job_id(self, job_id: str) -> int:
        return (
            await self.r.table("results")
            .get_all(job_id, index="job_id")
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
        start_condition = (
            (self.r.row["mol_id"] >= start_mol_id) if start_mol_id is not None else True
        )
        end_condition = (
            (self.r.row["mol_id"] <= end_mol_id) if end_mol_id is not None else True
        )

        cursor = (
            await self.r.table("results")
            .get_all(job_id, index="job_id")
            .filter(start_condition & end_condition)
            .order_by("mol_id")
            .run(self.connection)
        )

        if cursor is None:
            raise RecordNotFoundError(Result, job_id)

        return [Result(**item) for item in cursor]

    async def create_result(self, result: Result) -> Result:
        # TODO: return result
        await (
            self.r.table("results")
            .insert(result.model_dump(), conflict="error")
            .run(self.connection)
        )

    async def get_result_changes(
        self,
        job_id: str,
        start_mol_id: Optional[int] = None,
        end_mol_id: Optional[int] = None,
    ) -> AsyncIterable[Tuple[Optional[Result], Optional[Result]]]:
        start_condition = (
            (self.r.row["mol_id"] >= start_mol_id) if start_mol_id is not None else True
        )
        end_condition = (
            (self.r.row["mol_id"] <= end_mol_id) if end_mol_id is not None else True
        )

        cursor = (
            await self.r.table("results")
            .get_all(job_id, index="job_id")
            .filter(start_condition & end_condition)
            .changes(include_initial=True)
            .run(self.connection)
        )

        async for change in cursor:
            if "old_val" not in change or change["old_val"] is None:
                old_result = None
            else:
                old_result = Result(**change["old_val"])

            if "new_val" not in change or change["new_val"] is None:
                new_result = None
            else:
                new_result = Result(**change["new_val"])

            yield old_result, new_result
