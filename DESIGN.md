# SentinelZero UI/UX Design Specifications

## Design System

### Brand Identity
- **Primary Color**: #2563eb (Blue 600)
- **Secondary Color**: #10b981 (Emerald 500)
- **Danger Color**: #ef4444 (Red 500)
- **Warning Color**: #f59e0b (Amber 500)
- **Typography**: Inter/SF Pro for UI, JetBrains Mono for code
- **Icon Set**: Heroicons v2

### Component Library
- **Framework**: React 18 with TypeScript
- **UI Library**: Material-UI v5 / Tailwind CSS
- **State Management**: Redux Toolkit + RTK Query
- **Forms**: React Hook Form + Zod validation
- **Charts**: Recharts for metrics visualization
- **Tables**: TanStack Table v8

## User Journeys

### 1. First-Time User Setup
```
Landing → Sign Up → Email Verification → Dashboard Setup → Create First Process → View Status
```

### 2. Process Management Flow
```
Dashboard → Add Process → Configure (Command/Env/Schedule) → Start → Monitor → View Logs
```

### 3. Incident Response Flow
```
Alert Notification → Dashboard (Red Status) → Process Details → View Logs → Restart/Fix → Monitor Recovery
```

### 4. Multi-Tenant Admin Flow
```
Admin Login → Tenant Selection → User Management → Resource Allocation → Billing Dashboard
```

## Page Specifications

### 1. Dashboard (/)
**Layout**: Responsive grid with real-time updates via WebSocket

**Components**:
- **Header**: Logo, search bar, notifications bell, user menu
- **Stats Cards**: 
  - Active Processes (green)
  - Failed Processes (red)
  - Scheduled Tasks (blue)
  - System Resources (purple)
- **Process List Table**:
  - Columns: Name, Status, CPU%, Memory, Uptime, Actions
  - Inline actions: Start/Stop, Restart, View, Delete
  - Bulk selection for batch operations
- **Activity Timeline**: Recent events with color-coded severity
- **Quick Actions FAB**: Add Process, Add Schedule

### 2. Process Details (/process/:id)
**Layout**: Master-detail with tabs

**Sections**:
- **Header**: Process name, status badge, action buttons
- **Tabs**:
  - **Overview**: Real-time metrics charts (CPU/Memory over time)
  - **Logs**: Searchable, filterable log viewer with tail -f mode
  - **Configuration**: Editable form for command, env vars, working directory
  - **Restart Policy**: Visual editor for retry rules
  - **Schedules**: Associated cron schedules
  - **History**: Execution history with exit codes

### 3. Schedules (/schedules)
**Layout**: Calendar view + list view toggle

**Features**:
- **Calendar View**: Month/week/day views showing scheduled executions
- **List View**: Sortable table with next run time
- **Add Schedule Modal**:
  - Cron expression builder with visual preview
  - Natural language input ("every day at 2am")
  - Test execution button

### 4. Workflows (/workflows) - New
**Layout**: DAG editor with drag-and-drop

**Components**:
- **Canvas**: Visual workflow designer
- **Node Library**: Draggable process templates
- **Properties Panel**: Node configuration
- **Execution View**: Real-time workflow progress
- **Version History**: Workflow versioning with diff view

### 5. Settings (/settings)
**Layout**: Vertical tabs navigation

**Sections**:
- **Profile**: User info, avatar, timezone
- **Security**: Password change, 2FA, API keys
- **Notifications**: Alert preferences matrix
- **Team**: User management (admin only)
- **Billing**: Usage metrics, plan selection
- **Integration**: Webhook configuration, external services

### 6. Mobile App Design

**Navigation**: Bottom tab bar
- Dashboard (home icon)
- Processes (server icon)
- Schedules (calendar icon)
- Alerts (bell icon)
- Settings (gear icon)

**Key Screens**:
- **Dashboard**: Simplified card view, pull-to-refresh
- **Process Card**: Swipe actions (restart, stop)
- **Quick Actions**: Floating action button for emergency restart
- **Push Notifications**: Critical alerts with action buttons

## Responsive Breakpoints
- **Mobile**: 320px - 768px (single column, bottom nav)
- **Tablet**: 768px - 1024px (dual column, side nav collapsed)
- **Desktop**: 1024px+ (full layout, expanded side nav)

## Accessibility Requirements
- **WCAG 2.1 AA Compliance**
- **Keyboard Navigation**: Full tab support, shortcuts (? for help)
- **Screen Readers**: ARIA labels, live regions for status updates
- **Color Contrast**: 4.5:1 minimum ratio
- **Focus Indicators**: Visible focus rings
- **Error Messages**: Clear, actionable error descriptions

## Interactive Elements

### Forms
- **Inline validation** with debounced API checks
- **Auto-save** for configuration changes
- **Undo/Redo** support for critical actions
- **Smart defaults** based on usage patterns

### Tables
- **Virtual scrolling** for large datasets
- **Column resizing** and reordering
- **Sticky headers** and first column
- **Export** to CSV/JSON

### Real-Time Updates
- **WebSocket indicators**: Connection status badge
- **Optimistic updates**: Immediate UI feedback
- **Retry logic**: Automatic reconnection
- **Offline mode**: Queue actions for sync

## Multi-Tenant Considerations

### Tenant Switching
- **Dropdown selector** in header
- **Recent tenants** quick access
- **Visual tenant indicator** (color/logo)

### Permission-Based UI
- **Role badges**: Admin/User/Viewer
- **Disabled states** for unauthorized actions
- **Feature flags** for tenant-specific features

## Performance Targets
- **Initial Load**: < 3s (LCP)
- **Interaction**: < 100ms (FID)
- **Layout Shift**: < 0.1 (CLS)
- **Bundle Size**: < 500KB gzipped
- **API Response**: < 200ms p95

## Monitoring & Analytics
- **User behavior tracking**: Mixpanel/Amplitude
- **Error monitoring**: Sentry integration
- **Performance monitoring**: Web Vitals
- **Feature usage**: Custom events
- **A/B testing**: Feature flag framework

## Security UI Patterns
- **Session timeout** warnings
- **Secure input fields** for sensitive data
- **Copy protection** for API keys
- **Audit log** viewer for compliance
- **Data masking** in logs for PII

## Future Enhancements
- **Dark mode** with system preference detection
- **Customizable dashboards** with widget library
- **Process templates** marketplace
- **Collaborative features** (comments, sharing)
- **AI-powered insights** and anomaly detection