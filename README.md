# Game Test Platform

一个用于学习和面试展示的游戏测试开发平台。项目将逐步支持设备管理、自动化任务调度、游戏 UI 自动化、客户端性能采集和测试报告。

## 当前里程碑

Milestone 1：FastAPI 项目骨架与健康检查接口。

## 技术栈

- Python
- FastAPI
- pytest
- 后续：MySQL、Redis、Celery、GAutomator、Perfetto

## 本地启动

在项目目录中创建并激活虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

安装依赖：

```powershell
python -m pip install -r requirements-dev.txt
```

启动服务：

```powershell
python -m uvicorn app.main:app --reload
```

访问：

- 健康检查：http://127.0.0.1:8000/health
- Swagger 文档：http://127.0.0.1:8000/docs

运行测试：

```powershell
python -m pytest
```

