# AI Aggregation Platform (AI 聚合平台)

这是一个基于 **FastAPI** 和 **PostgreSQL** 构建的高性能 AI 聚合管理平台。它旨在为开发者和企业提供一个统一的接口来管理和调用多种大语言模型（LLM），实现无缝切换、统一计费和权限管理。

## ✨ 核心特性

*   **🧩 多模型统一接入**：支持 OpenAI、DeepSeek、硅基流动（SiliconFlow）、通义千问等多种主流模型，通过统一的 API 格式（OpenAI 兼容）进行调用。
*   **🔐 完善的用户鉴权**：基于 OAuth2 和 JWT 的用户认证系统，支持普通用户和管理员权限分级。
*   **💰 Token 计费与监控**：精确记录每一次调用的 Token 消耗和成本，提供详细的用量统计。
*   **📊 可视化管理后台**：内置基于 Vue.js 的管理仪表盘，提供流量监控、模型分布统计、用户管理和 API Key 管理功能。
*   **🛡️ 安全可靠**：支持强制密码修改策略、API Key 权限控制，保障系统安全。
*   **🚀 高性能与异步**：全链路异步设计（AsyncIO + AsyncPG），轻松应对高并发请求。
*   **🐳 Docker 一键部署**：提供完整的 Docker 和 Docker Compose 支持，开箱即用。

## 🛠️ 技术栈

*   **后端框架**: FastAPI (Python 3.13+)
*   **数据库**: PostgreSQL (AsyncPG 驱动)
*   **ORM**: SQLAlchemy (Async)
*   **依赖管理**: uv
*   **前端 (Admin)**: Vue.js 3 (CDN), Chart.js, Bootstrap 5
*   **部署**: Docker, Docker Compose

## 📂 项目结构

```plaintext
AI-aggregation-Platform/
├── app/
│   ├── adapters/      # LLM 模型适配器 (OpenAI, DeepSeek, etc.)
│   ├── api/           # API 路由定义 (v1)
│   ├── core/          # 核心配置 (Config, Security, Logger)
│   ├── crud/          # 数据库 CRUD 操作
│   ├── models/        # SQLAlchemy 数据模型
│   ├── schemas/       # Pydantic 数据验证模型
│   ├── services/      # 业务逻辑层 (ChatService)
│   └── templates/     # 静态模板 (Admin Dashboard)
├── alembic/           # 数据库迁移脚本
├── logs/              # 应用日志
├── test/              # 测试脚本
├── docker-compose.yml # Docker 编排文件
├── Dockerfile         # Docker 构建文件
└── pyproject.toml     # 项目依赖配置
```

### 1. 目前内置的 AI 适配器

- **DeepSeek**: [API-key 申请](https://www.deepseek.com/)
- **硅基流动 (SiliconFlow)**: [API-key 申请](https://www.siliconflow.cn/)
- **OpenAI**: [API-key 申请](https://platform.openai.com/)
- **通义千问 (Aliyun)**: [API-key 申请](https://bailian.console.aliyun.com/)

> **扩展性**: 如需添加自定义 AI 模型，只需继承 `app.adapters.base.BaseLLMAdapter` 抽象基类，并实现相关接口即可轻松扩展。

### 2. 如何使用?

#### 配置文件

配置.env文件

注意测试环境请创建 .env.dev 文件，生产环境请创建 .env.prod 文件



```dotenv
# .env.dev 
# 应用配置
APP_NAME=AI-aggregation
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true

# 服务器配置
HOST=127.0.0.1
PORT=8089

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
uvicorn app.main:app --reload --host 0.0.0.0 --port 8089
```

### 5.OpenAPI文档

打开浏览器访问：http://localhost:8089/docs
![http://localhost:8089/docs](img/docs.png)

### 6. Linux (Ubuntu) 部署指南 (Docker)

本指南将帮助您在 Ubuntu 服务器上使用 Docker 快速部署本项目。

#### 6.1 安装 Docker 和 Docker Compose

如果您尚未安装 Docker，请执行以下命令进行安装：

```bash
# 更新软件包索引
sudo apt-get update

# 安装必要的依赖
sudo apt-get install -y ca-certificates curl gnupg

# 添加 Docker 的官方 GPG 密钥
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 设置仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 验证安装
sudo docker run hello-world
```

#### 6.2 获取项目代码

```bash
git clone https://github.com/natsume37/AI-aggregation-Platform.git
cd AI-aggregation-Platform
```

#### 6.3 配置环境变量

复制示例配置文件并修改：

```bash
# 复制配置文件 (Docker 部署默认读取 .env)
cp .env.dev .env

# 编辑配置文件
nano .env
```

**重要修改项**：
在 Docker 环境下，数据库主机名应指向 `docker-compose.yml` 中定义的服务名 `db`，而不是 `localhost`。

请修改 `.env` 文件中的 `DATABASE_URL`：
```dotenv
# 将 localhost 修改为 db
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/ai_db
```
*注意：如果您修改了 docker-compose.yml 中的数据库密码，请同步修改此处。*

#### 6.4 启动服务

使用 Docker Compose 构建并启动服务：

```bash
sudo docker compose up -d --build
```

查看日志以确保服务正常启动：
```bash
sudo docker compose logs -f app
```

#### 6.5 初始化数据库

服务启动后，需要执行数据库迁移以创建表结构：

```bash
# 在容器内执行 Alembic 迁移
sudo docker compose exec app uv run alembic upgrade head
```

#### 6.6 访问服务

*   **API 文档**: http://您的服务器IP:8089/docs
*   **管理后台**: http://您的服务器IP:8089/admin

#### 6.7 常用管理命令

```bash
# 停止服务
sudo docker compose down

# 重启服务
sudo docker compose restart

# 查看应用日志
sudo docker compose logs -f app

# 进入应用容器终端
sudo docker compose exec app /bin/bash
```







