"""
Main job automation system orchestrator.
"""

import threading
import time
import atexit
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from .core.config import Config
from .core.logger import Logger, configure_logging
from .core.job import Job, JobStatus, JobPriority
from .core.job_queue import JobQueue
from .core.scheduler import JobScheduler
from .core.executor import TaskExecutor
from .core.storage import JobStorage, SQLiteStorageBackend, FileStorageBackend


class JobAutomationSystem:
    """
    Main orchestrator for the job automation system.
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the job automation system.
        
        Args:
            config: Configuration instance
        """
        self.config = config or Config()
        
        # Configure logging
        configure_logging({
            'name': 'job_automation',
            'level': self.config.logging.level,
            'format': self.config.logging.format,
            'file_path': self.config.logging.file_path,
            'max_file_size': self.config.logging.max_file_size,
            'backup_count': self.config.logging.backup_count
        })
        
        self.logger = Logger()
        
        # Initialize storage
        self.storage = self._create_storage()
        
        # Initialize core components
        self.job_queue = JobQueue(logger=self.logger)
        self.scheduler = JobScheduler(self.job_queue, logger=self.logger)
        self.executor = TaskExecutor(
            job_queue=self.job_queue,
            max_workers=self.config.executor.max_workers,
            storage=self.storage,
            logger=self.logger
        )
        
        # System state
        self.is_running = False
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Statistics
        self._stats = {
            'system_start_time': datetime.now(),
            'jobs_processed': 0,
            'jobs_failed': 0,
            'system_uptime': 0
        }
        
        # Register cleanup handler
        atexit.register(self.shutdown)
        
        self.logger.info("Job automation system initialized")

    def start(self):
        """Start the job automation system."""
        if self.is_running:
            self.logger.warning("Job automation system is already running")
            return

        self.logger.info("Starting job automation system")
        
        # Start core components
        self.executor.start()
        
        if self.config.scheduler.enabled:
            self.scheduler.start()
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        
        self.is_running = True
        self.logger.info("Job automation system started successfully")

    def shutdown(self, timeout: int = 30):
        """
        Shutdown the job automation system.
        
        Args:
            timeout: Maximum time to wait for shutdown
        """
        if not self.is_running:
            return

        self.logger.info("Shutting down job automation system")
        
        # Stop core components
        self.is_running = False
        self._stop_event.set()
        
        if self.scheduler:
            self.scheduler.stop()
        
        if self.executor:
            self.executor.stop(timeout=timeout)
        
        # Wait for cleanup thread
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        
        self.logger.info("Job automation system shutdown complete")

    def submit_job(self, job: Job) -> str:
        """
        Submit a job for execution.
        
        Args:
            job: Job to submit
            
        Returns:
            Job ID
        """
        # Save job to storage
        self.storage.save_job(job)
        
        # Add to queue
        self.job_queue.add_job(job)
        
        self.logger.info(f"Job '{job.name}' submitted with ID: {job.id}")
        return job.id

    def create_job(self, 
                   name: str, 
                   command: str, 
                   parameters: Optional[Dict[str, Any]] = None,
                   priority: JobPriority = JobPriority.NORMAL,
                   timeout: Optional[int] = None,
                   max_retries: int = 3,
                   tags: Optional[List[str]] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> Job:
        """
        Create a new job.
        
        Args:
            name: Job name
            command: Command to execute
            parameters: Job parameters
            priority: Job priority
            timeout: Job timeout in seconds
            max_retries: Maximum retry attempts
            tags: Job tags
            metadata: Job metadata
            
        Returns:
            Created job
        """
        job = Job(
            name=name,
            command=command,
            parameters=parameters or {},
            priority=priority,
            timeout=timeout,
            max_retries=max_retries,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        return job

    def schedule_job(self, job: Job, run_at: datetime) -> str:
        """
        Schedule a job to run at a specific time.
        
        Args:
            job: Job to schedule
            run_at: When to run the job
            
        Returns:
            Job ID
        """
        # Save job to storage
        self.storage.save_job(job)
        
        # Schedule job
        self.scheduler.schedule_job(job, run_at)
        
        self.logger.info(f"Job '{job.name}' scheduled for {run_at}")
        return job.id

    def schedule_delayed_job(self, job: Job, delay_seconds: int) -> str:
        """
        Schedule a job to run after a delay.
        
        Args:
            job: Job to schedule
            delay_seconds: Delay in seconds
            
        Returns:
            Job ID
        """
        run_at = datetime.now() + timedelta(seconds=delay_seconds)
        return self.schedule_job(job, run_at)

    def schedule_recurring_job(self, job: Job, cron_expression: str) -> str:
        """
        Schedule a recurring job.
        
        Args:
            job: Job to schedule
            cron_expression: Cron expression
            
        Returns:
            Job ID
        """
        # Save job to storage
        self.storage.save_job(job)
        
        # Schedule recurring job
        self.scheduler.schedule_recurring_job(job, cron_expression)
        
        self.logger.info(f"Recurring job '{job.name}' scheduled with cron: {cron_expression}")
        return job.id

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job.
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            True if cancelled successfully
        """
        # Try to cancel from scheduler
        scheduler_cancelled = self.scheduler.cancel_job(job_id)
        
        # Try to cancel from executor
        executor_cancelled = self.executor.cancel_job(job_id)
        
        # Remove from queue
        queue_cancelled = self.job_queue.remove_job(job_id)
        
        # Update job status in storage
        job = self.storage.get_job(job_id)
        if job:
            job.mark_cancelled()
            self.storage.update_job(job)
        
        cancelled = scheduler_cancelled or executor_cancelled or queue_cancelled
        
        if cancelled:
            self.logger.info(f"Job {job_id} cancelled")
        else:
            self.logger.warning(f"Job {job_id} not found for cancellation")
        
        return cancelled

    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get a job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job if found
        """
        return self.storage.get_job(job_id)

    def get_jobs(self, status: Optional[JobStatus] = None, limit: Optional[int] = None) -> List[Job]:
        """
        Get jobs with optional filtering.
        
        Args:
            status: Filter by status
            limit: Limit number of results
            
        Returns:
            List of jobs
        """
        return self.storage.get_jobs(status=status, limit=limit)

    def get_job_statistics(self) -> Dict[str, Any]:
        """
        Get job statistics.
        
        Returns:
            Dictionary of statistics
        """
        storage_stats = self.storage.get_statistics()
        queue_stats = self.job_queue.get_statistics()
        executor_stats = self.executor.get_statistics()
        
        # Calculate uptime
        uptime = (datetime.now() - self._stats['system_start_time']).total_seconds()
        
        return {
            'system': {
                'uptime_seconds': uptime,
                'is_running': self.is_running,
                'start_time': self._stats['system_start_time'].isoformat()
            },
            'storage': storage_stats,
            'queue': queue_stats,
            'executor': executor_stats
        }

    def get_running_jobs(self) -> List[str]:
        """
        Get list of currently running job IDs.
        
        Returns:
            List of running job IDs
        """
        return self.executor.get_running_jobs()

    def cleanup_old_jobs(self, older_than_days: int = 30) -> int:
        """
        Clean up old jobs.
        
        Args:
            older_than_days: Remove jobs older than this many days
            
        Returns:
            Number of jobs cleaned up
        """
        return self.storage.cleanup_old_jobs(older_than_days)

    def health_check(self) -> Dict[str, Any]:
        """
        Perform system health check.
        
        Returns:
            Health check results
        """
        health = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {
                'system': self.is_running,
                'executor': self.executor.is_running,
                'scheduler': self.scheduler.is_running,
                'storage': True  # Assume storage is healthy if no exceptions
            }
        }
        
        # Check for any failed components
        if not all(health['components'].values()):
            health['status'] = 'unhealthy'
        
        # Check if there are too many failed jobs
        failed_jobs = self.storage.get_job_count(JobStatus.FAILED)
        total_jobs = self.storage.get_job_count()
        
        if total_jobs > 0 and failed_jobs / total_jobs > 0.5:
            health['status'] = 'degraded'
            health['warning'] = f"High failure rate: {failed_jobs}/{total_jobs} jobs failed"
        
        return health

    def _create_storage(self) -> JobStorage:
        """Create storage backend based on configuration."""
        if self.config.database.type == 'sqlite':
            backend = SQLiteStorageBackend(
                db_path=self.config.database.database,
                logger=self.logger
            )
        elif self.config.database.type == 'file':
            backend = FileStorageBackend(
                storage_dir=self.config.database.database,
                logger=self.logger
            )
        else:
            # Default to SQLite
            backend = SQLiteStorageBackend(logger=self.logger)
        
        return JobStorage(backend=backend, logger=self.logger)

    def _cleanup_loop(self):
        """Background cleanup loop."""
        while not self._stop_event.is_set():
            try:
                # Clean up old jobs every hour
                self.cleanup_old_jobs()
                
                # Sleep for 1 hour
                self._stop_event.wait(3600)
                
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                self._stop_event.wait(60)  # Wait 1 minute before retrying

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()

    def __str__(self) -> str:
        """String representation."""
        return f"JobAutomationSystem(running={self.is_running})"