import pytest


class JsonRepository:
    def __init__(self):
        self.data = {}

    #
    # INITIALIZATION
    #
    async def initialize(self):
        # create tables
        await self.create_module_table()
        await self.create_sources_table()
        await self.create_jobs_table()
        await self.create_results_table()

    #
    # MODULES
    #
    async def get_module_changes(self):
        raise NotImplementedError()

    async def get_all_modules(self):
        return self.data["modules"]

    async def create_module_table(self):
        self.data["modules"] = []

    async def upsert_module(self, module):
        raise NotImplementedError()

    #
    # JOBS
    #
    async def create_jobs_table(self):
        self.data["jobs"] = []

    async def upsert_job(self, job):
        raise NotImplementedError()

    async def get_job_by_id(self, id):
        raise NotImplementedError()

    #
    # SOURCES
    #
    async def create_sources_table(self):
        self.data["sources"] = []

    async def upsert_source(self, source):
        raise NotImplementedError()

    async def get_source_by_id(self, id):
        raise NotImplementedError()

    #
    # RESULTS
    #
    async def create_results_table(self):
        self.data["results"] = []

    async def get_results_by_job_id(self, job_id, start_mol_id, end_mol_id):
        raise NotImplementedError()

    async def upsert_result(self, result):
        raise NotImplementedError()


@pytest.fixture
def repository(mocker):
    return mocker.patch(
        "nerdd_backend.data.repository",
        wraps=JsonRepository(),
    )
