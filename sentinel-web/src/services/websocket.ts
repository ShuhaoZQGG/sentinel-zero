import { io, Socket } from 'socket.io-client';
import { store } from '../store/store';
import { updateProcess, removeProcess } from '../store/slices/processesSlice';
import { updateMetrics } from '../store/slices/metricsSlice';
import { addLogEntry } from '../store/slices/logsSlice';

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect(token: string) {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    
    this.socket = io(apiUrl, {
      auth: {
        token,
      },
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectDelay,
    });

    this.setupEventListeners();
  }

  private setupEventListeners() {
    if (!this.socket) return;

    // Connection events
    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.subscribeToUpdates();
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.handleReconnect();
    });

    // Process events
    this.socket.on('process:update', (data) => {
      store.dispatch(updateProcess(data));
    });

    this.socket.on('process:started', (data) => {
      store.dispatch(updateProcess({ ...data, status: 'running' }));
    });

    this.socket.on('process:stopped', (data) => {
      store.dispatch(updateProcess({ ...data, status: 'stopped' }));
    });

    this.socket.on('process:crashed', (data) => {
      store.dispatch(updateProcess({ ...data, status: 'failed' }));
    });

    this.socket.on('process:removed', (processId) => {
      store.dispatch(removeProcess(processId));
    });

    // Metrics events
    this.socket.on('metrics:update', (data) => {
      store.dispatch(updateMetrics(data));
    });

    this.socket.on('metrics:system', (data) => {
      store.dispatch(updateMetrics({ systemMetrics: data }));
    });

    this.socket.on('metrics:process', (data) => {
      const { processId, ...metrics } = data;
      store.dispatch(updateProcess({ id: processId, ...metrics }));
    });

    // Log events
    this.socket.on('log:entry', (data) => {
      store.dispatch(addLogEntry(data));
    });

    this.socket.on('log:stream', (data) => {
      const { processId, content, type } = data;
      store.dispatch(addLogEntry({
        processId,
        content,
        type,
        timestamp: new Date().toISOString(),
      }));
    });

    // Schedule events
    this.socket.on('schedule:triggered', (data) => {
      console.log('Schedule triggered:', data);
    });

    this.socket.on('schedule:next_run', (data) => {
      // Update schedule next run time
    });

    // Error events
    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error);
    });
  }

  private subscribeToUpdates() {
    if (!this.socket) return;

    // Subscribe to all process updates
    this.socket.emit('subscribe:processes');
    
    // Subscribe to system metrics
    this.socket.emit('subscribe:metrics');
    
    // Subscribe to logs for all processes
    const state = store.getState();
    const processes = state.processes.processes;
    processes.forEach(process => {
      this.subscribeToProcess(process.id);
    });
  }

  subscribeToProcess(processId: string) {
    if (!this.socket) return;
    this.socket.emit('subscribe:process', processId);
  }

  unsubscribeFromProcess(processId: string) {
    if (!this.socket) return;
    this.socket.emit('unsubscribe:process', processId);
  }

  subscribeToLogs(processId: string) {
    if (!this.socket) return;
    this.socket.emit('subscribe:logs', processId);
  }

  unsubscribeFromLogs(processId: string) {
    if (!this.socket) return;
    this.socket.emit('unsubscribe:logs', processId);
  }

  sendCommand(command: string, data?: any) {
    if (!this.socket) return;
    this.socket.emit(command, data);
  }

  private handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      if (this.socket) {
        this.socket.connect();
      }
    }, delay);
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export default new WebSocketService();