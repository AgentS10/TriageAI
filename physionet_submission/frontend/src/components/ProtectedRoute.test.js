import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import ProtectedRoute from './ProtectedRoute';
import { useAuth } from '../contexts/AuthContext';

jest.mock('../contexts/AuthContext');

const renderAt = (initialEntry, element, adminOnly = false) =>
  render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route
          path="/protected"
          element={<ProtectedRoute adminOnly={adminOnly}>{element}</ProtectedRoute>}
        />
        <Route path="/login" element={<div>Login Page</div>} />
        <Route path="/dashboard" element={<div>Dashboard Page</div>} />
      </Routes>
    </MemoryRouter>
  );

describe('ProtectedRoute', () => {
  afterEach(() => jest.clearAllMocks());

  it('shows a loader while auth is loading', () => {
    useAuth.mockReturnValue({ loading: true });
    renderAt('/protected', <div>Secret</div>);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('redirects unauthenticated users to /login', () => {
    useAuth.mockReturnValue({ loading: false, isAuthenticated: false });
    renderAt('/protected', <div>Secret</div>);
    expect(screen.getByText('Login Page')).toBeInTheDocument();
    expect(screen.queryByText('Secret')).not.toBeInTheDocument();
  });

  it('renders children for authenticated users', () => {
    useAuth.mockReturnValue({ loading: false, isAuthenticated: true, isAdmin: false });
    renderAt('/protected', <div>Secret</div>);
    expect(screen.getByText('Secret')).toBeInTheDocument();
  });

  it('redirects non-admins away from admin-only routes', () => {
    useAuth.mockReturnValue({ loading: false, isAuthenticated: true, isAdmin: false });
    renderAt('/protected', <div>Admin Secret</div>, true);
    expect(screen.getByText('Dashboard Page')).toBeInTheDocument();
    expect(screen.queryByText('Admin Secret')).not.toBeInTheDocument();
  });

  it('allows admins into admin-only routes', () => {
    useAuth.mockReturnValue({ loading: false, isAuthenticated: true, isAdmin: true });
    renderAt('/protected', <div>Admin Secret</div>, true);
    expect(screen.getByText('Admin Secret')).toBeInTheDocument();
  });
});
