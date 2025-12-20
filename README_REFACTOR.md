# AI Middleware 重构说明

本项目已重构为专属 AI 服务中间件，核心变更如下：

## 核心变更

1.  **认证机制**：

    - 移除了普通用户的注册功能。
    - 保留了管理员登录接口 (`/api/v1/auth/login`)，用于访问管理后台。
    - 对外服务完全基于 **API Key** 进行鉴权。

2.  **数据模型**：

    - `Conversation` (会话) 现在直接关联到 `APIKey`，而不是 `User`。这意味着不同的 API Key 拥有独立的会话历史。
    - `UsageLog` (使用日志) 同样关联到 `APIKey`。
    - `User` 表保留，仅用于存储管理员账号。

3.  **管理后台**：
    - 新增了 `/admin` 路由，提供可视化的 API Key 管理界面。
    - 管理员可以创建、删除、查看 API Keys。

## 升级步骤

由于数据库模型发生了重大变更（外键关系改变），请执行以下步骤：

### 1. 数据库迁移

如果你正在使用 Alembic，请生成新的迁移脚本：

```bash
alembic revision --autogenerate -m "refactor_to_api_key_based"
alembic upgrade head
```

如果是新环境或开发环境，可以直接重置数据库。

### 2. 创建管理员账号

由于移除了注册接口，你需要通过脚本或直接操作数据库来创建第一个管理员账号。

可以使用以下 Python 脚本创建管理员：

```python
# create_admin.py
import asyncio
from app.core.database import async_session_maker
from app.crud.user import user_crud
from app.schemas.user import UserCreate

async def create_admin():
    async with async_session_maker() as db:
        user_in = UserCreate(
            username="admin",
            email="admin@example.com",
            password="your_secure_password",
            is_superuser=True,
            is_active=True
        )
        user = await user_crud.create(db, user_in)
        print(f"Admin created: {user.username}")
        await db.commit()

if __name__ == "__main__":
    asyncio.run(create_admin())
```

### 3. 访问管理后台

启动服务后，访问 `http://localhost:8089/admin` (端口取决于你的配置)。
使用管理员账号登录，即可管理 API Keys。

## API 使用

对外服务现在通过 Header `X-API-Key` 进行认证：

````http
POST /api/v1/chat/completions
X-API-Key: your_generated_api_key
Content-Type: application/json

{
  "model": "gpt-3.5-turbo",
  "messages": [{"role": "user", "content": "Hello"}]
}
## 多模态（图片理解）

`messages[].content` 支持：

- 纯文本：`"content": "..."`
- 多模态列表（OpenAI 兼容）：`"content": [{"type":"text"...}, {"type":"image_url"...}]`

### 豆包（火山 Ark）调用示例

```bash
curl -X POST "http://localhost:8089/api/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: YOUR_API_KEY" \
    -d '{
        "provider": "doubao",
        "model": "doubao-1-5-vision-pro-32k-250115",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "请描述图片内容"},
                    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,<BASE64>"}}
                ]
            }
        ]
    }'
````

### 常见问题

- `401 Invalid or expired API key`：平台 `X-API-Key` 不存在/过期；请在管理后台创建或使用 `create_test_key.py` 生成。
- `ModelNotOpen`：火山 Ark 控制台未开通/启用对应模型（或未绑定正确 Endpoint）；需要先在控制台启用。

## 开发辅助脚本

- 生成测试 Key：`uv run python .\\create_test_key.py`
- 校验 Key 是否存在：`uv run python .\\check_key.py`
- 图片理解测试：`uv run .\\test\\test_doubao_vision.py`

```

```
