"""
Main application file for job automation tool
Provides CLI interface and orchestrates all components
"""

import argparse
import sys
import logging
from typing import Dict, List
from database import JobDatabase
from search import JobSearcher
from apply import JobApplicator
from scheduler import JobAutomationScheduler
from utils import load_config, validate_config, setup_logging

logger = logging.getLogger(__name__)

class JobAutomationTool:
    """Main application class"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the job automation tool"""
        self.config_path = config_path
        self.config = load_config(config_path)
        
        # Setup logging
        setup_logging(self.config)
        
        # Validate configuration
        if not validate_config(self.config):
            logger.error("Invalid configuration. Please check config.json")
            sys.exit(1)
        
        # Initialize components
        self.database = JobDatabase(self.config.get('database', {}).get('path', 'data/jobs.db'))
        self.searcher = None
        self.applicator = None
        self.scheduler = None
        
        logger.info("Job automation tool initialized successfully")
    
    def search_jobs(self) -> List[Dict]:
        """Search for jobs across all portals"""
        try:
            logger.info("Starting job search...")
            
            if not self.searcher:
                self.searcher = JobSearcher(self.config, self.database)
            
            jobs = self.searcher.search_all_portals()
            
            logger.info(f"Job search completed. Found {len(jobs)} eligible jobs")
            return jobs
            
        except Exception as e:
            logger.error(f"Error searching jobs: {e}")
            return []
        finally:
            if self.searcher:
                self.searcher.close()
    
    def apply_to_jobs(self, jobs: List[Dict] = None) -> List[Dict]:
        """Apply to jobs"""
        try:
            logger.info("Starting job applications...")
            
            if not self.applicator:
                self.applicator = JobApplicator(self.config, self.database)
            
            # If no jobs provided, get eligible jobs from database
            if jobs is None:
                jobs = self.database.get_eligible_jobs(limit=20)
            
            if not jobs:
                logger.info("No eligible jobs found for application")
                return []
            
            results = self.applicator.apply_to_jobs(jobs)
            
            logger.info(f"Job applications completed. Applied to {len(results)} jobs")
            return results
            
        except Exception as e:
            logger.error(f"Error applying to jobs: {e}")
            return []
        finally:
            if self.applicator:
                self.applicator.close()
    
    def run_full_automation(self):
        """Run complete job automation pipeline"""
        try:
            logger.info("Starting full job automation pipeline...")
            
            # Step 1: Search for jobs
            jobs = self.search_jobs()
            
            if not jobs:
                logger.info("No eligible jobs found. Exiting.")
                return
            
            # Step 2: Apply to jobs
            results = self.apply_to_jobs(jobs)
            
            # Step 3: Display results
            self.display_results(results)
            
            logger.info("Full job automation pipeline completed")
            
        except Exception as e:
            logger.error(f"Error in full automation: {e}")
    
    def start_scheduler(self):
        """Start the job scheduler"""
        try:
            logger.info("Starting job automation scheduler...")
            
            if not self.scheduler:
                self.scheduler = JobAutomationScheduler(self.config_path)
            
            self.scheduler.start()
            
            # Keep running
            logger.info("Scheduler started. Press Ctrl+C to stop.")
            
            try:
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Stopping scheduler...")
                self.scheduler.stop()
                logger.info("Scheduler stopped")
                
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            if self.scheduler:
                self.scheduler.stop()
    
    def display_results(self, results: List[Dict]):
        """Display application results"""
        if not results:
            print("No applications were submitted.")
            return
        
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'failed']
        
        print(f"\n{'='*50}")
        print(f"APPLICATION RESULTS")
        print(f"{'='*50}")
        print(f"Total Applications: {len(results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        print(f"Success Rate: {(len(successful) / len(results) * 100):.1f}%")
        print(f"{'='*50}")
        
        if successful:
            print("\nSUCCESSFUL APPLICATIONS:")
            for result in successful:
                job = result['job']
                print(f"✓ {job['title']} at {job['company']} ({job['portal']})")
        
        if failed:
            print("\nFAILED APPLICATIONS:")
            for result in failed:
                job = result['job']
                error = result.get('error', 'Unknown error')
                print(f"✗ {job['title']} at {job['company']} ({job['portal']}) - {error}")
    
    def show_stats(self):
        """Show application statistics"""
        try:
            stats = self.database.get_application_stats()
            
            print(f"\n{'='*50}")
            print(f"APPLICATION STATISTICS")
            print(f"{'='*50}")
            print(f"Total Applications: {stats['total_applications']}")
            print(f"Today's Applications: {stats['today_applications']}")
            print(f"Success Rate: {stats['success_rate']:.1f}%")
            print(f"{'='*50}")
            
            if stats['status_breakdown']:
                print("\nSTATUS BREAKDOWN:")
                for status, count in stats['status_breakdown'].items():
                    print(f"  {status.title()}: {count}")
            
        except Exception as e:
            logger.error(f"Error showing stats: {e}")
    
    def show_recent_activity(self, limit: int = 10):
        """Show recent activity"""
        try:
            activities = self.database.get_recent_activity(limit)
            
            print(f"\n{'='*50}")
            print(f"RECENT ACTIVITY (Last {limit})")
            print(f"{'='*50}")
            
            for activity in activities:
                timestamp = activity['timestamp']
                action = activity['action']
                details = activity['details']
                status = "✓" if activity['success'] else "✗"
                
                print(f"{status} {timestamp} - {action}")
                if details:
                    print(f"    {details}")
            
        except Exception as e:
            logger.error(f"Error showing recent activity: {e}")
    
    def test_configuration(self):
        """Test configuration and connections"""
        try:
            print(f"\n{'='*50}")
            print(f"CONFIGURATION TEST")
            print(f"{'='*50}")
            
            # Test database connection
            try:
                stats = self.database.get_application_stats()
                print("✓ Database connection: OK")
            except Exception as e:
                print(f"✗ Database connection: FAILED - {e}")
            
            # Test resume file
            resume_path = self.config.get('user_info', {}).get('resume_path', '')
            if resume_path:
                import os
                if os.path.exists(resume_path):
                    print(f"✓ Resume file: OK ({resume_path})")
                else:
                    print(f"✗ Resume file: NOT FOUND ({resume_path})")
            else:
                print("⚠ Resume file: NOT CONFIGURED")
            
            # Test user info
            user_info = self.config.get('user_info', {})
            required_fields = ['name', 'email', 'phone']
            
            for field in required_fields:
                if user_info.get(field):
                    print(f"✓ User {field}: OK")
                else:
                    print(f"✗ User {field}: MISSING")
            
            # Test job portals
            portals = self.config.get('job_portals', {})
            enabled_portals = [name for name, config in portals.items() if config.get('enabled', False)]
            
            if enabled_portals:
                print(f"✓ Job portals: {len(enabled_portals)} enabled ({', '.join(enabled_portals)})")
            else:
                print("✗ Job portals: NONE ENABLED")
            
            print(f"{'='*50}")
            
        except Exception as e:
            logger.error(f"Error testing configuration: {e}")
    
    def setup_user_info(self):
        """Interactive setup for user information"""
        try:
            print(f"\n{'='*50}")
            print(f"USER INFORMATION SETUP")
            print(f"{'='*50}")
            
            user_info = self.config.get('user_info', {})
            
            # Get user information
            name = input(f"Full Name [{user_info.get('name', '')}]: ").strip()
            if name:
                user_info['name'] = name
            
            email = input(f"Email [{user_info.get('email', '')}]: ").strip()
            if email:
                user_info['email'] = email
            
            phone = input(f"Phone [{user_info.get('phone', '')}]: ").strip()
            if phone:
                user_info['phone'] = phone
            
            location = input(f"Location [{user_info.get('location', '')}]: ").strip()
            if location:
                user_info['location'] = location
            
            experience = input(f"Experience (years) [{user_info.get('experience_years', '')}]: ").strip()
            if experience:
                try:
                    user_info['experience_years'] = int(experience)
                except ValueError:
                    print("Invalid experience value. Using default.")
            
            resume_path = input(f"Resume Path [{user_info.get('resume_path', '')}]: ").strip()
            if resume_path:
                import os
                if os.path.exists(resume_path):
                    user_info['resume_path'] = resume_path
                    print("✓ Resume file found")
                else:
                    print("✗ Resume file not found. Please check the path.")
            
            # Save configuration
            self.config['user_info'] = user_info
            
            from utils import save_config
            save_config(self.config, self.config_path)
            
            print("✓ User information saved successfully")
            
        except Exception as e:
            logger.error(f"Error setting up user info: {e}")
    
    def backup_database(self):
        """Create database backup"""
        try:
            backup_path = self.database.backup_database()
            print(f"✓ Database backup created: {backup_path}")
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.searcher:
                self.searcher.close()
            if self.applicator:
                self.applicator.close()
            if self.scheduler:
                self.scheduler.stop()
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Job Automation Tool")
    parser.add_argument("--config", default="config.json", help="Configuration file path")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for jobs')
    
    # Apply command
    apply_parser = subparsers.add_parser('apply', help='Apply to jobs')
    
    # Run command (full automation)
    run_parser = subparsers.add_parser('run', help='Run full automation pipeline')
    
    # Scheduler command
    scheduler_parser = subparsers.add_parser('scheduler', help='Start job scheduler')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show application statistics')
    
    # Activity command
    activity_parser = subparsers.add_parser('activity', help='Show recent activity')
    activity_parser.add_argument('--limit', type=int, default=10, help='Number of activities to show')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test configuration')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup user information')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create database backup')
    
    args = parser.parse_args()
    
    # Show help if no command provided
    if not args.command:
        parser.print_help()
        return
    
    # Initialize tool
    try:
        tool = JobAutomationTool(args.config)
        
        # Execute command
        if args.command == 'search':
            tool.search_jobs()
        elif args.command == 'apply':
            tool.apply_to_jobs()
        elif args.command == 'run':
            tool.run_full_automation()
        elif args.command == 'scheduler':
            tool.start_scheduler()
        elif args.command == 'stats':
            tool.show_stats()
        elif args.command == 'activity':
            tool.show_recent_activity(args.limit)
        elif args.command == 'test':
            tool.test_configuration()
        elif args.command == 'setup':
            tool.setup_user_info()
        elif args.command == 'backup':
            tool.backup_database()
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        logger.info("Operation cancelled by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        try:
            tool.cleanup()
        except:
            pass

if __name__ == "__main__":
    main()