# SentinelZero - UI/UX Design Specifications (Cycle 5)

## Design Philosophy

### Principles
- **Clarity**: Every command and output should be self-explanatory
- **Efficiency**: Minimize keystrokes for common operations
- **Consistency**: Uniform patterns across all commands
- **Feedback**: Always provide clear status and error messages
- **Accessibility**: Support screen readers and keyboard navigation
- **Production Ready**: Enterprise-grade reliability and monitoring

## Command-Line Interface Design

### Command Structure
```
sentinel [global-options] <command> [command-options] [arguments]
```

### Global Options
- `--config PATH`: Specify config file location
- `--log-level LEVEL`: Set logging verbosity (debug|info|warn|error)
- `--format FORMAT`: Output format (table|json|yaml)
- `--no-color`: Disable colored output
- `--help`: Show help message
- `--version`: Show version information

## Core Commands

### Process Management

#### `sentinel start`
```bash
# Start a new process (FIXED: Issue #10 - Proper shlex parsing)
sentinel start --name <name> --cmd <command> [options]

Options:
  --name, -n          Process name (required)
  --cmd, -c           Command to execute (required, supports quoted strings)
  --args              Command arguments (supports spaces in quotes)
  --dir, -d           Working directory
  --env, -e           Environment variables (KEY=VALUE)
  --group, -g         Process group name
  --restart-policy    Restart policy name
  --restart-delay     Custom restart delay (NEW: Issue #11 - Format: 5h, 30m, 120s)
  --schedule          Schedule expression
  --detach            Run in background

Examples:
  # Complex command with spaces (Issue #10 fix)
  sentinel start -n web-server -c "python app.py --host 0.0.0.0" --args "--port 8080 --workers 4"
  
  # Custom restart delay (Issue #11 feature)
  sentinel start -n backup -c "backup.sh" --restart-delay 5h --restart-policy aggressive
```

#### `sentinel stop`
```bash
# Stop a running process
sentinel stop <name> [options]

Options:
  --force, -f         Force kill (SIGKILL)
  --timeout, -t       Grace period in seconds (default: 10)
  --all              Stop all processes

Example:
  sentinel stop web-server --timeout 30
```

#### `sentinel restart`
```bash
# Restart a process
sentinel restart <name> [options]

Options:
  --force, -f         Force restart
  --delay, -d         Delay between stop and start

Example:
  sentinel restart web-server --delay 5
```

#### `sentinel status`
```bash
# Show process status
sentinel status [name] [options]

Options:
  --watch, -w         Auto-refresh every N seconds
  --metrics, -m       Include resource metrics
  --history          Show status history

Output (table format):
┌──────────┬─────────┬─────┬──────┬────────┬────────┐
│ Name     │ Status  │ PID │ CPU% │ Memory │ Uptime │
├──────────┼─────────┼─────┼──────┼────────┼────────┤
│ web-srv  │ running │ 1234│ 2.3  │ 45 MB  │ 2h 15m │
│ worker-1 │ stopped │ -   │ -    │ -      │ -      │
│ backup   │ failed  │ -   │ -    │ -      │ -      │
└──────────┴─────────┴─────┴──────┴────────┴────────┘
```

#### `sentinel list`
```bash
# List all processes
sentinel list [options]

Options:
  --filter, -f        Filter by status/group
  --sort, -s          Sort by field
  --limit, -l         Limit results

Output includes:
- Process name
- Status (running/stopped/failed/scheduled)
- Command
- Last started
- Restart count
```

### Scheduling Commands

#### `sentinel schedule`
```bash
# Manage schedules
sentinel schedule <subcommand> [options]

Subcommands:
  add <name>          Add schedule to process
  remove <name>       Remove schedule
  list                List all schedules
  enable <name>       Enable schedule
  disable <name>      Disable schedule

Options for 'add':
  --cron              Cron expression
  --interval          Interval (e.g., 5m, 1h, 1d)
  --once              One-time execution at timestamp

Examples:
  sentinel schedule add web-backup --cron "0 2 * * *"
  sentinel schedule add health-check --interval 5m
  sentinel schedule list
```

### Restart Policy Commands

