# -*- coding: utf-8 -*-
"""
@File    : logger.py
@Author  : Martin
@Desc    : 通用项目日志配置
"""
import os
from logging import config as logging_config

# 计算项目根目录（AI 目录）
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir, os.pardir))

# 确保 logs 目录存在
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,

    # 格式化器
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },

    # 处理器
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
        },
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": os.path.join(LOG_DIR, "app.log"),
            "when": "midnight",
            "interval": 1,
            "backupCount": 7,
            "encoding": "utf-8",
        },
        "error_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "ERROR",
            "formatter": "standard",
            "filename": os.path.join(LOG_DIR, "error.log"),
            "when": "midnight",
            "interval": 1,
            "backupCount": 14,
            "encoding": "utf-8",
        },
    },

    # 日志器
    "loggers": {
        "app": {
            "handlers": ["console", "file", "error_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "": {
            "handlers": ["console", "file"],
            "level": "INFO",
        },
    },
}


def setup_logging():
    """初始化日志配置"""
    logging_config.dictConfig(LOGGING_CONFIG)
    import logging
    logger = logging.getLogger("app")
    logger.info(f"✅ 日志初始化完成，日志目录：{LOG_DIR}")
    return logger
