from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

TestTaskStatus = Literal[
    "pending",
    "running",
    "success",
    "failed",
]

TestOutcome = Literal["passed", "failed", "error", "skipped"]


class TestTaskCreate(BaseModel):
    name: str
    test_type: Literal[
        "compatibility",
        "automation",
        "performance",
        "security",
    ]
    platform: Literal["android", "ios", "windows"]


class TestTaskResponse(TestTaskCreate):
    id: int
    status: TestTaskStatus


class TestTaskBatchCreate(BaseModel):
    tasks: list[TestTaskCreate] = Field(
        min_length=1,
        max_length=100,
    )


class TestTaskLogResponse(BaseModel):
    task_id: int
    status: TestTaskStatus
    message: str
    created_at: datetime


class FailureAnalysisResponse(BaseModel):
    category: str
    reason: str
    suggestion: str


UnityTestPlatform = Literal["EditMode", "PlayMode"]


class UnityTestResultCreate(BaseModel):
    test_platform: UnityTestPlatform
    result: str
    total: int = Field(ge=0)
    passed: int = Field(ge=0)
    failed: int = Field(ge=0)
    skipped: int = Field(ge=0)
    inconclusive: int = Field(ge=0)
    duration_seconds: float = Field(ge=0)
    engine_version: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class UnityTestResultResponse(UnityTestResultCreate):
    task_id: int


class BugsInPyResultCreate(BaseModel):
    project: str = Field(min_length=1, max_length=100)
    bug_id: int = Field(gt=0)
    trigger_test: str = Field(min_length=1, max_length=255)
    buggy_outcome: TestOutcome
    fixed_outcome: TestOutcome
    failure_log: str = Field(min_length=1, max_length=10_000)


class BugsInPyResultResponse(BugsInPyResultCreate):
    id: int
    task_id: int
    category: str
    reason: str
    suggestion: str
    regression_passed: bool


class TestTaskReportResponse(BaseModel):
    task: TestTaskResponse
    logs: list[TestTaskLogResponse]
    total_logs: int
    execution_duration_seconds: float | None
    generated_at: datetime
    failure_analysis: FailureAnalysisResponse | None = None
    unity_results: list[UnityTestResultResponse] = Field(default_factory=list)
    bugsinpy_results: list[BugsInPyResultResponse] = Field(default_factory=list)
