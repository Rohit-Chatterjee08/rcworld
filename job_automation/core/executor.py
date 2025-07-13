"""
Task executor for running jobs with support for threading and error handling.
"""

import threading
import time
import subprocess
import signal
import os
from typing import Dict, Any, Optional, List, Callable
from concurrent.futures import ThreadPoolExecutor, Future
from contextlib import contextmanager

from .job import Job, JobStatus
from .job_queue import JobQueue
from .logger import Logger
from .storage import JobStorage


class TaskExecutor:
    """
    Executes jobs from the job queue with configurable concurrency.
    """

    def __init__(self, 
                 job_queue: JobQueue, 
                 max_workers: int = 4,
                 storage: Optional[JobStorage] = None,
                 logger: Optional[Logger] = None):
        """
        Initialize the task executor.
        
        Args:
            job_queue: Job queue to pull jobs from
            max_workers: Maximum number of concurrent workers
            storage: Storage instance for persisting job results
            logger: Logger instance for logging
        """
        self.job_queue = job_queue
        self.max_workers = max_workers
        self.storage = storage or JobStorage()
        self.logger = logger or Logger()
        
        self.is_running = False
        self._executor: Optional[ThreadPoolExecutor] = None
        self._stop_event = threading.Event()
        self._running_jobs: Dict[str, Future] = {}
        self._job_processes: Dict[str, subprocess.Popen] = {}
        self._lock = threading.RLock()
        
        # Statistics
        self._stats = {
            'jobs_completed': 0,
            'jobs_failed': 0,
            'jobs_cancelled': 0,
            'total_execution_time': 0
        }

    def start(self):
        """Start the task executor."""
        if self.is_running:
            self.logger.warning("Task executor is already running")
            return

        self.is_running = True
        self._stop_event.clear()
        self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Start the main execution loop
        execution_thread = threading.Thread(target=self._execution_loop, daemon=True)
        execution_thread.start()
        
        self.logger.info(f"Task executor started with {self.max_workers} workers")

    def stop(self, timeout: int = 30):
        """
        Stop the task executor.
        
        Args:
            timeout: Maximum time to wait for jobs to complete
        """
        if not self.is_running:
            return

        self.is_running = False
        self._stop_event.set()
        
        # Cancel all running jobs
        self._cancel_running_jobs()
        
        # Shutdown executor
        if self._executor:
            self._executor.shutdown(wait=True, timeout=timeout)
            
        self.logger.info("Task executor stopped")

    def execute_job(self, job: Job) -> Future:
        """
        Execute a single job asynchronously.
        
        Args:
            job: Job to execute
            
        Returns:
            Future representing the job execution
        """
        if not self.is_running or not self._executor:
            raise RuntimeError("Task executor is not running")
            
        future = self._executor.submit(self._execute_job_sync, job)
        
        with self._lock:
            self._running_jobs[job.id] = future
            
        return future

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.
        
        Args:
            job_id: ID of job to cancel
            
        Returns:
            True if job was cancelled, False if not found
        """
        with self._lock:
            # Cancel future
            if job_id in self._running_jobs:
                future = self._running_jobs[job_id]
                cancelled = future.cancel()
                if cancelled:
                    del self._running_jobs[job_id]
                    
            # Kill process if running
            if job_id in self._job_processes:
                try:
                    process = self._job_processes[job_id]
                    process.terminate()
                    # Give process time to terminate gracefully
                    time.sleep(2)
                    if process.poll() is None:
                        process.kill()
                    del self._job_processes[job_id]
                except Exception as e:
                    self.logger.error(f"Error killing process for job {job_id}: {e}")
                    
                return True
                
        return False

    def get_running_jobs(self) -> List[str]:
        """Get list of currently running job IDs."""
        with self._lock:
            return list(self._running_jobs.keys())

    def get_statistics(self) -> Dict[str, Any]:
        """Get executor statistics."""
        with self._lock:
            stats = self._stats.copy()
            stats.update({
                'running_jobs': len(self._running_jobs),
                'max_workers': self.max_workers,
                'is_running': self.is_running
            })
            return stats

    def _execution_loop(self):
        """Main execution loop that processes jobs from the queue."""
        while not self._stop_event.is_set():
            try:
                # Get next job from queue
                job = self.job_queue.get_next_job()
                
                if job is None:
                    time.sleep(0.1)  # Short sleep if no jobs available
                    continue
                
                # Execute job
                self.execute_job(job)
                
            except Exception as e:
                self.logger.error(f"Error in execution loop: {e}")
                time.sleep(1)  # Wait before retrying

    def _execute_job_sync(self, job: Job) -> Dict[str, Any]:
        """
        Execute a job synchronously.
        
        Args:
            job: Job to execute
            
        Returns:
            Dictionary containing execution result
        """
        start_time = time.time()
        
        try:
            # Mark job as started
            job.mark_started()
            self.storage.update_job(job)
            self.logger.info(f"Starting execution of job '{job.name}' (ID: {job.id})")
            
            # Execute the job command
            result = self._run_command(job)
            
            # Mark job as completed
            job.mark_completed(result)
            self.storage.update_job(job)
            
            # Update statistics
            execution_time = time.time() - start_time
            with self._lock:
                self._stats['jobs_completed'] += 1
                self._stats['total_execution_time'] += execution_time
                
            self.logger.info(f"Job '{job.name}' completed successfully in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            # Mark job as failed
            error_msg = str(e)
            job.mark_failed(error_msg)
            self.storage.update_job(job)
            
            # Update statistics
            with self._lock:
                self._stats['jobs_failed'] += 1
                
            self.logger.error(f"Job '{job.name}' failed: {error_msg}")
            
            # Check if job can be retried
            if job.can_retry():
                job.increment_retry()
                self.job_queue.add_job(job)
                self.logger.info(f"Job '{job.name}' queued for retry ({job.retry_count}/{job.max_retries})")
            
            raise
            
        finally:
            # Clean up
            with self._lock:
                self._running_jobs.pop(job.id, None)
                self._job_processes.pop(job.id, None)

    def _run_command(self, job: Job) -> Dict[str, Any]:
        """
        Run the job command.
        
        Args:
            job: Job containing command to run
            
        Returns:
            Dictionary containing command result
        """
        command = job.command
        parameters = job.parameters
        
        # Handle different command types
        if command.startswith("python:"):
            return self._run_python_command(command[7:], parameters, job)
        elif command.startswith("shell:"):
            return self._run_shell_command(command[6:], parameters, job)
        elif command.startswith("http:"):
            return self._run_http_request(command[5:], parameters, job)
        else:
            # Default to shell command
            return self._run_shell_command(command, parameters, job)

    def _run_shell_command(self, command: str, parameters: Dict[str, Any], job: Job) -> Dict[str, Any]:
        """Run a shell command."""
        try:
            # Substitute parameters in command
            formatted_command = command.format(**parameters)
            
            # Set up environment
            env = os.environ.copy()
            env.update(parameters.get('env', {}))
            
            # Execute command
            process = subprocess.Popen(
                formatted_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            
            # Store process for potential cancellation
            with self._lock:
                self._job_processes[job.id] = process
            
            # Wait for completion with timeout
            timeout = job.timeout or 3600  # Default 1 hour timeout
            stdout, stderr = process.communicate(timeout=timeout)
            
            return {
                'stdout': stdout,
                'stderr': stderr,
                'return_code': process.returncode,
                'command': formatted_command
            }
            
        except subprocess.TimeoutExpired:
            process.kill()
            raise Exception(f"Command timed out after {timeout} seconds")
        except Exception as e:
            raise Exception(f"Command execution failed: {e}")

    def _run_python_command(self, module_path: str, parameters: Dict[str, Any], job: Job) -> Dict[str, Any]:
        """Run a Python module or function."""
        try:
            # Import and execute Python module
            import importlib
            
            # Split module path and function name
            if '::' in module_path:
                module_name, func_name = module_path.split('::', 1)
            else:
                module_name = module_path
                func_name = 'main'
            
            # Import module
            module = importlib.import_module(module_name)
            
            # Get function
            if not hasattr(module, func_name):
                raise Exception(f"Function '{func_name}' not found in module '{module_name}'")
            
            func = getattr(module, func_name)
            
            # Execute function
            result = func(**parameters)
            
            return {
                'result': result,
                'module': module_name,
                'function': func_name
            }
            
        except Exception as e:
            raise Exception(f"Python execution failed: {e}")

    def _run_http_request(self, url: str, parameters: Dict[str, Any], job: Job) -> Dict[str, Any]:
        """Run an HTTP request."""
        try:
            import requests
            
            method = parameters.get('method', 'GET').upper()
            headers = parameters.get('headers', {})
            data = parameters.get('data')
            params = parameters.get('params')
            timeout = job.timeout or 30
            
            # Make request
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                params=params,
                timeout=timeout
            )
            
            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content': response.text,
                'url': response.url
            }
            
        except Exception as e:
            raise Exception(f"HTTP request failed: {e}")

    def _cancel_running_jobs(self):
        """Cancel all running jobs."""
        with self._lock:
            for job_id, future in list(self._running_jobs.items()):
                try:
                    future.cancel()
                    self._stats['jobs_cancelled'] += 1
                except Exception as e:
                    self.logger.error(f"Error cancelling job {job_id}: {e}")
            
            # Kill all processes
            for job_id, process in list(self._job_processes.items()):
                try:
                    process.terminate()
                    time.sleep(1)
                    if process.poll() is None:
                        process.kill()
                except Exception as e:
                    self.logger.error(f"Error killing process for job {job_id}: {e}")
            
            self._running_jobs.clear()
            self._job_processes.clear()