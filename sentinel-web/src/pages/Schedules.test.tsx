import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import Schedules from './Schedules';
import schedulesReducer from '../store/slices/schedulesSlice';
import processesReducer from '../store/slices/processesSlice';

// Create a test store
const createTestStore = (initialState?: any) => {
  return configureStore({
    reducer: {
      schedules: schedulesReducer,
      processes: processesReducer,
    },
    preloadedState: initialState,
  });
};

// Helper to render component with providers
const renderWithProviders = (ui: React.ReactElement, { initialState = {} } = {}) => {
  const store = createTestStore(initialState);
  
  return {
    ...render(
      <Provider store={store}>
        <BrowserRouter>
          {ui}
        </BrowserRouter>
      </Provider>
    ),
    store,
  };
};

describe('Schedules', () => {
  const mockSchedules = [
    {
      id: 'sched-1',
      name: 'Daily Backup',
      process_id: 'proc-1',
      process_name: 'backup-script',
      schedule_type: 'cron',
      cron_expression: '0 2 * * *',
      next_run: '2025-09-02T02:00:00Z',
      last_run: '2025-09-01T02:00:00Z',
      enabled: true,
      status: 'active',
    },
    {
      id: 'sched-2',
      name: 'Hourly Health Check',
      process_id: 'proc-2',
      process_name: 'health-check',
      schedule_type: 'interval',
      interval: 3600,
      interval_unit: 'seconds',
      next_run: '2025-09-01T11:00:00Z',
      last_run: '2025-09-01T10:00:00Z',
      enabled: true,
      status: 'active',
    },
    {
      id: 'sched-3',
      name: 'Weekly Report',
      process_id: 'proc-3',
      process_name: 'generate-report',
      schedule_type: 'cron',
      cron_expression: '0 9 * * 1',
      next_run: '2025-09-08T09:00:00Z',
      last_run: '2025-08-26T09:00:00Z',
      enabled: false,
      status: 'inactive',
    },
  ];

  const mockProcesses = [
    { id: 'proc-1', name: 'backup-script', command: 'python backup.py' },
    { id: 'proc-2', name: 'health-check', command: 'curl health.endpoint' },
    { id: 'proc-3', name: 'generate-report', command: 'python report.py' },
    { id: 'proc-4', name: 'unused-process', command: 'echo test' },
  ];

  describe('Schedule List View', () => {
    it('should display all schedules in a table', () => {
      const initialState = {
        schedules: {
          schedules: mockSchedules,
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<Schedules />, { initialState });

      expect(screen.getByText('Daily Backup')).toBeInTheDocument();
      expect(screen.getByText('Hourly Health Check')).toBeInTheDocument();
      expect(screen.getByText('Weekly Report')).toBeInTheDocument();
    });

    it('should display schedule details in table columns', () => {
      const initialState = {
        schedules: {
          schedules: [mockSchedules[0]],
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<Schedules />, { initialState });

      expect(screen.getByText('backup-script')).toBeInTheDocument();
      expect(screen.getByText('0 2 * * *')).toBeInTheDocument();
      expect(screen.getByText('Cron')).toBeInTheDocument();
    });

    it('should show enabled/disabled status with toggle', () => {
      const initialState = {
        schedules: {
          schedules: mockSchedules,
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<Schedules />, { initialState });

      const toggles = screen.getAllByRole('checkbox');
      expect(toggles[0]).toBeChecked(); // Daily Backup - enabled
      expect(toggles[1]).toBeChecked(); // Hourly Health Check - enabled
      expect(toggles[2]).not.toBeChecked(); // Weekly Report - disabled
    });

    it('should have action buttons for each schedule', () => {
      const initialState = {
        schedules: {
          schedules: [mockSchedules[0]],
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<Schedules />, { initialState });

      expect(screen.getByRole('button', { name: /run now/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
    });
  });

  describe('Calendar View', () => {
    it('should have a toggle to switch between list and calendar view', async () => {
      const initialState = {
        schedules: {
          schedules: mockSchedules,
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<Schedules />, { initialState });

      const calendarButton = screen.getByRole('button', { name: /calendar/i });
      expect(calendarButton).toBeInTheDocument();
      
      await userEvent.click(calendarButton);
      
      // Calendar should be visible
      expect(screen.getByTestId('calendar-view')).toBeInTheDocument();
    });

    it('should display schedules on calendar dates', async () => {
      const initialState = {
        schedules: {
          schedules: mockSchedules,
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<Schedules />, { initialState });

      const calendarButton = screen.getByRole('button', { name: /calendar/i });
      await userEvent.click(calendarButton);

      // Check for schedule events on calendar
      expect(screen.getByText('Daily Backup')).toBeInTheDocument();
    });

    it('should show next run times in calendar', async () => {
      const initialState = {
        schedules: {
          schedules: mockSchedules,
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<Schedules />, { initialState });

      const calendarButton = screen.getByRole('button', { name: /calendar/i });
      await userEvent.click(calendarButton);

      // Should display next run times
      expect(screen.getByText(/02:00/)).toBeInTheDocument(); // Daily Backup time
    });
  });

  describe('Create Schedule Dialog', () => {
    it('should open create schedule dialog when clicking add button', async () => {
      const initialState = {
        schedules: {
          schedules: [],
          loading: false,
          error: null,
        },
        processes: {
          processes: mockProcesses,
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<Schedules />, { initialState });

      const addButton = screen.getByRole('button', { name: /add schedule/i });
      await userEvent.click(addButton);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/create new schedule/i)).toBeInTheDocument();
    });

    it('should have form fields for schedule creation', async () => {
      const initialState = {
        schedules: {
          schedules: [],
          loading: false,
          error: null,
        },
        processes: {
          processes: mockProcesses,
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<Schedules />, { initialState });

      const addButton = screen.getByRole('button', { name: /add schedule/i });
      await userEvent.click(addButton);

      expect(screen.getByLabelText(/schedule name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/select process/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/schedule type/i)).toBeInTheDocument();
    });

    it('should show cron expression field when cron type is selected', async () => {
      const initialState = {
        schedules: {
          schedules: [],
          loading: false,
          error: null,
        },
        processes: {
          processes: mockProcesses,
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<Schedules />, { initialState });

      const addButton = screen.getByRole('button', { name: /add schedule/i });
      await userEvent.click(addButton);

      const typeSelect = screen.getByLabelText(/schedule type/i);
      await userEvent.selectOptions(typeSelect, 'cron');

      expect(screen.getByLabelText(/cron expression/i)).toBeInTheDocument();
      expect(screen.getByText(/cron helper/i)).toBeInTheDocument();
    });

    it('should show interval fields when interval type is selected', async () => {
      const initialState = {
        schedules: {
          schedules: [],
          loading: false,
          error: null,
        },
        processes: {
          processes: mockProcesses,
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<Schedules />, { initialState });

      const addButton = screen.getByRole('button', { name: /add schedule/i });
      await userEvent.click(addButton);

      const typeSelect = screen.getByLabelText(/schedule type/i);
      await userEvent.selectOptions(typeSelect, 'interval');

      expect(screen.getByLabelText(/interval value/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/interval unit/i)).toBeInTheDocument();
    });
  });

  describe('Edit Schedule', () => {
    it('should open edit dialog with pre-filled values', async () => {
      const initialState = {
        schedules: {
          schedules: [mockSchedules[0]],
          loading: false,
          error: null,
        },
        processes: {
          processes: mockProcesses,
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<Schedules />, { initialState });

      const editButton = screen.getByRole('button', { name: /edit/i });
      await userEvent.click(editButton);

      const nameInput = screen.getByLabelText(/schedule name/i) as HTMLInputElement;
      expect(nameInput.value).toBe('Daily Backup');

      const cronInput = screen.getByLabelText(/cron expression/i) as HTMLInputElement;
      expect(cronInput.value).toBe('0 2 * * *');
    });
  });

  describe('Schedule Filtering and Search', () => {
    it('should have search field to filter schedules', async () => {
      const initialState = {
        schedules: {
          schedules: mockSchedules,
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<Schedules />, { initialState });

      const searchField = screen.getByPlaceholderText(/search schedules/i);
      expect(searchField).toBeInTheDocument();

      await userEvent.type(searchField, 'backup');

      expect(screen.getByText('Daily Backup')).toBeInTheDocument();
      expect(screen.queryByText('Hourly Health Check')).not.toBeInTheDocument();
      expect(screen.queryByText('Weekly Report')).not.toBeInTheDocument();
    });

    it('should have filter for enabled/disabled schedules', async () => {
      const initialState = {
        schedules: {
          schedules: mockSchedules,
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<Schedules />, { initialState });

      const filterButton = screen.getByRole('button', { name: /filter/i });
      await userEvent.click(filterButton);

      const disabledFilter = screen.getByRole('checkbox', { name: /show disabled/i });
      await userEvent.click(disabledFilter);

      expect(screen.queryByText('Daily Backup')).not.toBeInTheDocument();
      expect(screen.queryByText('Hourly Health Check')).not.toBeInTheDocument();
      expect(screen.getByText('Weekly Report')).toBeInTheDocument();
    });
  });

  describe('Upcoming Runs Widget', () => {
    it('should display upcoming runs in chronological order', () => {
      const initialState = {
        schedules: {
          schedules: mockSchedules,
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<Schedules />, { initialState });

      const upcomingSection = screen.getByTestId('upcoming-runs');
      const runs = within(upcomingSection).getAllByRole('listitem');
      
      // Should be sorted by next_run time
      expect(runs[0]).toHaveTextContent('Hourly Health Check');
      expect(runs[1]).toHaveTextContent('Daily Backup');
      expect(runs[2]).toHaveTextContent('Weekly Report');
    });

    it('should show countdown timer for next run', () => {
      const initialState = {
        schedules: {
          schedules: [mockSchedules[0]],
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<Schedules />, { initialState });

      const upcomingSection = screen.getByTestId('upcoming-runs');
      expect(within(upcomingSection).getByText(/in \d+ hours?/i)).toBeInTheDocument();
    });
  });

  describe('Error States', () => {
    it('should display error message when loading fails', () => {
      const initialState = {
        schedules: {
          schedules: [],
          loading: false,
          error: 'Failed to load schedules',
        },
      };

      renderWithProviders(<Schedules />, { initialState });

      expect(screen.getByText(/failed to load schedules/i)).toBeInTheDocument();
    });

    it('should display loading state', () => {
      const initialState = {
        schedules: {
          schedules: [],
          loading: true,
          error: null,
        },
      };

      renderWithProviders(<Schedules />, { initialState });

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('should display empty state when no schedules exist', () => {
      const initialState = {
        schedules: {
          schedules: [],
          loading: false,
          error: null,
        },
      };

      renderWithProviders(<Schedules />, { initialState });

      expect(screen.getByText(/no schedules found/i)).toBeInTheDocument();
      expect(screen.getByText(/create your first schedule/i)).toBeInTheDocument();
    });
  });
});