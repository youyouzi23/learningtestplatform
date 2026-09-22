from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes import test_tasks as test_tasks_route
from app.database import Base, get_db
from app.main import app
from app.services.report_cache import InMemoryReportCache

client = TestClient(app)
client.headers.update({"X-API-Key": "dev-admin-key"})


@pytest.fixture(autouse=True)
def reset_test_state(monkeypatch) -> Generator[None, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    monkeypatch.setattr(
        test_tasks_route,
        "report_cache",
        InMemoryReportCache(),
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # 后台任务不走 Depends，所以把它使用的 SessionLocal 也替换为测试版
    monkeypatch.setattr(
        test_tasks_route,
        "SessionLocal",
        TestingSessionLocal,
    )

    monkeypatch.setattr(
        test_tasks_route,
        "TASK_EXECUTION_DELAY_SECONDS",
        0,
    )

    yield

    app.dependency_overrides.pop(get_db, None)
    engine.dispose()


def test_create_test_task() -> None:
    request_data = {
        "name": "Android 登录兼容性测试",
        "test_type": "compatibility",
        "platform": "android",
    }

    response = client.post("/test-tasks", json=request_data)

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "name": "Android 登录兼容性测试",
        "test_type": "compatibility",
        "platform": "android",
        "status": "pending",
    }


def test_create_task_with_invaild_platform() -> None:
    request_data = {
        "name": "错误平台测试",
        "test_type": "compatibility",
        "platform": "playstation",
    }

    response = client.post("/test-tasks", json=request_data)

    assert response.status_code == 422


def test_get_existing_task() -> None:
    request_data = {
        "name": "Android 登录兼容性测试",
        "test_type": "compatibility",
        "platform": "android",
    }

    create_response = client.post(
        "/test-tasks",
        json=request_data,
    )

    assert create_response.status_code == 201

    assert create_response.json()["status"] == "pending"

    task_id = create_response.json()["id"]

    response = client.get(f"/test-tasks/{task_id}")

    assert response.status_code == 200
    assert response.json()["id"] == task_id
    assert response.json()["name"] == "Android 登录兼容性测试"
    assert response.json()["status"] == "success"


def test_get_nonexistent_task() -> None:
    response = client.get("/test-tasks/999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Test task not found",
    }


def test_create_multiple_tasks_have_different_ids() -> None:
    first = client.post(
        "/test-tasks",
        json={
            "name": "任务一",
            "test_type": "automation",
            "platform": "android",
        },
    )

    second = client.post(
        "/test-tasks",
        json={
            "name": "任务二",
            "test_type": "performance",
            "platform": "windows",
        },
    )

    assert first.json()["id"] != second.json()["id"]


def test_create_test_tasks_batch() -> None:
    request_data = {
        "tasks": [
            {
                "name": "Android 批量任务",
                "test_type": "automation",
                "platform": "android",
            },
            {
                "name": "Windows 性能任务",
                "test_type": "performance",
                "platform": "windows",
            },
        ]
    }

    response = client.post(
        "/test-tasks/batch",
        json=request_data,
    )

    assert response.status_code == 201

    response_data = response.json()

    assert len(response_data) == 2
    assert response_data[0]["name"] == "Android 批量任务"
    assert response_data[1]["name"] == "Windows 性能任务"
    assert response_data[0]["status"] == "pending"
    assert response_data[1]["status"] == "pending"
    assert response_data[0]["id"] != response_data[1]["id"]


def test_create_empty_batch_returns_422() -> None:
    response = client.post(
        "/test-tasks/batch",
        json={"tasks": []},
    )

    assert response.status_code == 422


def test_get_task_logs() -> None:
    create_response = client.post(
        "/test-tasks",
        json={
            "name": "日志流程测试",
            "test_type": "automation",
            "platform": "android",
        },
    )

    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.get(f"/test-tasks/{task_id}/logs")

    assert response.status_code == 200

    logs = response.json()

    # 验证日志数量与状态顺序
    assert len(logs) == 3
    assert [log["status"] for log in logs] == [
        "pending",
        "running",
        "success",
    ]

    # 验证日志都属于当前任务
    assert all(log["task_id"] == task_id for log in logs)


def test_get_nonexistent_task_logs_returns_404() -> None:
    response = client.get("/test-tasks/999/logs")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Test task not found",
    }


