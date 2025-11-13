# AI Aggregation Platform

这是一个AI聚合平台、简单配置无缝切换各AI的管理平台、使用fastAPI+PostgreSQL来管理。
主要有以下特色：

- 多模型接入
- 多用户支持
- 用户鉴权
- 模型统一的访问接口：T http://localhost:8000/api/v1/...
- token计费
- 简单的模型配置
- 高拓展性

### 目前内置的AI适配器：

- deepseek
- 硅基流动
- openAI

> 如需添加自定义AI模型、请继承BaseLLMAdapter、定义相关的接口代码即可
> AI模型适配器代码位置：app/llm_adapters/目录下

### 2. 如何使用?

#### 配置文件

配置.env文件

```dotenv
# 应用配置
APP_NAME=AI-aggregation
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true

# 服务器配置
HOST=127.0.0.1
PORT=8000

# 数据库配置
DATABASE_URL=postgresql+asyncpg://用户名:密码@localhost:5432/数据库名
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=5

# 日志配置
LOG_LEVEL=DEBUG
LOG_FILE_PATH=./logs

# 安全配置（开发环境可以用简单的）
SECRET_KEY= bitianxiang# 必填项
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440


## 一下配置至少配置一个
# OpenAI配置
OPENAI_API_KEY=
# 可选
OPENAI_BASE_URL=https://api.siliconflow.cn/v1

# SiliconFlow
SILICONFLOW_API_KEY=
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1

# deepseek
DEEPSEEK_API_KEY=
DEEPSEEKBASE_URL=https://api.deepseek.com

# 超时设置 默认120s
CONNECT_TIMEOUT=120

#系统提示词设置 默认空！
SYSTEM_PROMPT='You are an AI assistant of the AI aggregation platform developed by Martin. Your name is Xiaomei'
```

### 3.初始化数据库

```bash
# 创建迁移
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

### 4.运行应用

```bash
# 开发模式
python -m app.main

# 或使用uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5.OpenAPI文档

打开浏览器访问：http://localhost:8000/docs