#### `sentinel policy`
```bash
# Manage restart policies (ENHANCED: Issue #11 - Flexible time formats)
sentinel policy <subcommand> [options]

Subcommands:
  create <name>       Create new policy
  update <name>       Update existing policy
  delete <name>       Delete policy
  list                List all policies
  apply <name>        Apply policy to process

Options for 'create':
  --max-retries       Maximum retry attempts
  --delay             Initial delay (NEW: Supports 5h, 30m, 120s formats)
  --backoff           Backoff multiplier
  --on-exit-codes     Restart on specific exit codes
  --health-check      Health check command
  --max-delay         Maximum delay cap (NEW: Time format support)

Examples:
  # Create policy with custom time delays (Issue #11)
  sentinel policy create patient --max-retries 5 --delay 30m --max-delay 5h
  sentinel policy create aggressive --max-retries 10 --delay 30s --backoff 2.0
  sentinel policy apply patient database-backup
```

### Monitoring Commands

#### `sentinel logs`
```bash
# View process logs
sentinel logs <name> [options]

Options:
  --follow, -f        Follow log output
  --tail, -t          Number of lines to show
  --since             Show logs since timestamp
  --level             Filter by log level
  --grep              Filter by pattern

Example:
  sentinel logs web-server -f --tail 100 --grep ERROR
```

#### `sentinel metrics`
```bash
# View process metrics
sentinel metrics <name> [options]

Options:
  --period, -p        Time period (1h, 1d, 1w)
  --interval          Data point interval
  --export            Export format (csv|json)

Output:
- CPU usage graph
- Memory usage graph
- Restart frequency
- Average uptime
```

### Configuration Commands

#### `sentinel config`
```bash
# Manage configuration
sentinel config <subcommand> [options]

Subcommands:
  show                Show current configuration
  set <key> <value>   Set configuration value
  get <key>           Get configuration value
  export              Export configuration
  import <file>       Import configuration

Example:
  sentinel config set log.retention 30d
  sentinel config export > config.yaml
```

## Output Formatting

### Status Indicators
- 🟢 Running (green)
- 🟡 Starting/Stopping (yellow)
- 🔴 Failed/Stopped (red)
- ⏸️  Paused
- 🔄 Restarting
- ⏰ Scheduled

### Progress Indicators
```
Starting web-server... [████████--] 80%
Stopping worker-1... Done ✓
Restarting backup... Failed ✗
```

### Error Messages
```
Error: Process 'web-server' not found
Hint: Use 'sentinel list' to see available processes

Error: Invalid cron expression '0 0 * *'
Expected format: MIN HOUR DAY MONTH WEEKDAY
Example: '0 2 * * *' (daily at 2 AM)
```

## Interactive Features

### Auto-completion
- Command completion
- Process name completion
- Option value suggestions
- File path completion

### Interactive Mode
```bash
sentinel interactive

SentinelZero> start -n test -c "echo hello"
Process 'test' started (PID: 1234)

SentinelZero> status
[Shows status table]

SentinelZero> help
[Shows available commands]

SentinelZero> exit
```

## Configuration File Format

### YAML Configuration
```yaml
# ~/.sentinel/config.yaml
defaults:
  log_level: info
  restart_policy: standard
  working_dir: ~/projects

processes:
  - name: web-server
    command: python app.py
    directory: /app
    environment:
      PORT: 8080
      ENV: production
    restart:
      max_retries: 5
      delay: 10s
    schedule:
      cron: "0 */6 * * *"

  - name: worker
    command: python worker.py
    group: background-jobs
    restart:
      policy: aggressive

policies:
  standard:
    max_retries: 3
    delay: 5s
    backoff: 1.5

  aggressive:
    max_retries: 10
    delay: 1s
    backoff: 2.0
```

## Web Dashboard (Cycle 5 - Complete Implementation)

### Technology Stack
- **Frontend**: React 18 + TypeScript + Material-UI v5
- **State**: Redux Toolkit + RTK Query
- **Real-time**: WebSocket with auto-reconnect
- **Charts**: Recharts for metrics visualization
- **Build**: Vite + SWC for fast development

### Dashboard Pages

