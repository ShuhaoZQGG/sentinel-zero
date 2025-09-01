import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import Settings from './Settings';
import authReducer from '../store/slices/authSlice';

// Create a test store
const createTestStore = (initialState?: any) => {
  return configureStore({
    reducer: {
      auth: authReducer,
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

describe('Settings', () => {
  const mockUser = {
    id: 'user-1',
    username: 'admin',
    email: 'admin@example.com',
    role: 'admin',
    created_at: '2025-08-01T10:00:00Z',
  };

  const mockSettings = {
    general: {
      systemName: 'SentinelZero',
      timezone: 'America/New_York',
      language: 'en',
      dateFormat: 'MM/DD/YYYY',
      timeFormat: '12h',
    },
    monitoring: {
      metricsInterval: 30,
      logRetention: 7,
      alertThreshold: 80,
      autoRestartDelay: 5,
    },
    notifications: {
      emailEnabled: true,
      slackEnabled: false,
      webhookEnabled: false,
      emailRecipients: ['admin@example.com'],
    },
    security: {
      sessionTimeout: 30,
      passwordExpiry: 90,
      twoFactorEnabled: false,
      apiTokenExpiry: 365,
    },
  };

  describe('Settings Tabs', () => {
    it('should display all settings tabs', () => {
      renderWithProviders(<Settings />);

      expect(screen.getByRole('tab', { name: /general/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /monitoring/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /notifications/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /security/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /api/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /backup/i })).toBeInTheDocument();
    });
  });

  describe('General Settings', () => {
    it('should display general settings fields', () => {
      renderWithProviders(<Settings />);

      expect(screen.getByLabelText(/system name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/timezone/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/language/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/date format/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/time format/i)).toBeInTheDocument();
    });

    it('should allow editing general settings', async () => {
      renderWithProviders(<Settings />);

      const systemNameInput = screen.getByLabelText(/system name/i);
      await userEvent.clear(systemNameInput);
      await userEvent.type(systemNameInput, 'My Process Manager');

      expect(systemNameInput).toHaveValue('My Process Manager');
    });

    it('should have save and reset buttons', () => {
      renderWithProviders(<Settings />);

      expect(screen.getByRole('button', { name: /save changes/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /reset/i })).toBeInTheDocument();
    });
  });

  describe('Monitoring Settings', () => {
    it('should display monitoring settings when tab is clicked', async () => {
      renderWithProviders(<Settings />);

      const monitoringTab = screen.getByRole('tab', { name: /monitoring/i });
      await userEvent.click(monitoringTab);

      expect(screen.getByLabelText(/metrics collection interval/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/log retention days/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/alert threshold/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/auto-restart delay/i)).toBeInTheDocument();
    });

    it('should have input validation for numeric fields', async () => {
      renderWithProviders(<Settings />);

      const monitoringTab = screen.getByRole('tab', { name: /monitoring/i });
      await userEvent.click(monitoringTab);

      const intervalInput = screen.getByLabelText(/metrics collection interval/i);
      await userEvent.clear(intervalInput);
      await userEvent.type(intervalInput, '-5');

      expect(screen.getByText(/must be positive/i)).toBeInTheDocument();
    });
  });

  describe('Notifications Settings', () => {
    it('should display notification settings', async () => {
      renderWithProviders(<Settings />);

      const notificationsTab = screen.getByRole('tab', { name: /notifications/i });
      await userEvent.click(notificationsTab);

      expect(screen.getByLabelText(/enable email notifications/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/enable slack notifications/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/enable webhook notifications/i)).toBeInTheDocument();
    });

    it('should show email configuration when email is enabled', async () => {
      renderWithProviders(<Settings />);

      const notificationsTab = screen.getByRole('tab', { name: /notifications/i });
      await userEvent.click(notificationsTab);

      const emailToggle = screen.getByLabelText(/enable email notifications/i);
      if (!emailToggle.checked) {
        await userEvent.click(emailToggle);
      }

      expect(screen.getByLabelText(/smtp server/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/smtp port/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/sender email/i)).toBeInTheDocument();
    });

    it('should show slack configuration when slack is enabled', async () => {
      renderWithProviders(<Settings />);

      const notificationsTab = screen.getByRole('tab', { name: /notifications/i });
      await userEvent.click(notificationsTab);

      const slackToggle = screen.getByLabelText(/enable slack notifications/i);
      await userEvent.click(slackToggle);

      expect(screen.getByLabelText(/slack webhook url/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/slack channel/i)).toBeInTheDocument();
    });
  });

  describe('Security Settings', () => {
    it('should display security settings', async () => {
      renderWithProviders(<Settings />);

      const securityTab = screen.getByRole('tab', { name: /security/i });
      await userEvent.click(securityTab);

      expect(screen.getByLabelText(/session timeout/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password expiry/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/enable two-factor authentication/i)).toBeInTheDocument();
    });

    it('should have change password section', async () => {
      const initialState = {
        auth: {
          user: mockUser,
          isAuthenticated: true,
        },
      };

      renderWithProviders(<Settings />, { initialState });

      const securityTab = screen.getByRole('tab', { name: /security/i });
      await userEvent.click(securityTab);

      expect(screen.getByText(/change password/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/current password/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/new password/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/confirm new password/i)).toBeInTheDocument();
    });
  });

  describe('API Settings', () => {
    it('should display API configuration', async () => {
      renderWithProviders(<Settings />);

      const apiTab = screen.getByRole('tab', { name: /api/i });
      await userEvent.click(apiTab);

      expect(screen.getByText(/api configuration/i)).toBeInTheDocument();
      expect(screen.getByText(/api endpoint/i)).toBeInTheDocument();
      expect(screen.getByText(/api tokens/i)).toBeInTheDocument();
    });

    it('should allow generating new API token', async () => {
      renderWithProviders(<Settings />);

      const apiTab = screen.getByRole('tab', { name: /api/i });
      await userEvent.click(apiTab);

      const generateButton = screen.getByRole('button', { name: /generate new token/i });
      expect(generateButton).toBeInTheDocument();
    });

    it('should display existing API tokens', async () => {
      renderWithProviders(<Settings />);

      const apiTab = screen.getByRole('tab', { name: /api/i });
      await userEvent.click(apiTab);

      expect(screen.getByText(/active tokens/i)).toBeInTheDocument();
    });
  });

  describe('Backup Settings', () => {
    it('should display backup configuration', async () => {
      renderWithProviders(<Settings />);

      const backupTab = screen.getByRole('tab', { name: /backup/i });
      await userEvent.click(backupTab);

      expect(screen.getByText(/backup configuration/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/enable automatic backups/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/backup frequency/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/backup retention/i)).toBeInTheDocument();
    });

    it('should have manual backup button', async () => {
      renderWithProviders(<Settings />);

      const backupTab = screen.getByRole('tab', { name: /backup/i });
      await userEvent.click(backupTab);

      expect(screen.getByRole('button', { name: /backup now/i })).toBeInTheDocument();
    });

    it('should display backup history', async () => {
      renderWithProviders(<Settings />);

      const backupTab = screen.getByRole('tab', { name: /backup/i });
      await userEvent.click(backupTab);

      expect(screen.getByText(/backup history/i)).toBeInTheDocument();
    });
  });

  describe('Settings Persistence', () => {
    it('should show confirmation dialog when saving', async () => {
      renderWithProviders(<Settings />);

      const saveButton = screen.getByRole('button', { name: /save changes/i });
      await userEvent.click(saveButton);

      expect(screen.getByText(/confirm save/i)).toBeInTheDocument();
      expect(screen.getByText(/are you sure you want to save/i)).toBeInTheDocument();
    });

    it('should show success message after saving', async () => {
      renderWithProviders(<Settings />);

      const saveButton = screen.getByRole('button', { name: /save changes/i });
      await userEvent.click(saveButton);

      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      await userEvent.click(confirmButton);

      await waitFor(() => {
        expect(screen.getByText(/settings saved successfully/i)).toBeInTheDocument();
      });
    });

    it('should reset form when reset button is clicked', async () => {
      renderWithProviders(<Settings />);

      const systemNameInput = screen.getByLabelText(/system name/i);
      await userEvent.clear(systemNameInput);
      await userEvent.type(systemNameInput, 'Modified Name');

      const resetButton = screen.getByRole('button', { name: /reset/i });
      await userEvent.click(resetButton);

      expect(systemNameInput).toHaveValue('SentinelZero');
    });
  });

  describe('Import/Export Settings', () => {
    it('should have export settings button', () => {
      renderWithProviders(<Settings />);

      expect(screen.getByRole('button', { name: /export settings/i })).toBeInTheDocument();
    });

    it('should have import settings button', () => {
      renderWithProviders(<Settings />);

      expect(screen.getByRole('button', { name: /import settings/i })).toBeInTheDocument();
    });
  });
});