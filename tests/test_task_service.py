import asyncio

import pytest

from app.repositories.test_task import InMemoryTaskRepository
from app.repositories.test_task_log import InMemoryTaskLogRepository
from app.schemas import test_task as task_schemas
from app.services import test_task as test_task_service_module
from app.services.test_task import TaskService


def test_execute_failure_updates_status_and_adds_log(
    monkeypatch,
) -> None:
    task_repository = InMemoryTaskRepository()
    log_repository = InMemoryTaskLogRepository()

    service = TaskService(
        task_repository,
        log_repository,
    )

    task = service.create(
        task_schemas.TestTaskCreate(
            name="失败任务测试",
            test_type="automation",
            platform="windows",
        )
    )

    async def raise_execution_error(
        delay_seconds: float,
    ) -> None:
        raise RuntimeError("device offline")

    monkeypatch.setattr(
        test_task_service_module.asyncio,
        "sleep",
        raise_execution_error,
    )

    with pytest.raises(RuntimeError, match="device offline"):
        asyncio.run(
            service.execute(
                task.id,
                delay_seconds=0,
            )
        )

    saved_task = task_repository.get(task.id)
    assert saved_task is not None
    assert saved_task.status == "failed"

    logs = log_repository.get_by_task_id(task.id)
    assert [log.status for log in logs] == [
        "pending",
        "running",
        "failed",
    ]
    assert logs[-1].message == ("Test task failed: RuntimeError: device offline")

    report = service.get_report(task.id)

    assert report is not None
    assert report.failure_analysis is not None
    assert report.failure_analysis.category == "device_offline"
    assert report.failure_analysis.reason == "测试设备离线"
    assert report.failure_analysis.suggestion
