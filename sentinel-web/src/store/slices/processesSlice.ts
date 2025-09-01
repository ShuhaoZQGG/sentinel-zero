import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';

interface Process {
  id: string;
  name: string;
  command: string;
  status: 'running' | 'stopped' | 'failed' | 'pending';
  pid?: number;
  cpu_percent?: number;
  memory_percent?: number;
  started_at?: string;
  stopped_at?: string;
  environment?: Record<string, string>;
  working_directory?: string;
  restart_policy?: string;
  schedule?: string;
}

interface ProcessesState {
  processes: Process[];
  loading: boolean;
  error: string | null;
}

const initialState: ProcessesState = {
  processes: [],
  loading: false,
  error: null,
};

// Async thunks
export const fetchProcesses = createAsyncThunk(
  'processes/fetchProcesses',
  async () => {
    const response = await axios.get('/api/processes');
    return response.data;
  }
);

export const startProcess = createAsyncThunk(
  'processes/startProcess',
  async (processId: string) => {
    const response = await axios.post(`/api/processes/${processId}/start`);
    return response.data;
  }
);

export const stopProcess = createAsyncThunk(
  'processes/stopProcess',
  async (processId: string) => {
    const response = await axios.post(`/api/processes/${processId}/stop`);
    return response.data;
  }
);

export const restartProcess = createAsyncThunk(
  'processes/restartProcess',
  async (processId: string) => {
    const response = await axios.post(`/api/processes/${processId}/restart`);
    return response.data;
  }
);

export const createProcess = createAsyncThunk(
  'processes/createProcess',
  async (processData: Partial<Process>) => {
    const response = await axios.post('/api/processes', processData);
    return response.data;
  }
);

export const deleteProcess = createAsyncThunk(
  'processes/deleteProcess',
  async (processId: string) => {
    await axios.delete(`/api/processes/${processId}`);
    return processId;
  }
);

const processesSlice = createSlice({
  name: 'processes',
  initialState,
  reducers: {
    setProcesses: (state, action: PayloadAction<Process[]>) => {
      state.processes = action.payload;
    },
    updateProcess: (state, action: PayloadAction<Partial<Process> & { id: string }>) => {
      const index = state.processes.findIndex(p => p.id === action.payload.id);
      if (index !== -1) {
        state.processes[index] = { ...state.processes[index], ...action.payload };
      }
    },
    removeProcess: (state, action: PayloadAction<string>) => {
      state.processes = state.processes.filter(p => p.id !== action.payload);
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch processes
      .addCase(fetchProcesses.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchProcesses.fulfilled, (state, action) => {
        state.loading = false;
        state.processes = action.payload;
      })
      .addCase(fetchProcesses.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch processes';
      })
      // Start process
      .addCase(startProcess.fulfilled, (state, action) => {
        const index = state.processes.findIndex(p => p.id === action.payload.id);
        if (index !== -1) {
          state.processes[index] = action.payload;
        }
      })
      // Stop process
      .addCase(stopProcess.fulfilled, (state, action) => {
        const index = state.processes.findIndex(p => p.id === action.payload.id);
        if (index !== -1) {
          state.processes[index] = action.payload;
        }
      })
      // Restart process
      .addCase(restartProcess.fulfilled, (state, action) => {
        const index = state.processes.findIndex(p => p.id === action.payload.id);
        if (index !== -1) {
          state.processes[index] = action.payload;
        }
      })
      // Create process
      .addCase(createProcess.fulfilled, (state, action) => {
        state.processes.push(action.payload);
      })
      // Delete process
      .addCase(deleteProcess.fulfilled, (state, action) => {
        state.processes = state.processes.filter(p => p.id !== action.payload);
      });
  },
});

export const { setProcesses, updateProcess, removeProcess, setLoading, setError } = processesSlice.actions;
export default processesSlice.reducer;