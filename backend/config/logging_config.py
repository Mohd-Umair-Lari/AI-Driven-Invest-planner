"""
config/logging_config.py
------------------------
Structured JSON logging using loguru.
In dev: human-readable colored output.
In prod: JSON lines (compatible with any log aggregator — Datadog, Loki, etc.)
"""
import sys
from loguru import logger
from config.settings import get_settings


def setup_logging():
    settings = get_settings()
    logger.remove()

    if settings.ENV == "development":
        fmt = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>"
        )
        logger.add(sys.stderr, format=fmt, level=settings.LOG_LEVEL, colorize=True)
    else:
        # JSON lines for production log aggregators
        logger.add(
            sys.stderr,
            format="{time} {level} {name} {message}",
            level=settings.LOG_LEVEL,
            serialize=True,   # outputs JSON
        )

    return logger
