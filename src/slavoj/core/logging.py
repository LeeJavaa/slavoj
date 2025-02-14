import json
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record):
        log_record = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if hasattr(record, "props"):
            log_record.update(record.props)

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


class LoggerFactory:
    """Factory class for creating and configuring loggers."""

    @staticmethod
    def create_logger(
        name: str,
        level: str = "INFO",
        log_file: Optional[str] = None,
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5,
        json_format: bool = True,
    ) -> logging.Logger:
        """
        Create a configured logger instance.

        Args:
            name: Logger name
            level: Logging level
            log_file: Optional file path for logging
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
            json_format: Whether to use JSON formatting
        """
        logger = logging.getLogger(name)

        # Prevent adding handlers multiple times
        if logger.handlers:
            return logger

        logger.setLevel(getattr(logging, level.upper()))

        # Create formatters
        if json_format:
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler (if log_file specified)
        if log_file:
            file_handler = RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    @staticmethod
    def with_context(**context):
        """
        Context manager for adding temporary context to logs.

        Usage:
            with LoggerFactory.with_context(user_id='123'):
                logger.info('User action')  # Will include user_id in log
        """

        class LogContextManager:
            def __init__(self, context_data):
                self.context_data = context_data
                self.old_factory = logging.getLogRecordFactory()

            def __enter__(self):
                def record_factory(*args, **kwargs):
                    record = self.old_factory(*args, **kwargs)
                    record.props = self.context_data
                    return record

                logging.setLogRecordFactory(record_factory)
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                logging.setLogRecordFactory(self.old_factory)

        return LogContextManager(context)
