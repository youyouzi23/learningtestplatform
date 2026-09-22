# 测试计划

## 目标与范围

验证测试任务、日志、统一报告、Unity NUnit XML、BugsInPy 缺陷对比、API
鉴权、MySQL 持久化和 Redis 缓存降级。健康检查属于公开接口，其余测试任务
接口均要求 `X-API-Key`。

## 测试分层

- 单元测试：服务规则、失败分类、XML 解析、缓存逻辑。
- 集成测试：Repository 与数据库、真实 MySQL/Redis 往返和 TTL。
- 接口测试：FastAPI TestClient 验证正常、异常、边界、鉴权和回归场景。
- 系统/黑盒测试：Postman/Newman 从任务创建到报告查询执行完整流程。
- 性能测试：JMeter 执行健康检查和任务/报告读取场景。

## 准入与准出

准入条件：依赖可安装，配置文件完整，MySQL/Redis 健康，测试数据可重复创建。

准出条件：

1. Ruff 和格式检查通过；
2. 单元及接口测试全部通过；
3. MySQL/Redis 集成测试通过；
4. Postman/Newman 黑盒流程通过；
5. 高优先级缺陷均有回归用例，无未说明的阻塞问题。

## 环境

- Python 3.11
- MySQL 8.4、Redis 7.4
- FastAPI、SQLAlchemy、pytest
- Newman、JMeter 5.6+

## 风险与处理

- Redis 不可用：回退到数据库生成报告，并记录告警。
- 外部数据集执行时间长：只在独立环境运行 BugsInPy，平台导入结构化结果。
- Unity License 不可用：保留核心 .NET 测试，Unity EditMode/PlayMode 作条件任务。
- 密钥泄露：仓库只保留示例值，生产密钥通过环境变量或 CI Secret 注入。
