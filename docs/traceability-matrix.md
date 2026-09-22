# 需求—测试追踪矩阵

| 需求 | 测试层级 | 自动化证据 |
|---|---|---|
| 创建单个/批量任务 | 功能、接口、黑盒 | `tests/test_test_tasks.py`、Postman |
| 状态流转与日志查询 | 单元、集成、系统 | `tests/test_task_service.py`、API 测试 |
| 筛选、分页、非法参数 | 功能、边界、黑盒 | `tests/test_test_tasks.py` |
| 401/403 权限边界 | 安全、接口 | `test_missing_and_invalid_api_key_return_401`、`test_viewer_can_read_but_cannot_create` |
| MySQL 持久化 | Repository、集成 | `tests/integration/test_mysql_redis.py` |
| Redis TTL、删除与降级 | 单元、集成 | `tests/test_report_cache.py`、真实 Redis 集成测试 |
| Unity NUnit XML 导入 | 集成、回归 | `tests/test_unity_test_report.py`、API 导入测试 |
| BugsInPy buggy/fixed 对比 | 数据驱动、回归 | `test_import_bugsinpy_result_and_compare_versions` |
| 完整 API 用户流程 | 系统、黑盒 | Postman 集合与 Newman CI |
| 查询接口响应能力 | 性能 | `jmeter/api-read-test.jmx` |
