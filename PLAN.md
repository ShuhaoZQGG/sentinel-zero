# Sentinel Zero - Cycle 5 Development Plan

## Executive Summary
Sentinel Zero is a production-ready macOS service for process management with monitoring, scheduling, and auto-restart capabilities. Cycle 5 focuses on fixing critical GitHub issues #10 and #11, and enhancing production readiness with CI/CD and complete UI functionality.

## Open Issues Analysis

### Issue #10: CLI Argument Parsing Bug (CRITICAL)
- **Problem**: Long strings in `-c` and `--args` options fail with "unexpected extra argument" error
- **Root Cause**: Improper shell-style argument parsing in Click CLI
- **Solution**: Implement proper shlex parsing for command strings
- **Impact**: Blocks basic functionality for complex commands

### Issue #11: Custom Restart Delay (ENHANCEMENT)
- **Request**: Add option to specify custom delay periods (e.g., 5h) for restart policies
- **Solution**: Extend restart policy with flexible time format parsing
- **Benefit**: Improved flexibility for production use cases

## Current State (Post Cycle 4)

### Completed Features
- ✅ Core process management with 98% test coverage
- ✅ Scheduling system (cron/interval)
- ✅ Auto-restart & retry policies
- ✅ REST API with FastAPI
- ✅ JWT authentication (database-backed)
- ✅ WebSocket real-time updates
- ✅ React dashboard scaffolding
- ✅ Docker containerization
- ✅ Prometheus metrics integration
- ✅ macOS launchd integration

### Technical Debt
- CLI argument parsing issues blocking complex commands
- Incomplete UI pages (process details, schedules, settings)
- Missing CI/CD pipeline
- Limited integration test coverage

## Cycle 5 Requirements

### Priority 1: Critical Bug Fixes (Days 1-2)
1. **Fix Issue #10 - CLI Argument Parsing**
   - Implement shlex-based command parsing
   - Support quoted strings in `-c` and `--args`
   - Handle special characters and spaces
   - Add comprehensive test cases

2. **Fix Issue #11 - Custom Restart Delays**
   - Add time format parser (5h, 30m, 120s)
   - Update restart policy model
   - Extend CLI with delay option
   - Document new functionality

### Priority 2: CI/CD Pipeline (Days 3-4)
1. **GitHub Actions Workflow**
   - Automated testing on PR
   - Python 3.9+ matrix testing
   - Code coverage reporting
   - Security scanning (SAST)

2. **Release Automation**
   - Semantic versioning
   - Docker image building
   - GitHub releases
   - PyPI publishing preparation

### Priority 3: UI Completion (Days 5-7)
1. **Process Details Page**
   - Real-time log viewer
   - Resource usage charts
   - Control buttons (start/stop/restart)
   - Environment variable editor

2. **Schedules Management**
   - CRUD operations
   - Cron expression builder
   - Visual calendar view
   - Enable/disable toggles

3. **Settings Configuration**
   - User management
   - System preferences
   - API key management
   - Theme selection

### Priority 4: Integration Testing (Days 8-9)
1. **API Test Suite**
   - All endpoint coverage
   - Authentication flows
   - Error scenarios
   - Performance benchmarks

2. **E2E Testing**
   - Critical user journeys
   - WebSocket stability
   - Database migrations
   - Recovery scenarios

## Technical Architecture

### System Components
```
┌─────────────────────────────────────────────┐
│            Web Dashboard (React)             │
│     Material-UI + Redux + TypeScript         │
└─────────────────┬───────────────────────────┘
                  │ WebSocket/REST
┌─────────────────▼───────────────────────────┐
│              FastAPI Server                  │
│      JWT Auth + WebSocket + Metrics         │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│           Core Services                      │
│   Process Manager + Scheduler + Monitor      │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│         Data Layer (SQLAlchemy)             │
│          SQLite + Migrations                │
└──────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│         Observability Stack                  │
│       Prometheus + Grafana + Logs           │
└──────────────────────────────────────────────┘
```

### Technology Stack
- **Backend**: Python 3.9+, FastAPI, SQLAlchemy, APScheduler, psutil
- **Frontend**: React 18, TypeScript, Redux Toolkit, Material-UI
- **Database**: SQLite (default), PostgreSQL-ready
- **Monitoring**: Prometheus + Grafana
- **Testing**: pytest, Jest, Playwright
- **CI/CD**: GitHub Actions, Docker
- **Documentation**: OpenAPI, Sphinx

## Implementation Plan

### Week 1: Bug Fixes & CI/CD
```
Day 1-2: Critical Bug Fixes
- Fix CLI argument parsing (Issue #10)
- Add custom restart delays (Issue #11)
- Write comprehensive tests
- Update documentation

Day 3-4: CI/CD Pipeline
- Create GitHub Actions workflow
- Set up test matrix
- Configure Docker builds
- Add security scanning
```

### Week 2: UI & Testing
```
Day 5-7: Complete UI Pages
- Process details with logs
- Schedule management interface
- Settings configuration
- Mobile responsive design

Day 8-9: Integration Testing
- API endpoint tests
- WebSocket stability tests
- E2E user journeys
- Performance benchmarks
```

### Week 3: Production Ready
```
Day 10: Final Polish
- Grafana dashboards
- Alert configurations
- Documentation review
- Release preparation
```

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