import logging
from threading import Lock
from typing import Protocol

from redis import Redis
from redis.exceptions import RedisError

from app.schemas.test_task import TestTaskReportResponse

logger = logging.getLogger(__name__)


class ReportCache(Protocol):
    def get(
        self,
        task_id: int,
    ) -> TestTaskReportResponse | None: ...

    def set(
        self,
        report: TestTaskReportResponse,
    ) -> None: ...

    def delete(
        self,
        task_id: int,
    ) -> None: ...


class InMemoryReportCache:
    def __init__(self) -> None:
        self._reports: dict[int, TestTaskReportResponse] = {}
        self._lock = Lock()

    def get(self, task_id: int) -> TestTaskReportResponse | None:
        with self._lock:
            return self._reports.get(task_id)

    def set(self, report: TestTaskReportResponse) -> None:
        with self._lock:
            self._reports[report.task.id] = report

    def delete(self, task_id: int) -> None:
        with self._lock:
            self._reports.pop(task_id, None)


class RedisReportCache:
    def __init__(
        self,
        client: Redis,
        ttl_seconds: int = 300,
    ) -> None:
        self._client = client
        self._ttl_seconds = ttl_seconds

    @staticmethod
    def _key(task_id: int) -> str:
        return f"test-task-report:{task_id}"

    def get(self, task_id: int) -> TestTaskReportResponse | None:
        try:
            data = self._client.get(self._key(task_id))
        except RedisError:
            logger.warning(
                "Failed to read report cache for task %s",
                task_id,
                exc_info=True,
            )
            return None

        if data is None:
            return None

        return TestTaskReportResponse.model_validate_json(data)

    def set(self, report: TestTaskReportResponse) -> None:
        try:
            self._client.setex(
                self._key(report.task.id),
                self._ttl_seconds,
                report.model_dump_json(),
            )
        except RedisError:
            logger.warning(
                "Failed to write report cache for task %s",
                report.task.id,
                exc_info=True,
            )

    def delete(self, task_id: int) -> None:
        try:
            self._client.delete(self._key(task_id))
        except RedisError:
            logger.warning(
                "Failed to delete report cache for task %s",
                task_id,
                exc_info=True,
            )
