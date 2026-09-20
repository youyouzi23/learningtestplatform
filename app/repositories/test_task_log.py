from app.schemas.test_task import (
    TestTaskLogResponse,
    TestTaskStatus,
)


class InMemoryTaskLogRepository:
    def __init__(self) -> None:
        self._logs: dict[int, list[TestTaskLogResponse]] = {}

    def add(self, log: TestTaskLogResponse) -> None:
        self._logs.setdefault(log.task_id, []).append(log)

    def get_by_task_id(
        self,
        task_id: int,
        status: TestTaskStatus | None = None,
        keyword: str | None = None,
        offset: int = 0,
        limit: int | None = None,
    ) -> list[TestTaskLogResponse]:
        logs = list(self._logs.get(task_id, []))

        if status is not None:
            logs = [log for log in logs if log.status == status]

        if keyword is not None:
            keyword_lower = keyword.lower()
            logs = [log for log in logs if keyword_lower in log.message.lower()]
        if limit is None:
            return logs[offset:]

        return logs[offset : offset + limit]

    def clear(self) -> None:
        self._logs.clear()
