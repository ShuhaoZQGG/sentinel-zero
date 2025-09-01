# SentinelZero - Cycle 5 Development Plan

## Project Vision
A macOS service that starts, monitors, schedules, and automatically restarts command-line processes with configurable retry policies.

## Executive Summary
SentinelZero is a production-ready macOS service for process management with enterprise features. The project has completed its core MVP, enterprise features, bug fixes, and production deployment capabilities. This plan outlines the comprehensive architecture and next steps for the project.

## Completed Features (All Cycles)

### Core MVP (Cycles 1-2) ✅
- Process management with start/stop/monitor
- Scheduling system (cron/interval)
- Auto-restart & retry policies
- CLI interface
- SQLite persistence
- 98% test coverage

### Enterprise Features (Cycle 3) ✅
- REST API with FastAPI
- JWT authentication
- WebSocket real-time updates
- React dashboard with Material-UI
- Redux state management
- macOS launchd integration

### Bug Fixes (Cycle 4) ✅
- Fixed CLI argument parsing (Issue #10)
- Added custom restart delay (Issue #11)
- Enhanced command parsing with shlex
- Comprehensive test coverage

### Production Features (Cycle 5) ✅
- Database-backed authentication
- Prometheus metrics at /metrics
- Docker containerization
- Grafana dashboard support
- GitHub Actions CI/CD pipeline
- Integration tests for API/WebSocket/auth
- Security scanning (Trivy, Bandit)
- Automated releases

## Architecture Overview

### System Components
```
┌─────────────────────────────────────────────────────┐
│                    Frontend                          │
│         React + TypeScript + Material-UI             │
│              Redux + WebSocket Client                │
└────────────────────────┬────────────────────────────┘
                         │ HTTPS/WSS
┌────────────────────────┴────────────────────────────┐
│                   API Gateway                        │
│            FastAPI + JWT Auth + WebSocket            │
│                 Prometheus Metrics                   │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────┐
│                  Core Services                       │
├──────────────┬───────────────┬──────────────────────┤
│Process Manager│   Scheduler   │    Monitor          │
│   psutil     │  APScheduler  │  Health Checks      │
└──────────────┴───────────────┴──────────────────────┘
                         │
┌─────────────────────────────────────────────────────┐
│              Persistence Layer                       │
│         PostgreSQL / SQLite + SQLAlchemy            │
└─────────────────────────────────────────────────────┘
```

### Technology Stack
- **Backend**: Python 3.9-3.12, FastAPI, SQLAlchemy, psutil, APScheduler
- **Frontend**: React 18, TypeScript, Material-UI v5, Redux Toolkit
- **Database**: PostgreSQL (production), SQLite (development)
- **Monitoring**: Prometheus + Grafana
- **Deployment**: Docker, GitHub Actions, PyPI
- **Testing**: pytest, Playwright, Jest
- **Security**: JWT auth, Trivy, Bandit

## Requirements Analysis

### Functional Requirements
1. **Process Management**
   - Start/stop/restart processes with complex commands
   - Environment variables and working directory support
   - Process grouping and bulk operations
   - Resource monitoring (CPU, memory, disk)

2. **Scheduling**
   - Cron-like syntax support
   - Interval-based scheduling
   - One-time scheduled execution
   - Schedule enable/disable functionality

3. **Reliability**
   - Configurable retry policies with custom delays
   - Exponential backoff support
   - Conditional restarts based on exit codes
   - Health check integration

4. **Monitoring**
   - Real-time process metrics
   - Prometheus metrics export
   - Log aggregation and streaming
   - Alert notifications

### Non-Functional Requirements
1. **Performance**
   - Handle 50+ concurrent processes
   - Sub-100ms API response times
   - Real-time WebSocket updates
   - Efficient resource usage

2. **Security**
   - JWT-based authentication
   - Database-backed user management
   - Input validation and sanitization
   - Security scanning in CI/CD

3. **Scalability**
   - Horizontal scaling support
   - Database connection pooling
   - Efficient log rotation
   - Containerized deployment

## Database Schema Updates

```sql
-- Updated restart_policies table for Issue #11
CREATE TABLE restart_policies (
    id INTEGER PRIMARY KEY,
    process_id INTEGER REFERENCES processes(id),
    max_retries INTEGER DEFAULT 3,
    delay_seconds INTEGER,  -- Computed from delay_format
    delay_format VARCHAR(20),  -- Human-readable: "5h", "30m", "120s"
    backoff_multiplier FLOAT DEFAULT 1.5,
    on_failure_only BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for performance
CREATE INDEX idx_processes_status ON processes(status);
CREATE INDEX idx_schedules_next_run ON schedules(next_run);
CREATE INDEX idx_logs_timestamp ON process_logs(timestamp);
```

## API Enhancements

### New Endpoints
```
# Metrics & Monitoring
GET /api/metrics/prometheus    - Prometheus format metrics
GET /api/health/live           - Liveness probe
GET /api/health/ready          - Readiness probe

# Bulk Operations
POST /api/processes/bulk/start - Start multiple processes
POST /api/processes/bulk/stop  - Stop multiple processes

# Export/Import
GET  /api/config/export        - Export configuration
POST /api/config/import        - Import configuration
```

## Testing Strategy

### Unit Tests (Existing + New)
- CLI argument parser (NEW)
- Time format parser (NEW)
- Restart delay logic (NEW)
- Process manager
- Scheduler operations

### Integration Tests (NEW)
```python
# Example test structure
tests/
├── integration/
│   ├── test_api_auth.py
│   ├── test_api_processes.py
│   ├── test_api_schedules.py
│   ├── test_websocket.py
│   └── test_database.py
├── e2e/
│   ├── test_process_lifecycle.py
│   ├── test_schedule_execution.py
│   └── test_restart_policies.py
└── performance/
    ├── test_concurrent_processes.py
    └── test_api_throughput.py
```

## Risk Mitigation

### Technical Risks
1. **CLI Breaking Changes**
   - Risk: Existing scripts may break
   - Mitigation: Backward compatibility layer

2. **Database Migration Failures**
   - Risk: Data corruption during schema updates
   - Mitigation: Automated backup before migrations

3. **UI Performance**
   - Risk: Slow rendering with many processes
   - Mitigation: Virtual scrolling, pagination

### Operational Risks
1. **Resource Exhaustion**
   - Risk: Too many concurrent processes
   - Mitigation: Configurable limits, resource quotas

2. **Security Vulnerabilities**
   - Risk: Command injection, privilege escalation
   - Mitigation: Input validation, sandboxing

## Success Metrics

### Functional Metrics
- ✅ Issues #10 and #11 resolved
- ✅ 100% UI pages functional
- ✅ CI/CD pipeline operational
- ✅ >80% test coverage

### Performance Metrics
- CLI response: <100ms
- API p99 latency: <200ms
- Process start: <500ms
- Memory usage: <100MB base
- Docker image: <150MB

### Quality Metrics
- Zero critical bugs
- Zero security vulnerabilities
- 100% documentation coverage
- <5% test flakiness

## Deliverables

1. **Bug Fixes**
   - Resolved Issue #10 (CLI parsing)
   - Resolved Issue #11 (custom delays)
   - Regression test suite

2. **CI/CD Pipeline**
   - GitHub Actions workflow
   - Automated testing
   - Docker image builds
   - Release automation

3. **Complete UI**
   - All pages functional
   - Mobile responsive
   - Real-time updates
   - Intuitive UX

4. **Documentation**
   - API reference
   - Deployment guide
   - User manual
   - Developer guide

## Future Roadmap (Cycle 6+)

### Near Term
- Kubernetes deployment
- Multi-tenant support
- Plugin architecture
- Advanced scheduling

### Long Term
- ML-based failure prediction
- Cloud provider integrations
- Mobile applications
- Enterprise SSO/LDAP
- SaaS offering

## Conclusion

Cycle 5 transforms Sentinel Zero from a functional prototype to a production-ready system. By fixing critical bugs, completing the UI, and establishing CI/CD, we create a solid foundation for enterprise adoption and future enhancements.