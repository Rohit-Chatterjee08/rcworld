"""
Logging system for the job automation framework.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class Logger:
    """
    Centralized logging system for the job automation framework.
    """

    def __init__(self, 
                 name: str = "job_automation",
                 level: str = "INFO",
                 log_format: Optional[str] = None,
                 file_path: Optional[str] = None,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5,
                 console_output: bool = True):
        """
        Initialize the logger.
        
        Args:
            name: Logger name
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_format: Log message format
            file_path: Path to log file
            max_file_size: Maximum file size before rotation
            backup_count: Number of backup files to keep
            console_output: Whether to output to console
        """
        self.name = name
        self.level = level
        self.file_path = file_path
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.console_output = console_output
        
        # Default log format
        self.log_format = log_format or (
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Set up handlers
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up log handlers."""
        formatter = logging.Formatter(self.log_format)
        
        # Console handler
        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler
        if self.file_path:
            # Create directory if it doesn't exist
            log_dir = Path(self.file_path).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Use rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                self.file_path,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        self._log(logging.DEBUG, message, extra)

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self._log(logging.INFO, message, extra)

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self._log(logging.WARNING, message, extra)

    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log error message."""
        self._log(logging.ERROR, message, extra)

    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log critical message."""
        self._log(logging.CRITICAL, message, extra)

    def exception(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log exception with traceback."""
        self.logger.exception(message, extra=extra)

    def _log(self, level: int, message: str, extra: Optional[Dict[str, Any]] = None):
        """Internal log method."""
        if extra:
            # Format extra data
            extra_str = " | ".join([f"{k}={v}" for k, v in extra.items()])
            message = f"{message} | {extra_str}"
        
        self.logger.log(level, message)

    def set_level(self, level: str):
        """
        Set log level.
        
        Args:
            level: New log level
        """
        self.level = level
        self.logger.setLevel(getattr(logging, level.upper()))

    def add_file_handler(self, file_path: str, level: Optional[str] = None):
        """
        Add additional file handler.
        
        Args:
            file_path: Path to log file
            level: Log level for this handler
        """
        # Create directory if it doesn't exist
        log_dir = Path(file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create handler
        handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count
        )
        
        # Set level
        if level:
            handler.setLevel(getattr(logging, level.upper()))
        
        # Set formatter
        formatter = logging.Formatter(self.log_format)
        handler.setFormatter(formatter)
        
        # Add to logger
        self.logger.addHandler(handler)

    def remove_console_handler(self):
        """Remove console handler."""
        handlers_to_remove = [
            h for h in self.logger.handlers 
            if isinstance(h, logging.StreamHandler) and h.stream == sys.stdout
        ]
        
        for handler in handlers_to_remove:
            self.logger.removeHandler(handler)

    def get_log_files(self) -> list:
        """
        Get list of log files.
        
        Returns:
            List of log file paths
        """
        if not self.file_path:
            return []
        
        log_dir = Path(self.file_path).parent
        log_name = Path(self.file_path).name
        
        # Find all log files (including rotated ones)
        log_files = []
        if Path(self.file_path).exists():
            log_files.append(str(self.file_path))
        
        # Find backup files
        for i in range(1, self.backup_count + 1):
            backup_path = log_dir / f"{log_name}.{i}"
            if backup_path.exists():
                log_files.append(str(backup_path))
        
        return log_files

    def clear_logs(self):
        """Clear all log files."""
        log_files = self.get_log_files()
        
        for log_file in log_files:
            try:
                os.remove(log_file)
            except Exception as e:
                self.error(f"Could not remove log file {log_file}: {e}")

    def get_recent_logs(self, num_lines: int = 100) -> list:
        """
        Get recent log entries.
        
        Args:
            num_lines: Number of recent lines to return
            
        Returns:
            List of recent log lines
        """
        if not self.file_path or not Path(self.file_path).exists():
            return []
        
        try:
            with open(self.file_path, 'r') as f:
                lines = f.readlines()
                return lines[-num_lines:]
        except Exception as e:
            self.error(f"Could not read log file: {e}")
            return []

    def create_child_logger(self, name: str) -> 'Logger':
        """
        Create a child logger.
        
        Args:
            name: Name for the child logger
            
        Returns:
            Child logger instance
        """
        child_name = f"{self.name}.{name}"
        
        return Logger(
            name=child_name,
            level=self.level,
            log_format=self.log_format,
            file_path=self.file_path,
            max_file_size=self.max_file_size,
            backup_count=self.backup_count,
            console_output=self.console_output
        )

    def log_job_event(self, job_id: str, event: str, message: str, extra: Optional[Dict[str, Any]] = None):
        """
        Log a job-related event.
        
        Args:
            job_id: Job ID
            event: Event type
            message: Log message
            extra: Additional context
        """
        log_extra = {'job_id': job_id, 'event': event}
        if extra:
            log_extra.update(extra)
        
        self.info(message, log_extra)

    def log_performance(self, operation: str, duration: float, extra: Optional[Dict[str, Any]] = None):
        """
        Log performance metrics.
        
        Args:
            operation: Operation name
            duration: Duration in seconds
            extra: Additional context
        """
        log_extra = {'operation': operation, 'duration': duration}
        if extra:
            log_extra.update(extra)
        
        self.info(f"Performance: {operation} took {duration:.3f}s", log_extra)

    def __str__(self) -> str:
        """String representation of logger."""
        return f"Logger(name={self.name}, level={self.level}, file={self.file_path})"


# Global logger instance
_global_logger: Optional[Logger] = None


def get_logger(name: str = "job_automation") -> Logger:
    """
    Get or create global logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    global _global_logger
    
    if _global_logger is None:
        _global_logger = Logger(name=name)
    
    return _global_logger


def configure_logging(config_dict: Dict[str, Any]):
    """
    Configure global logging from configuration dictionary.
    
    Args:
        config_dict: Configuration dictionary
    """
    global _global_logger
    
    _global_logger = Logger(
        name=config_dict.get('name', 'job_automation'),
        level=config_dict.get('level', 'INFO'),
        log_format=config_dict.get('format'),
        file_path=config_dict.get('file_path'),
        max_file_size=config_dict.get('max_file_size', 10 * 1024 * 1024),
        backup_count=config_dict.get('backup_count', 5),
        console_output=config_dict.get('console_output', True)
    )