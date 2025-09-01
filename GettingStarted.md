# Getting Started with SentinelZero

SentinelZero is a powerful macOS service for managing, monitoring, and scheduling command-line processes with automatic restart capabilities. This guide will help you get started quickly.

## Table of Contents
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Basic Commands](#basic-commands)
- [Advanced Features](#advanced-features)
- [Configuration Files](#configuration-files)
- [Web Dashboard](#web-dashboard)
- [macOS Integration](#macos-integration)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites
- macOS 10.15 or later
- Python 3.8 or later
- pip package manager

### Install from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/sentinel-zero.git
cd sentinel-zero

# Install dependencies
pip install -r requirements.txt

# Install SentinelZero
pip install -e .
```

### Verify Installation

```bash
sentinel-zero --version
# Output: 0.1.0
```

## Quick Start

### 1. Start Your First Process

```bash
# Start a simple Python script
sentinel-zero start --name "my-script" --cmd "python script.py"

# Start a process with arguments
sentinel-zero start --name "web-server" --cmd "python" --args "-m" --args "http.server" --args "8080"

# Start with a working directory
sentinel-zero start --name "my-app" --cmd "npm start" --dir "/path/to/project"
```

### 2. Check Process Status

```bash
# Check specific process
sentinel-zero status my-script

# List all processes
sentinel-zero list

# Show detailed status with metrics
sentinel-zero status --metrics
```

### 3. Stop a Process

```bash
# Graceful stop
sentinel-zero stop my-script

# Force stop with timeout
sentinel-zero stop my-script --force --timeout 5
```

## Basic Commands

### Process Management

#### Starting Processes
```bash
# Basic start
sentinel-zero start -n "process-name" -c "command"

# With environment variables
sentinel-zero start -n "api" -c "python app.py" \
  -e "DATABASE_URL=postgres://localhost/db" \
  -e "DEBUG=true"

# With process group
sentinel-zero start -n "worker-1" -c "python worker.py" -g "workers"

# Run in background (detached)
sentinel-zero start -n "daemon" -c "python daemon.py" --detach
```

#### Monitoring Processes
```bash
# Real-time status
sentinel-zero status --watch 5  # Refresh every 5 seconds

# View process logs
sentinel-zero logs process-name

# Follow logs in real-time
sentinel-zero logs process-name --follow

# Filter logs
sentinel-zero logs process-name --tail 50 --grep "ERROR"
```

#### Process Control
```bash
# Restart a process
sentinel-zero restart process-name

# Stop all processes
sentinel-zero stop --all

# Stop process group
sentinel-zero stop --group workers
```

## Advanced Features

### Scheduling

SentinelZero supports both cron-style and interval-based scheduling:

```bash
# Cron schedule (runs daily at 2 AM)
sentinel-zero start -n "backup" -c "bash backup.sh" \
  --schedule "0 2 * * *"

# Interval schedule (every 30 minutes)
sentinel-zero start -n "health-check" -c "python check.py" \
  --schedule "30m"

# Special cron syntax
sentinel-zero start -n "hourly-task" -c "python task.py" \
  --schedule "@hourly"
```

### Restart Policies

Configure automatic restart behavior:

```bash
# Apply standard restart policy
sentinel-zero start -n "api" -c "python api.py" \
  --restart-policy standard

# Custom restart configuration (via config file)
# See Configuration Files section below
```

### Process Groups

Manage related processes together:

```bash
# Start processes in a group
sentinel-zero start -n "web" -c "python web.py" -g "app-stack"
sentinel-zero start -n "worker" -c "python worker.py" -g "app-stack"
sentinel-zero start -n "cache" -c "redis-server" -g "app-stack"

# List processes by group
sentinel-zero list --filter "group=app-stack"
```

## Configuration Files

### Creating a Configuration File

```bash
# Generate example config
sentinel-zero config init --path my-config.yaml
```

### Example Configuration

```yaml
# my-config.yaml
version: 1.0
defaults:
  directory: /home/user/projects
  restart:
    max_retries: 3
    delay: 5
    backoff: 2.0

processes:
  - name: web-server
    command: python
    args: ["-m", "http.server", "8080"]
    directory: /var/www
    environment:
      PORT: "8080"
      ENV: "production"
    restart:
      max_retries: 5
      delay: 10
      restart_on_codes: [1, 2]
    schedule:
      type: cron
      expression: "0 */6 * * *"  # Every 6 hours
      enabled: true

  - name: background-worker
    command: python
    args: ["worker.py"]
    group: workers
    restart:
      max_retries: -1  # Infinite retries
      delay: 30
      backoff: 1.5

  - name: monitoring
    command: bash
    args: ["monitor.sh"]
    schedule:
      type: interval
      expression: "5m"  # Every 5 minutes
      enabled: true

policies:
  - name: aggressive
    max_retries: 10
    delay: 1
    backoff: 2.0
    restart_on_codes: [1]
  
  - name: conservative
    max_retries: 3
    delay: 60
    backoff: 1.0
```

### Loading Configuration

```bash
# Validate configuration
sentinel-zero config validate --path my-config.yaml

# Dry run to preview what will be loaded
sentinel-zero config load --path my-config.yaml --dry-run

# Load and apply configuration
sentinel-zero config load --path my-config.yaml
```

## Web Dashboard

### Starting the Dashboard

```bash
# Run as daemon with API server
sentinel-zero daemon --port 8000 --host 0.0.0.0
```

### Accessing the Dashboard

Open your browser and navigate to:
```
http://localhost:8000
```

The dashboard provides:
- Real-time process status monitoring
- Interactive process control (start/stop/restart)
- Live log streaming
- Resource usage graphs
- Schedule management
- Configuration editor

## macOS Integration

### Setting up as a System Service (launchd)

1. Create a launch daemon configuration:

```xml
<!-- ~/Library/LaunchAgents/com.sentinelzero.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.sentinelzero</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/sentinel-zero</string>
        <string>daemon</string>
        <string>--port</string>
        <string>8000</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/sentinelzero.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/sentinelzero.error.log</string>
</dict>
</plist>
```

2. Load the service:

```bash
# Load the service
launchctl load ~/Library/LaunchAgents/com.sentinelzero.plist

# Start the service
launchctl start com.sentinelzero

# Check service status
launchctl list | grep sentinelzero
```

## Examples

### Web Development Stack

```bash
# Start database
sentinel-zero start -n "postgres" \
  -c "postgres" \
  -e "POSTGRES_DB=myapp" \
  -g "dev-stack"

# Start Redis cache
sentinel-zero start -n "redis" \
  -c "redis-server" \
  -g "dev-stack"

# Start web application
sentinel-zero start -n "webapp" \
  -c "npm" --args "run" --args "dev" \
  -d "/path/to/webapp" \
  -e "DATABASE_URL=postgres://localhost/myapp" \
  -e "REDIS_URL=redis://localhost:6379" \
  -g "dev-stack" \
  --restart-policy aggressive
```

### Data Processing Pipeline

```bash
# Data collector (runs every hour)
sentinel-zero start -n "collector" \
  -c "python" --args "collect_data.py" \
  --schedule "@hourly" \
  --restart-policy standard

# Data processor (continuous)
sentinel-zero start -n "processor" \
  -c "python" --args "process_data.py" \
  --restart-policy aggressive

# Report generator (daily at 6 AM)
sentinel-zero start -n "reporter" \
  -c "python" --args "generate_report.py" \
  --schedule "0 6 * * *"
```

### Monitoring Setup

```bash
# System metrics collector
sentinel-zero start -n "metrics" \
  -c "python" --args "collect_metrics.py" \
  --schedule "1m" \
  -e "METRICS_HOST=localhost" \
  -e "METRICS_PORT=9090"

# Alert handler
sentinel-zero start -n "alerts" \
  -c "python" --args "alert_handler.py" \
  --restart-policy conservative \
  -e "SLACK_WEBHOOK=https://..."

# Log aggregator
sentinel-zero start -n "logs" \
  -c "python" --args "log_aggregator.py" \
  -d "/var/log/apps"
```

## Troubleshooting

### Common Issues

#### Process Won't Start
```bash
# Check logs for errors
sentinel-zero logs process-name --tail 100

# Verify command works manually
cd /working/directory
command-to-run

# Check permissions
ls -la /path/to/executable
```

#### Process Keeps Crashing
```bash
# Check restart count
sentinel-zero status process-name

# View recent logs
sentinel-zero logs process-name --tail 50 --grep ERROR

# Adjust restart policy
sentinel-zero config show  # Review current policy
```

#### High Resource Usage
```bash
# Monitor resources
sentinel-zero status --metrics --watch 1

# Set resource limits (via config file)
# Add to process configuration:
# limits:
#   cpu: 50  # percentage
#   memory: 512  # MB
```

### Debug Mode

```bash
# Run with debug logging
sentinel-zero --log-level debug start -n "test" -c "command"

# Check service logs
tail -f /tmp/sentinelzero.log
tail -f /tmp/sentinelzero.error.log
```

### Getting Help

```bash
# General help
sentinel-zero --help

# Command-specific help
sentinel-zero start --help
sentinel-zero config --help

# Version information
sentinel-zero --version
```

## Next Steps

- Explore the [REST API documentation](API.md) for programmatic access
- Read about [advanced scheduling patterns](SCHEDULING.md)
- Learn about [custom restart policies](POLICIES.md)
- Check out [integration examples](INTEGRATIONS.md)

## Support

For issues, questions, or feature requests:
- GitHub Issues: https://github.com/yourusername/sentinel-zero/issues
- Documentation: https://sentinelzero.docs
- Email: support@sentinelzero.io

---

Happy process monitoring with SentinelZero! 🚀