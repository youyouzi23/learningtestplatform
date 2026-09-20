import pytest

from app.services.failure_analysis import analyze_failure


@pytest.mark.parametrize(
    ("message", "expected_category", "expected_reason"),
    [
        (
            "ADB reports DEVICE OFFLINE",
            "device_offline",
            "测试设备离线",
        ),
        (
            "Operation timed out after 30 seconds",
            "timeout",
            "操作超时",
        ),
        (
            "Connection refused by target service",
            "connection_refused",
            "连接被拒绝",
        ),
        (
            "Unexpected rendering error",
            "unknown",
            "未匹配到已知故障规则",
        ),
    ],
)
def test_analyze_failure(
    message: str,
    expected_category: str,
    expected_reason: str,
) -> None:
    result = analyze_failure(message)

    assert result["category"] == expected_category
    assert result["reason"] == expected_reason
    assert result["suggestion"]
