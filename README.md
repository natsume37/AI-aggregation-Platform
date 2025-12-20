# AI Aggregation Platform (AI 聚合平台)

这是一个基于 **FastAPI** 和 **PostgreSQL** 构建的高性能 AI 聚合管理平台。它旨在为开发者和企业提供一个统一的接口来管理和调用多种大语言模型（LLM），实现无缝切换、统一计费和权限管理。

## ✨ 核心特性

- **🧩 多模型统一接入**：支持 OpenAI、DeepSeek、硅基流动（SiliconFlow）、通义千问、豆包等多种主流模型，通过统一的 API 格式（OpenAI 兼容）进行调用。
- **🖼️ 多模态支持**：支持图片上传与识别（需配合支持视觉的模型，如豆包 Pro、GPT-4o 等），兼容 OpenAI 多模态 API 格式。
- **🔐 完善的用户鉴权**：基于 OAuth2 和 JWT 的用户认证系统，支持普通用户和管理员权限分级。
- **💰 Token 计费与监控**：精确记录每一次调用的 Token 消耗和成本，提供详细的用量统计。
- **📊 可视化管理后台**：内置基于 Vue.js 的管理仪表盘，提供流量监控、模型分布统计、用户管理和 API Key 管理功能。
- **🛡️ 安全可靠**：支持强制密码修改策略、API Key 权限控制，保障系统安全。
- **🚀 高性能与异步**：全链路异步设计（AsyncIO + AsyncPG），轻松应对高并发请求。经过深度优化，消除了冗余的 I/O 调用，CPU 占用极低。
- **🧩 插件系统**：内置扩展插件模块，支持每日新闻（60 秒读懂世界）等实用工具，可轻松扩展更多功能。
- **🐳 Docker 一键部署**：提供完整的 Docker 和 Docker Compose 支持，开箱即用。

## 🛠️ 技术栈

- **后端框架**: FastAPI (Python 3.13+)
- **数据库**: PostgreSQL (AsyncPG 驱动)
- **ORM**: SQLAlchemy (Async)
- **依赖管理**: uv
- **前端 (Admin)**: Vue.js 3 (CDN), Chart.js, Bootstrap 5
- **部署**: Docker, Docker Compose

## 📂 项目结构

```plaintext
AI-aggregation-Platform/
├── app/
│   ├── adapters/      # LLM 模型适配器 (OpenAI, DeepSeek, etc.)
│   ├── api/           # API 路由定义 (v1)
│   ├── core/          # 核心配置 (Config, Security, Logger)
│   ├── crud/          # 数据库 CRUD 操作
│   ├── models/        # SQLAlchemy 数据模型
│   ├── plugins/       # 扩展插件 (News, etc.)
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
- **豆包 (Volcengine)**: [API-key 申请](https://console.volcengine.com/ark/region:ark+cn-beijing/endpoint)

> **扩展性**: 如需添加自定义 AI 模型，只需继承 `app.adapters.base.BaseLLMAdapter` 抽象基类，并实现相关接口即可轻松扩展。

### 2. 如何使用?

#### 配置文件

配置.env 文件

注意测试环境请创建 .env.dev 文件，生产环境请创建 .env.prod 文件

```dotenv
# 应用配置
APP_NAME="FastAPI AI Backend"
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true

# 服务器配置
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ai_backend
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# 日志配置
LOG_LEVEL=INFO
LOG_FILE_PATH=./logs

# 安全配置
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

#AI配置、至少配置一种目前支持：硅基流动、deeseek、OpenAI（openAPI由于贫穷没法测试）
# OpenAI配置
OPENAI_API_KEY=
# 可选 有默认值
OPENAI_BASE_URL=

# SiliconFlow
SILICONFLOW_API_KEY=
#可选
SILICONFLOW_BASE_URL=

# deepseek
DEEPSEEK_API_KEY=
#可选
DEEPSEEKBASE_URL=

#豆包
DOUBAO_API_KEY=
DOUBAO_BASE_URL=

#系统提示词设置
SYSTEM_PROMPT='You are an AI assistant of the AI aggregation platform developed by Martin. Your name is Xiaomei'
```

#### 豆包（火山 Ark）重要说明

- 本项目对豆包使用 **OpenAI 兼容接口**：`POST {DOUBAO_BASE_URL}/chat/completions`。
- 如果调用返回 `ModelNotOpen`，表示你的火山账号尚未在 Ark 控制台开通/启用对应模型（或未绑定正确 Endpoint）。请先在控制台启用模型服务后再调用。

### 3. 快速开始（Windows + uv）

1. 初始化数据库（首次运行/新环境）：

```powershell
uv run alembic upgrade head
```

2. 启动服务（保持窗口不退出）：

```powershell
uv run python -m app.main
```

3. 访问文档：`http://localhost:8089/docs`

