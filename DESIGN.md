# SentinelZero UI/UX Design Specifications

## Design System

### Brand Identity
- **Primary Color**: #0066FF (Blue)
- **Secondary Color**: #00D4AA (Teal)
- **Success**: #10B981
- **Warning**: #F59E0B
- **Error**: #EF4444
- **Background**: #F9FAFB (Light), #111827 (Dark)
- **Typography**: Inter (UI), SF Mono (Code)

### Design Principles
1. **Clarity**: Real-time process status at a glance
2. **Efficiency**: Quick access to critical actions
3. **Reliability**: Visual feedback for all operations
4. **Scalability**: Handle 100+ processes seamlessly

## User Journeys

### 1. First-Time Setup
```
Landing → Auth (Supabase) → Workspace Creation → Dashboard → Quick Start Guide
```
- OAuth integration (GitHub, Google)
- Guided onboarding with sample process
- Interactive tutorial highlights

### 2. Process Management Flow
```
Dashboard → Add Process → Configure → Monitor → Logs → Adjust Settings
```
- One-click process creation
- Template library for common tasks
- Live validation of commands

### 3. Schedule Creation
```
Processes → Schedule Tab → Add Schedule → Configure Cron → Preview → Save
```
- Visual cron builder with preview
- Calendar view of upcoming executions
- Conflict detection

### 4. Incident Response
```
Alert Notification → Dashboard → Failed Process → Logs → Restart/Debug
```
- Push notifications for failures
- One-click log access
- Suggested fixes based on error patterns

## Component Architecture

### Layout Components

#### AppShell
```
┌─────────────────────────────────────────────┐
│ TopBar (Logo | Search | User | Notifications)│
├───────────┬─────────────────────────────────┤
│ Sidebar   │                                 │
│           │     Main Content Area           │
│ Nav Menu  │                                 │
│           │                                 │
│ Quick     │                                 │
│ Actions   │                                 │
└───────────┴─────────────────────────────────┘
```

#### Navigation Structure
- **Dashboard** (Overview)
- **Processes** (List/Grid view)
- **Schedules** (Calendar/List)
- **Logs** (Aggregated view)
- **Metrics** (Charts/Stats)
- **Settings** (Config/Users)
- **API Keys** (Management)

### Page Specifications

#### 1. Dashboard
**Components:**
- SystemHealthCard (CPU, Memory, Active Processes)
- ProcessStatusGrid (Running/Stopped/Failed counts)
- RecentActivityFeed (Last 10 events)
- UpcomingSchedules (Next 5 executions)
- QuickActions (Start all, Stop all, Clear logs)

**Real-time Updates:**
- WebSocket connection indicator
- Live process status changes
- Resource usage graphs (60s refresh)

#### 2. Process Management
**List View:**
- DataTable with sortable columns
- Inline status indicators
- Bulk actions toolbar
- Search/filter sidebar

**Detail View:**
- ProcessHeader (Name, Status, PID)
- ResourceMonitor (Live CPU/Memory charts)
- LogViewer (Streaming stdout/stderr)
- ConfigurationPanel (Env vars, working dir)
- RestartPolicyEditor
- SchedulesList (Associated schedules)

**Add/Edit Modal:**
- Multi-step wizard
- Command builder with syntax highlighting
- Environment variable editor
- Restart policy configurator
- Test run capability

#### 3. Scheduling Interface
**Calendar View:**
- Monthly/Weekly/Daily views
- Drag-and-drop rescheduling
- Color coding by process
- Execution history overlay

**Schedule Builder:**
- Visual cron expression builder
- Natural language input ("Every Monday at 9am")
- Timezone selector
- Conflict checker
- Preview next 10 runs

#### 4. Logs Viewer
**Features:**
- Unified log stream
- Process filtering
- Severity levels (Info/Warning/Error)
- Full-text search
- Export functionality
- Tail mode (real-time following)

**Log Entry Format:**
```
[2024-01-15 10:23:45] [Process: backup-script] [INFO]
Starting backup operation...
```

