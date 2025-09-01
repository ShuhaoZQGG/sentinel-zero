# SentinelZero - Cycle 2 Project Plan

## Executive Summary
SentinelZero is a macOS service for process lifecycle management with automatic restart capabilities, scheduling, and comprehensive monitoring. Cycle 1 established core functionality with 100% test coverage. Cycle 2 focuses on configuration management, REST API, and integration testing.

## Current Status
- ✅ Core process management implemented
- ✅ Scheduling system operational 
- ✅ CLI interface functional
- ✅ GitHub issues #10 and #11 resolved
- 🔄 Configuration management needed
- 🔄 REST API pending
- 🔄 Integration tests required

## Requirements Analysis

### Functional Requirements
1. **Process Management** ✅
   - Start/stop/restart processes
   - Resource monitoring (CPU/memory)
   - Output capture and logging
   - Process groups

2. **Scheduling** ✅
   - Cron expressions
   - Interval-based schedules
   - One-time execution

3. **Restart Policies** ✅
   - Configurable retry limits
   - Exponential backoff
   - Exit code conditions

4. **Configuration** 🔄
   - YAML file support
   - Process templates
   - Environment management

5. **API Access** 🔄
   - REST API endpoints
   - WebSocket for real-time logs
   - Authentication

### Non-Functional Requirements
- Performance: <100ms CLI response, <50MB memory
- Reliability: Graceful shutdown, state persistence
- Security: Input validation, permission management
- Usability: Intuitive CLI, clear error messages

## Architecture

### System Components
```
┌─────────────────────────────────────────────┐
│              CLI Interface                  │
├─────────────────────────────────────────────┤
│              REST API (FastAPI)             │
├─────────────────────────────────────────────┤
│           Business Logic Layer              │
│  ┌──────────┬──────────┬──────────┐       │
│  │Process   │Scheduler │Restart   │       │
│  │Manager   │          │Policy    │       │
│  └──────────┴──────────┴──────────┘       │
├─────────────────────────────────────────────┤
│         Data Access Layer (SQLAlchemy)      │
├─────────────────────────────────────────────┤
│            SQLite Database                  │
└─────────────────────────────────────────────┘
```

### Technology Stack
- **Language**: Python 3.11+
- **Process Management**: psutil
- **Scheduling**: APScheduler
- **CLI**: Click + Rich
- **API**: FastAPI
- **Database**: SQLAlchemy + SQLite
- **Testing**: pytest
- **Logging**: structlog

### Database Schema
```sql
-- Processes
CREATE TABLE processes (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    command TEXT NOT NULL,
    working_dir TEXT,
    status TEXT,
    pid INTEGER,
    restart_policy_id INTEGER
);

-- Schedules
CREATE TABLE schedules (
    id INTEGER PRIMARY KEY,
    process_id INTEGER,
    expression TEXT,
    type TEXT,
    enabled BOOLEAN,
    next_run TIMESTAMP
);

-- Restart Policies
CREATE TABLE restart_policies (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    max_retries INTEGER,
    delay REAL,
    backoff_multiplier REAL
);

-- Process Logs
CREATE TABLE process_logs (
    id INTEGER PRIMARY KEY,
    process_id INTEGER,
    timestamp TIMESTAMP,
    level TEXT,
    message TEXT
);
```

## Implementation Phases

### Phase 1: Configuration Management (Week 1)
- [ ] YAML configuration parser
- [ ] Configuration schema validation (Pydantic)
- [ ] Process templates support
- [ ] `sentinel config` command group
- [ ] Environment-specific configs

### Phase 2: REST API Development (Week 2)
- [ ] FastAPI project setup
- [ ] Process management endpoints
- [ ] Schedule management endpoints
- [ ] Metrics endpoints
- [ ] WebSocket for real-time logs
- [ ] OpenAPI documentation

### Phase 3: Integration Testing (Week 3)
- [ ] End-to-end workflow tests
- [ ] Process lifecycle tests
- [ ] Schedule execution tests
- [ ] API integration tests
- [ ] Performance benchmarks

### Phase 4: Advanced Features (Week 4)
- [ ] Custom health checks
- [ ] HTTP/TCP health monitoring
- [ ] Process dependencies
- [ ] Group operations
- [ ] Resource quotas

### Phase 5: macOS Integration (Week 5)
- [ ] launchd plist generation
- [ ] Service installation scripts
- [ ] Auto-start configuration
- [ ] System permissions handling

### Phase 6: Polish & Documentation (Week 6)
- [ ] API documentation
- [ ] User guide
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Release preparation

## Risk Analysis

### Technical Risks
1. **macOS Permissions**: Process management requires elevated permissions
   - Mitigation: Clear documentation, permission checks
   
2. **Resource Leaks**: Long-running processes may leak memory
   - Mitigation: Regular profiling, resource limits

3. **Database Corruption**: SQLite concurrent access issues
   - Mitigation: WAL mode, transaction management

### Project Risks
1. **Scope Creep**: Feature requests beyond MVP
   - Mitigation: Strict phase boundaries, backlog management

2. **Performance Degradation**: Scaling issues with many processes
   - Mitigation: Load testing, optimization passes

## Success Metrics
- 90%+ test coverage
- <100ms CLI response time
- Support for 50+ concurrent processes
- Zero critical bugs in production
- Complete API documentation
- 5-minute installation process

## Immediate Next Steps (Cycle 2)
1. **Configuration Management** (Priority 1)
   - Implement YAML parser
   - Create Pydantic schemas
   - Add config commands

2. **REST API** (Priority 1)
   - Setup FastAPI
   - Create core endpoints
   - Add authentication

3. **Integration Tests** (Priority 2)
   - End-to-end scenarios
   - Performance tests
   - Stress testing

## Future Enhancements (Backlog)
- Web dashboard (React/Vue.js)
- Distributed process management
- Webhook notifications
- Container support
- Prometheus metrics export

## Supabase Integration Potential
While the current implementation uses SQLite, Supabase could enhance:
- **Authentication**: Secure API access
- **Real-time**: Live process status updates
- **Storage**: Log file management
- **Edge Functions**: Custom health checks
- **Row-Level Security**: Multi-tenant support

Decision: Continue with SQLite for MVP, evaluate Supabase for v2.0 with multi-user/distributed features.

## Dependencies
```txt
# Core
python>=3.11
psutil>=5.9.0
apscheduler>=3.10.0
sqlalchemy>=2.0.0
click>=8.1.0
rich>=13.0.0
structlog>=23.0.0

# API (Phase 2)
fastapi>=0.100.0
uvicorn>=0.23.0
pydantic>=2.0.0
websockets>=11.0.0

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
```

## Conclusion
SentinelZero has a solid foundation from Cycle 1. Cycle 2 will focus on configuration management and REST API to make the service production-ready. The modular architecture supports incremental feature addition while maintaining stability.