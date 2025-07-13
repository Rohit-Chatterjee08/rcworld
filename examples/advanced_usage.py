#!/usr/bin/env python3
"""
Advanced usage example for the job automation system.
"""

import time
from datetime import datetime, timedelta
from job_automation import JobAutomationSystem, Job, JobPriority
from job_automation.utils.decorators import job_task, retry_on_failure


# Example task functions
@job_task(name="Data Processing", priority=JobPriority.HIGH, tags=["data", "processing"])
def process_data(input_file: str, output_file: str):
    """Example data processing task."""
    print(f"Processing data from {input_file} to {output_file}")
    time.sleep(2)  # Simulate processing time
    return {"processed_records": 1000, "status": "completed"}


@job_task(name="Email Notification", priority=JobPriority.NORMAL, tags=["notification"])
@retry_on_failure(max_retries=3, delay=1.0)
def send_notification(recipient: str, message: str):
    """Example notification task."""
    print(f"Sending notification to {recipient}: {message}")
    # Simulate potential failure
    import random
    if random.random() < 0.3:  # 30% chance of failure
        raise Exception("Network error")
    return {"sent": True, "recipient": recipient}


def main():
    """Demonstrate advanced usage of the job automation system."""
    print("Job Automation System - Advanced Usage Example")
    print("=" * 55)
    
    # Create system with custom configuration
    system = JobAutomationSystem()
    
    try:
        system.start()
        print("✅ Job automation system started")
        
        # 1. Batch job processing
        print("\n📦 Creating batch jobs...")
        batch_jobs = []
        
        for i in range(5):
            job = system.create_job(
                name=f"Batch Job {i+1}",
                command=f"echo 'Processing batch item {i+1}' && sleep 1",
                priority=JobPriority.NORMAL,
                tags=["batch", f"item-{i+1}"],
                metadata={"batch_id": "batch_001", "item_number": i+1}
            )
            batch_jobs.append(job)
        
        # Submit batch jobs
        batch_job_ids = []
        for job in batch_jobs:
            job_id = system.submit_job(job)
            batch_job_ids.append(job_id)
            print(f"   Submitted batch job: {job.name} (ID: {job_id})")
        
        # 2. Priority-based job scheduling
        print("\n🏃 Creating priority jobs...")
        
        # Low priority job
        low_job = system.create_job(
            name="Low Priority Cleanup",
            command="echo 'Cleaning up temporary files...' && sleep 2",
            priority=JobPriority.LOW,
            tags=["cleanup", "maintenance"]
        )
        
        # High priority job
        high_job = system.create_job(
            name="High Priority Alert",
            command="echo 'URGENT: System alert detected!'",
            priority=JobPriority.HIGH,
            tags=["alert", "urgent"]
        )
        
        # Urgent job
        urgent_job = system.create_job(
            name="Emergency Response",
            command="echo 'EMERGENCY: Immediate action required!'",
            priority=JobPriority.URGENT,
            tags=["emergency", "critical"]
        )
        
        # Submit priority jobs (in reverse order to test priority queue)
        low_job_id = system.submit_job(low_job)
        high_job_id = system.submit_job(high_job)
        urgent_job_id = system.submit_job(urgent_job)
        
        print(f"   Low priority job: {low_job_id}")
        print(f"   High priority job: {high_job_id}")
        print(f"   Urgent job: {urgent_job_id}")
        
        # 3. Complex scheduling scenarios
        print("\n📅 Setting up complex schedules...")
        
        # Schedule job for specific time (1 minute from now)
        future_time = datetime.now() + timedelta(minutes=1)
        scheduled_job = system.create_job(
            name="Scheduled Report",
            command="echo 'Generating scheduled report...'",
            tags=["report", "scheduled"]
        )
        scheduled_job_id = system.schedule_job(scheduled_job, future_time)
        print(f"   Scheduled job for {future_time}: {scheduled_job_id}")
        
        # Recurring job (every 30 seconds)
        recurring_job = system.create_job(
            name="Health Check",
            command="echo 'Health check: System is running normally'",
            tags=["health", "monitoring"]
        )
        recurring_job_id = system.schedule_recurring_job(recurring_job, "*/30 * * * * *")
        print(f"   Recurring health check: {recurring_job_id}")
        
        # 4. Job monitoring and management
        print("\n🔍 Monitoring job execution...")
        
        # Wait for some jobs to complete
        time.sleep(5)
        
        # Get running jobs
        running_jobs = system.get_running_jobs()
        print(f"   Currently running jobs: {len(running_jobs)}")
        
        # Check specific job status
        if batch_job_ids:
            first_job = system.get_job(batch_job_ids[0])
            if first_job:
                print(f"   First batch job status: {first_job.status.value}")
        
        # 5. Job filtering and statistics
        print("\n📊 Job analytics...")
        
        # Get jobs by status
        completed_jobs = system.get_jobs(status=None, limit=10)
        print(f"   Recent jobs: {len(completed_jobs)}")
        
        # Get statistics
        stats = system.get_job_statistics()
        print(f"   Queue size: {stats['queue']['current_size']}")
        print(f"   Completed jobs: {stats['storage']['completed_jobs']}")
        print(f"   Failed jobs: {stats['storage']['failed_jobs']}")
        
        # 6. Error handling and recovery
        print("\n🛠️ Testing error handling...")
        
        # Create a job that will fail
        failing_job = system.create_job(
            name="Failing Job",
            command="exit 1",  # This will fail
            max_retries=2,
            tags=["test", "failure"]
        )
        failing_job_id = system.submit_job(failing_job)
        print(f"   Submitted failing job: {failing_job_id}")
        
        # Wait for it to fail and retry
        time.sleep(3)
        
        # Check the failed job
        failed_job = system.get_job(failing_job_id)
        if failed_job:
            print(f"   Failed job status: {failed_job.status.value}")
            print(f"   Retry count: {failed_job.retry_count}")
        
        # 7. System health and maintenance
        print("\n🏥 System health check...")
        health = system.health_check()
        print(f"   System status: {health['status']}")
        
        for component, status in health['components'].items():
            status_icon = "✅" if status else "❌"
            print(f"   {component}: {status_icon}")
        
        # 8. Cleanup demonstration
        print("\n🧹 Demonstrating cleanup...")
        
        # Clean up old jobs (keeping recent ones)
        cleaned_count = system.cleanup_old_jobs(older_than_days=0)  # Clean all for demo
        print(f"   Cleaned up {cleaned_count} old jobs")
        
        # Cancel recurring job
        system.cancel_job(recurring_job_id)
        print("   Cancelled recurring job")
        
        # Final statistics
        print("\n📈 Final Statistics:")
        final_stats = system.get_job_statistics()
        print(f"   Total jobs processed: {final_stats['storage']['total_jobs']}")
        print(f"   Success rate: {final_stats['storage']['completed_jobs'] / max(1, final_stats['storage']['total_jobs']) * 100:.1f}%")
        
        print("\n✅ Advanced example completed successfully!")
        
    finally:
        system.shutdown()
        print("🔄 Job automation system shut down")


if __name__ == "__main__":
    main()