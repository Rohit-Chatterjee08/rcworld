"""
Helper utility functions for job automation.
"""

import uuid
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from croniter import croniter

from ..core.job import Job, JobStatus, JobPriority


def generate_job_id() -> str:
    """
    Generate a unique job ID.
    
    Returns:
        Unique job ID string
    """
    return str(uuid.uuid4())


def validate_cron_expression(cron_expr: str) -> bool:
    """
    Validate a cron expression.
    
    Args:
        cron_expr: Cron expression to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        croniter(cron_expr)
        return True
    except (ValueError, TypeError):
        return False


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:
        days = seconds / 86400
        return f"{days:.1f}d"


def parse_duration(duration_str: str) -> int:
    """
    Parse duration string to seconds.
    
    Args:
        duration_str: Duration string (e.g., "1h", "30m", "120s")
        
    Returns:
        Duration in seconds
    """
    pattern = r'^(\d+)([smhd])$'
    match = re.match(pattern, duration_str.lower())
    
    if not match:
        raise ValueError(f"Invalid duration format: {duration_str}")
    
    value, unit = match.groups()
    value = int(value)
    
    multipliers = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400
    }
    
    return value * multipliers[unit]


def calculate_next_run(cron_expr: str, base_time: Optional[datetime] = None) -> datetime:
    """
    Calculate next run time for a cron expression.
    
    Args:
        cron_expr: Cron expression
        base_time: Base time to calculate from (defaults to now)
        
    Returns:
        Next run time
    """
    base_time = base_time or datetime.now()
    cron = croniter(cron_expr, base_time)
    return cron.get_next(datetime)


def create_job_from_dict(job_data: Dict[str, Any]) -> Job:
    """
    Create a Job object from dictionary data.
    
    Args:
        job_data: Job data dictionary
        
    Returns:
        Job object
    """
    return Job.from_dict(job_data)


def job_to_dict(job: Job) -> Dict[str, Any]:
    """
    Convert Job object to dictionary.
    
    Args:
        job: Job object
        
    Returns:
        Job data dictionary
    """
    return job.to_dict()


def filter_jobs_by_status(jobs: list, status: JobStatus) -> list:
    """
    Filter jobs by status.
    
    Args:
        jobs: List of Job objects
        status: Status to filter by
        
    Returns:
        Filtered list of jobs
    """
    return [job for job in jobs if job.status == status]


def filter_jobs_by_priority(jobs: list, priority: JobPriority) -> list:
    """
    Filter jobs by priority.
    
    Args:
        jobs: List of Job objects
        priority: Priority to filter by
        
    Returns:
        Filtered list of jobs
    """
    return [job for job in jobs if job.priority == priority]


def filter_jobs_by_tag(jobs: list, tag: str) -> list:
    """
    Filter jobs by tag.
    
    Args:
        jobs: List of Job objects
        tag: Tag to filter by
        
    Returns:
        Filtered list of jobs
    """
    return [job for job in jobs if tag in job.tags]


def get_job_age(job: Job) -> timedelta:
    """
    Get the age of a job.
    
    Args:
        job: Job object
        
    Returns:
        Age of the job as timedelta
    """
    return datetime.now() - job.created_at


def is_job_expired(job: Job, max_age_hours: int = 24) -> bool:
    """
    Check if a job is expired based on age.
    
    Args:
        job: Job object
        max_age_hours: Maximum age in hours
        
    Returns:
        True if expired, False otherwise
    """
    age = get_job_age(job)
    return age > timedelta(hours=max_age_hours)


def format_job_summary(job: Job) -> str:
    """
    Format a job summary string.
    
    Args:
        job: Job object
        
    Returns:
        Formatted job summary
    """
    status_icon = {
        JobStatus.PENDING: "⏳",
        JobStatus.RUNNING: "🔄",
        JobStatus.COMPLETED: "✅",
        JobStatus.FAILED: "❌",
        JobStatus.CANCELLED: "🚫",
        JobStatus.RETRY: "🔄"
    }
    
    priority_icon = {
        JobPriority.LOW: "🔵",
        JobPriority.NORMAL: "🟢",
        JobPriority.HIGH: "🟡",
        JobPriority.URGENT: "🔴"
    }
    
    age = get_job_age(job)
    
    return (f"{status_icon.get(job.status, '?')} {priority_icon.get(job.priority, '?')} "
            f"{job.name} ({job.id[:8]}) - {job.status.value} - "
            f"Age: {format_duration(age.total_seconds())}")


def validate_job_data(job_data: Dict[str, Any]) -> bool:
    """
    Validate job data dictionary.
    
    Args:
        job_data: Job data to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['name', 'command']
    
    for field in required_fields:
        if field not in job_data:
            return False
    
    # Validate types
    if not isinstance(job_data['name'], str):
        return False
    
    if not isinstance(job_data['command'], str):
        return False
    
    # Validate optional fields
    if 'priority' in job_data:
        try:
            JobPriority(job_data['priority'])
        except ValueError:
            return False
    
    if 'status' in job_data:
        try:
            JobStatus(job_data['status'])
        except ValueError:
            return False
    
    return True


def merge_job_metadata(job: Job, additional_metadata: Dict[str, Any]) -> Job:
    """
    Merge additional metadata into a job.
    
    Args:
        job: Job object
        additional_metadata: Additional metadata to merge
        
    Returns:
        Job with merged metadata
    """
    job.metadata.update(additional_metadata)
    return job


def get_jobs_statistics(jobs: list) -> Dict[str, Any]:
    """
    Get statistics for a list of jobs.
    
    Args:
        jobs: List of Job objects
        
    Returns:
        Statistics dictionary
    """
    if not jobs:
        return {}
    
    status_counts = {}
    priority_counts = {}
    
    for job in jobs:
        status_counts[job.status.value] = status_counts.get(job.status.value, 0) + 1
        priority_counts[job.priority.value] = priority_counts.get(job.priority.value, 0) + 1
    
    total_jobs = len(jobs)
    completed_jobs = [job for job in jobs if job.status == JobStatus.COMPLETED]
    failed_jobs = [job for job in jobs if job.status == JobStatus.FAILED]
    
    # Calculate success rate
    processed_jobs = len(completed_jobs) + len(failed_jobs)
    success_rate = (len(completed_jobs) / processed_jobs) * 100 if processed_jobs > 0 else 0
    
    return {
        'total_jobs': total_jobs,
        'status_breakdown': status_counts,
        'priority_breakdown': priority_counts,
        'success_rate': success_rate,
        'completed_jobs': len(completed_jobs),
        'failed_jobs': len(failed_jobs)
    }