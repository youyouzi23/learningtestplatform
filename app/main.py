from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.models  # noqa: F401 - register SQLAlchemy models before create_all
from app.api.routes.health import router as health_router
from app.api.routes.test_tasks import router as test_tasks_router
from app.database import Base, engine


@asynccontextmanager
async def lifespan(_application: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Test Platform",
        description="自动化、接口、数据驱动与游戏测试统一平台",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.include_router(health_router)
    application.include_router(test_tasks_router)
    return application


app = create_app()
