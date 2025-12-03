from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    """应用配置类"""

    # 连接超时设置
    CONNECT_TIMEOUT: int = Field(default=120, description='AI连接超时时间，单位秒')

    # 系统提示词设置
    SYSTEM_PROMPT: str = Field(
        default='You are an AI assistant of the AI aggregation platform developed by Martin. Your name is Xiaomei',
        description='默认系统提示词',
    )
    # AI_API_KEY 配置
    # OpenAI配置
    OPENAI_API_KEY: str = Field(default='', description='OpenAI API密钥')
    OPENAI_BASE_URL: str | None = Field(default=None, description='OpenAI API基础URL')
    # 硅基流动配置
    SILICONFLOW_API_KEY: str = Field(default='', description='硅基流动API密钥')
    SILICONFLOW_BASE_URL: str | None = Field(default=None, description='硅基流动 API基础URL')
    # deepseek配置
    DEEPSEEK_API_KEY: str = Field(default='', description='deepseek API密钥')
    DEEPSEEK_BASE_URL: str | None = Field(default=None, description='deepseek API基础URL')
    # 阿里云配置
    ALIYUNCS_API_KEY: str = Field(default='', description='阿里云API密钥')
    ALIYUNCS_BASE_URL: str | None = Field(default=None, description='阿里云 API基础URL')

    # 应用基础配置
    APP_NAME: str = Field(default='FastAPI AI Backend', description='应用名称')
    APP_VERSION: str = Field(default='1.0.0', description='应用版本')
    ENVIRONMENT: Literal['development', 'staging', 'production'] = Field(default='development', description='运行环境')
    DEBUG: bool = Field(default=False, description='调试模式')

    # 服务器配置
    HOST: str = Field(default='0.0.0.0', description='服务器主机')
    PORT: int = Field(default=8089, description='服务器端口')

    # 数据库配置
    DATABASE_URL: PostgresDsn = Field(description='数据库连接URL')
    DATABASE_POOL_SIZE: int = Field(default=20, description='数据库连接池大小')
    DATABASE_MAX_OVERFLOW: int = Field(default=10, description='数据库最大溢出连接')

    # 日志配置
    LOG_LEVEL: str = Field(default='INFO', description='日志级别')
    LOG_FILE_PATH: str = Field(default='./logs', description='日志文件路径')

    # 安全配置
    SECRET_KEY: str = Field(description='JWT密钥')
    ALGORITHM: str = Field(default='HS256', description='JWT算法')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description='访问令牌过期时间(分钟)')

    # Pydantic配置
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', case_sensitive=True, extra='ignore')

    @field_validator('DATABASE_URL', mode='before')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """验证数据库URL"""
        if not v:
            raise ValueError('DATABASE_URL must be set')
        return v

    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.ENVIRONMENT == 'development'

    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.ENVIRONMENT == 'production'

    @property
    def database_url_sync(self) -> str:
        """同步数据库URL (用于Alembic)"""
        return str(self.DATABASE_URL).replace('+asyncpg', '')


# 根据环境加载不同配置文件
def get_settings() -> Settings:
    import os
    import pathlib

    # 项目根目录（假设 settings.py 在 app/core/）
    BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent  # 项目根 AI

    env = os.getenv('ENVIRONMENT', 'development')
    # print(f'[DEBUG] 系统环境变量 ENVIRONMENT = {env}')

    # 使用绝对路径
    env_file_map = {
        'development': BASE_DIR / '.env.dev',
        'staging': BASE_DIR / '.env.staging',
        'production': BASE_DIR / '.env.prod',
    }
    env_file = env_file_map.get(env, BASE_DIR / '.env')
    # print(f'[DEBUG] 即将加载配置文件: {env_file}')

    # 强制打印文件是否存在
    print(f'[DEBUG] 文件是否存在？: {env_file.exists()} -> {env_file.resolve()}')

    settings = Settings(_env_file=env_file)

    # print(f'[DEBUG] 成功加载 OPENAI_API_KEY: {settings.OPENAI_API_KEY[:10]}...')
    # print(f'[DEBUG] 成功加载 OPENAI_BASE_URL: {settings.OPENAI_BASE_URL}')

    return settings


# 全局配置实例
settings = get_settings()
