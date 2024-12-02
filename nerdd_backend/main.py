import asyncio
import logging
import os
from contextlib import asynccontextmanager

import hydra
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from omegaconf import DictConfig, OmegaConf

from .actions import SaveModuleToDb, UpdateJobSize
from .lifespan import ActionLifespan, CreateModuleLifespan, InitializeAppLifespan
from .routers import (
    jobs_router,
    modules_router,
    results_router,
    sources_router,
    websockets_router,
)

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def create_app(cfg: DictConfig):
    lifespans = [
        InitializeAppLifespan(cfg),
        ActionLifespan(
            lambda app: UpdateJobSize(app.state.channel, app.state.repository)
        ),
        ActionLifespan(
            lambda app: SaveModuleToDb(app.state.channel, app.state.repository)
        ),
        CreateModuleLifespan(),
    ]

    if cfg.mock_infra:
        from nerdd_link import (
            PredictCheckpointsAction,
            ProcessJobsAction,
            RegisterModuleAction,
        )
        from nerdd_module.tests import MolWeightModel

        model = MolWeightModel()

        lifespans = [
            *lifespans,
            ActionLifespan(lambda app: RegisterModuleAction(app.state.channel, model)),
            ActionLifespan(
                lambda app: PredictCheckpointsAction(
                    app.state.channel, model, cfg.media_root
                )
            ),
            ActionLifespan(
                lambda app: ProcessJobsAction(
                    app.state.channel,
                    checkpoint_size=100,
                    max_num_molecules=10_000,
                    num_test_entries=10,
                    ratio_valid_entries=0.5,
                    maximum_depth=100,
                    max_num_lines_mol_block=10_000,
                    data_dir=cfg.media_root,
                )
            ),
        ]

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Starting tasks")
        start_tasks = asyncio.gather(
            *[asyncio.create_task(lifespan.start(app)) for lifespan in lifespans]
        )

        await start_tasks

        logger.info("Running tasks")
        run_tasks = asyncio.gather(
            *[asyncio.create_task(lifespan.run()) for lifespan in lifespans]
        )

        yield

        logger.info("Attempting to cancel all tasks")
        run_tasks.cancel()

        try:
            await run_tasks
        except asyncio.CancelledError:
            logger.info("Tasks successfully cancelled")

    app = FastAPI(lifespan=lifespan)

    origins = [
        "http://localhost",
        "http://localhost:8000",
        "http://localhost:3000",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(jobs_router)
    app.include_router(sources_router)
    app.include_router(results_router)
    app.include_router(modules_router)
    app.include_router(websockets_router)

    return app


@hydra.main(version_base=None, config_path="settings", config_name="config")
def main(cfg: DictConfig) -> None:
    logger.info(
        f"Starting server with the following configuration:\n{OmegaConf.to_yaml(cfg)}"
    )
    app = create_app(cfg)

    uvicorn.run(
        app,
        host=cfg.host,
        port=cfg.port,
    )


if __name__ == "__main__":
    main()
