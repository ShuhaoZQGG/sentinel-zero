import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import ProcessDetails from './ProcessDetails';
import processesReducer from '../store/slices/processesSlice';
import logsReducer from '../store/slices/logsSlice';
import metricsReducer from '../store/slices/metricsSlice';

// Create a test store
const createTestStore = (initialState?: any) => {
  return configureStore({
    reducer: {
      processes: processesReducer,
      logs: logsReducer,
      metrics: metricsReducer,
    },
    preloadedState: initialState,
  });
};

// Helper to render component with providers
const renderWithProviders = (ui: React.ReactElement, { initialState = {}, route = '/process/test-id' } = {}) => {
  const store = createTestStore(initialState);
  window.history.pushState({}, 'Test page', route);
  
  return {
    ...render(
      <Provider store={store}>
        <BrowserRouter>
          <Routes>
            <Route path="/process/:id" element={ui} />
          </Routes>
        </BrowserRouter>
      </Provider>
    ),
    store,
  };
};

describe('ProcessDetails', () => {
  const mockProcess = {
    id: 'test-id',
    name: 'test-process',
    command: 'python script.py',
    status: 'running' as const,
    pid: 12345,
    cpu_percent: 25.5,
    memory_percent: 10.2,
    started_at: '2025-09-01T10:00:00Z',
    environment: { NODE_ENV: 'production' },
    working_directory: '/app',
    restart_policy: 'on-failure:3',
  };

  const mockLogs = [
    { timestamp: '2025-09-01T10:00:01Z', level: 'info', message: 'Process started' },
    { timestamp: '2025-09-01T10:00:02Z', level: 'error', message: 'Connection failed' },
  ];

  const mockMetrics = {
    cpu: [
      { timestamp: '10:00', value: 20 },
      { timestamp: '10:01', value: 25 },
      { timestamp: '10:02', value: 30 },
    ],
    memory: [
      { timestamp: '10:00', value: 100 },
      { timestamp: '10:01', value: 105 },
      { timestamp: '10:02', value: 110 },
    ],
  };

  describe('Process Information Tab', () => {
    it('should display process basic information', () => {
      const initialState = {
        processes: {
          processes: [mockProcess],
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<ProcessDetails />, { initialState });

      expect(screen.getByText('test-process')).toBeInTheDocument();
      expect(screen.getByText('python script.py')).toBeInTheDocument();
      expect(screen.getByText('Running')).toBeInTheDocument();
      expect(screen.getByText('PID: 12345')).toBeInTheDocument();
    });

    it('should display environment variables', () => {
      const initialState = {
        processes: {
          processes: [mockProcess],
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<ProcessDetails />, { initialState });

      expect(screen.getByText('Environment Variables')).toBeInTheDocument();
      expect(screen.getByText('NODE_ENV')).toBeInTheDocument();
      expect(screen.getByText('production')).toBeInTheDocument();
    });

    it('should display restart policy', () => {
      const initialState = {
        processes: {
          processes: [mockProcess],
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<ProcessDetails />, { initialState });

      expect(screen.getByText('Restart Policy')).toBeInTheDocument();
      expect(screen.getByText('on-failure:3')).toBeInTheDocument();
    });
  });

  describe('Process Actions', () => {
    it('should have start, stop, and restart buttons', () => {
      const initialState = {
        processes: {
          processes: [mockProcess],
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<ProcessDetails />, { initialState });

      expect(screen.getByRole('button', { name: /stop/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /restart/i })).toBeInTheDocument();
    });

    it('should disable stop button when process is stopped', () => {
      const stoppedProcess = { ...mockProcess, status: 'stopped' as const };
      const initialState = {
        processes: {
          processes: [stoppedProcess],
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<ProcessDetails />, { initialState });

      expect(screen.getByRole('button', { name: /stop/i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /start/i })).toBeEnabled();
    });
  });

  describe('Metrics Tab', () => {
    it('should display CPU and memory charts', async () => {
      const initialState = {
        processes: {
          processes: [mockProcess],
          loading: false,
          error: null,
        },
        metrics: {
          data: mockMetrics,
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<ProcessDetails />, { initialState });

      // Click on Metrics tab
      const metricsTab = screen.getByRole('tab', { name: /metrics/i });
      await userEvent.click(metricsTab);

      expect(screen.getByText('CPU Usage (%)')).toBeInTheDocument();
      expect(screen.getByText('Memory Usage (MB)')).toBeInTheDocument();
    });

    it('should display current resource usage', async () => {
      const initialState = {
        processes: {
          processes: [mockProcess],
          loading: false,
          error: null,
        },
        metrics: {
          data: mockMetrics,
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<ProcessDetails />, { initialState });

      const metricsTab = screen.getByRole('tab', { name: /metrics/i });
      await userEvent.click(metricsTab);

      expect(screen.getByText('25.5%')).toBeInTheDocument(); // CPU
      expect(screen.getByText('10.2%')).toBeInTheDocument(); // Memory
    });
  });

  describe('Logs Tab', () => {
    it('should display process logs', async () => {
      const initialState = {
        processes: {
          processes: [mockProcess],
          loading: false,
          error: null,
        },
        logs: {
          logs: mockLogs,
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<ProcessDetails />, { initialState });

      // Click on Logs tab
      const logsTab = screen.getByRole('tab', { name: /logs/i });
      await userEvent.click(logsTab);

      expect(screen.getByText('Process started')).toBeInTheDocument();
      expect(screen.getByText('Connection failed')).toBeInTheDocument();
    });

    it('should have log level filters', async () => {
      const initialState = {
        processes: {
          processes: [mockProcess],
          loading: false,
          error: null,
        },
        logs: {
          logs: mockLogs,
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<ProcessDetails />, { initialState });

      const logsTab = screen.getByRole('tab', { name: /logs/i });
      await userEvent.click(logsTab);

      expect(screen.getByRole('button', { name: /info/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /error/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /warning/i })).toBeInTheDocument();
    });

    it('should have auto-scroll toggle', async () => {
      const initialState = {
        processes: {
          processes: [mockProcess],
          loading: false,
          error: null,
        },
        logs: {
          logs: mockLogs,
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<ProcessDetails />, { initialState });

      const logsTab = screen.getByRole('tab', { name: /logs/i });
      await userEvent.click(logsTab);

      expect(screen.getByRole('checkbox', { name: /auto-scroll/i })).toBeInTheDocument();
    });
  });

  describe('Configuration Tab', () => {
    it('should display editable configuration', async () => {
      const initialState = {
        processes: {
          processes: [mockProcess],
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<ProcessDetails />, { initialState });

      const configTab = screen.getByRole('tab', { name: /configuration/i });
      await userEvent.click(configTab);

      expect(screen.getByLabelText(/command/i)).toHaveValue('python script.py');
      expect(screen.getByLabelText(/working directory/i)).toHaveValue('/app');
    });

    it('should have save and cancel buttons in edit mode', async () => {
      const initialState = {
        processes: {
          processes: [mockProcess],
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<ProcessDetails />, { initialState });

      const configTab = screen.getByRole('tab', { name: /configuration/i });
      await userEvent.click(configTab);

      const editButton = screen.getByRole('button', { name: /edit/i });
      await userEvent.click(editButton);

      expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });
  });

  describe('Error States', () => {
    it('should display error when process not found', () => {
      const initialState = {
        processes: {
          processes: [],
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<ProcessDetails />, { initialState });

      expect(screen.getByText(/process not found/i)).toBeInTheDocument();
    });

    it('should display loading state', () => {
      const initialState = {
        processes: {
          processes: [],
          loading: true,
          error: null,
        },
      };

      renderWithProviders(<ProcessDetails />, { initialState });

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });
});