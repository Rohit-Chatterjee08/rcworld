"""
Storage system for persisting job data and results.
"""

import os
import json
import sqlite3
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from .job import Job, JobStatus, JobPriority
from .logger import Logger


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def save_job(self, job: Job) -> bool:
        """Save a job to storage."""
        pass
    
    @abstractmethod
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        pass
    
    @abstractmethod
    def update_job(self, job: Job) -> bool:
        """Update a job in storage."""
        pass
    
    @abstractmethod
    def delete_job(self, job_id: str) -> bool:
        """Delete a job from storage."""
        pass
    
    @abstractmethod
    def get_jobs(self, status: Optional[JobStatus] = None, limit: Optional[int] = None) -> List[Job]:
        """Get jobs with optional filtering."""
        pass
    
    @abstractmethod
    def get_job_count(self, status: Optional[JobStatus] = None) -> int:
        """Get count of jobs with optional filtering."""
        pass
    
    @abstractmethod
    def cleanup_old_jobs(self, older_than_days: int) -> int:
        """Clean up old jobs."""
        pass


class SQLiteStorageBackend(StorageBackend):
    """SQLite storage backend."""
    
    def __init__(self, db_path: str = "jobs.db", logger: Optional[Logger] = None):
        """
        Initialize SQLite storage.
        
        Args:
            db_path: Path to SQLite database file
            logger: Logger instance
        """
        self.db_path = db_path
        self.logger = logger or Logger()
        self._lock = threading.RLock()
        
        # Create database directory if it doesn't exist
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                
                # Create jobs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS jobs (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        command TEXT NOT NULL,
                        parameters TEXT,
                        status TEXT NOT NULL,
                        priority INTEGER NOT NULL,
                        created_at TEXT NOT NULL,
                        scheduled_at TEXT,
                        started_at TEXT,
                        completed_at TEXT,
                        retry_count INTEGER DEFAULT 0,
                        max_retries INTEGER DEFAULT 3,
                        timeout INTEGER,
                        tags TEXT,
                        metadata TEXT,
                        error_message TEXT,
                        result TEXT
                    )
                ''')
                
                # Create indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_priority ON jobs(priority)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_scheduled_at ON jobs(scheduled_at)')
                
                conn.commit()
                
            finally:
                conn.close()
    
    def save_job(self, job: Job) -> bool:
        """Save a job to SQLite database."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO jobs (
                        id, name, command, parameters, status, priority,
                        created_at, scheduled_at, started_at, completed_at,
                        retry_count, max_retries, timeout, tags, metadata,
                        error_message, result
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job.id,
                    job.name,
                    job.command,
                    json.dumps(job.parameters),
                    job.status.value,
                    job.priority.value,
                    job.created_at.isoformat(),
                    job.scheduled_at.isoformat() if job.scheduled_at else None,
                    job.started_at.isoformat() if job.started_at else None,
                    job.completed_at.isoformat() if job.completed_at else None,
                    job.retry_count,
                    job.max_retries,
                    job.timeout,
                    json.dumps(job.tags),
                    json.dumps(job.metadata),
                    job.error_message,
                    json.dumps(job.result) if job.result else None
                ))
                
                conn.commit()
                return True
                
            except Exception as e:
                self.logger.error(f"Error saving job {job.id}: {e}")
                return False
            finally:
                conn.close()
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID from SQLite database."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_job(row)
                return None
                
            except Exception as e:
                self.logger.error(f"Error getting job {job_id}: {e}")
                return None
            finally:
                conn.close()
    
    def update_job(self, job: Job) -> bool:
        """Update a job in SQLite database."""
        return self.save_job(job)  # INSERT OR REPLACE handles updates
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job from SQLite database."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
                conn.commit()
                return cursor.rowcount > 0
                
            except Exception as e:
                self.logger.error(f"Error deleting job {job_id}: {e}")
                return False
            finally:
                conn.close()
    
    def get_jobs(self, status: Optional[JobStatus] = None, limit: Optional[int] = None) -> List[Job]:
        """Get jobs from SQLite database with optional filtering."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                
                query = 'SELECT * FROM jobs'
                params = []
                
                if status:
                    query += ' WHERE status = ?'
                    params.append(status.value)
                
                query += ' ORDER BY created_at DESC'
                
                if limit:
                    query += ' LIMIT ?'
                    params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [self._row_to_job(row) for row in rows]
                
            except Exception as e:
                self.logger.error(f"Error getting jobs: {e}")
                return []
            finally:
                conn.close()
    
    def get_job_count(self, status: Optional[JobStatus] = None) -> int:
        """Get count of jobs from SQLite database."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                
                query = 'SELECT COUNT(*) FROM jobs'
                params = []
                
                if status:
                    query += ' WHERE status = ?'
                    params.append(status.value)
                
                cursor.execute(query, params)
                return cursor.fetchone()[0]
                
            except Exception as e:
                self.logger.error(f"Error getting job count: {e}")
                return 0
            finally:
                conn.close()
    
    def cleanup_old_jobs(self, older_than_days: int) -> int:
        """Clean up old jobs from SQLite database."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                
                # Calculate cutoff date
                cutoff_date = datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                cutoff_date = cutoff_date.replace(day=cutoff_date.day - older_than_days)
                
                cursor.execute('''
                    DELETE FROM jobs 
                    WHERE created_at < ? 
                    AND status IN ('completed', 'failed', 'cancelled')
                ''', (cutoff_date.isoformat(),))
                
                conn.commit()
                deleted_count = cursor.rowcount
                
                self.logger.info(f"Cleaned up {deleted_count} old jobs")
                return deleted_count
                
            except Exception as e:
                self.logger.error(f"Error cleaning up old jobs: {e}")
                return 0
            finally:
                conn.close()
    
    def _row_to_job(self, row) -> Job:
        """Convert database row to Job object."""
        return Job(
            id=row[0],
            name=row[1],
            command=row[2],
            parameters=json.loads(row[3]) if row[3] else {},
            status=JobStatus(row[4]),
            priority=JobPriority(row[5]),
            created_at=datetime.fromisoformat(row[6]),
            scheduled_at=datetime.fromisoformat(row[7]) if row[7] else None,
            started_at=datetime.fromisoformat(row[8]) if row[8] else None,
            completed_at=datetime.fromisoformat(row[9]) if row[9] else None,
            retry_count=row[10],
            max_retries=row[11],
            timeout=row[12],
            tags=json.loads(row[13]) if row[13] else [],
            metadata=json.loads(row[14]) if row[14] else {},
            error_message=row[15],
            result=json.loads(row[16]) if row[16] else None
        )


class FileStorageBackend(StorageBackend):
    """File-based storage backend using JSON files."""
    
    def __init__(self, storage_dir: str = "job_storage", logger: Optional[Logger] = None):
        """
        Initialize file storage.
        
        Args:
            storage_dir: Directory to store job files
            logger: Logger instance
        """
        self.storage_dir = Path(storage_dir)
        self.logger = logger or Logger()
        self._lock = threading.RLock()
        
        # Create storage directory
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def save_job(self, job: Job) -> bool:
        """Save a job to JSON file."""
        with self._lock:
            try:
                file_path = self.storage_dir / f"{job.id}.json"
                with open(file_path, 'w') as f:
                    json.dump(job.to_dict(), f, indent=2)
                return True
                
            except Exception as e:
                self.logger.error(f"Error saving job {job.id}: {e}")
                return False
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID from JSON file."""
        with self._lock:
            try:
                file_path = self.storage_dir / f"{job_id}.json"
                if not file_path.exists():
                    return None
                
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    return Job.from_dict(data)
                
            except Exception as e:
                self.logger.error(f"Error getting job {job_id}: {e}")
                return None
    
    def update_job(self, job: Job) -> bool:
        """Update a job in JSON file."""
        return self.save_job(job)
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job JSON file."""
        with self._lock:
            try:
                file_path = self.storage_dir / f"{job_id}.json"
                if file_path.exists():
                    file_path.unlink()
                    return True
                return False
                
            except Exception as e:
                self.logger.error(f"Error deleting job {job_id}: {e}")
                return False
    
    def get_jobs(self, status: Optional[JobStatus] = None, limit: Optional[int] = None) -> List[Job]:
        """Get jobs from JSON files with optional filtering."""
        with self._lock:
            try:
                jobs = []
                
                for file_path in self.storage_dir.glob("*.json"):
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            job = Job.from_dict(data)
                            
                            if status is None or job.status == status:
                                jobs.append(job)
                                
                    except Exception as e:
                        self.logger.warning(f"Error loading job from {file_path}: {e}")
                        continue
                
                # Sort by created_at descending
                jobs.sort(key=lambda j: j.created_at, reverse=True)
                
                if limit:
                    jobs = jobs[:limit]
                
                return jobs
                
            except Exception as e:
                self.logger.error(f"Error getting jobs: {e}")
                return []
    
    def get_job_count(self, status: Optional[JobStatus] = None) -> int:
        """Get count of jobs from JSON files."""
        jobs = self.get_jobs(status=status)
        return len(jobs)
    
    def cleanup_old_jobs(self, older_than_days: int) -> int:
        """Clean up old job files."""
        with self._lock:
            try:
                deleted_count = 0
                cutoff_date = datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                cutoff_date = cutoff_date.replace(day=cutoff_date.day - older_than_days)
                
                for file_path in self.storage_dir.glob("*.json"):
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            job = Job.from_dict(data)
                            
                            if (job.created_at < cutoff_date and 
                                job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]):
                                file_path.unlink()
                                deleted_count += 1
                                
                    except Exception as e:
                        self.logger.warning(f"Error processing {file_path} during cleanup: {e}")
                        continue
                
                self.logger.info(f"Cleaned up {deleted_count} old job files")
                return deleted_count
                
            except Exception as e:
                self.logger.error(f"Error cleaning up old jobs: {e}")
                return 0


class JobStorage:
    """
    Main storage interface for job persistence.
    """
    
    def __init__(self, backend: Optional[StorageBackend] = None, logger: Optional[Logger] = None):
        """
        Initialize job storage.
        
        Args:
            backend: Storage backend to use
            logger: Logger instance
        """
        self.backend = backend or SQLiteStorageBackend()
        self.logger = logger or Logger()
    
    def save_job(self, job: Job) -> bool:
        """Save a job to storage."""
        return self.backend.save_job(job)
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        return self.backend.get_job(job_id)
    
    def update_job(self, job: Job) -> bool:
        """Update a job in storage."""
        return self.backend.update_job(job)
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job from storage."""
        return self.backend.delete_job(job_id)
    
    def get_jobs(self, status: Optional[JobStatus] = None, limit: Optional[int] = None) -> List[Job]:
        """Get jobs with optional filtering."""
        return self.backend.get_jobs(status=status, limit=limit)
    
    def get_job_count(self, status: Optional[JobStatus] = None) -> int:
        """Get count of jobs."""
        return self.backend.get_job_count(status=status)
    
    def get_jobs_by_tag(self, tag: str) -> List[Job]:
        """Get jobs by tag."""
        all_jobs = self.get_jobs()
        return [job for job in all_jobs if tag in job.tags]
    
    def get_failed_jobs(self, limit: Optional[int] = None) -> List[Job]:
        """Get failed jobs."""
        return self.get_jobs(status=JobStatus.FAILED, limit=limit)
    
    def get_completed_jobs(self, limit: Optional[int] = None) -> List[Job]:
        """Get completed jobs."""
        return self.get_jobs(status=JobStatus.COMPLETED, limit=limit)
    
    def get_running_jobs(self) -> List[Job]:
        """Get currently running jobs."""
        return self.get_jobs(status=JobStatus.RUNNING)
    
    def cleanup_old_jobs(self, older_than_days: int = 30) -> int:
        """Clean up old jobs."""
        return self.backend.cleanup_old_jobs(older_than_days)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return {
            'total_jobs': self.get_job_count(),
            'pending_jobs': self.get_job_count(JobStatus.PENDING),
            'running_jobs': self.get_job_count(JobStatus.RUNNING),
            'completed_jobs': self.get_job_count(JobStatus.COMPLETED),
            'failed_jobs': self.get_job_count(JobStatus.FAILED),
            'cancelled_jobs': self.get_job_count(JobStatus.CANCELLED)
        }