#### 1. Main Dashboard (/)
```
┌─────────────────────────────────────────────────────────┐
│ SentinelZero      [🔍 Search] [🔔 3] [👤 Admin] [⚙️]    │
├─────────────────────────────────────────────────────────┤
│ System Overview                          [Refresh] [Export]│
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │
│ │ Active      │ │ CPU Usage   │ │ Memory      │        │
│ │ 12/15       │ │ 45%         │ │ 2.4/8 GB    │        │
│ └─────────────┘ └─────────────┘ └─────────────┘        │
│                                                           │
│ Quick Actions              Recent Activity               │
│ ┌──────────────────┐ ┌──────────────────────────────┐  │
│ │ [+] New Process  │ │ 10:45 nginx started          │  │
│ │ [📅] Schedule    │ │ 10:30 backup completed       │  │
│ │ [↻] Bulk Action │ │ 10:15 api-server crashed     │  │
│ │ [📊] Reports    │ │ 10:00 health-check passed    │  │
│ └──────────────────┘ └──────────────────────────────┘  │
│                                                           │
│ Process Grid View                    [List] [Grid] [Table]│
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│ │ nginx   │ │postgres │ │ redis   │ │ worker  │       │
│ │ ● Run   │ │ ● Run   │ │ ○ Stop  │ │ ⚠ Error │       │
│ │ CPU: 2% │ │ CPU: 8% │ │ CPU: -- │ │ CPU: -- │       │
│ │ 2h 15m  │ │ 5d 3h   │ │ --      │ │ Retry 2 │       │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
└─────────────────────────────────────────────────────────┘
```

#### 2. Process Details (/processes/:id)
```
┌─────────────────────────────────────────────────────────┐
│ ← Processes / nginx                     [Edit] [Delete]  │
├─────────────────────────────────────────────────────────┤
│ Status: ● Running (PID: 1234)   [Stop] [Restart] [Kill] │
├─────────────────────────────────────────────────────────┤
│ [Overview] [Logs] [Metrics] [Config] [History]          │
├─────────────────────────────────────────────────────────┤
│ Real-time Metrics                    [1h] [6h] [24h] [7d]│
│ ┌─────────────────────────────────────────────────────┐│
│ │ CPU Usage                                           ││
│ │ 100%┤                                               ││
│ │  50%┤    ╱╲    ╱╲                                  ││
│ │   0%└────╯──╲──╯──╲─────────────────────           ││
│ │     └─────────────────────────────────┘            ││
│ │ Memory Usage                                        ││
│ │ 2GB┤                                                ││
│ │ 1GB┤━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                ││
│ │  0└─────────────────────────────────┘              ││
│ └─────────────────────────────────────────────────────┘│
│                                                           │
│ Live Logs            [Follow] [Filter] [Download] [Clear]│
│ ┌─────────────────────────────────────────────────────┐│
│ │ 2024-01-20 10:45:23 INFO  Request from 192.168.1.1 ││
│ │ 2024-01-20 10:45:24 INFO  Response 200 OK (23ms)   ││
│ │ 2024-01-20 10:45:25 WARN  High memory usage (85%)  ││
│ │ 2024-01-20 10:45:26 INFO  Cache cleared            ││
│ │ ▌                                                    ││
│ └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

#### 3. Schedules Management (/schedules)
```
┌─────────────────────────────────────────────────────────┐
│ Schedule Management                    [+ New Schedule]  │
├─────────────────────────────────────────────────────────┤
│ View: [Calendar] [List] [Timeline]    Filter: [All ▼]   │
├─────────────────────────────────────────────────────────┤
│ Calendar View                         « January 2024 »   │
│ ┌─────────────────────────────────────────────────────┐│
│ │ Sun   Mon   Tue   Wed   Thu   Fri   Sat            ││
│ │       1     2     3     4     5     6               ││
│ │       ●2am  ●2am  ●2am  ●2am  ●2am  ●2am            ││
│ │ 7     8     9     10    11    12    13              ││
│ │ ●2am  ●2am  ●2am  ●2am  ●2am  ●2am  ●2am            ││
│ │       ●6pm                                           ││
│ └─────────────────────────────────────────────────────┘│
│                                                           │
│ Active Schedules                                         │
│ ┌─────────────────────────────────────────────────────┐│
│ │ □ Daily Backup    0 2 * * *    Next: Tomorrow 2am  ││
│ │    Process: backup.sh          [ON] [Edit] [Delete] ││
│ │ □ Health Check    */5 * * * *  Next: 5 minutes     ││
│ │    Process: health.py          [OFF] [Edit] [Delete]││
│ │ □ Weekly Report   0 0 * * 0    Next: Sunday        ││
│ │    Process: report.sh          [ON] [Edit] [Delete] ││
│ └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

