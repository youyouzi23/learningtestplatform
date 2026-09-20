from datetime import UTC, datetime
from unittest.mock import Mock

from redis import Redis
from redis.exceptions import RedisError

from app.schemas import test_task as task_schemas
from app.services.report_cache import RedisReportCache


def make_report() -> task_schemas.TestTaskReportResponse:
    return task_schemas.TestTaskReportResponse(
        task=task_schemas.TestTaskResponse(
            id=1,
            name="Redis cache test",
            test_type="automation",
            platform="windows",
            status="success",
        ),
        logs=[],
        total_logs=0,
        execution_duration_seconds=0.0,
        generated_at=datetime.now(UTC),
    )


def test_redis_report_cache_get() -> None:
    report = make_report()
    client = Mock(spec=Redis)
    client.get.return_value = report.model_dump_json()

    cache = RedisReportCache(client)
    result = cache.get(1)

    assert result == report
    client.get.assert_called_once_with("test-task-report:1")


def test_redis_report_cache_set_and_delete() -> None:
    report = make_report()
    client = Mock(spec=Redis)
    cache = RedisReportCache(client, ttl_seconds=300)

    cache.set(report)
    cache.delete(1)

    client.setex.assert_called_once_with(
        "test-task-report:1",
        300,
        report.model_dump_json(),
    )
    client.delete.assert_called_once_with("test-task-report:1")


def test_redis_report_cache_degrades_on_connection_error() -> None:
    client = Mock(spec=Redis)
    client.get.side_effect = RedisError("Redis unavailable")
    client.setex.side_effect = RedisError("Redis unavailable")
    client.delete.side_effect = RedisError("Redis unavailable")

    cache = RedisReportCache(client)
    report = make_report()

    assert cache.get(1) is None
    cache.set(report)
    cache.delete(1)
