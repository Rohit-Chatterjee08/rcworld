"""
Job queue management for prioritized job execution.
"""

import threading
import heapq
from typing import List, Optional, Dict, Any
from collections import defaultdict

from .job import Job, JobStatus, JobPriority
from .logger import Logger


class JobQueue:
    """
    Manages job queues with priority handling.
    """

    def __init__(self, logger: Optional[Logger] = None):
        """
        Initialize the job queue.
        
        Args:
            logger: Logger instance for logging
        """
        self.logger = logger or Logger()
        self._queues: Dict[JobPriority, List] = {
            priority: [] for priority in JobPriority
        }
        self._job_lookup: Dict[str, Job] = {}
        self._lock = threading.RLock()
        self._stats = defaultdict(int)

    def add_job(self, job: Job):
        """
        Add a job to the appropriate priority queue.
        
        Args:
            job: Job to add to queue
        """
        with self._lock:
            if job.id in self._job_lookup:
                self.logger.warning(f"Job {job.id} already exists in queue")
                return

            # Create a tuple for heap: (priority_value, job_id, job)
            # Lower priority values have higher priority in heapq
            priority_value = -job.priority.value  # Negative for max-heap behavior
            heap_item = (priority_value, job.id, job)
            
            heapq.heappush(self._queues[job.priority], heap_item)
            self._job_lookup[job.id] = job
            self._stats['total_added'] += 1
            self._stats[f'priority_{job.priority.name.lower()}'] += 1
            
            self.logger.info(f"Job '{job.name}' added to {job.priority.name} priority queue")

    def get_next_job(self) -> Optional[Job]:
        """
        Get the next job from the highest priority queue.
        
        Returns:
            Next job to execute or None if no jobs available
        """
        with self._lock:
            # Check queues in priority order (URGENT -> HIGH -> NORMAL -> LOW)
            for priority in sorted(JobPriority, key=lambda p: p.value, reverse=True):
                queue = self._queues[priority]
                
                while queue:
                    try:
                        _, job_id, job = heapq.heappop(queue)
                        
                        # Check if job is still valid
                        if job_id in self._job_lookup:
                            del self._job_lookup[job_id]
                            self._stats['total_retrieved'] += 1
                            self.logger.info(f"Retrieved job '{job.name}' from {priority.name} queue")
                            return job
                        
                    except IndexError:
                        break
            
            return None

    def peek_next_job(self) -> Optional[Job]:
        """
        Peek at the next job without removing it from queue.
        
        Returns:
            Next job or None if no jobs available
        """
        with self._lock:
            for priority in sorted(JobPriority, key=lambda p: p.value, reverse=True):
                queue = self._queues[priority]
                
                while queue:
                    _, job_id, job = queue[0]  # Peek at top of heap
                    
                    if job_id in self._job_lookup:
                        return job
                    else:
                        # Remove invalid job
                        heapq.heappop(queue)
                        
            return None

    def remove_job(self, job_id: str) -> bool:
        """
        Remove a job from the queue.
        
        Args:
            job_id: ID of job to remove
            
        Returns:
            True if job was removed, False if not found
        """
        with self._lock:
            if job_id not in self._job_lookup:
                return False
            
            job = self._job_lookup.pop(job_id)
            self._stats['total_removed'] += 1
            self.logger.info(f"Job '{job.name}' removed from queue")
            return True

    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get a job by ID without removing it.
        
        Args:
            job_id: Job ID to look up
            
        Returns:
            Job if found, None otherwise
        """
        with self._lock:
            return self._job_lookup.get(job_id)

    def get_all_jobs(self) -> List[Job]:
        """
        Get all jobs in the queue.
        
        Returns:
            List of all jobs in queue
        """
        with self._lock:
            return list(self._job_lookup.values())

    def get_jobs_by_priority(self, priority: JobPriority) -> List[Job]:
        """
        Get all jobs with specific priority.
        
        Args:
            priority: Priority level to filter by
            
        Returns:
            List of jobs with the specified priority
        """
        with self._lock:
            return [job for job in self._job_lookup.values() if job.priority == priority]

    def get_jobs_by_status(self, status: JobStatus) -> List[Job]:
        """
        Get all jobs with specific status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of jobs with the specified status
        """
        with self._lock:
            return [job for job in self._job_lookup.values() if job.status == status]

    def get_jobs_by_tag(self, tag: str) -> List[Job]:
        """
        Get all jobs with specific tag.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of jobs with the specified tag
        """
        with self._lock:
            return [job for job in self._job_lookup.values() if tag in job.tags]

    def clear_queue(self, priority: Optional[JobPriority] = None):
        """
        Clear jobs from queue.
        
        Args:
            priority: If specified, only clear jobs with this priority
        """
        with self._lock:
            if priority:
                # Clear specific priority queue
                queue = self._queues[priority]
                while queue:
                    try:
                        _, job_id, _ = heapq.heappop(queue)
                        self._job_lookup.pop(job_id, None)
                    except IndexError:
                        break
                self.logger.info(f"Cleared {priority.name} priority queue")
            else:
                # Clear all queues
                for priority_level in JobPriority:
                    self._queues[priority_level].clear()
                self._job_lookup.clear()
                self.logger.info("Cleared all job queues")

    def size(self, priority: Optional[JobPriority] = None) -> int:
        """
        Get the size of the queue.
        
        Args:
            priority: If specified, get size of specific priority queue
            
        Returns:
            Number of jobs in queue
        """
        with self._lock:
            if priority:
                return len([job for job in self._job_lookup.values() if job.priority == priority])
            else:
                return len(self._job_lookup)

    def is_empty(self) -> bool:
        """
        Check if the queue is empty.
        
        Returns:
            True if queue is empty, False otherwise
        """
        with self._lock:
            return len(self._job_lookup) == 0

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get queue statistics.
        
        Returns:
            Dictionary containing queue statistics
        """
        with self._lock:
            stats = dict(self._stats)
            stats.update({
                'current_size': len(self._job_lookup),
                'priority_breakdown': {
                    priority.name: len([j for j in self._job_lookup.values() if j.priority == priority])
                    for priority in JobPriority
                },
                'status_breakdown': {
                    status.name: len([j for j in self._job_lookup.values() if j.status == status])
                    for status in JobStatus
                }
            })
            return stats