#### 5. Metrics Dashboard
**Charts:**
- Process uptime (Bar chart)
- Resource usage trends (Line chart)
- Failure rate (Pie chart)
- Schedule execution history (Timeline)

**Stats Cards:**
- Total processes
- Average uptime
- Success rate
- Active schedules

#### 6. Settings
**Sections:**
- General (Theme, Timezone, Notifications)
- Security (2FA, Sessions, API keys)
- Team (User management, Roles)
- Integrations (Webhooks, Slack)
- Billing (Supabase integration)

## Responsive Design

### Breakpoints
- Mobile: 320px - 768px
- Tablet: 768px - 1024px
- Desktop: 1024px - 1920px
- Wide: 1920px+

### Mobile Adaptations
- Bottom navigation bar
- Collapsible process cards
- Swipe actions for quick controls
- Simplified dashboard widgets
- Full-screen modals

### Tablet Optimizations
- Split-view for list/detail
- Touch-optimized controls
- Floating action buttons
- Gesture support

## Component States

### Process Card States
1. **Running**: Green border, pulsing indicator
2. **Stopped**: Gray background, start button
3. **Failed**: Red border, error icon, retry button
4. **Starting**: Yellow border, spinner
5. **Scheduled**: Blue border, clock icon

### Interactive Elements
- **Buttons**: Hover, Active, Loading, Disabled
- **Forms**: Focus, Valid, Invalid, Submitting
- **Tables**: Hover row, Selected, Sorting
- **Cards**: Default, Hover, Selected, Dragging

## Accessibility Requirements

### WCAG 2.1 AA Compliance
- Color contrast ratio: 4.5:1 minimum
- Keyboard navigation for all features
- Screen reader announcements
- Focus indicators
- Alt text for icons
- ARIA labels and landmarks

### Keyboard Shortcuts
- `Cmd+K`: Global search
- `Cmd+N`: New process
- `Cmd+S`: Save changes
- `Cmd+/`: Keyboard shortcuts help
- `Space`: Start/stop selected process
- `L`: View logs
- `R`: Restart process

## Real-time Features

### WebSocket Events
```javascript
// Connection status indicator
ws.onopen: "Connected" (green)
ws.onclose: "Disconnected" (red)
ws.reconnecting: "Reconnecting..." (yellow)

// Live updates
process.status.changed
process.resource.update
schedule.executed
log.new.entry
alert.triggered
```

### Optimistic UI Updates
- Immediate visual feedback
- Rollback on server error
- Loading states for async operations
- Skeleton screens for initial loads

## Error Handling

### User-Friendly Messages
- "Process failed to start" → Show reason + suggestion
- "Schedule conflict" → Highlight conflicting times
- "Connection lost" → Auto-retry with countdown
- "Permission denied" → Clear action required

### Recovery Actions
- Retry buttons with exponential backoff
- Fallback to cached data
- Graceful degradation
- Clear error boundaries

## Performance Optimizations

### Frontend
- Code splitting by route
- Lazy loading for modals
- Virtual scrolling for large lists
- Debounced search inputs
- Memoized expensive computations
- Service worker for offline support

### Data Management
- Pagination (25 items default)
- Infinite scroll option
- Client-side caching
- Optimistic updates
- Background data refresh

## Integration Points

### Supabase Auth UI
- Pre-built auth components
- Social login buttons
- Password reset flow
- Email verification
- Session management

### API Integration
- REST endpoints visualization
- WebSocket connection status
- Rate limit indicators
- Request/response inspector

### Third-party Services
- Slack notification preview
- Webhook configuration UI
- Prometheus metrics export
- Docker status integration

## Mobile App Considerations

### React Native Components
- NativeProcessCard
- NativeLogViewer
- NativeSchedulePicker
- Push notification handler
- Biometric authentication

### Platform-Specific
- iOS: Haptic feedback, 3D touch
- Android: Material Design, back button
- Deep linking support
- Background sync

