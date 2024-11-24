from abc import ABC, abstractmethod

__all__ = ["Repository"]


class Repository(ABC):
    def __init__(self):
        pass

    #
    # INITIALIZATION
    #
    @abstractmethod
    async def initialize(self):
        pass

    #
    # MODULES
    #
    @abstractmethod
    async def get_module_changes(self):
        pass

    @abstractmethod
    async def get_all_modules(self):
        pass

    @abstractmethod
    async def get_module_by_id(self, id):
        """
        Returns
        -------
        dict
            The module with the given id or None if not found
        """
        pass

    @abstractmethod
    async def get_most_recent_version(self, module_id):
        pass

    @abstractmethod
    async def upsert_module(self, module):
        pass

    #
    # JOBS
    #
    @abstractmethod
    async def upsert_job(self, job):
        pass

    @abstractmethod
    async def get_job_by_id(self, id):
        pass

    @abstractmethod
    async def delete_job_by_id(self, id):
        pass

    #
    # SOURCES
    #
    @abstractmethod
    async def upsert_source(self, source):
        pass

    @abstractmethod
    async def get_source_by_id(self, id):
        pass

    @abstractmethod
    async def delete_source_by_id(self, id):
        pass

    #
    # RESULTS
    #

    @abstractmethod
    async def get_all_results_by_job_id(self, job_id):
        pass

    @abstractmethod
    async def get_num_processed_entries_by_job_id(self, job_id):
        pass

    @abstractmethod
    async def get_results_by_job_id(self, job_id, start_mol_id, end_mol_id):
        pass

    @abstractmethod
    async def upsert_result(self, result):
        pass

    @abstractmethod
    async def get_job_changes(self, job_id):
        pass

    @abstractmethod
    async def get_result_changes(self, job_id, start_mol_id, end_mol_id):
        pass
