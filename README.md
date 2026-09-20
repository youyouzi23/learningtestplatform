# Game Test Platform

一个面向测试开发学习与作品展示的游戏测试平台。项目使用 FastAPI 提供测试任务、执行日志、失败分析和统一报告 API，并支持导入 Unity Test Framework 生成的 NUnit XML 报告。

## 功能

- 创建单个或批量测试任务，支持状态筛选与分页查询。
- 记录任务执行日志，并生成包含耗时、失败原因和 Unity 结果的统一报告。
- 导入 Unity EditMode 和 PlayMode 的 NUnit XML，同一任务可汇总两类结果。
- 使用 Redis 缓存报告，Redis 不可用时自动回退到数据库查询。
- 提供 Postman 集合、JMeter 测试计划和 PowerShell Unity 自动化流水线。
- 使用 pytest 覆盖接口、服务、仓储、缓存降级、XML 解析与失败分析。

## 技术栈

- Python 3.11+
- FastAPI、Pydantic、Uvicorn
- SQLAlchemy、MySQL / SQLite
- Redis
- pytest、Postman、JMeter
- Unity Test Framework、PowerShell

## 快速开始

### 1. 创建环境并安装依赖

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

### 2. 配置环境变量

项目默认使用本地 SQLite，零配置即可启动。使用 MySQL 时，先参照 `.env.example` 设置环境变量：

```powershell
$env:DATABASE_URL = "mysql+pymysql://game_test:password@127.0.0.1:3306/game_test_platform?charset=utf8mb4"
$env:REDIS_URL = "redis://127.0.0.1:6379/0"
```

需要先创建数据库：

```sql
CREATE DATABASE game_test_platform
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

### 3. 启动服务

```powershell
python -m uvicorn app.main:app --reload
```

- 健康检查：http://127.0.0.1:8000/health
- Swagger：http://127.0.0.1:8000/docs

## 测试与代码检查

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

## Unity 报告导入

创建自动化任务后，将 Unity 生成的 NUnit XML 作为 `application/xml` 上传：

```powershell
$taskId = 1
$reportPath = "C:\path\to\editmode-results.xml"

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/test-tasks/$taskId/unity-results" `
  -ContentType "application/xml" `
  -InFile $reportPath
```

查询统一报告：

```text
GET /test-tasks/{task_id}/report
```

## Unity 自动化流水线

关闭 Unity Editor，启动平台 API 与 Redis，然后传入本机 Unity 和项目路径：

```powershell
.\scripts\run-unity-test-pipeline.ps1 `
  -UnityExe "C:\Program Files\Unity\Hub\Editor\2022.3.62f3c1\Editor\Unity.exe" `
  -UnityProjectPath "C:\path\to\unity-project"
```

也可以通过 `UNITY_EXE` 和 `UNITY_PROJECT_PATH` 环境变量配置。脚本会创建任务、依次运行 EditMode 与 PlayMode 测试、上传 XML，并保存统一报告。

## Postman 与 JMeter

- Postman 集合：`postman/game-test-platform.postman_collection.json`
- API 测试计划：`jmeter/api-read-test.jmx`
- 健康检查计划：`jmeter/health-test.jmx`

JMeter 的 `.jtl`、HTML 报告和日志属于可再生成产物，已通过 `.gitignore` 排除。

## 项目结构

```text
app/
  api/            FastAPI 路由
  models/         SQLAlchemy 模型
  repositories/   数据访问层
  schemas/        请求与响应模型
  services/       任务、报告、缓存与失败分析
jmeter/           JMeter 测试计划
postman/          Postman 集合
scripts/          Unity 自动化流水线
sql/              数据库建表脚本
tests/            自动化测试
```

## 上传 GitHub 前

确认以下命令只显示计划提交的源码和配置文件：

```powershell
git status --short
```

不要提交 `.env`、本地数据库、虚拟环境、JMeter 结果文件或 Unity 运行日志。
