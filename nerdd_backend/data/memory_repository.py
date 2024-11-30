from typing import AsyncIterable, List, Optional

from .exceptions import RecordNotFoundError
from .job import Job
from .module import Module
from .repository import Repository
from .result import Result
from .source import Source

__all__ = ["MemoryRepository"]


class MemoryRepository(Repository):
    def __init__(self) -> None:
        self.jobs: List[Job] = []
        self.modules: List[Module] = []
        self.sources: List[Source] = []
        self.results: List[Result] = []

    #
    # INITIALIZATION
    #
    async def initialize(self) -> None:
        pass

    #
    # MODULES
    #
    async def get_module_changes(self) -> AsyncIterable:
        yield NotImplementedError()

    async def get_all_modules(self) -> List[Module]:
        return self.modules

    async def upsert_module(self, module: Module) -> None:
        assert module.id is not None
        existing = any(
            existing_module.id == module.id for existing_module in self.modules
        )
        if existing:
            existing_module = module
            self.modules = [
                Module(**module, **existing_module)
                if existing_module.id == module.id
                else module
                for module in self.modules
            ]
        else:
            self.modules.append(module)

    async def get_module_by_id(self, id: str) -> Module:
        try:
            return next((module for module in self.modules if module.id == id))
        except StopIteration as e:
            raise RecordNotFoundError(Module, id) from e

    #
    # JOBS
    #
    async def get_job_changes(self, job_id: str) -> AsyncIterable:
        yield NotImplementedError()

    async def upsert_job(self, job: Job) -> None:
        try:
            existing_job = await self.get_job_by_id(job.id)
        except RecordNotFoundError:
            existing_job = None

        if existing_job:
            self.jobs = [
                existing_job if existing_job.id == job.id else job for job in self.jobs
            ]
        else:
            self.jobs.append(job)

    async def get_job_by_id(self, id: str) -> Job:
        try:
            return next((job for job in self.jobs if job.id == id))
        except StopIteration as e:
            raise RecordNotFoundError(Job, id) from e

    async def delete_job_by_id(self, id: str) -> None:
        self.jobs = [job for job in self.jobs if job.id != id]

    #
    # SOURCES
    #
    async def upsert_source(self, source: Source) -> None:
        try:
            existing_source = await self.get_source_by_id(source.id)
        except RecordNotFoundError:
            existing_source = None

        if existing_source:
            self.sources = [
                existing_source if existing_source.id == source.id else source
                for source in self.sources
            ]
        else:
            self.sources.append(source)

    async def get_source_by_id(self, id: str) -> Source:
        try:
            return next((source for source in self.sources if source.id == id))
        except StopIteration as e:
            raise RecordNotFoundError(Source, id) from e

    async def delete_source_by_id(self, id: str) -> None:
        self.sources = [source for source in self.sources if source.id != id]

    #
    # RESULTS
    #
    async def get_result_changes(
        self,
        job_id: str,
        start_mol_id: Optional[int] = None,
        end_mol_id: Optional[int] = None,
    ) -> AsyncIterable:
        yield NotImplementedError()

    async def get_result_by_id(self, id: str) -> Result:
        try:
            return next((result for result in self.results if result.id == id))
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
            for result in self.results
            if result.job_id == job_id and start_mol_id <= result.mol_id <= end_mol_id
        ]

    async def upsert_result(self, result: Result) -> None:
        try:
            existing_result = await self.get_result_by_id(result.id)
        except RecordNotFoundError:
            existing_result = None

        if existing_result:
            self.results = [
                existing_result if existing_result.id == result.id else result
                for result in self.results
            ]
        else:
            self.results.append(result)

    async def get_all_results_by_job_id(self, job_id: str) -> List[Result]:
        return [result for result in self.results if result.job_id == job_id]

    async def get_num_processed_entries_by_job_id(self, job_id: str) -> int:
        return len(await self.get_all_results_by_job_id(job_id))
