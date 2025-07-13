#!/usr/bin/env python3
"""
Basic usage example for the job automation system.
"""

import time
from datetime import datetime, timedelta
from job_automation import JobAutomationSystem, Job, JobPriority


def main():
    """Demonstrate basic usage of the job automation system."""
    print("Job Automation System - Basic Usage Example")
    print("=" * 50)
    
    # Create and start the automation system
    with JobAutomationSystem() as system:
        print("✅ Job automation system started")
        
        # Create some example jobs
        
        # 1. Simple shell command
        job1 = system.create_job(
            name="List Files",
            command="ls -la",
            priority=JobPriority.NORMAL,
            tags=["example", "shell"]
        )
        
        # 2. Python script execution
        job2 = system.create_job(
            name="Python Hello World",
            command="python:-c print('Hello from Python job!')",
            priority=JobPriority.HIGH,
            tags=["example", "python"]
        )
        
        # 3. HTTP request job
        job3 = system.create_job(
            name="HTTP Health Check",
            command="http:https://httpbin.org/status/200",
            parameters={
                "method": "GET",
                "headers": {"User-Agent": "JobAutomation/1.0"}
            },
            priority=JobPriority.LOW,
            tags=["example", "http"]
        )
        
        # Submit immediate jobs
        print("\n📤 Submitting immediate jobs...")
        job1_id = system.submit_job(job1)
        job2_id = system.submit_job(job2)
        job3_id = system.submit_job(job3)
        
        print(f"   Job 1 ID: {job1_id}")
        print(f"   Job 2 ID: {job2_id}")
        print(f"   Job 3 ID: {job3_id}")
        
        # Schedule a delayed job
        print("\n⏰ Scheduling delayed job...")
        delayed_job = system.create_job(
            name="Delayed Echo",
            command="echo 'This is a delayed job!'",
            tags=["example", "delayed"]
        )
        delayed_job_id = system.schedule_delayed_job(delayed_job, delay_seconds=5)
        print(f"   Delayed job ID: {delayed_job_id}")
        
        # Schedule a recurring job (every 10 seconds)
        print("\n🔄 Scheduling recurring job...")
        recurring_job = system.create_job(
            name="Recurring Status",
            command="echo 'Recurring job running at $(date)'",
            tags=["example", "recurring"]
        )
        recurring_job_id = system.schedule_recurring_job(recurring_job, "*/10 * * * * *")
        print(f"   Recurring job ID: {recurring_job_id}")
        
        # Wait for jobs to complete
        print("\n⏳ Waiting for jobs to complete...")
        time.sleep(8)
        
        # Show job statistics
        print("\n📊 Job Statistics:")
        stats = system.get_job_statistics()
        
        print(f"   Total jobs: {stats['storage']['total_jobs']}")
        print(f"   Completed: {stats['storage']['completed_jobs']}")
        print(f"   Failed: {stats['storage']['failed_jobs']}")
        print(f"   Running: {stats['storage']['running_jobs']}")
        
        # List all jobs
        print("\n📋 All Jobs:")
        all_jobs = system.get_jobs()
        for job in all_jobs:
            print(f"   • {job.name} - {job.status.value} - {job.priority.value} priority")
        
        # Show system health
        print("\n🏥 System Health:")
        health = system.health_check()
        print(f"   Status: {health['status']}")
        
        # Cancel the recurring job
        print("\n🛑 Cancelling recurring job...")
        system.cancel_job(recurring_job_id)
        
        print("\n✅ Example completed successfully!")


if __name__ == "__main__":
    main()