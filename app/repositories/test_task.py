from app.schemas.test_task import (
    TestTaskCreate,
    TestTaskResponse,
)


class InMemoryTaskRepository:
    def __init__(self) -> None:
        self._tasks: dict[int, TestTaskResponse] = {}

    def create(
        self,
        data: TestTaskCreate,
    ) -> TestTaskResponse:
        task_id = max(self._tasks, default=0) + 1

        task = TestTaskResponse(
            id=task_id,
            name=data.name,
            test_type=data.test_type,
            platform=data.platform,
            status="pending",
        )

        self._tasks[task.id] = task
        return task

    def save(self, task: TestTaskResponse) -> None:
        self._tasks[task.id] = task

    def get(self, task_id: int) -> TestTaskResponse | None:
        return self._tasks.get(task_id)

    def clear(self) -> None:
        self._tasks.clear()
