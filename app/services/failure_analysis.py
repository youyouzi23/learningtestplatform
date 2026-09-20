from typing import TypedDict


class FailureAnalysis(TypedDict):
    category: str
    reason: str
    suggestion: str


def analyze_failure(message: str) -> FailureAnalysis:
    text = message.lower()

    if "device offline" in text:
        return {
            "category": "device_offline",
            "reason": "测试设备离线",
            "suggestion": "检查设备连接和调试授权，确认设备在线后重试。",
        }

    if "timeout" in text or "timed out" in text:
        return {
            "category": "timeout",
            "reason": "操作超时",
            "suggestion": "检查设备响应、网络和执行日志，确认耗时原因。",
        }

    if "connection refused" in text:
        return {
            "category": "connection_refused",
            "reason": "连接被拒绝",
            "suggestion": "检查目标服务是否启动，以及地址和端口是否正确。",
        }

    return {
        "category": "unknown",
        "reason": "未匹配到已知故障规则",
        "suggestion": "查看完整日志和异常堆栈，进一步定位原因。",
    }
