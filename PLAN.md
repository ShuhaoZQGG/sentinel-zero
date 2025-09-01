# SentinelZero - Cycle 3 Development Plan

## Executive Summary
Building upon the successful completion of all core MVP features in Cycle 2, Cycle 3 focuses on expanding SentinelZero with enterprise-grade capabilities: REST API, web dashboard, and macOS system integration.

## Current State Analysis
### Completed (Cycle 2)
- ✅ Process Management (start/stop/monitor)
- ✅ Scheduling System (cron/interval)
- ✅ Auto-Restart & Retry Policies
- ✅ CLI Interface
- ✅ Database Persistence
- ✅ 98% test coverage (60 tests passing)

### Technical Foundation
- **Language**: Python 3.13
- **Database**: SQLAlchemy with SQLite
- **CLI**: Click framework
- **Testing**: pytest with 98% coverage
- **Architecture**: Modular service-oriented design

## Cycle 3 Requirements

### 1. REST API Development
**Priority**: HIGH
**Estimated Effort**: 2 weeks

#### Endpoints Design
```
POST   /api/processes           - Start new process
GET    /api/processes           - List all processes
GET    /api/processes/{id}      - Get process details
DELETE /api/processes/{id}      - Stop process
PUT    /api/processes/{id}      - Update process config

POST   /api/schedules           - Create schedule
GET    /api/schedules           - List schedules
DELETE /api/schedules/{id}      - Remove schedule
PUT    /api/schedules/{id}      - Update schedule

GET    /api/processes/{id}/logs - Get process logs
GET    /api/processes/{id}/metrics - Get resource metrics
GET    /api/health              - Service health check
```

#### Technical Stack
- **Framework**: FastAPI (async, OpenAPI, modern)
- **Authentication**: JWT tokens with refresh
- **Validation**: Pydantic models
- **CORS**: Configurable for web clients
- **Rate Limiting**: Redis-based or in-memory

### 2. Web Dashboard
**Priority**: HIGH
**Estimated Effort**: 2 weeks

#### Core Features
- Real-time process status monitoring
- Interactive process control (start/stop/restart)
- Log streaming with filtering
- Resource usage charts (CPU/memory)
- Schedule management UI
- Configuration editor

#### Technical Stack
- **Frontend**: React + TypeScript
- **State Management**: Redux Toolkit or Zustand
- **UI Components**: Material-UI or Ant Design
- **Charts**: Recharts or Chart.js
- **WebSocket**: Socket.io for real-time updates
- **Build Tool**: Vite

### 3. macOS System Integration
**Priority**: MEDIUM
**Estimated Effort**: 1 week

#### launchd Integration
```xml
<!-- com.sentinelzero.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.sentinelzero</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/sentinelzero</string>
        <string>daemon</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

#### Installation Package
- Homebrew formula creation
- Installation script with permissions setup
- Uninstaller script
- Auto-update mechanism

### 4. Advanced Monitoring
**Priority**: MEDIUM
**Estimated Effort**: 1 week

#### Features
- Prometheus metrics export
- Custom health check scripts
- Webhook notifications (Slack, Discord, email)
- Alert thresholds configuration
- Historical metrics storage

### 5. Configuration Management
**Priority**: LOW
**Estimated Effort**: 3 days

#### Enhancements
- YAML/JSON config file support
- Hot-reload capability
- Config validation schema
- Environment-specific configs
- Secrets management

## Architecture Updates

### API Layer Architecture
```
sentinelzero/
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── routers/
│   │   ├── processes.py
│   │   ├── schedules.py
│   │   ├── metrics.py
│   │   └── auth.py
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   ├── middleware/
│   │   ├── auth.py
│   │   └── cors.py
│   └── websocket/
│       └── connections.py
```

### Frontend Architecture
```
sentinel-web/
├── src/
│   ├── components/
│   │   ├── ProcessList/
│   │   ├── LogViewer/
│   │   ├── MetricsChart/
│   │   └── ScheduleManager/
│   ├── services/
│   │   ├── api.ts
│   │   └── websocket.ts
│   ├── store/
│   │   └── slices/
│   └── App.tsx
```

## Database Schema Updates

### New Tables
```sql
-- API Authentication
CREATE TABLE api_tokens (
    id INTEGER PRIMARY KEY,
    token_hash VARCHAR(255) UNIQUE,
    user_id INTEGER,
    created_at TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN
);

-- Webhook Configurations
CREATE TABLE webhooks (
    id INTEGER PRIMARY KEY,
    url VARCHAR(500),
    event_type VARCHAR(50),
    is_active BOOLEAN,
    created_at TIMESTAMP
);

-- Metrics History
CREATE TABLE metrics_history (
    id INTEGER PRIMARY KEY,
    process_id INTEGER,
    cpu_percent FLOAT,
    memory_mb FLOAT,
    timestamp TIMESTAMP,
    FOREIGN KEY (process_id) REFERENCES processes(id)
);
```

## Implementation Phases

### Phase 1: API Foundation (Week 1)
1. Set up FastAPI project structure
2. Implement core endpoints
3. Add authentication/authorization
4. Create OpenAPI documentation
5. Write API integration tests

### Phase 2: Web Dashboard (Week 2-3)
1. Initialize React project
2. Build component library
3. Implement state management
4. Add WebSocket connections
5. Create responsive layouts

### Phase 3: System Integration (Week 4)
1. Create launchd configuration
2. Build installation scripts
3. Implement Homebrew formula
4. Test system startup/shutdown

### Phase 4: Advanced Features (Week 5)
1. Add Prometheus metrics
2. Implement webhooks
3. Create custom health checks
4. Build alert system

## Risk Assessment

### Technical Risks
1. **WebSocket Scalability**: Multiple dashboard connections
   - Mitigation: Connection pooling, rate limiting
   
2. **API Security**: Authentication vulnerabilities
   - Mitigation: JWT best practices, rate limiting, HTTPS only

3. **macOS Permissions**: System-level access restrictions
   - Mitigation: Proper entitlements, user guidance

### Dependencies
- FastAPI ecosystem maturity ✅
- React ecosystem stability ✅
- macOS API stability ✅

## Testing Strategy

### Unit Tests
- API endpoint tests (pytest)
- Frontend component tests (Jest)
- WebSocket connection tests

### Integration Tests
- API + Database interactions
- Frontend + API communication
- launchd service lifecycle

### Performance Tests
- API load testing (locust)
- Dashboard rendering performance
- WebSocket message throughput

## Success Metrics

### Quantitative
- API response time < 100ms (p95)
- Dashboard load time < 2s
- WebSocket latency < 50ms
- Zero-downtime deployments

### Qualitative
- Intuitive dashboard UX
- Comprehensive API documentation
- Smooth installation experience
- Reliable system integration

## Technology Decisions

### API Framework: FastAPI
- **Rationale**: Modern, async, automatic OpenAPI docs, Pydantic integration

### Frontend: React + TypeScript
- **Rationale**: Industry standard, strong ecosystem, type safety

### Real-time: WebSockets
- **Rationale**: Native browser support, bidirectional communication

### Deployment: Docker + docker-compose
- **Rationale**: Consistent environments, easy distribution

## Next Cycle Recommendations

### Cycle 4 Focus Areas
1. Distributed architecture (multiple hosts)
2. Container/Kubernetes support
3. Advanced analytics and ML predictions
4. Enterprise features (LDAP, SSO)
5. Mobile app development

## Conclusion
Cycle 3 transforms SentinelZero from a robust CLI tool into a comprehensive process management platform with modern API, real-time dashboard, and native macOS integration. The plan maintains backward compatibility while adding enterprise-grade capabilities.