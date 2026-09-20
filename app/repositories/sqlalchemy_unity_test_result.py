from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.unity_test_result import UnityTestResultModel
from app.schemas.test_task import UnityTestResultCreate, UnityTestResultResponse


class SQLAlchemyUnityTestResultRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def save(
        self,
        task_id: int,
        result: UnityTestResultCreate,
    ) -> UnityTestResultResponse:
        statement = select(UnityTestResultModel).where(
            UnityTestResultModel.task_id == task_id,
            UnityTestResultModel.test_platform == result.test_platform,
        )
        model = self.db.scalar(statement)

        if model is None:
            model = UnityTestResultModel(
                task_id=task_id,
                test_platform=result.test_platform,
            )
            self.db.add(model)

        for field, value in result.model_dump().items():
            setattr(model, field, value)

        self.db.commit()
        self.db.refresh(model)
        return self._to_response(model)

    def get_by_task_id(self, task_id: int) -> list[UnityTestResultResponse]:
        statement = (
            select(UnityTestResultModel)
            .where(UnityTestResultModel.task_id == task_id)
            .order_by(UnityTestResultModel.test_platform)
        )
        return [self._to_response(model) for model in self.db.scalars(statement).all()]

    @staticmethod
    def _to_response(model: UnityTestResultModel) -> UnityTestResultResponse:
        return UnityTestResultResponse.model_validate(model, from_attributes=True)
