# SentinelZero - Cycle 4 Development Plan

## Project Vision
A production-ready macOS service that starts, monitors, schedules, and automatically restarts command-line processes with configurable retry policies, featuring REST API, web dashboard, and native system integration.

## Current State Analysis

### Completed Features (Cycles 1-3)
- ✅ Core process management (start/stop/monitor)
- ✅ Scheduling system (cron, interval, one-time)
- ✅ Auto-restart & retry policies
- ✅ CLI interface with rich output
- ✅ SQLite persistence
- ✅ REST API with JWT auth
- ✅ WebSocket real-time updates
- ✅ React dashboard scaffold
- ✅ macOS launchd integration
- ✅ 98% test coverage (67 tests passing)

### Technical Stack in Use
- **Backend**: Python 3.11, FastAPI, SQLAlchemy, APScheduler
- **Frontend**: React 18, TypeScript, Material-UI, Redux Toolkit
- **Database**: SQLite (local), in-memory auth store
- **Testing**: pytest, unittest
- **Build**: Vite (frontend), setuptools (backend)

## Cycle 4 Requirements

### Primary Goals
1. **Complete Web Dashboard Implementation**
   - Implement all React components (currently scaffold only)
   - Real-time data visualization with WebSockets
   - Full CRUD operations via UI

2. **Production Database Integration**
   - Replace in-memory auth with persistent database
   - User management and RBAC
   - Session management

3. **Enhanced Monitoring**
   - Prometheus metrics integration
   - Alerting system with webhooks
   - Health check endpoints

## Architecture Decisions

### Database Strategy
- **PostgreSQL** for production (auth, users, sessions)
- **Redis** for caching and real-time data
- **SQLite** remains for local process data
- Consider **Supabase** for managed backend services

### Frontend Architecture
- Component-based with atomic design pattern
- Redux for global state, React Query for API state
- WebSocket manager for real-time updates
- Lazy loading and code splitting

### Deployment Architecture
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│  CloudFlare │────▶│   Nginx     │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                         ┌─────▼─────┐
                                         │  FastAPI  │
                                         └─────┬─────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
              ┌─────▼─────┐            ┌──────▼──────┐            ┌──────▼──────┐
              │PostgreSQL │            │   Redis     │            │  Sentinel   │
              └───────────┘            └─────────────┘            │   Daemon    │
                                                                   └─────────────┘
```

## Implementation Phases

### Phase 1: Dashboard Completion (Week 1-2)
- [ ] Process monitoring dashboard with real-time updates
- [ ] Schedule management interface
- [ ] Log viewer with filtering and search
- [ ] System metrics visualization (charts)
- [ ] Settings and configuration page
- [ ] WebSocket connection manager
- [ ] Error boundaries and loading states

### Phase 2: Database & Auth (Week 2-3)
- [ ] PostgreSQL setup and migrations
- [ ] User model and authentication tables
- [ ] Role-based access control (Admin, User, Viewer)
- [ ] Session management with Redis
- [ ] Password reset flow
- [ ] API key authentication option

### Phase 3: Monitoring & Alerts (Week 3-4)
- [ ] Prometheus metrics endpoint (/metrics)
- [ ] Custom metrics for process health
- [ ] Webhook notifications system
- [ ] Email/Slack integration
- [ ] Alert rules configuration
- [ ] Health check dashboard

### Phase 4: Production Readiness (Week 4-5)
- [ ] Docker containerization
- [ ] Docker Compose for development
- [ ] Kubernetes manifests
- [ ] CI/CD with GitHub Actions
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Load testing

### Phase 5: Documentation & Testing (Week 5-6)
- [ ] API documentation improvements
- [ ] User guide for dashboard
- [ ] Deployment documentation
- [ ] End-to-end tests
- [ ] Security audit
- [ ] Performance benchmarks

## Risk Analysis

### Technical Risks
1. **WebSocket Scalability**: May need connection pooling and load balancing
   - Mitigation: Implement Redis pub/sub for multi-instance support

2. **Database Migration**: Moving from SQLite to PostgreSQL
   - Mitigation: Create migration scripts, test thoroughly

3. **React Performance**: Real-time updates may impact performance
   - Mitigation: Use React.memo, virtualization, debouncing

### Security Risks
1. **JWT Token Management**: Token theft, XSS attacks
   - Mitigation: HttpOnly cookies, CSP headers, token rotation

2. **Command Injection**: User-provided commands
   - Mitigation: Already using shlex, add additional validation

3. **Resource Exhaustion**: Too many processes/schedules
   - Mitigation: Rate limiting, resource quotas

## Success Metrics
- Dashboard loads in <2 seconds
- WebSocket latency <100ms
- API response time <200ms (p95)
- 99.9% uptime for daemon service
- Support 100+ concurrent processes
- Handle 1000+ API requests/second

## Technology Decisions

### Frontend Libraries
- **React Query**: API state management
- **Recharts**: Data visualization
- **React Hook Form**: Form handling
- **date-fns**: Date manipulation
- **Socket.io-client**: WebSocket management

### Backend Libraries
- **Alembic**: Database migrations
- **Celery**: Background tasks (future)
- **Prometheus Client**: Metrics export
- **Pydantic**: Enhanced validation
- **python-multipart**: File uploads

### Infrastructure
- **Docker**: Containerization
- **GitHub Actions**: CI/CD
- **PostgreSQL 15**: Production database
- **Redis 7**: Caching layer
- **Nginx**: Reverse proxy

## Development Workflow
1. Feature branch from main
2. Implement with TDD approach
3. Update documentation
4. Create PR with tests passing
5. Code review and approval
6. Merge to main
7. Auto-deploy to staging
8. Manual promotion to production

## Next Immediate Steps
1. Complete React component implementations
2. Set up PostgreSQL and create auth schema
3. Implement WebSocket data flow
4. Add comprehensive integration tests
5. Create Docker development environment

## Cycle 4 Deliverables
- Fully functional web dashboard
- Production-ready authentication system
- Monitoring and alerting capabilities
- Docker deployment configuration
- Comprehensive documentation
- 95%+ test coverage maintained