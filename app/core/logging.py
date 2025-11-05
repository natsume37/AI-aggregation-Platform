# -*- coding: utf-8 -*-
"""
@File    : logging.py.py
@Author  : Martin
@Time    : 2025/11/1 22:47
@Desc    :
"""

import sys
from pathlib import Path
from loguru import logger
from app.core.config import settings


def setup_logging():
    """配置日志系统"""

    # 移除默认处理器
    logger.remove()

    # 控制台输出格式
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # 文件输出格式
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )

    # 添加控制台处理器
    logger.add(
        sys.stdout,
        format=console_format,
        level=settings.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # 创建日志目录
    log_path = Path(settings.LOG_FILE_PATH)
    log_path.mkdir(parents=True, exist_ok=True)

    # 添加文件处理器 - INFO及以上
    logger.add(
        log_path / "app_{time:YYYY-MM-DD}.log",
        format=file_format,
        level="INFO",
        rotation="00:00",  # 每天轮转
        retention="30 days",  # 保留30天
        compression="zip",  # 压缩
        encoding="utf-8",
    )

    # 添加错误日志文件处理器
    logger.add(
        log_path / "error_{time:YYYY-MM-DD}.log",
        format=file_format,
        level="ERROR",
        rotation="00:00",
        retention="90 days",  # 错误日志保留更久
        compression="zip",
        encoding="utf-8",
    )

    logger.info(
        f"Logging initialized - Level: {settings.LOG_LEVEL}, Environment: {settings.ENVIRONMENT}"
    )

    return logger


# 初始化日志
log = setup_logging()
