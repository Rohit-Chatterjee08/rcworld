"""
Command-line interface for job automation system.
"""

import argparse
import sys
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..automation_system import JobAutomationSystem
from ..core.job import Job, JobStatus, JobPriority
from ..core.config import Config
from .helpers import format_duration, format_job_summary, parse_duration


class JobAutomationCLI:
    """
    Command-line interface for the job automation system.
    """

    def __init__(self, system: Optional[JobAutomationSystem] = None):
        """
        Initialize CLI.
        
        Args:
            system: JobAutomationSystem instance
        """
        self.system = system or JobAutomationSystem()

    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Run the CLI with given arguments.
        
        Args:
            args: Command line arguments (defaults to sys.argv[1:])
            
        Returns:
            Exit code
        """
        parser = self._create_parser()
        parsed_args = parser.parse_args(args)
        
        try:
            return parsed_args.func(parsed_args)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser."""
        parser = argparse.ArgumentParser(
            description="Job Automation System CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Start command
        start_parser = subparsers.add_parser('start', help='Start the job automation system')
        start_parser.add_argument('--daemon', action='store_true', help='Run as daemon')
        start_parser.set_defaults(func=self.cmd_start)
        
        # Submit command
        submit_parser = subparsers.add_parser('submit', help='Submit a job')
        submit_parser.add_argument('name', help='Job name')
        submit_parser.add_argument('command', help='Command to execute')
        submit_parser.add_argument('--priority', choices=['low', 'normal', 'high', 'urgent'], 
                                 default='normal', help='Job priority')
        submit_parser.add_argument('--timeout', type=int, help='Job timeout in seconds')
        submit_parser.add_argument('--retries', type=int, default=3, help='Maximum retries')
        submit_parser.add_argument('--tags', nargs='*', help='Job tags')
        submit_parser.add_argument('--params', help='Job parameters (JSON string)')
        submit_parser.set_defaults(func=self.cmd_submit)
        
        # Schedule command
        schedule_parser = subparsers.add_parser('schedule', help='Schedule a job')
        schedule_parser.add_argument('name', help='Job name')
        schedule_parser.add_argument('command', help='Command to execute')
        schedule_parser.add_argument('--cron', help='Cron expression for recurring jobs')
        schedule_parser.add_argument('--delay', help='Delay before execution (e.g., 1h, 30m, 120s)')
        schedule_parser.add_argument('--at', help='Specific time to run (ISO format)')
        schedule_parser.add_argument('--priority', choices=['low', 'normal', 'high', 'urgent'], 
                                   default='normal', help='Job priority')
        schedule_parser.set_defaults(func=self.cmd_schedule)
        
        # List command
        list_parser = subparsers.add_parser('list', help='List jobs')
        list_parser.add_argument('--status', choices=['pending', 'running', 'completed', 'failed', 'cancelled'],
                               help='Filter by status')
        list_parser.add_argument('--limit', type=int, help='Limit number of results')
        list_parser.add_argument('--format', choices=['table', 'json'], default='table',
                               help='Output format')
        list_parser.set_defaults(func=self.cmd_list)
        
        # Status command
        status_parser = subparsers.add_parser('status', help='Get job status')
        status_parser.add_argument('job_id', help='Job ID')
        status_parser.set_defaults(func=self.cmd_status)
        
        # Cancel command
        cancel_parser = subparsers.add_parser('cancel', help='Cancel a job')
        cancel_parser.add_argument('job_id', help='Job ID')
        cancel_parser.set_defaults(func=self.cmd_cancel)
        
        # Stats command
        stats_parser = subparsers.add_parser('stats', help='Show system statistics')
        stats_parser.set_defaults(func=self.cmd_stats)
        
        # Health command
        health_parser = subparsers.add_parser('health', help='Check system health')
        health_parser.set_defaults(func=self.cmd_health)
        
        # Cleanup command
        cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old jobs')
        cleanup_parser.add_argument('--days', type=int, default=30, 
                                  help='Remove jobs older than N days')
        cleanup_parser.set_defaults(func=self.cmd_cleanup)
        
        # Config command
        config_parser = subparsers.add_parser('config', help='Manage configuration')
        config_parser.add_argument('--create-default', action='store_true',
                                 help='Create default configuration file')
        config_parser.add_argument('--show', action='store_true',
                                 help='Show current configuration')
        config_parser.set_defaults(func=self.cmd_config)
        
        return parser

    def cmd_start(self, args) -> int:
        """Start the job automation system."""
        print("Starting job automation system...")
        
        self.system.start()
        
        if args.daemon:
            print("Running as daemon. Press Ctrl+C to stop.")
            try:
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutting down...")
                self.system.shutdown()
        else:
            print("Job automation system started successfully.")
        
        return 0

    def cmd_submit(self, args) -> int:
        """Submit a job."""
        priority_map = {
            'low': JobPriority.LOW,
            'normal': JobPriority.NORMAL,
            'high': JobPriority.HIGH,
            'urgent': JobPriority.URGENT
        }
        
        parameters = {}
        if args.params:
            try:
                parameters = json.loads(args.params)
            except json.JSONDecodeError:
                print("Error: Invalid JSON in parameters", file=sys.stderr)
                return 1
        
        job = self.system.create_job(
            name=args.name,
            command=args.command,
            priority=priority_map[args.priority],
            timeout=args.timeout,
            max_retries=args.retries,
            tags=args.tags or [],
            parameters=parameters
        )
        
        job_id = self.system.submit_job(job)
        print(f"Job submitted with ID: {job_id}")
        
        return 0

    def cmd_schedule(self, args) -> int:
        """Schedule a job."""
        priority_map = {
            'low': JobPriority.LOW,
            'normal': JobPriority.NORMAL,
            'high': JobPriority.HIGH,
            'urgent': JobPriority.URGENT
        }
        
        job = self.system.create_job(
            name=args.name,
            command=args.command,
            priority=priority_map[args.priority]
        )
        
        if args.cron:
            job_id = self.system.schedule_recurring_job(job, args.cron)
            print(f"Recurring job scheduled with ID: {job_id}")
        elif args.delay:
            try:
                delay_seconds = parse_duration(args.delay)
                job_id = self.system.schedule_delayed_job(job, delay_seconds)
                print(f"Delayed job scheduled with ID: {job_id}")
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                return 1
        elif args.at:
            try:
                run_at = datetime.fromisoformat(args.at)
                job_id = self.system.schedule_job(job, run_at)
                print(f"Job scheduled with ID: {job_id}")
            except ValueError:
                print("Error: Invalid datetime format", file=sys.stderr)
                return 1
        else:
            print("Error: Must specify --cron, --delay, or --at", file=sys.stderr)
            return 1
        
        return 0

    def cmd_list(self, args) -> int:
        """List jobs."""
        status_map = {
            'pending': JobStatus.PENDING,
            'running': JobStatus.RUNNING,
            'completed': JobStatus.COMPLETED,
            'failed': JobStatus.FAILED,
            'cancelled': JobStatus.CANCELLED
        }
        
        status_filter = status_map.get(args.status) if args.status else None
        jobs = self.system.get_jobs(status=status_filter, limit=args.limit)
        
        if args.format == 'json':
            job_data = [job.to_dict() for job in jobs]
            print(json.dumps(job_data, indent=2))
        else:
            if not jobs:
                print("No jobs found.")
            else:
                print(f"Found {len(jobs)} jobs:")
                for job in jobs:
                    print(f"  {format_job_summary(job)}")
        
        return 0

    def cmd_status(self, args) -> int:
        """Get job status."""
        job = self.system.get_job(args.job_id)
        
        if not job:
            print(f"Job {args.job_id} not found.", file=sys.stderr)
            return 1
        
        print(f"Job Status: {job.name} ({job.id})")
        print(f"  Status: {job.status.value}")
        print(f"  Priority: {job.priority.value}")
        print(f"  Command: {job.command}")
        print(f"  Created: {job.created_at}")
        print(f"  Scheduled: {job.scheduled_at}")
        
        if job.started_at:
            print(f"  Started: {job.started_at}")
        
        if job.completed_at:
            print(f"  Completed: {job.completed_at}")
        
        if job.error_message:
            print(f"  Error: {job.error_message}")
        
        print(f"  Retries: {job.retry_count}/{job.max_retries}")
        
        if job.tags:
            print(f"  Tags: {', '.join(job.tags)}")
        
        return 0

    def cmd_cancel(self, args) -> int:
        """Cancel a job."""
        if self.system.cancel_job(args.job_id):
            print(f"Job {args.job_id} cancelled.")
        else:
            print(f"Job {args.job_id} not found or could not be cancelled.", file=sys.stderr)
            return 1
        
        return 0

    def cmd_stats(self, args) -> int:
        """Show system statistics."""
        stats = self.system.get_job_statistics()
        
        print("Job Automation System Statistics")
        print("=" * 40)
        
        # System stats
        system_stats = stats['system']
        uptime = format_duration(system_stats['uptime_seconds'])
        print(f"System Uptime: {uptime}")
        print(f"System Status: {'Running' if system_stats['is_running'] else 'Stopped'}")
        
        # Storage stats
        storage_stats = stats['storage']
        print(f"\nStorage Statistics:")
        print(f"  Total Jobs: {storage_stats['total_jobs']}")
        print(f"  Pending: {storage_stats['pending_jobs']}")
        print(f"  Running: {storage_stats['running_jobs']}")
        print(f"  Completed: {storage_stats['completed_jobs']}")
        print(f"  Failed: {storage_stats['failed_jobs']}")
        print(f"  Cancelled: {storage_stats['cancelled_jobs']}")
        
        # Queue stats
        queue_stats = stats['queue']
        print(f"\nQueue Statistics:")
        print(f"  Current Size: {queue_stats['current_size']}")
        print(f"  Total Added: {queue_stats['total_added']}")
        print(f"  Total Retrieved: {queue_stats['total_retrieved']}")
        
        # Executor stats
        executor_stats = stats['executor']
        print(f"\nExecutor Statistics:")
        print(f"  Max Workers: {executor_stats['max_workers']}")
        print(f"  Running Jobs: {executor_stats['running_jobs']}")
        print(f"  Completed Jobs: {executor_stats['jobs_completed']}")
        print(f"  Failed Jobs: {executor_stats['jobs_failed']}")
        
        return 0

    def cmd_health(self, args) -> int:
        """Check system health."""
        health = self.system.health_check()
        
        print(f"System Health: {health['status'].upper()}")
        print(f"Timestamp: {health['timestamp']}")
        
        print("\nComponent Status:")
        for component, status in health['components'].items():
            status_icon = "✅" if status else "❌"
            print(f"  {component}: {status_icon}")
        
        if 'warning' in health:
            print(f"\nWarning: {health['warning']}")
        
        return 0 if health['status'] == 'healthy' else 1

    def cmd_cleanup(self, args) -> int:
        """Clean up old jobs."""
        count = self.system.cleanup_old_jobs(args.days)
        print(f"Cleaned up {count} old jobs (older than {args.days} days).")
        
        return 0

    def cmd_config(self, args) -> int:
        """Manage configuration."""
        if args.create_default:
            config_path = self.system.config.create_default_config()
            print(f"Default configuration created at: {config_path}")
        elif args.show:
            print("Current Configuration:")
            print(str(self.system.config))
        else:
            print("Use --create-default or --show")
            return 1
        
        return 0


def main():
    """Main CLI entry point."""
    cli = JobAutomationCLI()
    sys.exit(cli.run())