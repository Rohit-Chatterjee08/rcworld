"""
Job automation scheduler module
Handles scheduled job searches and applications using APScheduler
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pytz
from database import JobDatabase
from search import JobSearcher
from apply import JobApplicator
from utils import load_config, setup_logging

logger = logging.getLogger(__name__)

class JobAutomationScheduler:
    """Main scheduler class for job automation"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = load_config(config_path)
        self.scheduler = BackgroundScheduler()
        self.database = JobDatabase(self.config.get('database', {}).get('path', 'data/jobs.db'))
        self.job_searcher = None
        self.job_applicator = None
        self.is_running = False
        
        # Setup logging
        setup_logging(self.config)
        
        # Initialize scheduler settings
        self.scheduler_config = self.config.get('scheduler', {})
        self.timezone = pytz.timezone(self.scheduler_config.get('timezone', 'Asia/Kolkata'))
        
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        try:
            # Schedule periodic job searches
            self.schedule_job_searches()
            
            # Schedule daily cleanup
            self.schedule_daily_cleanup()
            
            # Schedule backup
            self.schedule_backup()
            
            # Start scheduler
            self.scheduler.start()
            self.is_running = True
            
            logger.info("Job automation scheduler started successfully")
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        try:
            self.scheduler.shutdown()
            self.is_running = False
            
            # Close connections
            if self.job_searcher:
                self.job_searcher.close()
            if self.job_applicator:
                self.job_applicator.close()
            
            logger.info("Job automation scheduler stopped")
            
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    def schedule_job_searches(self):
        """Schedule periodic job searches"""
        if not self.scheduler_config.get('enabled', True):
            logger.info("Scheduler is disabled in configuration")
            return
        
        run_times = self.scheduler_config.get('run_times', ['09:00', '14:00', '18:00'])
        
        for run_time in run_times:
            try:
                hour, minute = map(int, run_time.split(':'))
                
                # Schedule job search and application
                self.scheduler.add_job(
                    func=self.run_job_automation,
                    trigger=CronTrigger(
                        hour=hour,
                        minute=minute,
                        timezone=self.timezone
                    ),
                    id=f'job_automation_{run_time}',
                    name=f'Job Automation at {run_time}',
                    max_instances=1,
                    coalesce=True,
                    replace_existing=True
                )
                
                logger.info(f"Scheduled job automation for {run_time}")
                
            except Exception as e:
                logger.error(f"Error scheduling job for {run_time}: {e}")
    
    def schedule_daily_cleanup(self):
        """Schedule daily cleanup tasks"""
        # Clean up old logs, screenshots, and update job statuses
        self.scheduler.add_job(
            func=self.run_daily_cleanup,
            trigger=CronTrigger(
                hour=23,
                minute=30,
                timezone=self.timezone
            ),
            id='daily_cleanup',
            name='Daily Cleanup',
            max_instances=1,
            coalesce=True,
            replace_existing=True
        )
        
        logger.info("Scheduled daily cleanup task")
    
    def schedule_backup(self):
        """Schedule database backup"""
        backup_config = self.config.get('database', {})
        
        if not backup_config.get('backup_enabled', True):
            return
        
        frequency = backup_config.get('backup_frequency', 'daily')
        
        if frequency == 'daily':
            trigger = CronTrigger(hour=1, minute=0, timezone=self.timezone)
        elif frequency == 'weekly':
            trigger = CronTrigger(day_of_week='mon', hour=1, minute=0, timezone=self.timezone)
        elif frequency == 'hourly':
            trigger = CronTrigger(minute=0, timezone=self.timezone)
        else:
            logger.warning(f"Unknown backup frequency: {frequency}")
            return
        
        self.scheduler.add_job(
            func=self.run_backup,
            trigger=trigger,
            id='database_backup',
            name='Database Backup',
            max_instances=1,
            coalesce=True,
            replace_existing=True
        )
        
        logger.info(f"Scheduled database backup ({frequency})")
    
    def run_job_automation(self):
        """Run the complete job automation pipeline"""
        try:
            logger.info("Starting scheduled job automation run")
            
            # Check if max daily runs exceeded
            daily_runs = self.get_daily_runs_count()
            max_daily_runs = self.scheduler_config.get('max_daily_runs', 3)
            
            if daily_runs >= max_daily_runs:
                logger.warning(f"Maximum daily runs ({max_daily_runs}) reached")
                return
            
            # Record automation run
            self.database.log_activity("automation_run_started", "Scheduled automation run started")
            
            # Step 1: Search for jobs
            logger.info("Searching for jobs...")
            jobs = self.search_jobs()
            
            if not jobs:
                logger.info("No eligible jobs found")
                self.database.log_activity("automation_run_completed", "No eligible jobs found")
                return
            
            # Step 2: Apply to jobs
            logger.info(f"Applying to {len(jobs)} jobs...")
            results = self.apply_to_jobs(jobs)
            
            # Step 3: Generate summary
            self.generate_run_summary(results)
            
            logger.info("Scheduled job automation run completed")
            self.database.log_activity("automation_run_completed", f"Applied to {len(results)} jobs")
            
        except Exception as e:
            logger.error(f"Error in job automation run: {e}")
            self.database.log_activity("automation_run_failed", f"Error: {str(e)}", success=False)
    
    def search_jobs(self) -> List[Dict]:
        """Search for jobs using JobSearcher"""
        try:
            if not self.job_searcher:
                self.job_searcher = JobSearcher(self.config, self.database)
            
            jobs = self.job_searcher.search_all_portals()
            
            logger.info(f"Found {len(jobs)} eligible jobs")
            return jobs
            
        except Exception as e:
            logger.error(f"Error searching jobs: {e}")
            return []
    
    def apply_to_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Apply to jobs using JobApplicator"""
        try:
            if not self.job_applicator:
                self.job_applicator = JobApplicator(self.config, self.database)
            
            results = self.job_applicator.apply_to_jobs(jobs)
            
            logger.info(f"Applied to {len(results)} jobs")
            return results
            
        except Exception as e:
            logger.error(f"Error applying to jobs: {e}")
            return []
    
    def run_daily_cleanup(self):
        """Run daily cleanup tasks"""
        try:
            logger.info("Starting daily cleanup...")
            
            # Clean up old screenshots (older than 7 days)
            self.cleanup_old_files("screenshots", days=7)
            
            # Clean up old logs (older than 30 days)
            self.cleanup_old_files("logs", days=30)
            
            # Update job statuses
            self.update_job_statuses()
            
            logger.info("Daily cleanup completed")
            self.database.log_activity("daily_cleanup", "Daily cleanup completed")
            
        except Exception as e:
            logger.error(f"Error in daily cleanup: {e}")
            self.database.log_activity("daily_cleanup_failed", f"Error: {str(e)}", success=False)
    
    def run_backup(self):
        """Run database backup"""
        try:
            logger.info("Starting database backup...")
            
            backup_path = self.database.backup_database()
            
            logger.info(f"Database backup completed: {backup_path}")
            
        except Exception as e:
            logger.error(f"Error in database backup: {e}")
            self.database.log_activity("backup_failed", f"Error: {str(e)}", success=False)
    
    def cleanup_old_files(self, directory: str, days: int = 7):
        """Clean up old files in specified directory"""
        import os
        import glob
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            pattern = os.path.join(directory, "*")
            
            for file_path in glob.glob(pattern):
                if os.path.isfile(file_path):
                    file_date = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_date < cutoff_date:
                        os.remove(file_path)
                        logger.debug(f"Deleted old file: {file_path}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up {directory}: {e}")
    
    def update_job_statuses(self):
        """Update job statuses based on application results"""
        try:
            # Get jobs with pending applications older than 7 days
            # Mark them as timeout or no response
            
            # This is a placeholder for more complex status updates
            # You could add logic to:
            # - Check email for responses
            # - Update job statuses based on external factors
            # - Mark old applications as expired
            
            logger.info("Job statuses updated")
            
        except Exception as e:
            logger.error(f"Error updating job statuses: {e}")
    
    def get_daily_runs_count(self) -> int:
        """Get number of automation runs today"""
        try:
            activities = self.database.get_recent_activity(100)
            
            today = datetime.now().date()
            daily_runs = 0
            
            for activity in activities:
                activity_date = datetime.fromisoformat(activity['timestamp']).date()
                if activity_date == today and activity['action'] == 'automation_run_started':
                    daily_runs += 1
            
            return daily_runs
            
        except Exception as e:
            logger.error(f"Error getting daily runs count: {e}")
            return 0
    
    def generate_run_summary(self, results: List[Dict]):
        """Generate summary of automation run"""
        try:
            successful_applications = [r for r in results if r['status'] == 'success']
            failed_applications = [r for r in results if r['status'] == 'failed']
            
            summary = {
                'total_applications': len(results),
                'successful_applications': len(successful_applications),
                'failed_applications': len(failed_applications),
                'success_rate': (len(successful_applications) / len(results) * 100) if results else 0,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Run Summary: {summary}")
            
            # Store summary in database
            self.database.log_activity(
                "run_summary",
                f"Applied: {summary['total_applications']}, "
                f"Success: {summary['successful_applications']}, "
                f"Failed: {summary['failed_applications']}, "
                f"Success Rate: {summary['success_rate']:.1f}%"
            )
            
        except Exception as e:
            logger.error(f"Error generating run summary: {e}")
    
    def run_manual_search(self) -> List[Dict]:
        """Run manual job search (for testing/debugging)"""
        try:
            logger.info("Running manual job search...")
            jobs = self.search_jobs()
            logger.info(f"Manual search completed. Found {len(jobs)} jobs")
            return jobs
            
        except Exception as e:
            logger.error(f"Error in manual search: {e}")
            return []
    
    def run_manual_application(self, job_ids: List[int] = None) -> List[Dict]:
        """Run manual job application (for testing/debugging)"""
        try:
            logger.info("Running manual job application...")
            
            if job_ids:
                # Apply to specific jobs
                jobs = []
                for job_id in job_ids:
                    # Get job from database
                    # This would need to be implemented in database.py
                    pass
            else:
                # Apply to eligible jobs
                jobs = self.database.get_eligible_jobs(limit=5)
            
            results = self.apply_to_jobs(jobs)
            logger.info(f"Manual application completed. Applied to {len(results)} jobs")
            return results
            
        except Exception as e:
            logger.error(f"Error in manual application: {e}")
            return []
    
    def get_scheduler_status(self) -> Dict:
        """Get scheduler status information"""
        try:
            jobs = self.scheduler.get_jobs()
            
            status = {
                'is_running': self.is_running,
                'scheduled_jobs': len(jobs),
                'next_run': None,
                'last_run': None,
                'job_details': []
            }
            
            for job in jobs:
                job_info = {
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                }
                status['job_details'].append(job_info)
            
            # Get next run time
            if jobs:
                next_runs = [job.next_run_time for job in jobs if job.next_run_time]
                if next_runs:
                    status['next_run'] = min(next_runs).isoformat()
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
            return {'is_running': False, 'error': str(e)}
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
        
        # Close database connection
        if hasattr(self.database, 'close'):
            self.database.close()

# Convenience function for running scheduler
def run_scheduler(config_path: str = "config.json"):
    """Run the job automation scheduler"""
    with JobAutomationScheduler(config_path) as scheduler:
        scheduler.start()
        
        try:
            # Keep the scheduler running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            raise

if __name__ == "__main__":
    run_scheduler()