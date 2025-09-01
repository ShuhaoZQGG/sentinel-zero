import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';

interface LogEntry {
  id: string;
  processId: string;
  content: string;
  type: 'stdout' | 'stderr' | 'system';
  timestamp: string;
  level?: 'info' | 'warning' | 'error' | 'debug';
}

interface LogsState {
  logs: Record<string, LogEntry[]>; // Grouped by processId
  loading: boolean;
  error: string | null;
  filter: {
    processId?: string;
    type?: string;
    level?: string;
    searchTerm?: string;
  };
}

const initialState: LogsState = {
  logs: {},
  loading: false,
  error: null,
  filter: {},
};

// Async thunks
export const fetchLogs = createAsyncThunk(
  'logs/fetchLogs',
  async (processId: string) => {
    const response = await axios.get(`/api/metrics/logs/${processId}`);
    return { processId, logs: response.data };
  }
);

export const clearLogs = createAsyncThunk(
  'logs/clearLogs',
  async (processId: string) => {
    await axios.delete(`/api/metrics/logs/${processId}`);
    return processId;
  }
);

const logsSlice = createSlice({
  name: 'logs',
  initialState,
  reducers: {
    addLogEntry: (state, action: PayloadAction<LogEntry>) => {
      const { processId } = action.payload;
      if (!state.logs[processId]) {
        state.logs[processId] = [];
      }
      state.logs[processId].push(action.payload);
      // Keep only last 1000 logs per process
      if (state.logs[processId].length > 1000) {
        state.logs[processId] = state.logs[processId].slice(-1000);
      }
    },
    setLogFilter: (state, action: PayloadAction<Partial<LogsState['filter']>>) => {
      state.filter = { ...state.filter, ...action.payload };
    },
    clearProcessLogs: (state, action: PayloadAction<string>) => {
      delete state.logs[action.payload];
    },
    clearAllLogs: (state) => {
      state.logs = {};
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchLogs.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchLogs.fulfilled, (state, action) => {
        state.loading = false;
        const { processId, logs } = action.payload;
        state.logs[processId] = logs;
      })
      .addCase(fetchLogs.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch logs';
      })
      .addCase(clearLogs.fulfilled, (state, action) => {
        delete state.logs[action.payload];
      });
  },
});

export const { addLogEntry, setLogFilter, clearProcessLogs, clearAllLogs } = logsSlice.actions;
export default logsSlice.reducer;