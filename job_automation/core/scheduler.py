"""
Job scheduler for managing job execution timing and scheduling.
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from croniter import croniter

from .job import Job, JobStatus
from .job_queue import JobQueue
from .logger import Logger


class JobScheduler:
    """
    Manages job scheduling and execution timing.
    """

    def __init__(self, job_queue: JobQueue, logger: Optional[Logger] = None):
        """
        Initialize the job scheduler.
        
        Args:
            job_queue: Job queue instance for managing jobs
            logger: Logger instance for logging
        """
        self.job_queue = job_queue
        self.logger = logger or Logger()
        self.scheduled_jobs: Dict[str, Job] = {}
        self.recurring_jobs: Dict[str, Dict] = {}
        self.is_running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self):
        """Start the scheduler."""
        if self.is_running:
            self.logger.warning("Scheduler is already running")
            return

        self.is_running = True
        self._stop_event.clear()
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        self.logger.info("Job scheduler started")

    def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            return

        self.is_running = False
        self._stop_event.set()
        
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
            
        self.logger.info("Job scheduler stopped")

    def schedule_job(self, job: Job, run_at: datetime):
        """
        Schedule a job to run at a specific time.
        
        Args:
            job: Job to schedule
            run_at: When to run the job
        """
        job.scheduled_at = run_at
        self.scheduled_jobs[job.id] = job
        self.logger.info(f"Job '{job.name}' scheduled to run at {run_at}")

    def schedule_delayed_job(self, job: Job, delay_seconds: int):
        """
        Schedule a job to run after a delay.
        
        Args:
            job: Job to schedule
            delay_seconds: Delay in seconds
        """
        run_at = datetime.now() + timedelta(seconds=delay_seconds)
        self.schedule_job(job, run_at)

    def schedule_recurring_job(self, job: Job, cron_expression: str):
        """
        Schedule a recurring job using cron expression.
        
        Args:
            job: Job to schedule
            cron_expression: Cron expression for scheduling
        """
        try:
            cron = croniter(cron_expression, datetime.now())
            next_run = cron.get_next(datetime)
            
            self.recurring_jobs[job.id] = {
                'job': job,
                'cron': cron_expression,
                'next_run': next_run
            }
            
            self.logger.info(f"Recurring job '{job.name}' scheduled with cron: {cron_expression}")
            
        except Exception as e:
            self.logger.error(f"Invalid cron expression '{cron_expression}': {e}")
            raise

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a scheduled job.
        
        Args:
            job_id: ID of the job to cancel
            
        Returns:
            True if job was cancelled, False if not found
        """
        cancelled = False
        
        if job_id in self.scheduled_jobs:
            job = self.scheduled_jobs.pop(job_id)
            job.mark_cancelled()
            cancelled = True
            
        if job_id in self.recurring_jobs:
            self.recurring_jobs.pop(job_id)
            cancelled = True
            
        if cancelled:
            self.logger.info(f"Job {job_id} cancelled")
            
        return cancelled

    def get_scheduled_jobs(self) -> List[Job]:
        """Get all scheduled jobs."""
        return list(self.scheduled_jobs.values())

    def get_recurring_jobs(self) -> List[Dict]:
        """Get all recurring jobs."""
        return list(self.recurring_jobs.values())

    def _scheduler_loop(self):
        """Main scheduler loop."""
        while not self._stop_event.is_set():
            try:
                current_time = datetime.now()
                
                # Check scheduled jobs
                self._process_scheduled_jobs(current_time)
                
                # Check recurring jobs
                self._process_recurring_jobs(current_time)
                
                # Sleep for a short interval
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                time.sleep(5)  # Wait before retrying

    def _process_scheduled_jobs(self, current_time: datetime):
        """Process scheduled jobs that are ready to run."""
        ready_jobs = []
        
        for job_id, job in list(self.scheduled_jobs.items()):
            if job.scheduled_at and job.scheduled_at <= current_time:
                ready_jobs.append(job)
                del self.scheduled_jobs[job_id]
        
        for job in ready_jobs:
            self.job_queue.add_job(job)
            self.logger.info(f"Job '{job.name}' added to queue for execution")

    def _process_recurring_jobs(self, current_time: datetime):
        """Process recurring jobs that are ready to run."""
        for job_id, job_info in list(self.recurring_jobs.items()):
            if job_info['next_run'] <= current_time:
                # Create a new job instance for this run
                original_job = job_info['job']
                new_job = Job(
                    name=original_job.name,
                    command=original_job.command,
                    parameters=original_job.parameters.copy(),
                    priority=original_job.priority,
                    timeout=original_job.timeout,
                    tags=original_job.tags.copy(),
                    metadata=original_job.metadata.copy()
                )
                
                # Add to queue
                self.job_queue.add_job(new_job)
                self.logger.info(f"Recurring job '{new_job.name}' added to queue")
                
                # Calculate next run time
                try:
                    cron = croniter(job_info['cron'], current_time)
                    job_info['next_run'] = cron.get_next(datetime)
                except Exception as e:
                    self.logger.error(f"Error calculating next run for job {job_id}: {e}")
                    # Remove invalid recurring job
                    del self.recurring_jobs[job_id]