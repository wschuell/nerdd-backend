from abc import ABC, abstractmethod
from typing import AsyncIterable, List, Optional, Tuple

from ..models import Job, JobInternal, JobUpdate, Module, Result, Source, NerddWarning

__all__ = ["Repository"]


class Repository(ABC):
    #
    # INITIALIZATION
    #
    @abstractmethod
    async def initialize(self):
        pass

    #
    # WARNINGS
    #
    @abstractmethod
    async def get_all_warnings(self) -> List[NerddWarning]:
        pass

    @abstractmethod
    async def create_warning(self, warning: NerddWarning) -> NerddWarning:
        pass

    #
    # MODULES
    #
    @abstractmethod
    def get_module_changes(
        self,
    ) -> AsyncIterable[Tuple[Optional[Module], Optional[Module]]]:
        pass

    @abstractmethod
    async def get_all_modules(self) -> List[Module]:
        pass

    @abstractmethod
    async def get_module_by_id(self, module_id) -> Module:
        """
        Returns
        -------
        dict
            The module with the given id or None if not found
        """
        pass

    @abstractmethod
    async def create_module(self, module: Module) -> Module:
        pass

    @abstractmethod
    async def update_module(self, module: Module) -> Module:
        pass

    #
    # JOBS
    #
    @abstractmethod
    def get_job_changes(
        self, job_id: str
    ) -> AsyncIterable[Tuple[Optional[JobInternal], Optional[JobInternal]]]:
        pass

    @abstractmethod
    async def create_job(self, job: Job) -> JobInternal:
        pass

    @abstractmethod
    async def update_job(self, job_update: JobUpdate) -> JobInternal:
        pass

    @abstractmethod
    async def get_job_by_id(self, job_id: str) -> JobInternal:
        pass

    @abstractmethod
    async def delete_job_by_id(self, job_id) -> None:
        pass

    #
    # SOURCES
    #
    @abstractmethod
    async def create_source(self, source: Source) -> Source:
        pass

    @abstractmethod
    async def get_source_by_id(self, source_id: str) -> Source:
        pass

    @abstractmethod
    async def delete_source_by_id(self, source_id: str) -> None:
        pass

    #
    # RESULTS
    #
    @abstractmethod
    async def get_num_processed_entries_by_job_id(self, job_id: str) -> int:
        pass

    @abstractmethod
    async def get_results_by_job_id(
        self,
        job_id: str,
        start_mol_id: Optional[int] = None,
        end_mol_id: Optional[int] = None,
    ) -> List[Result]:
        pass

    @abstractmethod
    async def create_result(self, result: Result) -> Result:
        pass

    @abstractmethod
    def get_result_changes(
        self,
        job_id,
        start_mol_id: Optional[int] = None,
        end_mol_id: Optional[int] = None,
    ) -> AsyncIterable[Tuple[Optional[Result], Optional[Result]]]:
        pass
