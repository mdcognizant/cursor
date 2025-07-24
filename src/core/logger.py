"""
Logging configuration for Development Automation Suite
Provides comprehensive logging with both file and console output.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(log_level: str = "INFO", log_dir: Path = None):
    """
    Setup comprehensive logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: ~/.dev_automation/logs)
    """
    # Create logs directory
    if log_dir is None:
        log_dir = Path.home() / ".dev_automation" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(levelname)s: %(message)s'
    )
    
    # Console handler (simplified output)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs (detailed)
    log_file = log_dir / f"dev_automation_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler (errors only)
    error_file = log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")
    logger.debug(f"Log files location: {log_dir}")

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)

class TaskLogger:
    """Context manager for task-specific logging."""
    
    def __init__(self, task_name: str, logger: logging.Logger = None):
        self.task_name = task_name
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting task: {self.task_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = datetime.now() - self.start_time
        if exc_type is None:
            self.logger.info(f"Task completed: {self.task_name} (Duration: {duration.total_seconds():.2f}s)")
        else:
            self.logger.error(f"Task failed: {self.task_name} (Duration: {duration.total_seconds():.2f}s) - {exc_val}")
        return False  # Don't suppress exceptions
    
    def info(self, message: str):
        """Log info message with task context."""
        self.logger.info(f"[{self.task_name}] {message}")
    
    def error(self, message: str):
        """Log error message with task context."""
        self.logger.error(f"[{self.task_name}] {message}")
    
    def warning(self, message: str):
        """Log warning message with task context."""
        self.logger.warning(f"[{self.task_name}] {message}")
    
    def debug(self, message: str):
        """Log debug message with task context."""
        self.logger.debug(f"[{self.task_name}] {message}") 