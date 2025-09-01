import { createSlice } from '@reduxjs/toolkit';

const metricsSlice = createSlice({
  name: 'metrics',
  initialState: {
    metrics: [],
    loading: false,
  },
  reducers: {
    setMetrics: (state, action) => {
      state.metrics = action.payload;
    },
  },
});

export const { setMetrics } = metricsSlice.actions;
export default metricsSlice.reducer;