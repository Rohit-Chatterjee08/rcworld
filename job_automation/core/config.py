"""
Configuration management for the job automation system.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    """Database configuration."""
    type: str = "sqlite"
    host: str = "localhost"
    port: int = 5432
    database: str = "jobs.db"
    username: str = ""
    password: str = ""
    connection_pool_size: int = 10


@dataclass
class ExecutorConfig:
    """Executor configuration."""
    max_workers: int = 4
    job_timeout: int = 3600
    retry_delay: int = 300
    max_retries: int = 3


@dataclass
class SchedulerConfig:
    """Scheduler configuration."""
    enabled: bool = True
    check_interval: int = 1
    timezone: str = "UTC"


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class SecurityConfig:
    """Security configuration."""
    api_key: Optional[str] = None
    jwt_secret: Optional[str] = None
    jwt_expiration: int = 3600
    rate_limit: int = 100
    allowed_hosts: list = field(default_factory=lambda: ["localhost", "127.0.0.1"])


@dataclass
class APIConfig:
    """API configuration."""
    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = 8080
    cors_enabled: bool = True
    debug: bool = False


class Config:
    """
    Central configuration management for the job automation system.
    """

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file or os.getenv("JOB_CONFIG_FILE", "config.yaml")
        self._config_data: Dict[str, Any] = {}
        
        # Initialize with default configurations
        self.database = DatabaseConfig()
        self.executor = ExecutorConfig()
        self.scheduler = SchedulerConfig()
        self.logging = LoggingConfig()
        self.security = SecurityConfig()
        self.api = APIConfig()
        
        # Load configuration
        self.load_config()

    def load_config(self):
        """Load configuration from file and environment variables."""
        # Load from file first
        if os.path.exists(self.config_file):
            self._load_from_file()
        
        # Override with environment variables
        self._load_from_env()
        
        # Apply configuration to dataclasses
        self._apply_config()

    def _load_from_file(self):
        """Load configuration from file."""
        try:
            with open(self.config_file, 'r') as f:
                if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                    self._config_data = yaml.safe_load(f) or {}
                elif self.config_file.endswith('.json'):
                    self._config_data = json.load(f)
                else:
                    raise ValueError(f"Unsupported config file format: {self.config_file}")
        except Exception as e:
            print(f"Warning: Could not load config file {self.config_file}: {e}")

    def _load_from_env(self):
        """Load configuration from environment variables."""
        env_mappings = {
            # Database
            'JOB_DB_TYPE': ('database', 'type'),
            'JOB_DB_HOST': ('database', 'host'),
            'JOB_DB_PORT': ('database', 'port'),
            'JOB_DB_DATABASE': ('database', 'database'),
            'JOB_DB_USERNAME': ('database', 'username'),
            'JOB_DB_PASSWORD': ('database', 'password'),
            'JOB_DB_POOL_SIZE': ('database', 'connection_pool_size'),
            
            # Executor
            'JOB_EXECUTOR_MAX_WORKERS': ('executor', 'max_workers'),
            'JOB_EXECUTOR_TIMEOUT': ('executor', 'job_timeout'),
            'JOB_EXECUTOR_RETRY_DELAY': ('executor', 'retry_delay'),
            'JOB_EXECUTOR_MAX_RETRIES': ('executor', 'max_retries'),
            
            # Scheduler
            'JOB_SCHEDULER_ENABLED': ('scheduler', 'enabled'),
            'JOB_SCHEDULER_INTERVAL': ('scheduler', 'check_interval'),
            'JOB_SCHEDULER_TIMEZONE': ('scheduler', 'timezone'),
            
            # Logging
            'JOB_LOG_LEVEL': ('logging', 'level'),
            'JOB_LOG_FORMAT': ('logging', 'format'),
            'JOB_LOG_FILE': ('logging', 'file_path'),
            'JOB_LOG_MAX_SIZE': ('logging', 'max_file_size'),
            'JOB_LOG_BACKUP_COUNT': ('logging', 'backup_count'),
            
            # Security
            'JOB_API_KEY': ('security', 'api_key'),
            'JOB_JWT_SECRET': ('security', 'jwt_secret'),
            'JOB_JWT_EXPIRATION': ('security', 'jwt_expiration'),
            'JOB_RATE_LIMIT': ('security', 'rate_limit'),
            
            # API
            'JOB_API_ENABLED': ('api', 'enabled'),
            'JOB_API_HOST': ('api', 'host'),
            'JOB_API_PORT': ('api', 'port'),
            'JOB_API_CORS': ('api', 'cors_enabled'),
            'JOB_API_DEBUG': ('api', 'debug'),
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Ensure section exists
                if section not in self._config_data:
                    self._config_data[section] = {}
                
                # Convert value to appropriate type
                if key in ['port', 'connection_pool_size', 'max_workers', 'job_timeout', 
                          'retry_delay', 'max_retries', 'check_interval', 'jwt_expiration',
                          'rate_limit', 'max_file_size', 'backup_count']:
                    value = int(value)
                elif key in ['enabled', 'cors_enabled', 'debug']:
                    value = value.lower() in ('true', '1', 'yes', 'on')
                
                self._config_data[section][key] = value

    def _apply_config(self):
        """Apply configuration data to dataclass instances."""
        if 'database' in self._config_data:
            self.database = DatabaseConfig(**self._config_data['database'])
        
        if 'executor' in self._config_data:
            self.executor = ExecutorConfig(**self._config_data['executor'])
        
        if 'scheduler' in self._config_data:
            self.scheduler = SchedulerConfig(**self._config_data['scheduler'])
        
        if 'logging' in self._config_data:
            self.logging = LoggingConfig(**self._config_data['logging'])
        
        if 'security' in self._config_data:
            self.security = SecurityConfig(**self._config_data['security'])
        
        if 'api' in self._config_data:
            self.api = APIConfig(**self._config_data['api'])

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key in dot notation (e.g., 'database.host')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value

    def set(self, key: str, value: Any):
        """
        Set a configuration value by key.
        
        Args:
            key: Configuration key in dot notation (e.g., 'database.host')
            value: Value to set
        """
        keys = key.split('.')
        config = self._config_data
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        
        # Reapply configuration
        self._apply_config()

    def save_config(self, file_path: Optional[str] = None):
        """
        Save configuration to file.
        
        Args:
            file_path: Path to save configuration to
        """
        file_path = file_path or self.config_file
        
        try:
            with open(file_path, 'w') as f:
                if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                    yaml.dump(self._config_data, f, default_flow_style=False)
                elif file_path.endswith('.json'):
                    json.dump(self._config_data, f, indent=2)
                else:
                    raise ValueError(f"Unsupported config file format: {file_path}")
        except Exception as e:
            raise Exception(f"Could not save config to {file_path}: {e}")

    def create_default_config(self, file_path: Optional[str] = None) -> str:
        """
        Create a default configuration file.
        
        Args:
            file_path: Path to create configuration file at
            
        Returns:
            Path to created configuration file
        """
        file_path = file_path or "config.yaml"
        
        default_config = {
            'database': {
                'type': 'sqlite',
                'database': 'jobs.db',
                'connection_pool_size': 10
            },
            'executor': {
                'max_workers': 4,
                'job_timeout': 3600,
                'retry_delay': 300,
                'max_retries': 3
            },
            'scheduler': {
                'enabled': True,
                'check_interval': 1,
                'timezone': 'UTC'
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file_path': 'logs/app.log',
                'max_file_size': 10485760,  # 10MB
                'backup_count': 5
            },
            'security': {
                'rate_limit': 100,
                'allowed_hosts': ['localhost', '127.0.0.1']
            },
            'api': {
                'enabled': True,
                'host': '0.0.0.0',
                'port': 8080,
                'cors_enabled': True,
                'debug': False
            }
        }
        
        with open(file_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        
        return file_path

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self._config_data.copy()

    def __str__(self) -> str:
        """String representation of configuration."""
        return yaml.dump(self._config_data, default_flow_style=False)