"""
Database module for job automation tool
Handles job storage, application tracking, and user data management
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

class JobDatabase:
    """Database handler for job automation tool"""
    
    def __init__(self, db_path: str = "data/jobs.db"):
        self.db_path = db_path
        self.ensure_directory_exists()
        self.init_database()
    
    def ensure_directory_exists(self):
        """Create database directory if it doesn't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Jobs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    salary TEXT,
                    experience_required TEXT,
                    job_url TEXT UNIQUE,
                    portal TEXT NOT NULL,
                    description TEXT,
                    requirements TEXT,
                    posted_date TEXT,
                    discovered_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    is_eligible BOOLEAN DEFAULT 1,
                    eligibility_score REAL DEFAULT 0.0,
                    keywords_matched TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Applications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER,
                    status TEXT DEFAULT 'pending',
                    applied_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    application_method TEXT,
                    resume_used TEXT,
                    cover_letter TEXT,
                    response_received TEXT,
                    notes TEXT,
                    screenshot_path TEXT,
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES jobs (id)
                )
            ''')
            
            # User activity log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN DEFAULT 1
                )
            ''')
            
            # Configuration storage
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config_storage (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def add_job(self, job_data: Dict) -> int:
        """Add a new job to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO jobs 
                (title, company, location, salary, experience_required, job_url, 
                 portal, description, requirements, posted_date, is_eligible, 
                 eligibility_score, keywords_matched)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_data.get('title', ''),
                job_data.get('company', ''),
                job_data.get('location', ''),
                job_data.get('salary', ''),
                job_data.get('experience_required', ''),
                job_data.get('job_url', ''),
                job_data.get('portal', ''),
                job_data.get('description', ''),
                job_data.get('requirements', ''),
                job_data.get('posted_date', ''),
                job_data.get('is_eligible', True),
                job_data.get('eligibility_score', 0.0),
                json.dumps(job_data.get('keywords_matched', []))
            ))
            
            job_id = cursor.lastrowid
            conn.commit()
            
            # Log activity
            self.log_activity("job_added", f"Added job: {job_data.get('title')} at {job_data.get('company')}")
            
            return job_id
    
    def add_application(self, job_id: int, application_data: Dict) -> int:
        """Record a job application"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO applications 
                (job_id, status, application_method, resume_used, cover_letter, 
                 notes, screenshot_path, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_id,
                application_data.get('status', 'pending'),
                application_data.get('application_method', ''),
                application_data.get('resume_used', ''),
                application_data.get('cover_letter', ''),
                application_data.get('notes', ''),
                application_data.get('screenshot_path', ''),
                application_data.get('error_message', '')
            ))
            
            application_id = cursor.lastrowid
            conn.commit()
            
            # Update job status
            self.update_job_application_status(job_id, application_data.get('status', 'applied'))
            
            return application_id
    
    def get_eligible_jobs(self, limit: int = 50) -> List[Dict]:
        """Get eligible jobs that haven't been applied to"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT j.*, a.status as application_status
                FROM jobs j
                LEFT JOIN applications a ON j.id = a.job_id
                WHERE j.is_eligible = 1 AND (a.status IS NULL OR a.status = 'failed')
                ORDER BY j.eligibility_score DESC, j.discovered_date DESC
                LIMIT ?
            ''', (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            jobs = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return jobs
    
    def get_application_stats(self) -> Dict:
        """Get application statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total applications
            cursor.execute("SELECT COUNT(*) FROM applications")
            total_applications = cursor.fetchone()[0]
            
            # Applications by status
            cursor.execute('''
                SELECT status, COUNT(*) 
                FROM applications 
                GROUP BY status
            ''')
            status_counts = dict(cursor.fetchall())
            
            # Applications today
            cursor.execute('''
                SELECT COUNT(*) 
                FROM applications 
                WHERE DATE(applied_date) = DATE('now')
            ''')
            today_applications = cursor.fetchone()[0]
            
            # Success rate
            success_rate = 0.0
            if total_applications > 0:
                successful = status_counts.get('success', 0) + status_counts.get('interview', 0)
                success_rate = (successful / total_applications) * 100
            
            return {
                'total_applications': total_applications,
                'today_applications': today_applications,
                'status_breakdown': status_counts,
                'success_rate': success_rate
            }
    
    def update_job_application_status(self, job_id: int, status: str):
        """Update job application status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE applications 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE job_id = ?
            ''', (status, job_id))
            
            conn.commit()
    
    def log_activity(self, action: str, details: str = "", success: bool = True):
        """Log user activity"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO activity_log (action, details, success)
                VALUES (?, ?, ?)
            ''', (action, details, success))
            
            conn.commit()
    
    def get_recent_activity(self, limit: int = 20) -> List[Dict]:
        """Get recent activity log"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM activity_log 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            activities = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return activities
    
    def check_job_exists(self, job_url: str) -> bool:
        """Check if job already exists in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM jobs WHERE job_url = ?', (job_url,))
            return cursor.fetchone() is not None
    
    def get_daily_application_count(self) -> int:
        """Get number of applications submitted today"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM applications 
                WHERE DATE(applied_date) = DATE('now')
            ''')
            
            return cursor.fetchone()[0]
    
    def backup_database(self, backup_path: str = None):
        """Create database backup"""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backups/jobs_backup_{timestamp}.db"
        
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as source:
            with sqlite3.connect(backup_path) as backup:
                source.backup(backup)
        
        self.log_activity("database_backup", f"Database backed up to {backup_path}")
        return backup_path
    
    def close(self):
        """Close database connection"""
        pass  # Using context manager, no explicit close needed