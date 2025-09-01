import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import processesReducer from './slices/processesSlice';
import schedulesReducer from './slices/schedulesSlice';
import metricsReducer from './slices/metricsSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    processes: processesReducer,
    schedules: schedulesReducer,
    metrics: metricsReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;