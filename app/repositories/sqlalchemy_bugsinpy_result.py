from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.bugsinpy_result import BugsInPyResultModel
from app.schemas.test_task import BugsInPyResultCreate, BugsInPyResultResponse
from app.services.failure_analysis import analyze_failure


class SQLAlchemyBugsInPyResultRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _to_response(model: BugsInPyResultModel) -> BugsInPyResultResponse:
        return BugsInPyResultResponse(
            id=model.id,
            task_id=model.task_id,
            project=model.project,
            bug_id=model.bug_id,
            trigger_test=model.trigger_test,
            buggy_outcome=model.buggy_outcome,
            fixed_outcome=model.fixed_outcome,
            failure_log=model.failure_log,
            category=model.category,
            reason=model.reason,
            suggestion=model.suggestion,
            regression_passed=model.regression_passed,
        )

    def save(
        self, task_id: int, result: BugsInPyResultCreate
    ) -> BugsInPyResultResponse:
        analysis = analyze_failure(result.failure_log)
        model = BugsInPyResultModel(
            task_id=task_id,
            **result.model_dump(),
            **analysis,
            regression_passed=(
                result.buggy_outcome in {"failed", "error"}
                and result.fixed_outcome == "passed"
            ),
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_response(model)

    def get_by_task_id(self, task_id: int) -> list[BugsInPyResultResponse]:
        statement = (
            select(BugsInPyResultModel)
            .where(BugsInPyResultModel.task_id == task_id)
            .order_by(BugsInPyResultModel.id)
        )
        return [self._to_response(item) for item in self.db.scalars(statement)]
