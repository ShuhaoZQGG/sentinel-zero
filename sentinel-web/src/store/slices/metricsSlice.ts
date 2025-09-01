import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';

interface SystemMetrics {
  cpu_percent: number;
  memory_percent: number;
  disk_usage: number;
  network_io: {
    bytes_sent: number;
    bytes_recv: number;
  };
  process_count: number;
  uptime: number;
}

interface ProcessMetrics {
  processId: string;
  cpu_percent: number;
  memory_percent: number;
  memory_mb: number;
  threads: number;
  open_files: number;
  connections: number;
}

interface MetricsState {
  systemMetrics: SystemMetrics | null;
  processMetrics: Record<string, ProcessMetrics>;
  loading: boolean;
  error: string | null;
}

const initialState: MetricsState = {
  systemMetrics: null,
  processMetrics: {},
  loading: false,
  error: null,
};

// Async thunks
export const fetchMetrics = createAsyncThunk(
  'metrics/fetchMetrics',
  async () => {
    const response = await axios.get('/api/metrics/system');
    return response.data;
  }
);

export const fetchProcessMetrics = createAsyncThunk(
  'metrics/fetchProcessMetrics',
  async (processId: string) => {
    const response = await axios.get(`/api/metrics/process/${processId}`);
    return { processId, metrics: response.data };
  }
);

const metricsSlice = createSlice({
  name: 'metrics',
  initialState,
  reducers: {
    setMetrics: (state, action: PayloadAction<SystemMetrics>) => {
      state.systemMetrics = action.payload;
    },
    updateMetrics: (state, action: PayloadAction<Partial<MetricsState>>) => {
      if (action.payload.systemMetrics) {
        state.systemMetrics = action.payload.systemMetrics;
      }
      if (action.payload.processMetrics) {
        state.processMetrics = { ...state.processMetrics, ...action.payload.processMetrics };
      }
    },
    setProcessMetrics: (state, action: PayloadAction<{ processId: string; metrics: ProcessMetrics }>) => {
      state.processMetrics[action.payload.processId] = action.payload.metrics;
    },
    clearProcessMetrics: (state, action: PayloadAction<string>) => {
      delete state.processMetrics[action.payload];
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch system metrics
      .addCase(fetchMetrics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchMetrics.fulfilled, (state, action) => {
        state.loading = false;
        state.systemMetrics = action.payload;
      })
      .addCase(fetchMetrics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch metrics';
      })
      // Fetch process metrics
      .addCase(fetchProcessMetrics.fulfilled, (state, action) => {
        const { processId, metrics } = action.payload;
        state.processMetrics[processId] = metrics;
      });
  },
});

export const { setMetrics, updateMetrics, setProcessMetrics, clearProcessMetrics } = metricsSlice.actions;
export default metricsSlice.reducer;