# Test Platform

[![CI](https://github.com/youyouzi23/learningtestplatform/actions/workflows/ci.yml/badge.svg)](https://github.com/youyouzi23/learningtestplatform/actions/workflows/ci.yml)

面向测试开发作品展示的统一测试平台。FastAPI 提供测试任务、执行日志、失败
分类和报告 API；MySQL 负责持久化，Redis 缓存完成报告；Unity NUnit XML 与
BugsInPy buggy/fixed 结果可接入同一报告。仓库同时提供 pytest、Postman/Newman、
JMeter、Docker Compose 和 GitHub Actions。

## 已实现能力

- 单个及批量任务创建、状态流转、日志筛选和分页。
- API Key 鉴权：管理员可写，查看者只读，覆盖 401/403 权限边界。
- Unity EditMode/PlayMode NUnit XML 解析、持久化和统一报告。
- BugsInPy buggy/fixed 结果导入、失败分类、前后对比和回归判定。
- Redis 报告缓存、TTL、主动失效，以及连接异常时的数据库降级。
- SQLite 零配置开发；Docker Compose 和 CI 使用真实 MySQL、Redis。
- 功能、单元、集成、系统、黑盒、边界及回归测试材料。

测试策略见 [`docs/test-plan.md`](docs/test-plan.md)，需求与自动化的对应关系见
[`docs/traceability-matrix.md`](docs/traceability-matrix.md)。

## 架构

```mermaid
flowchart LR
    Client[Postman / JMeter / Unity] -->|X-API-Key| API[FastAPI]
    API --> Service[Service]
    Service --> DB[(MySQL / SQLite)]
    Service --> Cache[(Redis)]
    Bugs[BugsInPy] --> API
    API --> Report[Unified Report]
```

## 快速开始

### Docker Compose（推荐）

```powershell
docker compose up --build
```

- API：http://127.0.0.1:8000
- Swagger：http://127.0.0.1:8000/docs
- 管理员示例密钥：`local-admin-key`
- 查看者示例密钥：`local-viewer-key`

示例密钥仅用于本地演示，生产环境必须通过环境变量替换。

### Python 本地环境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload
```

默认使用 SQLite。切换到 MySQL、Redis 和自定义密钥时参考 `.env.example`：

```powershell
$env:DATABASE_URL = "mysql+pymysql://game_test:password@127.0.0.1:3306/game_test_platform?charset=utf8mb4"
$env:REDIS_URL = "redis://127.0.0.1:6379/0"
$env:API_ADMIN_KEY = "replace-with-a-long-random-key"
$env:API_VIEWER_KEY = "replace-with-another-long-random-key"
```

应用启动时会创建所需表。正式项目建议改用 Alembic 管理数据库迁移。

## API 示例

```powershell
$headers = @{ "X-API-Key" = "dev-admin-key" }
$body = @{
  name = "接口回归测试"
  test_type = "automation"
  platform = "windows"
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/test-tasks" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $body
```

## 自动化验证

```powershell
python -m pytest --ignore=tests/integration
python -m ruff check .
python -m ruff format --check .
```

启动 MySQL、Redis 后执行真实集成测试：

```powershell
$env:RUN_INTEGRATION_TESTS = "1"
$env:INTEGRATION_DATABASE_URL = "mysql+pymysql://game_test:game_test_password@127.0.0.1:3306/game_test_platform?charset=utf8mb4"
$env:INTEGRATION_REDIS_URL = "redis://127.0.0.1:6379/0"
python -m pytest tests/integration
```

GitHub Actions 分别执行代码检查与覆盖率、真实 MySQL/Redis 集成测试，以及
Newman 黑盒流程，并保存覆盖率和服务日志 Artifact。

## BugsInPy 回归结果

本项目引用维护版
[BugsInPy](https://github.com/reproducing-research-projects/BugsInPy)，不复制整个
上游数据集。按照 [`datasets/bugsinpy/README.md`](datasets/bugsinpy/README.md)
运行 buggy 与 fixed 版本，将真实结果写入样例清单后导入：

```powershell
python scripts/import_bugsinpy.py `
  --manifest datasets/bugsinpy/sample_manifest.json `
  --task-id 1 `
  --api-key dev-admin-key
```

## Unity 自动化流水线

关闭 Unity Editor，启动平台后执行：

```powershell
.\scripts\run-unity-test-pipeline.ps1 `
  -UnityExe "C:\Program Files\Unity\Hub\Editor\2022.3.62f3c1\Editor\Unity.exe" `
  -UnityProjectPath "C:\path\to\unity-match3" `
  -ApiKey "dev-admin-key"
```

脚本依次运行 EditMode、PlayMode，上传 NUnit XML 并保存统一报告。

## Postman 与 JMeter

- Postman/Newman：`postman/game-test-platform.postman_collection.json`
- API 读取性能场景：`jmeter/api-read-test.jmx`
- 健康检查性能场景：`jmeter/health-test.jmx`

JMeter 读取受保护接口时可传入密钥：

```powershell
jmeter -n -t jmeter/api-read-test.jmx -Jtask_id=1 -Japi_key=dev-admin-key
```

## 目录结构

```text
app/                 FastAPI、Service、Repository、SQLAlchemy 模型
datasets/bugsinpy/   数据集来源说明和小型导入样例
docs/                架构、测试计划、用例和追踪矩阵
jmeter/              性能测试计划
postman/             黑盒 API 集合
scripts/             Unity 流水线与 BugsInPy 导入工具
sql/                 MySQL 建表参考
tests/               单元、接口及真实服务集成测试
```

## 仓库卫生

`.env`、虚拟环境、本地数据库、缓存、JMeter 原始结果、Unity 日志和许可证均不
应提交。上传前运行 `git status --short`，只提交源码、测试、配置、少量可复核
样例和文档。
