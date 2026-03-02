import sys

from loguru import logger

from app.core.config import get_settings

settings = get_settings()


def setup_logging() -> None:
    logger.remove()
    log_level = "DEBUG" if settings.app_debug else "INFO"
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    logger.add(sys.stdout, level=log_level, format=log_format, colorize=True)
    logger.add(
        "logs/app.log",
        level="INFO",
        format=log_format,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )
