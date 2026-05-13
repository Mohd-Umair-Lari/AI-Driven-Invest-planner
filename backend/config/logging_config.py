"""
config/logging_config.py
------------------------
Structured logging. Uses loguru when installed, falls back to stdlib logging.
"""
import sys
import logging as _stdlib_logging
from config.settings import get_settings


try:
    from loguru import logger as _loguru_logger
    _HAS_LOGURU = True
except ImportError:
    _HAS_LOGURU = False


def setup_logging():
    settings = get_settings()

    if _HAS_LOGURU:
        _loguru_logger.remove()
        if settings.ENV == "development":
            fmt = (
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>"
            )
            _loguru_logger.add(sys.stderr, format=fmt, level=settings.LOG_LEVEL, colorize=True)
        else:
            _loguru_logger.add(
                sys.stderr,
                format="{time} {level} {name} {message}",
                level=settings.LOG_LEVEL,
                serialize=True,
            )
        return _loguru_logger

    # Fallback: stdlib logging
    _stdlib_logging.basicConfig(
        stream=sys.stderr,
        level=getattr(_stdlib_logging, settings.LOG_LEVEL, _stdlib_logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return _stdlib_logging.getLogger("finpass")