### 4. 创建 API Key

对外接口使用 `X-API-Key` 鉴权，你可以二选一：

- **方式 A：管理后台**：启动服务后访问 `http://localhost:8089/admin` 登录并创建 API Key。
- **方式 B：脚本生成（开发用）**：

```powershell
uv run python .\create_test_key.py
```

脚本会在数据库中创建一个可用的测试 Key 并打印出来。

### 5. API 调用示例

#### 5.1 纯文本（统一 OpenAI 格式）

```http
POST /api/v1/chat/completions
X-API-Key: <your_api_key>
Content-Type: application/json

{
  "provider": "doubao",
  "model": "doubao-1-5-vision-pro-32k-250115",
  "messages": [
    {"role": "user", "content": "你好，简单介绍一下你自己"}
  ]
}
```

#### 5.2 图片理解（Base64 Data URL，多模态）

`messages[].content` 支持传字符串（纯文本）或多模态列表：

```http
POST /api/v1/chat/completions
X-API-Key: <your_api_key>
Content-Type: application/json

{
  "provider": "doubao",
  "model": "doubao-1-5-vision-pro-32k-250115",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "这是什么植物？"},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,<BASE64>"}}
      ]
    }
  ]
}
```

### 6. 测试脚本

项目已提供图片理解测试脚本：`test/test_doubao_vision.py`（图片示例：`test/花.jpg`）。

```powershell
uv run .\test\test_doubao_vision.py
```

### 7. 工具箱 (Tools)

平台内置了实用的工具接口，方便集成到 AI Agent 或直接调用。

#### 每日 60 秒新闻 (Daily News)

提供 "60 秒读懂世界" 的每日新闻服务，支持图片流、图片链接和纯文本格式。

- **获取图片链接**: `GET /api/v1/tools/news`
  - 返回包含图片 URL 和日期的 JSON 数据。
- **获取图片流**: `GET /api/v1/tools/news/image`
  - 直接返回图片二进制流，可直接嵌入 `<img>` 标签。
- **获取完整 JSON 数据**: `GET /api/v1/tools/news/json`
  - 返回包含新闻列表、微语、农历日期等完整信息的结构化数据。
- **获取纯文本**: `GET /api/v1/tools/news/text`
  - 返回格式化后的纯文本新闻摘要。

### 4.初始化数据库

**⚠️ 前提**：执行迁移前，必须先在 PostgreSQL 中创建数据库（如 `ai_db`）。

如果尚未创建，请先连接数据库创建：

```sql
CREATE DATABASE ai_db;
```

然后执行以下命令初始化表结构：

```bash
# 执行迁移
uv run alembic upgrade head
```

### 5.运行应用

```bash
# 开发模式
python -m app.main

# 或使用uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8089
```

### 6.OpenAPI 文档