#### 4. Settings & Configuration (/settings)
```
┌─────────────────────────────────────────────────────────┐
│ Settings                                    [Save] [Reset]│
├────────────┬────────────────────────────────────────────┤
│ General    │ System Configuration                        │
│ Security   │ ┌────────────────────────────────────────┐ │
│ API Keys   │ │ Process Defaults                       │ │
│ Alerts     │ │ Working Directory: [/opt/processes  ]  │ │
│ Backup     │ │ Max Processes:     [50            ▼]  │ │
│ Users      │ │ Log Retention:     [30 days       ▼]  │ │
│ Theme      │ │ Default Policy:    [standard      ▼]  │ │
│            │ └────────────────────────────────────────┘ │
│            │                                             │
│            │ Resource Limits                            │
│            │ ┌────────────────────────────────────────┐ │
│            │ │ CPU Limit:         [80%           ]   │ │
│            │ │ Memory Limit:      [4GB           ]   │ │
│            │ │ Disk Usage Alert:  [90%           ]   │ │
│            │ └────────────────────────────────────────┘ │
│            │                                             │
│            │ Monitoring                                 │
│            │ ┌────────────────────────────────────────┐ │
│            │ │ ☑ Enable Prometheus metrics           │ │
│            │ │ ☑ Enable health checks                │ │
│            │ │ ☑ Send alerts via webhook             │ │
│            │ │ Webhook URL: [________________]       │ │
│            │ └────────────────────────────────────────┘ │
└────────────┴────────────────────────────────────────────┘
```

### Component Design System

#### Status Indicators
```tsx
// Process status components with consistent styling
<StatusBadge status="running" />   // 🟢 Green pulse
<StatusBadge status="stopped" />   // ⚫ Gray
<StatusBadge status="failed" />    // 🔴 Red with X
<StatusBadge status="starting" />  // 🔵 Blue spinner
<StatusBadge status="stopping" />  // 🟠 Orange fade
```

#### Command Input (Issue #10 Fix)
```tsx
// Enhanced command input with shlex parsing preview
<CommandInput 
  onSubmit={(cmd) => startProcess(cmd)}
  preview={true}  // Shows parsed arguments
  history={true}  // Command history with ↑/↓
  validation={true} // Real-time validation
/>

// Example rendering:
┌──────────────────────────────────────────────┐
│ Command: python "my script.py" --arg "value" │
│ Parsed: ['python', 'my script.py', '--arg',  │
│         'value']                              │
│ ✓ Valid command syntax                       │
└──────────────────────────────────────────────┘
```

#### Time Duration Input (Issue #11 Feature)
```tsx
// Flexible time format input component
<TimeDurationInput
  value="5h"
  onChange={(val) => setDelay(val)}
  suggestions={['30s', '5m', '1h', '6h', '24h']}
  validation={true}
/>

// Supports: 30s, 5m, 2h, 1d, combinations like "1h 30m"
```

### Mobile Responsive Design

#### Breakpoint Strategy
- Mobile: 320-768px (Single column, stacked cards)
- Tablet: 769-1024px (Two column grid)
- Desktop: 1025px+ (Full layout)

#### Mobile Navigation
```
┌─────────────────┐
│ ☰ SentinelZero  │
├─────────────────┤
│ Active: 12/15   │
├─────────────────┤
│ ┌─────────────┐ │
│ │ Process Card│ │
│ │ Swipe →     │ │
│ │ for actions │ │
│ └─────────────┘ │
│                 │
│ [+] Floating Btn│
└─────────────────┘
```

### Real-time Features

#### WebSocket Integration
```typescript
// Auto-reconnecting WebSocket for live updates
const ws = useWebSocket('/api/ws', {
  reconnectInterval: 3000,
  heartbeat: true,
  onMessage: (event) => {
    switch(event.type) {
      case 'process.status':
        updateProcessStatus(event.data);
        break;
      case 'metrics.update':
        updateMetrics(event.data);
        break;
      case 'logs.new':
        appendLog(event.data);
        break;
    }
  }
});
```

### Accessibility Features

