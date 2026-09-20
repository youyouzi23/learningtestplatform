from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.test_task_log import TestTaskLogModel
from app.schemas.test_task import TestTaskLogResponse, TestTaskStatus


class SQLAlchemyTaskLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, log: TestTaskLogResponse) -> None:
        model = TestTaskLogModel(
            task_id=log.task_id,
            status=log.status,
            message=log.message,
            created_at=log.created_at,
        )
        self.db.add(model)
        self.db.commit()

    def get_by_task_id(
        self,
        task_id: int,
        status: TestTaskStatus | None = None,
        keyword: str | None = None,
        offset: int = 0,
        limit: int | None = None,
    ) -> list[TestTaskLogResponse]:
        # 先创建查询
        statement = select(TestTaskLogModel).where(TestTaskLogModel.task_id == task_id)

        if status is not None:
            statement = statement.where(TestTaskLogModel.status == status)

        if keyword is not None:
            statement = statement.where(
                TestTaskLogModel.message.contains(
                    keyword,
                    autoescape=True,
                )
            )

        # 再对已有查询排序、分页
        statement = statement.order_by(
            TestTaskLogModel.created_at,
            TestTaskLogModel.id,
        ).offset(offset)

        if limit is not None:
            statement = statement.limit(limit)

        models = self.db.scalars(statement).all()

        return [
            TestTaskLogResponse.model_validate(
                model,
                from_attributes=True,
            )
            for model in models
        ]
