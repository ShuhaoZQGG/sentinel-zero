# Next Cycle Tasks - SentinelZero

## Cycle 2 Review Update
**Status**: PR #3 Merged - All integration tests fixed, deprecation warnings resolved
**Date**: 2025-09-01

### Completed in Cycle 2
- ✅ Fixed all integration test failures (60 tests passing)
- ✅ Fixed API mismatches and method signatures
- ✅ Resolved SQLAlchemy 2.0 deprecation warnings
- ✅ Fixed Python 3.13 datetime deprecation
- ✅ Enhanced CLI with shlex command parsing

## Priority 1: Code Quality & Testing
- [x] ~~Add `.gitignore` file to exclude __pycache__ and other build artifacts~~ (Completed in Cycle 2)
- [x] ~~Implement integration tests for end-to-end scenarios~~ (Completed in Cycle 2)
- [ ] Add code coverage reporting
- [ ] Set up pre-commit hooks for code formatting
- [ ] Fix skipped CLI test (Click runner limitation)

## Priority 2: Configuration & Usability
- [ ] Implement YAML/JSON configuration file support
- [ ] Add config validation and schema
- [ ] Create example configuration templates
- [ ] Implement config hot-reload capability

## Priority 3: REST API
- [ ] Design RESTful API endpoints
- [ ] Implement FastAPI server
- [ ] Add authentication/authorization
- [ ] Create OpenAPI documentation
- [ ] Add CORS support for web clients

## Priority 4: Advanced Features
- [ ] Implement advanced health checks
  - HTTP endpoint monitoring
  - Custom health check scripts
  - Resource threshold alerts
- [ ] Add process dependency management
- [ ] Implement process templates/profiles
- [ ] Add webhook notifications for events

## Priority 5: Platform Integration
- [ ] macOS launchd integration for system startup
- [ ] Create installation script/package
- [ ] Add Homebrew formula
- [ ] Implement proper macOS permissions handling

## Priority 6: Monitoring & Observability
- [ ] Add Prometheus metrics export
- [ ] Implement structured logging with log levels
- [ ] Create log rotation policy
- [ ] Add performance profiling

## Priority 7: Documentation
- [ ] Write comprehensive user guide
- [ ] Create API documentation
- [ ] Add architecture diagrams
- [ ] Write troubleshooting guide
- [ ] Create video tutorials

## Technical Debt
- [ ] Refactor large methods in ProcessManager
- [ ] Improve error handling consistency
- [ ] Add more type hints
- [ ] Optimize database queries
- [ ] Implement connection pooling

## Future Enhancements (Post-MVP)
- [ ] Web dashboard with real-time metrics
- [ ] Distributed process management
- [ ] Container/Docker support
- [ ] Process migration between hosts
- [ ] Machine learning for predictive restarts