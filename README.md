# Job Automation System

A comprehensive Python-based job automation system for scheduling, executing, and monitoring automated tasks with support for priorities, retries, and multiple execution backends.

## Features

- **Job Scheduling**: Schedule jobs to run immediately, at specific times, or on recurring schedules using cron expressions
- **Priority Queue**: Jobs are executed based on priority levels (LOW, NORMAL, HIGH, URGENT)
- **Multiple Execution Backends**: Support for shell commands, Python functions, and HTTP requests
- **Retry Logic**: Automatic retry with configurable attempts and backoff strategies
- **Persistent Storage**: Jobs and results are stored in SQLite or file-based storage
- **Monitoring & Logging**: Comprehensive logging and job status tracking
- **Web API**: RESTful API for job management (optional)
- **CLI Interface**: Command-line interface for easy job management
- **Configuration Management**: Flexible configuration via files or environment variables

## Installation

```bash
pip install job-automation
```

Or install from source:

```bash
git clone https://github.com/example/job-automation.git
cd job-automation
pip install -e .
```

## Quick Start

### Basic Usage

```python
from job_automation import JobAutomationSystem, JobPriority

# Create and start the system
system = JobAutomationSystem()
system.start()

# Create a simple job
job = system.create_job(
    name="Hello World",
    command="echo 'Hello, World!'",
    priority=JobPriority.NORMAL
)

# Submit the job
job_id = system.submit_job(job)
print(f"Job submitted with ID: {job_id}")

# Check job status
job_status = system.get_job(job_id)
print(f"Job status: {job_status.status}")

# Shutdown the system
system.shutdown()
```

### Using Context Manager

```python
from job_automation import JobAutomationSystem

with JobAutomationSystem() as system:
    # Create and submit jobs
    job = system.create_job(
        name="Data Processing",
        command="python:mymodule.process_data",
        parameters={"input_file": "data.csv", "output_file": "result.json"}
    )
    
    job_id = system.submit_job(job)
    
    # System will automatically shutdown when exiting context
```

### Scheduling Jobs

```python
from datetime import datetime, timedelta
from job_automation import JobAutomationSystem

with JobAutomationSystem() as system:
    # Schedule a job to run in 1 hour
    future_time = datetime.now() + timedelta(hours=1)
    job = system.create_job(name="Hourly Report", command="python:reports.generate_hourly")
    system.schedule_job(job, future_time)
    
    # Schedule a recurring job (every day at 9 AM)
    daily_job = system.create_job(name="Daily Backup", command="./backup.sh")
    system.schedule_recurring_job(daily_job, "0 9 * * *")
```

## Command Line Interface

The system includes a comprehensive CLI:

```bash
# Start the system
job-automation start --daemon

# Submit a job
job-automation submit "My Job" "echo 'Hello World'" --priority high

# Schedule a job
job-automation schedule "Daily Report" "python:reports.daily" --cron "0 9 * * *"

# List jobs
job-automation list --status running

# Get job status
job-automation status JOB_ID

# Cancel a job
job-automation cancel JOB_ID

# View system statistics
job-automation stats

# Check system health
job-automation health
```

## Configuration

Create a configuration file (`config.yaml`):

```yaml
database:
  type: sqlite
  database: jobs.db

executor:
  max_workers: 4
  job_timeout: 3600
  max_retries: 3

scheduler:
  enabled: true
  check_interval: 1

logging:
  level: INFO
  file_path: logs/job_automation.log
  max_file_size: 10485760  # 10MB
  backup_count: 5

api:
  enabled: true
  host: 0.0.0.0
  port: 8080
```

Or use environment variables:

```bash
export JOB_EXECUTOR_MAX_WORKERS=8
export JOB_LOG_LEVEL=DEBUG
export JOB_DB_TYPE=sqlite
```

## Job Types

### Shell Commands

```python
job = system.create_job(
    name="System Check",
    command="df -h && free -m",
    timeout=30
)
```

### Python Functions

```python
job = system.create_job(
    name="Data Processing",
    command="python:mymodule.process_data",
    parameters={"input": "data.csv", "output": "results.json"}
)
```

### HTTP Requests

```python
job = system.create_job(
    name="API Health Check",
    command="http:https://api.example.com/health",
    parameters={
        "method": "GET",
        "headers": {"Authorization": "Bearer token"}
    }
)
```

## Job Decorators

Use decorators to mark functions as job tasks:

```python
from job_automation.utils.decorators import job_task, retry_on_failure

@job_task(name="Data Processing", priority=JobPriority.HIGH, tags=["data"])
@retry_on_failure(max_retries=3, delay=1.0)
def process_data(input_file: str, output_file: str):
    # Your processing logic here
    pass
```

## Monitoring and Logging

### Job Statistics

```python
stats = system.get_job_statistics()
print(f"Total jobs: {stats['storage']['total_jobs']}")
print(f"Completed: {stats['storage']['completed_jobs']}")
print(f"Failed: {stats['storage']['failed_jobs']}")
```

### System Health

```python
health = system.health_check()
print(f"System status: {health['status']}")
print(f"Components: {health['components']}")
```

### Logging

The system provides comprehensive logging:

```python
from job_automation.core.logger import Logger

logger = Logger(
    name="my_app",
    level="INFO",
    file_path="logs/app.log"
)

logger.info("Application started")
logger.error("Something went wrong")
```

## Storage Backends

### SQLite (Default)

```python
from job_automation.core.storage import SQLiteStorageBackend

backend = SQLiteStorageBackend(db_path="jobs.db")
storage = JobStorage(backend=backend)
```

### File-based Storage

```python
from job_automation.core.storage import FileStorageBackend

backend = FileStorageBackend(storage_dir="job_storage")
storage = JobStorage(backend=backend)
```

## Advanced Features

### Job Priorities

Jobs are executed based on priority:

- `JobPriority.URGENT`: Highest priority
- `JobPriority.HIGH`: High priority
- `JobPriority.NORMAL`: Normal priority (default)
- `JobPriority.LOW`: Lowest priority

### Retry Logic

Configure automatic retries:

```python
job = system.create_job(
    name="Unreliable Task",
    command="python:unreliable_task.py",
    max_retries=5
)
```

### Job Tags and Metadata

Organize jobs with tags and metadata:

```python
job = system.create_job(
    name="Report Generation",
    command="python:reports.generate",
    tags=["report", "daily", "important"],
    metadata={"department": "sales", "format": "pdf"}
)
```

## API Reference

### Core Classes

- `JobAutomationSystem`: Main orchestrator class
- `Job`: Represents a job with all its properties
- `JobQueue`: Priority-based job queue
- `JobScheduler`: Handles job scheduling
- `TaskExecutor`: Executes jobs with configurable concurrency
- `JobStorage`: Handles job persistence

### Enums

- `JobStatus`: Job execution status (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)
- `JobPriority`: Job priority levels (LOW, NORMAL, HIGH, URGENT)

## Examples

See the `examples/` directory for more comprehensive examples:

- `basic_usage.py`: Basic system usage
- `advanced_usage.py`: Advanced features demonstration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:

- GitHub Issues: https://github.com/example/job-automation/issues
- Documentation: https://job-automation.readthedocs.io/
- Email: support@jobautomation.com

---

**Job Automation System** - Simplify your automation workflows with powerful scheduling and execution capabilities.