## Design Mockups

### Dashboard Wireframe
```
┌──────────────────────────────────────────────┐
│ ■ SentinelZero        🔍 Search    👤 ▼ 🔔 3 │
├──────────────────────────────────────────────┤
│ System Health              Quick Stats        │
│ ┌──────────┐ ┌──────────┐ ╔════════════════╗ │
│ │ CPU: 45% │ │ Mem: 2.1G│ ║ Running    12  ║ │
│ │ ▁▃▅▇▅▃▁  │ │ ▁▃▅▇▅▃▁  │ ║ Stopped     5  ║ │
│ └──────────┘ └──────────┘ ║ Failed      2  ║ │
│                            ╚════════════════╝ │
│                                               │
│ Active Processes                              │
│ ┌────────────────────────────────────────┐   │
│ │ 🟢 backup-daily     | CPU: 12% | 2.5h  │   │
│ │ 🟢 api-server       | CPU: 23% | 5d    │   │
│ │ 🔴 data-sync        | FAILED   | Retry  │   │
│ └────────────────────────────────────────┘   │
│                                               │
│ Upcoming Schedules                            │
│ ┌────────────────────────────────────────┐   │
│ │ 14:00  backup-daily    (in 2 hours)    │   │
│ │ 18:00  report-gen      (in 6 hours)    │   │
│ │ 02:00  cleanup         (tomorrow)      │   │
│ └────────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
```

### Process Detail View
```
┌──────────────────────────────────────────────┐
│ ← Back    backup-daily          [Stop] [Edit]│
├──────────────────────────────────────────────┤
│ Status: 🟢 Running | PID: 12345 | Uptime: 2h │
├──────────────────────────────────────────────┤
│ Resources          │ Configuration            │
│ CPU ▁▃▅▇▅▃▁ 12%   │ Command: backup.sh       │
│ MEM ▁▁▁▃▁▁▁ 256MB │ Dir: /var/backups        │
│                    │ Restart: On failure (3x) │
├────────────────────┴─────────────────────────┤
│ Logs                              [Clear][↓]  │
│ ┌────────────────────────────────────────┐   │
│ │ 2024-01-15 10:23:45 Starting backup... │   │
│ │ 2024-01-15 10:23:46 Scanning files...  │   │
│ │ 2024-01-15 10:24:12 Compressed 1.2GB   │   │
│ │ 2024-01-15 10:25:33 Upload complete    │   │
│ └────────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
```

## Implementation Framework

### React Component Structure
```
src/
├── components/
│   ├── common/
│   │   ├── Button/
│   │   ├── Card/
│   │   └── Modal/
│   ├── process/
│   │   ├── ProcessCard/
│   │   ├── ProcessList/
│   │   └── ProcessDetail/
│   ├── schedule/
│   │   ├── ScheduleCalendar/
│   │   └── CronBuilder/
│   └── layout/
│       ├── AppShell/
│       ├── Sidebar/
│       └── TopBar/
├── pages/
│   ├── Dashboard/
│   ├── Processes/
│   ├── Schedules/
│   └── Settings/
└── hooks/
    ├── useWebSocket/
    ├── useProcess/
    └── useSupabase/
```

### State Management (Redux Toolkit)
```javascript
store/
├── processes/
│   ├── slice.ts
│   └── api.ts
├── schedules/
├── logs/
├── metrics/
└── auth/
```

## Next Phase Handoff

### Development Priorities
1. Implement Dashboard with real-time updates
2. Create Process management CRUD
3. Build WebSocket connection manager
4. Integrate Supabase Auth UI
5. Add responsive mobile views

### Design Assets Needed
- Icon set (Process states, actions)
- Loading animations
- Empty state illustrations
- Error illustrations
- Onboarding graphics

### Technical Constraints
- React 18+ for concurrent features
- Material-UI v5 for components
- Recharts for data visualization
- Socket.io for WebSocket
- React Query for API state