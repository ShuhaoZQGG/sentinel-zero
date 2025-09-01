# SentinelZero

A macOS service that starts, monitors, schedules, and automatically restarts command-line processes with configurable retry policies.

## Core Features

### Process Management
- Start, stop, and monitor command-line processes
- Capture and log stdout/stderr output
- Track process PIDs and resource usage (CPU, memory)
- Support for environment variables and working directories
- Process groups management for related processes

### Scheduling System
- Cron-like scheduling syntax support
- One-time and recurring task execution
- Interval-based scheduling (every N minutes/hours)
- Schedule enable/disable functionality
- View upcoming scheduled executions

### Auto-Restart & Retry Policies
- Configurable retry count limits
- Exponential backoff for retry delays
- Conditional restarts based on exit codes
- Process health checks and monitoring
- Resource threshold monitoring (CPU/memory limits)

### Service Interface
- Command-line interface (CLI) for all operations
- Process status and resource usage reporting
- Log viewing and management
- Configuration persistence across service restarts
- Optional REST API for programmatic access

### Reliability & Security
- Graceful shutdown handling
- Transaction logging for critical operations
- Secure command input validation
- Appropriate permission management
- State persistence for service recovery

## Completed Features

- None (Project initialization phase)

## In Progress

- Project architecture planning
- Technology stack selection
- Database schema design

# MVP Architecture Overview
Your service will need these core components:

Process Manager: Handles starting, stopping, and monitoring processes
Scheduler: Manages scheduled tasks using cron-like functionality
Monitor: Tracks process health and handles restart logic
Storage: Persists process configurations and state
API/Interface: Allows users to interact with the service

# Technology Stack Recommendations
Backend Options:

Python (recommended for MVP): Excellent process management libraries (subprocess, psutil), built-in scheduling (APScheduler), rapid development
Go: Great for system programming, good concurrency, single binary deployment
Node.js: Good ecosystem, but less ideal for system-level operations

Key Libraries (Python approach):

psutil for process monitoring
APScheduler for scheduling
subprocess for process execution
SQLite for lightweight persistence
FastAPI or Flask for REST API
click or typer for CLI interface

# MVP Feature Breakdown
## Phase 1: Core Process Management

Process Execution

Start processes with custom commands
Capture stdout/stderr
Track PIDs
Environment variable support


Process Monitoring

Check if process is running
Monitor CPU/memory usage
Detect process crashes
Log process events


Data Model
python# Example schema
Process:
  - id
  - name
  - command
  - working_directory
  - environment_variables
  - status (running/stopped/failed)
  - pid
  - created_at
  - last_started_at


## Phase 2: Scheduling System

Schedule Types

One-time execution
Recurring (cron-like syntax)
Interval-based (every N minutes/hours)


Schedule Management

Add/remove schedules
Enable/disable schedules
View upcoming executions



## Phase 3: Auto-Restart & Retry Logic

Restart Configuration

Retry count limits
Retry delay (exponential backoff option)
Conditional restarts (based on exit codes)


Health Checks

Periodic liveness checks
Custom health check commands
Resource threshold monitoring



## Phase 4: User Interface

CLI Commands
bash# Example commands
procmon start --name "my-script" --cmd "python script.py"
procmon status --name "my-script"
procmon schedule --name "backup" --cmd "bash backup.sh" --cron "0 2 * * *"
procmon restart-policy --name "my-script" --retries 3 --delay 5h
procmon list
procmon logs --name "my-script"

Optional Web Dashboard

Process status overview
Start/stop controls
Log viewer
Schedule management



# Implementation Plan
## Week 1-2: Foundation

Set up project structure
Implement basic process starting/stopping
Create data models and SQLite integration
Build process monitoring with psutil

## Week 3: Scheduling

Integrate APScheduler
Implement cron and interval scheduling
Add schedule persistence
Create schedule management commands

## Week 4: Restart Logic

Implement restart policies
Add retry delay mechanisms
Build health check system
Handle edge cases (zombie processes, etc.)

## Week 5: CLI & Polish

Complete CLI interface
Add comprehensive logging
Write tests for critical paths
Create installation script

## Week 6: Documentation & Testing

Write user documentation
System testing
Performance optimization
Package for distribution

# Key Technical Considerations
macOS Specific:

Use launchd integration for running service at startup (optional enhancement)
Handle macOS security permissions (especially for accessing other processes)
Consider code signing requirements for distribution

Process Management:

Use process groups for managing child processes
Implement proper signal handling (SIGTERM, SIGKILL)
Handle zombie processes and orphaned children

Reliability:

Persist state to survive service restarts
Implement graceful shutdown
Add transaction logging for critical operations

Security:

Validate and sanitize command inputs
Run processes with appropriate permissions
Secure storage of sensitive environment variables

MVP Success Criteria
Your MVP should successfully:

Start and monitor at least 5 concurrent processes
Schedule processes with basic cron syntax
Automatically restart failed processes with configurable delays
Provide real-time status information via CLI
Persist configuration across service restarts
Generate logs for debugging

Example Project Structure
```
process-monitor/
├── src/
│   ├── core/
│   │   ├── process_manager.py
│   │   ├── scheduler.py
│   │   ├── monitor.py
│   │   └── restart_policy.py
│   ├── models/
│   │   ├── process.py
│   │   └── schedule.py
│   ├── storage/
│   │   └── database.py
│   ├── cli/
│   │   └── commands.py
│   └── utils/
│       └── logger.py
├── tests/
├── config/
│   └── settings.yaml
├── logs/
├── requirements.txt
└── setup.py
```
This plan provides a solid foundation for your MVP. Start with the core process management functionality and incrementally add features. The modular architecture will allow you to enhance the service over time, potentially adding features like process groups, dependency management, or a web UI in future iterations.