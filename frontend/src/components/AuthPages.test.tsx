import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import type { ReactNode } from 'react';
import { LoginPage } from './LoginPage';
import { SignupPage } from './SignupPage';

const auth = vi.hoisted(() => ({
  signIn: vi.fn(),
  signUp: vi.fn(),
  startOAuth: vi.fn(),
}));
vi.mock('../contexts/AuthContext', () => ({ useAuth: () => auth }));

function renderAt(page: ReactNode) {
  return render(
    <MemoryRouter initialEntries={['/page']}>
      <Routes>
        <Route path="/page" element={page} />
        <Route path="/login" element={<p>login page</p>} />
        <Route path="/profile" element={<p>profile page</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('LoginPage', () => {
  it('asks for both fields before calling the server', async () => {
    renderAt(<LoginPage />);
    await userEvent.click(screen.getByRole('button', { name: 'Login' }));
    expect(screen.getByText('Username is required')).toBeInTheDocument();
    expect(screen.getByText('Password is required')).toBeInTheDocument();
    expect(auth.signIn).not.toHaveBeenCalled();
  });

  it('signs in with a trimmed username and opens the profile', async () => {
    auth.signIn.mockResolvedValue({ error: null });
    renderAt(<LoginPage />);
    await userEvent.type(screen.getByLabelText('Username'), ' vyasa ');
    await userEvent.type(screen.getByLabelText('Password'), 'secret-pass');
    await userEvent.click(screen.getByRole('button', { name: 'Login' }));
    expect(auth.signIn).toHaveBeenCalledWith('vyasa', 'secret-pass');
    expect(await screen.findByText('profile page')).toBeInTheDocument();
  });

  it('shows a refused login', async () => {
    auth.signIn.mockResolvedValue({ error: 'Invalid username or password' });
    renderAt(<LoginPage />);
    await userEvent.type(screen.getByLabelText('Username'), 'vyasa');
    await userEvent.type(screen.getByLabelText('Password'), 'wrong');
    await userEvent.click(screen.getByRole('button', { name: 'Login' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid username or password');
  });

  it('says why Google sign-in could not start', async () => {
    auth.startOAuth.mockResolvedValue({ error: 'Google sign-in is not configured on this deployment' });
    renderAt(<LoginPage />);
    await userEvent.click(screen.getByRole('button', { name: 'Sign in with Google' }));
    expect(auth.startOAuth).toHaveBeenCalledWith('google');
    expect(await screen.findByRole('alert')).toHaveTextContent('Google sign-in is not configured on this deployment');
  });
});

describe('SignupPage', () => {
  async function fill(password: string, confirm: string) {
    await userEvent.type(screen.getByLabelText('Username'), ' panini ');
    await userEvent.type(screen.getByLabelText('Password'), password);
    await userEvent.type(screen.getByLabelText('Confirm Password'), confirm);
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }));
  }

  it('rejects a short password and a mismatched confirmation', async () => {
    renderAt(<SignupPage />);
    await fill('short', 'other');
    expect(screen.getByText('Password must be at least 8 characters')).toBeInTheDocument();
    expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
    expect(auth.signUp).not.toHaveBeenCalled();
  });

  it('creates the account and sends the user to login', async () => {
    auth.signUp.mockResolvedValue({ error: null });
    renderAt(<SignupPage />);
    await fill('long-enough', 'long-enough');
    expect(auth.signUp).toHaveBeenCalledWith('panini', 'long-enough');
    expect(await screen.findByText('login page')).toBeInTheDocument();
  });

  it('shows a taken username', async () => {
    auth.signUp.mockResolvedValue({ error: 'Username already exists' });
    renderAt(<SignupPage />);
    await fill('long-enough', 'long-enough');
    expect(await screen.findByRole('alert')).toHaveTextContent('Username already exists');
  });

  it('says why Google sign-up could not start', async () => {
    auth.startOAuth.mockResolvedValue({ error: 'Google sign-in is not configured on this deployment' });
    renderAt(<SignupPage />);
    await userEvent.click(screen.getByRole('button', { name: 'Sign up with Google' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Google sign-in is not configured on this deployment');
  });
});
