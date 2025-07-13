"""
Job model and related functionality.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


class JobStatus(Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


class JobPriority(Enum):
    """Job priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Job:
    """
    Represents a job in the automation system.
    """
    name: str
    command: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Post-initialization validation."""
        if self.scheduled_at is None:
            self.scheduled_at = self.created_at

    def is_ready_to_run(self) -> bool:
        """Check if job is ready to be executed."""
        return (
            self.status == JobStatus.PENDING and
            self.scheduled_at <= datetime.now()
        )

    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return (
            self.status == JobStatus.FAILED and
            self.retry_count < self.max_retries
        )

    def mark_started(self):
        """Mark job as started."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now()

    def mark_completed(self, result: Optional[Dict[str, Any]] = None):
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result

    def mark_failed(self, error_message: str):
        """Mark job as failed."""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error_message

    def mark_cancelled(self):
        """Mark job as cancelled."""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.now()

    def increment_retry(self):
        """Increment retry count and reset status for retry."""
        self.retry_count += 1
        self.status = JobStatus.RETRY
        self.started_at = None
        self.completed_at = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'command': self.command,
            'parameters': self.parameters,
            'status': self.status.value,
            'priority': self.priority.value,
            'created_at': self.created_at.isoformat(),
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'timeout': self.timeout,
            'tags': self.tags,
            'metadata': self.metadata,
            'error_message': self.error_message,
            'result': self.result
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create job from dictionary representation."""
        job_data = data.copy()
        
        # Convert status and priority back to enums
        job_data['status'] = JobStatus(job_data['status'])
        job_data['priority'] = JobPriority(job_data['priority'])
        
        # Convert datetime strings back to datetime objects
        for date_field in ['created_at', 'scheduled_at', 'started_at', 'completed_at']:
            if job_data.get(date_field):
                job_data[date_field] = datetime.fromisoformat(job_data[date_field])
        
        return cls(**job_data)