from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.repositories.sqlalchemy_test_task import (
    SQLAlchemyTaskRepository,
)
from app.schemas.test_task import TestTaskCreate as TaskCreate


def test_sqlalchemy_task_repository_crud() -> None:
    engine = create_engine("sqlite:///:memory:")

    TestingSessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    try:
        repository = SQLAlchemyTaskRepository(db)

        request_data = TaskCreate(
            name="Android 登录兼容性测试",
            test_type="compatibility",
            platform="android",
        )

        # Create
        created = repository.create(request_data)

        assert created.id == 1
        assert created.name == "Android 登录兼容性测试"
        assert created.status == "pending"

        # Read
        found = repository.get(created.id)

        assert found is not None
        assert found.id == created.id
        assert found.platform == "android"

        # Update
        created.status = "running"
        repository.save(created)

        updated = repository.get(created.id)

        assert updated is not None
        assert updated.status == "running"

    finally:
        db.close()
        engine.dispose()
