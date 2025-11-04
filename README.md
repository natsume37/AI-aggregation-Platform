# AI Aggregation Platform

这是一个AI聚合平台、简单配置无缝切换各AI的管理平台、使用fastAPI+PostgreSQL来管理。
主要有以下特色：

- 多模型接入
- 多用户支持
- 用户鉴权
- 模型统一的访问接口
- token计费
- 简单的模型配置
- 高拓展性

### 如何使用?

### 配置文件
配置.env文件
- 数据库url
- AI的basic—url 和 key
### 3. 初始化数据库
```bash
# 创建迁移
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

### 4. 运行应用
```bash
# 开发模式
python -m app.main

# 或使用uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问API文档

打开浏览器访问：http://localhost:8000/docs






