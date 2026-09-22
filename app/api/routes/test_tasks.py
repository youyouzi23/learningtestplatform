from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
)
from redis import Redis
from sqlalchemy.orm import Session

from app.config import (
    REDIS_URL,
    REPORT_CACHE_TTL_SECONDS,
    TASK_EXECUTION_DELAY_SECONDS,
)
from app.database import SessionLocal, get_db
from app.repositories.sqlalchemy_bugsinpy_result import (
    SQLAlchemyBugsInPyResultRepository,
)
from app.repositories.sqlalchemy_test_task import (
    SQLAlchemyTaskRepository,
)
from app.repositories.sqlalchemy_test_task_log import (
    SQLAlchemyTaskLogRepository,
)
from app.repositories.sqlalchemy_unity_test_result import (
    SQLAlchemyUnityTestResultRepository,
)
from app.schemas.test_task import (
    BugsInPyResultCreate,
    BugsInPyResultResponse,
    TestTaskBatchCreate,
    TestTaskCreate,
    TestTaskLogResponse,
    TestTaskReportResponse,
    TestTaskResponse,
    TestTaskStatus,
    UnityTestResultResponse,
)
from app.security import get_api_role, require_admin
from app.services.report_cache import RedisReportCache
from app.services.test_task import TaskService
from app.services.unity_test_report import parse_unity_test_report

redis_client = Redis.from_url(
    REDIS_URL,
    decode_responses=True,
)

report_cache = RedisReportCache(
    redis_client,
    ttl_seconds=REPORT_CACHE_TTL_SECONDS,
)

router = APIRouter(
    prefix="/test-tasks",
    tags=["test_tasks"],
)


def get_task_service(
    db: Session = Depends(get_db),
) -> TaskService:
    task_repository = SQLAlchemyTaskRepository(db)
    log_repository = SQLAlchemyTaskLogRepository(db)

    return TaskService(
        task_repository,
        log_repository,
        report_cache,
        SQLAlchemyUnityTestResultRepository(db),
        SQLAlchemyBugsInPyResultRepository(db),
    )


async def execute_test_task(task_id: int) -> None:
    db = SessionLocal()

    try:
        task_service = TaskService(
            SQLAlchemyTaskRepository(db),
            SQLAlchemyTaskLogRepository(db),
            report_cache,
            SQLAlchemyUnityTestResultRepository(db),
            SQLAlchemyBugsInPyResultRepository(db),
        )

        await task_service.execute(
            task_id,
            TASK_EXECUTION_DELAY_SECONDS,
        )
    finally:
        db.close()


@router.post(
    "",
    response_model=TestTaskResponse,
    status_code=201,
)
async def create_test_task(
    task: TestTaskCreate,
    background_tasks: BackgroundTasks,
    task_service: TaskService = Depends(get_task_service),
    _role: str = Depends(require_admin),
) -> TestTaskResponse:

    task_response = task_service.create(task)

    background_tasks.add_task(
        execute_test_task,
        task_response.id,
    )

    return task_response


@router.get("/{task_id}", response_model=TestTaskResponse)
async def get_test_task(
    task_id: int,
    task_service: TaskService = Depends(get_task_service),
    _role: str = Depends(get_api_role),
) -> TestTaskResponse:
    task = task_service.get(task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Test task not found",
        )

    return task


@router.post(
    "/batch",
    response_model=list[TestTaskResponse],
    status_code=201,
)
async def create_test_tasks_batch(
    batch: TestTaskBatchCreate,
    background_tasks: BackgroundTasks,
    task_service: TaskService = Depends(get_task_service),
    _role: str = Depends(require_admin),
) -> list[TestTaskResponse]:
    result = task_service.create_batch(batch.tasks)

    for task in result:
        background_tasks.add_task(
            execute_test_task,
            task.id,
        )

    return result


@router.get(
    "/{task_id}/logs",
    response_model=list[TestTaskLogResponse],
)
async def get_test_task_logs(
    task_id: int,
    status: TestTaskStatus | None = None,
    keyword: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    task_service: TaskService = Depends(get_task_service),
    _role: str = Depends(get_api_role),
) -> list[TestTaskLogResponse]:
    logs = task_service.get_logs(
        task_id, status=status, keyword=keyword, offset=offset, limit=limit
    )

    if logs is None:
        raise HTTPException(
            status_code=404,
            detail="Test task not found",
        )

    return logs


@router.get(
    "/{task_id}/report",
    response_model=TestTaskReportResponse,
)
async def get_test_task_report(
    task_id: int,
    task_service: TaskService = Depends(get_task_service),
    _role: str = Depends(get_api_role),
) -> TestTaskReportResponse:
    report = task_service.get_report(task_id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Test task not found",
        )

    return report


@router.post(
    "/{task_id}/unity-results",
    response_model=UnityTestResultResponse,
    status_code=201,
)
async def import_unity_test_result(
    task_id: int,
    request: Request,
    task_service: TaskService = Depends(get_task_service),
    _role: str = Depends(require_admin),
) -> UnityTestResultResponse:
    xml_content = await request.body()

    try:
        parsed_result = parse_unity_test_report(xml_content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    result = task_service.record_unity_result(task_id, parsed_result)
    if result is None:
        raise HTTPException(status_code=404, detail="Test task not found")
    return result


@router.post(
    "/{task_id}/bugsinpy-results",
    response_model=BugsInPyResultResponse,
    status_code=201,
)
async def import_bugsinpy_result(
    task_id: int,
    result_data: BugsInPyResultCreate,
    task_service: TaskService = Depends(get_task_service),
    _role: str = Depends(require_admin),
) -> BugsInPyResultResponse:
    result = task_service.record_bugsinpy_result(task_id, result_data)
    if result is None:
        raise HTTPException(status_code=404, detail="Test task not found")
    return result
