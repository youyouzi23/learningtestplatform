from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.repositories.sqlalchemy_test_task import (
    SQLAlchemyTaskRepository,
)
from app.repositories.sqlalchemy_test_task_log import (
    SQLAlchemyTaskLogRepository,
)
from app.schemas.test_task import (
    TestTaskCreate as TaskCreate,
)
from app.schemas.test_task import (
    TestTaskLogResponse as TaskLogResponse,
)
from app.services.test_task import TaskService


def test_sqlalchemy_task_log_repository() -> None:
    engine = create_engine("sqlite:///:memory:")

    TestingSessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    try:
        task_repository = SQLAlchemyTaskRepository(db)
        log_repository = SQLAlchemyTaskLogRepository(db)

        task = task_repository.create(
            TaskCreate(
                name="Android 登录兼容性测试",
                test_type="compatibility",
                platform="android",
            )
        )

        log_repository.add(
            TaskLogResponse(
                task_id=task.id,
                status="pending",
                message="Test task created",
                created_at=datetime(2026, 8, 31, 10, 0, tzinfo=UTC),
            )
        )

        log_repository.add(
            TaskLogResponse(
                task_id=task.id,
                status="running",
                message="Test task started",
                created_at=datetime(2026, 8, 31, 10, 1, tzinfo=UTC),
            )
        )

        logs = log_repository.get_by_task_id(task.id)

        assert len(logs) == 2
        assert logs[0].status == "pending"
        assert logs[1].status == "running"
        assert logs[0].task_id == task.id

    finally:
        db.close()
        engine.dispose()


def test_report_includes_more_than_20_logs() -> None:
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )
    Base.metadata.create_all(bind=engine)

    try:
        with TestingSessionLocal() as db:
            task_repository = SQLAlchemyTaskRepository(db)
            log_repository = SQLAlchemyTaskLogRepository(db)
            service = TaskService(
                task_repository,
                log_repository,
            )

            # 直接调用仓库创建，避免自动增加一条日志
            task = task_repository.create(
                TaskCreate(
                    name="报告完整性测试",
                    test_type="automation",
                    platform="windows",
                )
            )

            start = datetime(
                2026,
                9,
                6,
                10,
                0,
                tzinfo=UTC,
            )

            for i in range(25):
                log_repository.add(
                    TaskLogResponse(
                        task_id=task.id,
                        status="success" if i == 24 else "running",
                        message=f"log-{i}",
                        created_at=start + timedelta(seconds=i),
                    )
                )

            task.status = "success"
            task_repository.save(task)

            # 日志列表仍然默认只返回20条
            page = service.get_logs(task.id)
            assert page is not None
            assert len(page) == 20

            # 报告必须读取完整25条日志
            report = service.get_report(task.id)
            assert report is not None
            assert report.total_logs == 25
            assert len(report.logs) == 25
            assert report.logs[-1].status == "success"
            assert report.execution_duration_seconds == 24.0

    finally:
        engine.dispose()