def test_get_task_report() -> None:
    create_response = client.post(
        "/test-tasks",
        json={
            "name": "报告生成测试",
            "test_type": "automation",
            "platform": "android",
        },
    )

    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.get(f"/test-tasks/{task_id}/report")

    assert response.status_code == 200

    report = response.json()

    assert report["task"]["id"] == task_id
    assert report["task"]["status"] == "success"

    assert report["total_logs"] == 3
    assert [log["status"] for log in report["logs"]] == [
        "pending",
        "running",
        "success",
    ]

    assert report["execution_duration_seconds"] is not None
    assert report["execution_duration_seconds"] >= 0
    assert report["generated_at"] is not None
    assert report["failure_analysis"] is None


def test_get_nonexistent_task_report_returns_404() -> None:
    response = client.get("/test-tasks/999/report")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Test task not found",
    }


def test_task_report_is_cached() -> None:
    create_response = client.post(
        "/test-tasks",
        json={
            "name": "报告缓存测试",
            "test_type": "automation",
            "platform": "android",
        },
    )

    task_id = create_response.json()["id"]

    first_response = client.get(f"/test-tasks/{task_id}/report")
    second_response = client.get(f"/test-tasks/{task_id}/report")

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_report = first_response.json()
    second_report = second_response.json()

    assert first_report["generated_at"] == second_report["generated_at"]


def test_filter_task_logs() -> None:
    create_response = client.post(
        "/test-tasks",
        json={
            "name": "日志筛选测试",
            "test_type": "automation",
            "platform": "android",
        },
    )
    task_id = create_response.json()["id"]

    status_response = client.get(
        f"/test-tasks/{task_id}/logs",
        params={"status": "success"},
    )

    assert status_response.status_code == 200
    status_logs = status_response.json()
    assert len(status_logs) == 1
    assert status_logs[0]["status"] == "success"

    keyword_response = client.get(
        f"/test-tasks/{task_id}/logs",
        params={"keyword": "started"},
    )

    assert keyword_response.status_code == 200
    keyword_logs = keyword_response.json()
    assert len(keyword_logs) == 1
    assert keyword_logs[0]["message"] == "Test task started"

    combined_response = client.get(
        f"/test-tasks/{task_id}/logs",
        params={
            "status": "running",
            "keyword": "started",
        },
    )

    assert combined_response.status_code == 200
    combined_logs = combined_response.json()
    assert len(combined_logs) == 1
    assert combined_logs[0]["status"] == "running"


def test_filter_task_logs_with_invalid_status_returns_422() -> None:
    response = client.get(
        "/test-tasks/1/logs",
        params={"status": "unknown"},
    )

    assert response.status_code == 422


def test_filter_task_logs_with_empty_keyword_returns_422() -> None:
    response = client.get(
        "/test-tasks/1/logs",
        params={"keyword": ""},
    )

    assert response.status_code == 422


def test_get_task_logs_with_pagination() -> None:
    create_response = client.post(
        "/test-tasks",
        json={
            "name": "日志分页测试",
            "test_type": "automation",
            "platform": "android",
        },
    )
    task_id = create_response.json()["id"]

    first_page_response = client.get(
        f"/test-tasks/{task_id}/logs",
        params={
            "offset": 0,
            "limit": 2,
        },
    )

    assert first_page_response.status_code == 200
    first_page = first_page_response.json()
    assert len(first_page) == 2
    assert first_page[0]["status"] == "pending"
    assert first_page[1]["status"] == "running"

    second_page_response = client.get(
        f"/test-tasks/{task_id}/logs",
        params={
            "offset": 2,
            "limit": 2,
        },
    )

    assert second_page_response.status_code == 200
    second_page = second_page_response.json()
    assert len(second_page) == 1
    assert second_page[0]["status"] == "success"


def test_get_task_logs_with_invalid_offset_returns_422() -> None:
    response = client.get(
        "/test-tasks/1/logs",
        params={"offset": -1},
    )

    assert response.status_code == 422


def test_get_task_logs_with_invalid_limit_returns_422() -> None:
    zero_response = client.get(
        "/test-tasks/1/logs",
        params={"limit": 0},
    )
    too_large_response = client.get(
        "/test-tasks/1/logs",
        params={"limit": 101},
    )

    assert zero_response.status_code == 422
    assert too_large_response.status_code == 422


