from typing import AsyncIterable, List, Optional, Tuple

from nerdd_link.utils import ObservableList

from ..models import Job, Module, Result, Source
from .exceptions import RecordNotFoundError
from .repository import Repository

__all__ = ["MemoryRepository"]


class MemoryRepository(Repository):
    def __init__(self) -> None:
        pass

    #
    # INITIALIZATION
    #
    async def initialize(self) -> None:
        self.jobs = ObservableList[Job]()
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

    async def upsert_module(self, module: Module) -> None:
        assert module.id is not None
        try:
            existing_module = await self.get_module_by_id(module.id)
            self.modules.update(existing_module, module)
        except RecordNotFoundError:
            self.modules.append(module)

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
    ) -> AsyncIterable[Tuple[Optional[Job], Optional[Job]]]:
        async for old, new in self.jobs.changes():
            if (old is not None and old.id == job_id) or (new is not None and new.id == job_id):
                yield (old, new)

    async def upsert_job(self, job: Job) -> None:
        try:
            existing_job = await self.get_job_by_id(job.id)
            self.jobs.update(existing_job, job)
        except RecordNotFoundError:
            self.jobs.append(job)

    async def get_job_by_id(self, id: str) -> Job:
        try:
            return next((job for job in self.jobs.get_items() if job.id == id))
        except StopIteration as e:
            raise RecordNotFoundError(Job, id) from e

    async def delete_job_by_id(self, id: str) -> None:
        job = await self.get_job_by_id(id)
        self.jobs.remove(job)

    #
    # SOURCES
    #
    async def upsert_source(self, source: Source) -> None:
        try:
            existing_source = await self.get_source_by_id(source.id)
            self.sources.update(existing_source, source)
        except RecordNotFoundError:
            self.sources.append(source)

    async def get_source_by_id(self, id: str) -> Source:
        try:
            return next((source for source in self.sources.get_items() if source.id == id))
        except StopIteration as e:
            raise RecordNotFoundError(Source, id) from e

    async def delete_source_by_id(self, id: str) -> None:
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

    async def upsert_result(self, result: Result) -> None:
        try:
            existing_result = await self.get_result_by_id(result.id)
            self.results.update(existing_result, result)
        except RecordNotFoundError:
            self.results.append(result)

    async def get_all_results_by_job_id(self, job_id: str) -> List[Result]:
        return [result for result in self.results.get_items() if result.job_id == job_id]

    async def get_num_processed_entries_by_job_id(self, job_id: str) -> int:
        return len(await self.get_all_results_by_job_id(job_id))
