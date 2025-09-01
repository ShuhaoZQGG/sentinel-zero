import { createSlice } from '@reduxjs/toolkit';

const schedulesSlice = createSlice({
  name: 'schedules',
  initialState: {
    schedules: [],
    loading: false,
    error: null,
  },
  reducers: {
    setSchedules: (state, action) => {
      state.schedules = action.payload;
    },
  },
});

export const { setSchedules } = schedulesSlice.actions;
export default schedulesSlice.reducer;