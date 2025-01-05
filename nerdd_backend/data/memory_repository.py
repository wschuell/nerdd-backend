from asyncio import Lock
from typing import AsyncIterable, List, Optional, Tuple

from nerdd_link.utils import ObservableList

from ..models import Job, JobInternal, JobUpdate, Module, Result, Source
from .exceptions import RecordAlreadyExistsError, RecordNotFoundError
from .repository import Repository

__all__ = ["MemoryRepository"]


class MemoryRepository(Repository):
    def __init__(self) -> None:
        pass

    #
    # INITIALIZATION
    #
    async def initialize(self) -> None:
        self.transaction_lock = Lock()
        self.jobs = ObservableList[JobInternal]()
        self.modules = ObservableList[Module]()
        self.sources = ObservableList[Source]()
        self.results = ObservableList[Result]()

    #
    # MODULES
    #
    async def get_module_changes(
        self,
    ) -> AsyncIterable[Tuple[Optional[Module], Optional[Module]]]:
        async for change in self.modules.changes():
            yield change

    async def get_all_modules(self) -> List[Module]:
        return self.modules.get_items()

    async def create_module(self, module: Module) -> Module:
        assert module.id is not None
        async with self.transaction_lock:
            try:
                await self.get_module_by_id(module.id)
                raise RecordAlreadyExistsError(Module, module.id)
            except RecordNotFoundError:
                self.modules.append(module)
                return module

    async def update_module(self, module: Module) -> Module:
        async with self.transaction_lock:
            existing_module = await self.get_module_by_id(module.id)
            self.modules.update(existing_module, module)
            return await self.get_module_by_id(module)

    async def get_module_by_id(self, id: str) -> Module:
        try:
            return next((module for module in self.modules.get_items() if module.id == id))
        except StopIteration as e:
            raise RecordNotFoundError(Module, id) from e

    #
    # JOBS
    #
    async def get_job_changes(
        self, job_id: str
    ) -> AsyncIterable[Tuple[Optional[JobInternal], Optional[JobInternal]]]:
        async for old, new in self.jobs.changes():
            if (old is not None and old.id == job_id) or (new is not None and new.id == job_id):
                yield (old, new)

    async def create_job(self, job: Job) -> JobInternal:
        async with self.transaction_lock:
            try:
                await self.get_job_by_id(job.id)
                raise RecordAlreadyExistsError(Job, job.id)
            except RecordNotFoundError:
                result = JobInternal(**job.model_dump())
                self.jobs.append(result)
                return result

    async def update_job(self, job: JobUpdate) -> JobInternal:
        async with self.transaction_lock:
            existing_job = await self.get_job_by_id(job.id)
            modified_job = JobInternal(**existing_job.model_dump())
            if job.status is not None:
                modified_job.status = job.status
            if job.num_entries_total is not None:
                modified_job.num_entries_total = job.num_entries_total
            if job.num_checkpoints_total is not None:
                modified_job.num_checkpoints_total = job.num_checkpoints_total
            if job.new_checkpoints_processed is not None:
                modified_job.checkpoints_processed.extend(job.new_checkpoints_processed)
            if job.new_output_formats is not None:
                modified_job.output_formats.extend(job.new_output_formats)
            self.jobs.update(existing_job, modified_job)
            return await self.get_job_by_id(job.id)

    async def get_job_by_id(self, id: str) -> JobInternal:
        try:
            return next((job for job in self.jobs.get_items() if job.id == id))
        except StopIteration as e:
            raise RecordNotFoundError(Job, id) from e

    async def delete_job_by_id(self, id: str) -> None:
        async with self.transaction_lock:
            job = await self.get_job_by_id(id)
            self.jobs.remove(job)

    #
    # SOURCES
    #
    async def create_source(self, source: Source) -> Source:
        async with self.transaction_lock:
            try:
                await self.get_source_by_id(source.id)
                raise RecordAlreadyExistsError(Source, source.id)
            except RecordNotFoundError:
                self.sources.append(source)
                return source

    async def get_source_by_id(self, id: str) -> Source:
        try:
            return next((source for source in self.sources.get_items() if source.id == id))
        except StopIteration as e:
            raise RecordNotFoundError(Source, id) from e

    async def delete_source_by_id(self, id: str) -> None:
        async with self.transaction_lock:
            source = await self.get_source_by_id(id)
            self.sources.remove(source)

    #
    # RESULTS
    #
    async def get_result_changes(
        self,
        job_id: str,
        start_mol_id: Optional[int] = None,
        end_mol_id: Optional[int] = None,
    ) -> AsyncIterable[Tuple[Optional[Result], Optional[Result]]]:
        async for change in self.results.changes():
            old, new = change
            if (
                old is not None
                and old.job_id == job_id
                and start_mol_id <= old.mol_id <= end_mol_id
            ) or (
                new is not None
                and new.job_id == job_id
                and start_mol_id <= new.mol_id <= end_mol_id
            ):
                yield change

    async def get_result_by_id(self, id: str) -> Result:
        try:
            return next((result for result in self.results.get_items() if result.id == id))
        except StopIteration as e:
            raise RecordNotFoundError(Result, id) from e

    async def get_results_by_job_id(
        self,
        job_id: str,
        start_mol_id: Optional[int] = None,
        end_mol_id: Optional[int] = None,
    ) -> List[Result]:
        return [
            result
            for result in self.results.get_items()
            if result.job_id == job_id and start_mol_id <= result.mol_id <= end_mol_id
        ]

    async def create_result(self, result: Result) -> None:
        async with self.transaction_lock:
            try:
                await self.get_result_by_id(result.id)
                raise RecordAlreadyExistsError(Result, result.id)
            except RecordNotFoundError:
                self.results.append(result)

    async def get_all_results_by_job_id(self, job_id: str) -> List[Result]:
        return [result for result in self.results.get_items() if result.job_id == job_id]

    async def get_num_processed_entries_by_job_id(self, job_id: str) -> int:
        return len(await self.get_all_results_by_job_id(job_id))
