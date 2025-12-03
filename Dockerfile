# 使用官方 Python 基础镜像
FROM python:3.13-slim-bookworm

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 设置工作目录
WORKDIR /app

# 设置环境变量
# 确保 uv 创建的虚拟环境在 PATH 中
ENV PATH="/app/.venv/bin:$PATH"
# 编译字节码，加快启动速度
ENV UV_COMPILE_BYTECODE=1
# 确保 uv 使用复制策略而不是硬链接
ENV UV_LINK_MODE=copy

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 安装依赖
# --frozen: 使用 lock 文件中的确切版本
# --no-install-project: 只安装依赖
RUN uv sync --frozen --no-install-project

# 复制项目代码
COPY . .

# 再次运行 sync 以确保环境完整
RUN uv sync --frozen

# 创建日志目录
RUN mkdir -p logs

# 暴露端口
EXPOSE 8089

# 启动命令
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8089"]
