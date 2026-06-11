import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axios from 'axios';
import { AuthProvider, useAuth } from './AuthContext';

jest.mock('axios');

// Provide the axios surface the provider touches
beforeEach(() => {
  localStorage.clear();
  axios.defaults = { headers: { common: {} } };
  axios.interceptors = { response: { use: jest.fn(), eject: jest.fn() } };
  axios.get = jest.fn().mockResolvedValue({ data: {} });
  axios.post = jest.fn();
});

const Consumer = () => {
  const { isAuthenticated, login, user } = useAuth();
  return (
    <div>
      <span data-testid="status">{isAuthenticated ? 'in' : 'out'}</span>
      <span data-testid="name">{user?.username || ''}</span>
      <button onClick={() => login('nurse_amara', 'Nurse123!')}>login</button>
    </div>
  );
};

describe('AuthContext', () => {
  it('starts unauthenticated when no token is stored', async () => {
    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>
    );
    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('out'));
  });

  it('authenticates and stores tokens on successful login', async () => {
    axios.post.mockResolvedValue({
      data: {
        access_token: 'abc',
        refresh_token: 'def',
        user: { username: 'nurse_amara', role: 'clinician' },
      },
    });

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>
    );

    await userEvent.click(screen.getByRole('button', { name: 'login' }));

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('in'));
    expect(screen.getByTestId('name')).toHaveTextContent('nurse_amara');
    expect(localStorage.getItem('access_token')).toBe('abc');
    expect(localStorage.getItem('refresh_token')).toBe('def');
  });

  it('surfaces an error message on failed login', async () => {
    axios.post.mockRejectedValue({ response: { data: { error: 'Invalid credentials' } } });

    const ErrConsumer = () => {
      const { error, login } = useAuth();
      return (
        <div>
          <span data-testid="err">{error || ''}</span>
          <button onClick={() => login('x', 'y')}>go</button>
        </div>
      );
    };

    render(
      <AuthProvider>
        <ErrConsumer />
      </AuthProvider>
    );

    await userEvent.click(screen.getByRole('button', { name: 'go' }));
    await waitFor(() => expect(screen.getByTestId('err')).toHaveTextContent('Invalid credentials'));
  });
});
