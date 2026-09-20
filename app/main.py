from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.test_tasks import router as test_tasks_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Game Test Platform",
        description="游戏自动化与性能测试平台",
        version="0.1.0",
    )
    application.include_router(health_router)
    application.include_router(test_tasks_router)
    return application


app = create_app()