打开浏览器访问：http://localhost:8089/docs
![http://localhost:8089/docs](img/docs.png)

### 7. Linux (Ubuntu) 部署指南 (Docker)

本指南将帮助您在 Ubuntu 服务器上使用 Docker 快速部署本项目。

#### 7.1 安装 Docker 和 Docker Compose

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

#### 7.2 获取项目代码

```bash
git clone https://github.com/natsume37/AI-aggregation-Platform.git
cd AI-aggregation-Platform
```

#### 7.3 配置环境变量

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

_注意：如果您修改了 docker-compose.yml 中的数据库密码，请同步修改此处。_

#### 7.4 启动服务

使用 Docker Compose 构建并启动服务：

```bash
sudo docker compose up -d --build
```

查看日志以确保服务正常启动：

```bash
sudo docker compose logs -f app
```

#### 7.5 初始化数据库

服务启动后，需要执行数据库迁移以创建表结构：

```bash
# 在容器内执行 Alembic 迁移
sudo docker compose exec app uv run alembic upgrade head
```

#### 7.6 访问服务

- **API 文档**: http://您的服务器 IP:8089/docs
- **管理后台**: http://您的服务器 IP:8089/admin

#### 7.7 常用管理命令

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

### 8. Linux (Ubuntu) 完整部署指南 (手动部署)

本指南将引导您在 Linux 服务器（Ubuntu 20.04/22.04+）上从零开始部署本项目。

#### 8.1 安装 PostgreSQL 数据库

首先更新系统并安装 PostgreSQL。

```bash
# 更新软件源
sudo apt update && sudo apt upgrade -y

# 安装 PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# 启动并设置开机自启
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### 8.2 配置数据库用户与库

默认 PostgreSQL 使用 `postgres` 用户。我们需要创建一个专用的数据库用户和数据库。

```bash
# 切换到 postgres 用户
sudo -i -u postgres

# 进入数据库命令行
psql

# --- 以下在 SQL 终端执行 ---

# 1. 创建用户 (请将 'your_secure_password' 替换为您的强密码)
CREATE USER ai_user WITH PASSWORD 'your_secure_password';

# 2. 创建数据库
CREATE DATABASE ai_db OWNER ai_user;

# 3. 授予权限
GRANT ALL PRIVILEGES ON DATABASE ai_db TO ai_user;

# 4. 退出
\q

# --- SQL 结束 ---

# 退出 postgres 用户
exit
```

#### 8.3 环境准备 (Python & uv)

本项目使用 `uv` 进行极速依赖管理。

```bash
# 1. 安装基础依赖
sudo apt install -y git curl build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget llvm libncurses5-dev \
libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python3-openssl

# 2. 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. 使 uv 生效
source $HOME/.cargo/env
```

#### 8.4 克隆项目

```bash
# 切换到部署目录 (例如 /opt)
cd /opt

# 获取代码 (使用 SSH)
# 请确保您的服务器已配置 GitHub SSH Key，否则请使用 HTTPS 链接
sudo git clone git@github.com:natsume37/AI-aggregation-Platform.git

# 设置权限 (将 owner 改为当前登录用户，例如 ubuntu)
sudo chown -R $USER:$USER AI-aggregation-Platform

# 进入项目目录
cd AI-aggregation-Platform

# 安装依赖 (uv 会自动创建虚拟环境并同步依赖)
uv sync
```

#### 8.5 配置文件与数据库初始化 (Alembic)

```bash
# 1. 复制生产环境配置
cp .env.dev .env.prod

# 2. 修改配置
nano .env.prod
```

**修改 `.env.prod` 中的关键项**：

```dotenv
# 数据库连接 (使用 7.2 步设置的密码)
DATABASE_URL=postgresql+asyncpg://ai_user:your_secure_password@localhost:5432/ai_db

# 环境模式
ENVIRONMENT=production
DEBUG=false

# 端口
PORT=8089
```

**初始化数据库表结构**：
使用 Alembic 将数据表结构应用到数据库中。

```bash
# 运行迁移
uv run alembic upgrade head
```

_成功执行后，数据库中将生成所有必要的表。_

#### 8.6 运行测试

在配置后台服务前，先手动启动测试一下是否正常。

```bash
# 指定 .env.prod 启动
uv run uvicorn app.main:app --host 0.0.0.0 --port 8089 --env-file .env.prod
```

- 如果看到 `Uvicorn running on ...` 说明启动成功。
- 按 `Ctrl+C` 停止服务。

#### 8.7 配置 Systemd 守护进程

为了让服务在后台稳定运行并开机自启，我们需要配置 Systemd。

```bash
sudo nano /etc/systemd/system/ai-platform.service
```

写入以下内容 (请根据实际情况修改 `User` 和路径)：

```ini
[Unit]
Description=AI Aggregation Platform Service
After=network.target postgresql.service

[Service]
# 运行服务的用户 (建议使用当前非 root 用户，如 ubuntu)
User=ubuntu
Group=ubuntu

# 项目根目录
WorkingDirectory=/opt/AI-aggregation-Platform

# 启动命令
# 注意：需使用 uv 的绝对路径，通常在 /home/用户名/.cargo/bin/uv
# 可通过 `which uv` 查看
ExecStart=/home/ubuntu/.cargo/bin/uv run uvicorn app.main:app --host 0.0.0.0 --port 8089 --workers 4 --env-file .env.prod

# 重启策略
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## 注意文件的执行权限

```bash
chmod +x /root/work/AI-aggregation-Platform/gunicorn_start.sh
```

#### 8.8 启动服务

```bash
# 重载配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start ai-platform

# 设置开机自启
sudo systemctl enable ai-platform

# 查看运行状态
sudo systemctl status ai-platform
```

#### 8.9 配置 Nginx 反向代理 (可选)

```bash
sudo apt install -y nginx
sudo nano /etc/nginx/sites-available/ai-platform
```

配置示例：

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:8089;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/ai-platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```