#### WCAG 2.1 AA Compliance
- Color contrast ratios ≥ 4.5:1
- Keyboard navigation for all interactive elements
- ARIA labels and live regions for screen readers
- Focus management for modals and dialogs
- Skip navigation links

#### Keyboard Shortcuts
```
Global:
  Ctrl/Cmd + K    Quick search
  Ctrl/Cmd + N    New process
  Ctrl/Cmd + /    Keyboard shortcuts help
  
Process Page:
  S              Start process
  R              Restart process
  L              View logs
  M              View metrics
```

### Performance Optimizations

#### Code Splitting
```typescript
// Lazy load heavy components
const ProcessMetrics = lazy(() => import('./ProcessMetrics'));
const LogViewer = lazy(() => import('./LogViewer'));
const ScheduleCalendar = lazy(() => import('./ScheduleCalendar'));
```

#### Virtual Scrolling
- Log viewer: Virtual scroll for 10,000+ lines
- Process list: Virtual grid for 100+ processes
- Metrics: Canvas rendering for real-time charts

### Testing Strategy

#### Component Testing
```typescript
describe('ProcessCard', () => {
  it('displays correct status indicator');
  it('handles start/stop actions correctly');
  it('shows real-time resource usage');
  it('updates via WebSocket events');
});
```

#### E2E Testing with Playwright
```typescript
test('complete process lifecycle', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-testid="new-process"]');
  await page.fill('[name="command"]', 'echo "test"');
  await page.click('[type="submit"]');
  await expect(page.locator('.status')).toHaveText('Running');
});
```

## Accessibility

### Screen Reader Support
- Semantic command output
- Descriptive error messages
- Status announcements
- Table headers for data

### Keyboard Navigation
- Tab through options
- Arrow keys for selection
- Escape to cancel
- Enter to confirm

## Color Schemes

### Default Theme
- Success: Green (#10B981)
- Warning: Yellow (#F59E0B)
- Error: Red (#EF4444)
- Info: Blue (#3B82F6)
- Muted: Gray (#6B7280)

### High Contrast Mode
- Increased color contrast ratios
- Bold text for emphasis
- Clear status indicators

## Error Handling

### Error Categories
1. **Configuration Errors**: Missing or invalid config
2. **Permission Errors**: Insufficient privileges
3. **Resource Errors**: Port in use, file not found
4. **Process Errors**: Failed to start, crashed
5. **Validation Errors**: Invalid input

### Error Response Format
```json
{
  "error": {
    "code": "PROCESS_NOT_FOUND",
    "message": "Process 'web-server' not found",
    "details": "No process with name 'web-server' exists",
    "hint": "Use 'sentinel list' to see available processes",
    "timestamp": "2024-01-20T10:15:30Z"
  }
}
```

## Performance Considerations

### CLI Response Times
- Command execution: <100ms
- Status query: <50ms
- Log streaming: Real-time
- Auto-completion: <20ms

### Resource Usage
- Idle memory: <10MB
- Active monitoring: <50MB
- CPU usage: <1% idle, <5% active

## User Journey Maps

### First-Time User
1. Install SentinelZero
2. Run `sentinel --help`
3. Start first process with `sentinel start`
4. Check status with `sentinel status`
5. View logs with `sentinel logs`
6. Configure restart policy
7. Set up schedule

### Power User
1. Import configuration file
2. Start process groups
3. Monitor metrics
4. Customize policies
5. Export configurations
6. Integrate with CI/CD

### System Administrator
1. Deploy system-wide
2. Configure service
3. Set up monitoring
4. Manage permissions
5. Review audit logs
6. Optimize performance

## Testing Considerations

### Usability Testing
- Command discoverability
- Error message clarity
- Help documentation
- Performance perception
- Learning curve

### A/B Testing
- Command syntax variations
- Output format preferences
- Color scheme effectiveness
- Default settings

## Documentation

### In-CLI Help
- Command descriptions
- Option explanations
- Usage examples
- Common patterns

### Man Pages
- Comprehensive documentation
- Examples section
- Troubleshooting guide
- Configuration reference

### Online Documentation
- Getting started guide
- API reference
- Best practices
- Video tutorials

## Metrics & Analytics

### Usage Metrics
- Most used commands
- Common error patterns
- Performance bottlenecks
- Feature adoption

### User Feedback
- Command suggestions
- Error message improvements
- Feature requests
- Bug reports