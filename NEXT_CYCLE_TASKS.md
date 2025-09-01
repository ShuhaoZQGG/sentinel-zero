# Next Cycle Tasks

## Priority 1: Core Features Completion

### Configuration Management
- [ ] Implement YAML configuration file support
- [ ] Create configuration schema with Pydantic
- [ ] Add `sentinel config` command group
- [ ] Support for process templates in config
- [ ] Environment-specific configurations

### Integration Testing
- [ ] End-to-end workflow tests
- [ ] Process lifecycle integration tests
- [ ] Schedule execution tests
- [ ] Restart policy integration tests
- [ ] Configuration loading tests

### REST API Development
- [ ] FastAPI setup and project structure
- [ ] Process management endpoints
- [ ] Schedule management endpoints
- [ ] Metrics and monitoring endpoints
- [ ] WebSocket support for real-time logs
- [ ] API authentication and authorization
- [ ] OpenAPI documentation

## Priority 2: Enhancements

### Advanced Health Checks
- [ ] Custom health check commands
- [ ] HTTP endpoint health checks
- [ ] TCP port availability checks
- [ ] Process memory/CPU thresholds
- [ ] Health check scheduling

### macOS Integration
- [ ] launchd plist generation
- [ ] Service installation scripts
- [ ] Auto-start on system boot
- [ ] System tray integration (optional)

### Process Groups
- [ ] Group start/stop operations
- [ ] Dependency management between processes
- [ ] Group-level restart policies
- [ ] Resource allocation per group

## Priority 3: Technical Debt

### Code Quality
- [ ] Update SQLAlchemy to 2.0 style (fix deprecation warning)
- [ ] Add type hints to all modules
- [ ] Increase test coverage to 90%+
- [ ] Performance profiling and optimization
- [ ] Memory leak detection

### Documentation
- [ ] API documentation
- [ ] User guide with examples
- [ ] Architecture documentation
- [ ] Contributing guidelines
- [ ] Installation guide for different platforms

### DevOps
- [ ] CI/CD pipeline setup
- [ ] Automated testing on PR
- [ ] Code coverage reporting
- [ ] Release automation
- [ ] Docker containerization

## Future Enhancements (Backlog)

### Web Dashboard
- [ ] React/Vue.js frontend
- [ ] Real-time process monitoring
- [ ] Interactive log viewer
- [ ] Schedule calendar view
- [ ] Metrics visualization

### Advanced Features
- [ ] Process templates library
- [ ] Webhook notifications
- [ ] Slack/Discord integration
- [ ] Distributed process management
- [ ] Resource quotas and limits
- [ ] Process migration between machines

### Security
- [ ] Secure credential storage
- [ ] Role-based access control
- [ ] Audit logging
- [ ] Rate limiting
- [ ] TLS/SSL support for API

## Bug Fixes & Improvements
- [ ] Handle edge cases in time parser (e.g., "1.5h")
- [ ] Improve error messages for CLI commands
- [ ] Add progress indicators for long operations
- [ ] Optimize database queries
- [ ] Add database migration system

## Testing Improvements
- [ ] Stress testing with 100+ processes
- [ ] Performance benchmarks
- [ ] Chaos testing for reliability
- [ ] Cross-platform testing
- [ ] Load testing for API

## Notes
- GitHub issues #10 and #11 have been resolved in cycle 6
- Focus on configuration management and REST API for next cycle
- Consider user feedback for prioritization changes
- Maintain backward compatibility with existing CLI