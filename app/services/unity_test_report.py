from datetime import datetime
from xml.etree import ElementTree

from app.schemas.test_task import UnityTestResultCreate

MAX_REPORT_BYTES = 5 * 1024 * 1024


def _parse_non_negative_int(root: ElementTree.Element, name: str) -> int:
    value = root.get(name)
    if value is None:
        raise ValueError(f"Unity test report is missing '{name}'")

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"Unity test report has an invalid '{name}'") from exc

    if parsed < 0:
        raise ValueError(f"Unity test report has a negative '{name}'")
    return parsed


def _parse_timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Unity test report has an invalid timestamp") from exc


def _find_test_platform(root: ElementTree.Element) -> str:
    for property_node in root.findall(".//property"):
        if property_node.get("name") == "platform":
            value = property_node.get("value")
            if value in ("EditMode", "PlayMode"):
                return value

    for assembly in root.findall(".//test-suite[@type='Assembly']"):
        name = assembly.get("name", "")
        if "EditMode" in name:
            return "EditMode"
        if "PlayMode" in name:
            return "PlayMode"

    raise ValueError("Unity test report does not identify EditMode or PlayMode")


def parse_unity_test_report(xml_content: bytes) -> UnityTestResultCreate:
    if not xml_content:
        raise ValueError("Unity test report is empty")
    if len(xml_content) > MAX_REPORT_BYTES:
        raise ValueError("Unity test report exceeds the 5 MB limit")

    try:
        root = ElementTree.fromstring(xml_content)
    except ElementTree.ParseError as exc:
        raise ValueError("Unity test report is not valid XML") from exc

    if root.tag != "test-run":
        raise ValueError("Unity test report root must be 'test-run'")

    total = _parse_non_negative_int(root, "total")
    passed = _parse_non_negative_int(root, "passed")
    failed = _parse_non_negative_int(root, "failed")
    skipped = _parse_non_negative_int(root, "skipped")
    inconclusive = _parse_non_negative_int(root, "inconclusive")

    if passed + failed + skipped + inconclusive != total:
        raise ValueError("Unity test report result counts do not match total")

    try:
        duration_seconds = float(root.get("duration", ""))
    except ValueError as exc:
        raise ValueError("Unity test report has an invalid duration") from exc
    if duration_seconds < 0:
        raise ValueError("Unity test report has a negative duration")

    result = root.get("result")
    if not result:
        raise ValueError("Unity test report is missing 'result'")

    return UnityTestResultCreate(
        test_platform=_find_test_platform(root),
        result=result,
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        inconclusive=inconclusive,
        duration_seconds=duration_seconds,
        engine_version=root.get("engine-version"),
        started_at=_parse_timestamp(root.get("start-time")),
        finished_at=_parse_timestamp(root.get("end-time")),
    )
