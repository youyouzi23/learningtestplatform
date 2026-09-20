import pytest

from app.services.unity_test_report import parse_unity_test_report


def _report_xml(
    *,
    platform: str = "EditMode",
    result: str = "Passed",
    total: int = 3,
    passed: int = 3,
    failed: int = 0,
) -> bytes:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<test-run result="{result}" total="{total}" passed="{passed}"
          failed="{failed}" skipped="0" inconclusive="0"
          duration="0.8341694" engine-version="3.5.0.0"
          start-time="2026-09-08 11:52:38Z"
          end-time="2026-09-08 11:52:39Z">
  <test-suite type="Assembly" name="Match3.Tests.{platform}.dll">
    <properties>
      <property name="platform" value="{platform}" />
    </properties>
  </test-suite>
</test-run>""".encode()


def test_parse_unity_test_report() -> None:
    result = parse_unity_test_report(_report_xml())

    assert result.test_platform == "EditMode"
    assert result.result == "Passed"
    assert result.total == 3
    assert result.passed == 3
    assert result.failed == 0
    assert result.duration_seconds == pytest.approx(0.8341694)
    assert result.engine_version == "3.5.0.0"
    assert result.started_at is not None
    assert result.finished_at is not None


def test_parse_unity_test_report_rejects_invalid_xml() -> None:
    with pytest.raises(ValueError, match="not valid XML"):
        parse_unity_test_report(b"<test-run")


def test_parse_unity_test_report_rejects_inconsistent_counts() -> None:
    with pytest.raises(ValueError, match="counts do not match"):
        parse_unity_test_report(_report_xml(total=4))
