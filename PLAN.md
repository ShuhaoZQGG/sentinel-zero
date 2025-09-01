# SentinelZero - Project Plan

## Project Overview

SentinelZero is a robust macOS service for managing command-line processes with advanced monitoring, scheduling, and auto-restart capabilities.

## Requirements Analysis

### Functional Requirements

#### Core Process Management
- Start/stop processes with custom commands and arguments
- Real-time process monitoring with PID tracking
- Stdout/stderr capture and logging
- Environment variable injection
- Working directory configuration
- Process group management for related processes

#### Scheduling Engine
- Cron expression support for complex schedules
- One-time task execution
- Interval-based scheduling
- Schedule persistence and recovery
- Schedule conflict resolution

#### Auto-Restart System
- Configurable retry policies (count, delay, backoff)
- Exit code-based conditional restarts
- Health check integration
- Resource threshold monitoring
- Crash detection and recovery

#### User Interface
- CLI with intuitive commands
- Real-time status reporting
- Log streaming and filtering
- Configuration management
- Optional REST API

### Non-Functional Requirements
- High reliability (99.9% uptime)
- Low resource footprint (<50MB RAM idle)
- Fast process startup (<100ms)
- Secure command execution
- macOS 11+ compatibility

## System Architecture

### Component Design

```
┌──────────────────────────────────────────┐
│              CLI Interface                │
├──────────────────────────────────────────┤
│              Core Service                 │
├────────┬──────────┬──────────┬──────────┤
│Process │Scheduler │Monitor   │Restart   │
│Manager │Engine    │Service   │Policy    │
├────────┴──────────┴──────────┴──────────┤
│           Data Layer (SQLite)            │
└──────────────────────────────────────────┘
```

### Technology Stack

#### Language: Python 3.11+
- Mature ecosystem for system programming
- Excellent process management libraries
- Rapid development and prototyping

#### Core Libraries
- `psutil`: Process monitoring and resource tracking
- `APScheduler`: Advanced scheduling with persistence
- `subprocess`: Process execution and control
- `SQLAlchemy`: ORM for database operations
- `click`: CLI framework
- `pydantic`: Data validation and settings
- `structlog`: Structured logging

#### Database: SQLite
- Lightweight embedded database
- Zero configuration
- ACID compliance
- File-based persistence

#### Optional Components
- `FastAPI`: REST API (future enhancement)
- `watchdog`: File system monitoring
- `prometheus-client`: Metrics export

## Database Schema

```sql
-- Processes table
CREATE TABLE processes (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    command TEXT NOT NULL,
    args TEXT,
    working_dir TEXT,
    env_vars TEXT,
    status TEXT DEFAULT 'stopped',
    pid INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Schedules table
CREATE TABLE schedules (
    id INTEGER PRIMARY KEY,
    process_id INTEGER REFERENCES processes(id),
    schedule_type TEXT NOT NULL,
    schedule_expr TEXT NOT NULL,
    enabled BOOLEAN DEFAULT true,
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    created_at TIMESTAMP
);

-- Restart policies table
CREATE TABLE restart_policies (
    id INTEGER PRIMARY KEY,
    process_id INTEGER REFERENCES processes(id),
    max_retries INTEGER DEFAULT 3,
    retry_delay INTEGER DEFAULT 5,
    backoff_multiplier FLOAT DEFAULT 1.5,
    restart_on_codes TEXT,
    created_at TIMESTAMP
);

-- Process logs table
CREATE TABLE process_logs (
    id INTEGER PRIMARY KEY,
    process_id INTEGER REFERENCES processes(id),
    log_type TEXT,
    message TEXT,
    timestamp TIMESTAMP
);

-- Metrics table
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY,
    process_id INTEGER REFERENCES processes(id),
    cpu_percent FLOAT,
    memory_mb FLOAT,
    timestamp TIMESTAMP
);
```

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- Project structure setup
- Basic process start/stop functionality
- Database models and migrations
- Process monitoring with psutil
- Logging infrastructure

### Phase 2: Scheduling (Week 3)
- APScheduler integration
- Cron expression parsing
- Schedule persistence
- Schedule management CLI commands

### Phase 3: Auto-Restart (Week 4)
- Retry policy implementation
- Exponential backoff algorithm
- Health check system
- Resource threshold monitoring

### Phase 4: CLI & API (Week 5)
- Complete CLI command set
- Configuration management
- Log streaming
- Optional REST API scaffolding

### Phase 5: Testing & Polish (Week 6)
- Unit and integration tests
- Performance optimization
- Documentation
- Installation scripts
- macOS-specific optimizations

## Risk Analysis

### Technical Risks
1. **Process Zombies**: Implement proper signal handling and process group management
2. **Resource Leaks**: Use context managers and cleanup handlers
3. **Database Corruption**: Implement WAL mode and backup strategies
4. **Permission Issues**: Clear documentation on required permissions

### Mitigation Strategies
- Comprehensive error handling
- Graceful degradation
- Regular state snapshots
- Extensive logging
- Automated testing pipeline

## Success Metrics

- Successfully manage 20+ concurrent processes
- <100ms command response time
- <1% CPU usage when idle
- Zero data loss on crashes
- 99.9% service availability

## Future Enhancements

- Web dashboard with real-time metrics
- Process dependency management
- Distributed process management
- Integration with launchd
- Webhook notifications
- Process templates and profiles
- Resource allocation limits
- Container support

## Development Guidelines

### Code Standards
- Type hints for all functions
- Docstrings for public APIs
- 90% test coverage
- Black/isort formatting
- Pre-commit hooks

### Security Considerations
- Input validation for all commands
- Least privilege principle
- Secure credential storage
- Audit logging
- Rate limiting for API

## Deliverables

1. Core service executable
2. CLI tool
3. Configuration examples
4. User documentation
5. API documentation
6. Installation guide
7. Test suite
8. Performance benchmarks