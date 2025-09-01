import { createSlice } from '@reduxjs/toolkit';

const processesSlice = createSlice({
  name: 'processes',
  initialState: {
    processes: [],
    loading: false,
    error: null,
  },
  reducers: {
    setProcesses: (state, action) => {
      state.processes = action.payload;
    },
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
    },
  },
});

export const { setProcesses, setLoading, setError } = processesSlice.actions;
export default processesSlice.reducer;