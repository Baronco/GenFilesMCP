import logging

DEFAULT_LOGGER_NAME = "genfilesmcp"
DEFAULT_LOG_LEVEL = logging.INFO

def configure_logging() -> None:
    """Configure the logging system with the default logger name and log level."""
    logging.basicConfig(level=DEFAULT_LOG_LEVEL, force=True)


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger instance with the specified name or the default logger name."""
    return logging.getLogger(name or DEFAULT_LOGGER_NAME)
