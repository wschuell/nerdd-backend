import pytest_asyncio
from nerdd_backend.data import Repository
from nerdd_module.tests import MolWeightModel
from pytest_bdd import given

from ..async_step import async_step


class JsonRepository(Repository):
    def __init__(self):
        self.jobs = []
        self.modules = []
        self.sources = []
        self.results = []

    #
    # INITIALIZATION
    #
    async def initialize(self):
        pass

    #
    # MODULES
    #
    async def get_module_changes(self):
        raise NotImplementedError()

    async def get_all_modules(self):
        return self.modules

    async def upsert_module(self, module):
        module["id"] = module["name"]
        existing_module = await self.get_module_by_id(module["id"])
        if existing_module:
            self.modules = [
                existing_module if existing_module["id"] != module["id"] else module
                for module in self.modules
            ]
        else:
            self.modules.append(module)

    async def get_module_by_id(self, id):
        return next((module for module in self.modules if module["id"] == id), None)

    #
    # JOBS
    #
    async def get_job_changes(self, job_id):
        raise NotImplementedError()

    async def upsert_job(self, job):
        existing_job = self.get_job_by_id(job["id"])
        if existing_job:
            self.jobs = [
                existing_job if existing_job["id"] != job["id"] else job
                for job in self.jobs
            ]
        else:
            self.jobs.append(job)

    async def get_job_by_id(self, id):
        return next((job for job in self.jobs if job["id"] == id), None)

    async def delete_job_by_id(self, id):
        self.jobs = [job for job in self.jobs if job["id"] != id]

    #
    # SOURCES
    #
    async def upsert_source(self, source):
        existing_source = self.get_source_by_id(source["id"])
        if existing_source:
            self.sources = [
                existing_source if existing_source["id"] != source["id"] else source
                for source in self.sources
            ]
        else:
            self.sources.append(source)

    async def get_source_by_id(self, id):
        return next((source for source in self.sources if source["id"] == id), None)

    async def delete_source_by_id(self, id):
        self.sources = [source for source in self.sources if source["id"] != id]

    #
    # RESULTS
    #
    async def get_result_changes(self, job_id, start_mol_id, end_mol_id):
        raise NotImplementedError()

    async def get_results_by_job_id(self, job_id, start_mol_id, end_mol_id):
        return [
            result
            for result in self.results
            if result["job_id"] == job_id
            and start_mol_id <= result["mol_id"] <= end_mol_id
        ]

    async def upsert_result(self, result):
        existing_result = self.get_result_by_id(result["id"])
        if existing_result:
            self.results = [
                existing_result if existing_result["id"] != result["id"] else result
                for result in self.results
            ]
        else:
            self.results.append(result)

    async def get_all_results_by_job_id(self, job_id):
        return [result for result in self.results if result["job_id"] == job_id]

    async def get_num_processed_entries_by_job_id(self, job_id):
        return len(self.get_all_results_by_job_id(job_id))


@pytest_asyncio.fixture(scope="function")
async def repository(mocker):
    return JsonRepository()


@given("a mocked repository")
def mocked_repository(mocker, repository):
    mocker.patch(
        "nerdd_backend.lifespan.InitializeAppLifespan.get_repository",
        return_value=repository,
    )


@given("the repository contains the mol weight module")
@async_step
async def mol_weight_module(repository):
    model = MolWeightModel()
    await repository.upsert_module(model.get_config().model_dump())
