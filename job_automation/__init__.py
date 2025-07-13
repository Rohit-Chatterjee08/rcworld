"""
Job Automation System

A comprehensive system for managing and executing automated jobs and tasks.
"""

__version__ = "0.1.0"
__author__ = "Job Automation Team"

from .core.scheduler import JobScheduler
from .core.executor import TaskExecutor
from .core.job_queue import JobQueue
from .core.config import Config

__all__ = [
    "JobScheduler",
    "TaskExecutor", 
    "JobQueue",
    "Config"
]