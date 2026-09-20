from sqlalchemy.orm import Session

from app.models.test_task import TestTaskModel
from app.schemas.test_task import (
    TestTaskCreate,
    TestTaskResponse,
)


class SQLAlchemyTaskRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        data: TestTaskCreate,
    ) -> TestTaskResponse:
        model = TestTaskModel(
            name=data.name,
            test_type=data.test_type,
            platform=data.platform,
            status="pending",
        )

        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        return self._to_response(model)

    def get(
        self,
        task_id: int,
    ) -> TestTaskResponse | None:
        model = self.db.get(TestTaskModel, task_id)

        if model is None:
            return None

        return self._to_response(model)

    def save(
        self,
        task: TestTaskResponse,
    ) -> None:
        model = self.db.get(TestTaskModel, task.id)

        if model is None:
            return

        model.name = task.name
        model.test_type = task.test_type
        model.platform = task.platform
        model.status = task.status

        self.db.commit()

    @staticmethod
    def _to_response(
        model: TestTaskModel,
    ) -> TestTaskResponse:
        return TestTaskResponse.model_validate(
            model,
            from_attributes=True,
        )
