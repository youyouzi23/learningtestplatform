import asyncio
from datetime import UTC, datetime
from typing import Protocol

from app.schemas.test_task import (
    FailureAnalysisResponse,
    TestTaskCreate,
    TestTaskLogResponse,
    TestTaskReportResponse,
    TestTaskResponse,
    TestTaskStatus,
    UnityTestResultCreate,
    UnityTestResultResponse,
)
from app.services.failure_analysis import analyze_failure
from app.services.report_cache import ReportCache


class TaskRepository(Protocol):
    def create(
        self,
        data: TestTaskCreate,
    ) -> TestTaskResponse: ...

    def get(
        self,
        task_id: int,
    ) -> TestTaskResponse | None: ...

    def save(
        self,
        task: TestTaskResponse,
    ) -> None: ...


class TaskLogRepository(Protocol):
    def add(
        self,
        log: TestTaskLogResponse,
    ) -> None: ...

    def get_by_task_id(
        self,
        task_id: int,
        status: TestTaskStatus | None = None,
        keyword: str | None = None,
        offset: int = 0,
        limit: int | None = None,
    ) -> list[TestTaskLogResponse]: ...


class UnityTestResultRepository(Protocol):
    def save(
        self,
        task_id: int,
        result: UnityTestResultCreate,
    ) -> UnityTestResultResponse: ...

    def get_by_task_id(
        self,
        task_id: int,
    ) -> list[UnityTestResultResponse]: ...


class TaskService:
    def __init__(
        self,
        task_repository: TaskRepository,
        log_repository: TaskLogRepository,
        report_cache: ReportCache | None = None,
        unity_result_repository: UnityTestResultRepository | None = None,
    ) -> None:
        self.task_repository = task_repository
        self.log_repository = log_repository
        self.report_cache = report_cache
        self.unity_result_repository = unity_result_repository

    def add_log(
        self,
        task_id: int,
        status: TestTaskStatus,
        message: str,
    ) -> None:
        log = TestTaskLogResponse(
            task_id=task_id,
            status=status,
            message=message,
            created_at=datetime.now(UTC),
        )
        self.log_repository.add(log)

    def create(self, data: TestTaskCreate) -> TestTaskResponse:
        task = self.task_repository.create(data)

        self.add_log(
            task.id,
            "pending",
            "Test task created",
        )

        return task

    async def execute(
        self,
        task_id: int,
        delay_seconds: float,
    ) -> None:
        task = self.task_repository.get(task_id)
        if task is None:
            return

        if self.report_cache is not None:
            self.report_cache.delete(task_id)

        task.status = "running"
        self.task_repository.save(task)
        self.add_log(task_id, "running", "Test task started")

        try:
            await asyncio.sleep(delay_seconds)
        except Exception as exc:
            task.status = "failed"
            self.task_repository.save(task)

            self.add_log(
                task_id,
                "failed",
                f"Test task failed: {type(exc).__name__}: {exc}",
            )
            raise
        else:
            task.status = "success"
            self.task_repository.save(task)

            self.add_log(
                task_id,
                "success",
                "Test task completed",
            )

    def get(self, task_id: int) -> TestTaskResponse | None:
        return self.task_repository.get(task_id)

    def get_logs(
        self,
        task_id: int,
        status: TestTaskStatus | None = None,
        keyword: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[TestTaskLogResponse] | None:
        if self.get(task_id) is None:
            return None

        return self.log_repository.get_by_task_id(
            task_id,
            status=status,
            keyword=keyword,
            offset=offset,
            limit=limit,
        )

    def create_batch(self, tasks: list[TestTaskCreate]) -> list[TestTaskResponse]:
        result = []
        for task in tasks:
            task_response = self.create(task)
            result.append(task_response)
        return result

    def record_unity_result(
        self,
        task_id: int,
        result: UnityTestResultCreate,
    ) -> UnityTestResultResponse | None:
        task = self.task_repository.get(task_id)
        if task is None:
            return None
        if self.unity_result_repository is None:
            raise RuntimeError("Unity test result repository is not configured")

        saved_result = self.unity_result_repository.save(task_id, result)
        succeeded = result.result.lower() == "passed" and result.failed == 0
        task.status = "success" if succeeded else "failed"
        self.task_repository.save(task)

        status: TestTaskStatus = "success" if succeeded else "failed"
        self.add_log(
            task_id,
            status,
            (
                f"Unity {result.test_platform} results imported: "
                f"{result.passed}/{result.total} passed, "
                f"{result.failed} failed"
            ),
        )

        if self.report_cache is not None:
            self.report_cache.delete(task_id)
        return saved_result

    def get_report(self, task_id: int) -> TestTaskReportResponse | None:
        if self.report_cache is not None:
            cached_report = self.report_cache.get(task_id)

            if cached_report is not None:
                return cached_report

        task = self.task_repository.get(task_id)

        if task is None:
            return None

        logs = self.log_repository.get_by_task_id(task_id)

        failed_log = next(
            (log for log in reversed(logs) if log.status == "failed"),
            None,
        )

        failure_analysis = (
            FailureAnalysisResponse(**analyze_failure(failed_log.message))
            if failed_log is not None
            else None
        )

        started_at = next(
            (log.created_at for log in logs if log.status == "running"),
            None,
        )

        finished_at = next(
            (
                log.created_at
                for log in reversed(logs)
                if log.status in ("success", "failed")
            ),
            None,
        )

        duration = None

        if started_at is not None and finished_at is not None:
            duration = (finished_at - started_at).total_seconds()

        report = TestTaskReportResponse(
            task=task,
            logs=logs,
            total_logs=len(logs),
            execution_duration_seconds=duration,
            generated_at=datetime.now(UTC),
            failure_analysis=failure_analysis,
            unity_results=(
                self.unity_result_repository.get_by_task_id(task_id)
                if self.unity_result_repository is not None
                else []
            ),
        )

        if self.report_cache is not None and task.status in ("success", "failed"):
            self.report_cache.set(report)

        return report