def test_import_unity_result_and_include_it_in_report() -> None:
    create_response = client.post(
        "/test-tasks",
        json={
            "name": "Unity EditMode 测试",
            "test_type": "automation",
            "platform": "windows",
        },
    )
    task_id = create_response.json()["id"]

    # Prime the report cache to verify that importing a result invalidates it.
    assert client.get(f"/test-tasks/{task_id}/report").json()["unity_results"] == []

    xml_report = b"""<?xml version="1.0" encoding="utf-8"?>
<test-run result="Passed" total="632" passed="632" failed="0"
          skipped="0" inconclusive="0" duration="3.8562931"
          engine-version="3.5.0.0" start-time="2026-09-08 11:45:56Z"
          end-time="2026-09-08 11:46:00Z">
  <test-suite type="Assembly" name="Match3.Tests.EditMode.dll">
    <properties>
      <property name="platform" value="EditMode" />
    </properties>
  </test-suite>
</test-run>"""
    response = client.post(
        f"/test-tasks/{task_id}/unity-results",
        content=xml_report,
        headers={"Content-Type": "application/xml"},
    )

    assert response.status_code == 201
    assert response.json()["task_id"] == task_id
    assert response.json()["test_platform"] == "EditMode"
    assert response.json()["passed"] == 632
    assert response.json()["failed"] == 0

    report = client.get(f"/test-tasks/{task_id}/report").json()
    assert report["task"]["status"] == "success"
    assert len(report["unity_results"]) == 1
    assert report["unity_results"][0]["total"] == 632
    assert report["logs"][-1]["message"] == (
        "Unity EditMode results imported: 632/632 passed, 0 failed"
    )


def test_import_invalid_unity_result_returns_422() -> None:
    create_response = client.post(
        "/test-tasks",
        json={
            "name": "Unity 非法报告",
            "test_type": "automation",
            "platform": "windows",
        },
    )
    task_id = create_response.json()["id"]

    response = client.post(
        f"/test-tasks/{task_id}/unity-results",
        content=b"not xml",
        headers={"Content-Type": "application/xml"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Unity test report is not valid XML",
    }


def test_missing_and_invalid_api_key_return_401() -> None:
    unauthenticated_client = TestClient(app)

    missing_response = unauthenticated_client.get("/test-tasks/1")
    invalid_response = unauthenticated_client.get(
        "/test-tasks/1",
        headers={"X-API-Key": "wrong-key"},
    )

    assert missing_response.status_code == 401
    assert invalid_response.status_code == 401


def test_viewer_can_read_but_cannot_create() -> None:
    create_response = client.post(
        "/test-tasks",
        json={
            "name": "权限边界测试",
            "test_type": "security",
            "platform": "windows",
        },
    )
    task_id = create_response.json()["id"]
    viewer_headers = {"X-API-Key": "dev-viewer-key"}

    read_response = client.get(
        f"/test-tasks/{task_id}",
        headers=viewer_headers,
    )
    forbidden_response = client.post(
        "/test-tasks",
        headers=viewer_headers,
        json={
            "name": "越权创建任务",
            "test_type": "security",
            "platform": "windows",
        },
    )

    assert read_response.status_code == 200
    assert forbidden_response.status_code == 403


def test_import_bugsinpy_result_and_compare_versions() -> None:
    create_response = client.post(
        "/test-tasks",
        json={
            "name": "BugsInPy 回归验证",
            "test_type": "automation",
            "platform": "windows",
        },
    )
    task_id = create_response.json()["id"]

    response = client.post(
        f"/test-tasks/{task_id}/bugsinpy-results",
        json={
            "project": "youtube-dl",
            "bug_id": 1,
            "trigger_test": "test_YoutubeDL.py::TestFormatSelection::test_format",
            "buggy_outcome": "failed",
            "fixed_outcome": "passed",
            "failure_log": "Timeout while selecting the requested format",
        },
    )

    assert response.status_code == 201
    assert response.json()["regression_passed"] is True
    assert response.json()["category"] == "timeout"

    report = client.get(f"/test-tasks/{task_id}/report").json()
    assert len(report["bugsinpy_results"]) == 1
    assert report["bugsinpy_results"][0]["project"] == "youtube-dl"
