import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import OAuthCallback from './OAuthCallback';
import { AuthProvider } from '../contexts/AuthContext';
import { supabase } from '../lib/supabase';

vi.mock('../lib/supabase', () => ({
  isSupabaseConfigured: true,
  supabase: {
    auth: {
      exchangeCodeForSession: vi.fn(),
      setSession: vi.fn(),
      getSession: vi.fn(),
      refreshSession: vi.fn(),
      signInWithOAuth: vi.fn(),
    },
  },
}));

const auth = vi.mocked(supabase.auth);
const SESSION = { access_token: 'sb-access', refresh_token: 'sb-refresh', user: { id: 'g1' } };

function renderCallback(url: string) {
  window.history.replaceState(null, '', url);
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/oauth/callback']}>
        <Routes>
          <Route path="/oauth/callback" element={<OAuthCallback />} />
          <Route path="/app" element={<p>app page</p>} />
          <Route path="/login" element={<p>login page</p>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  );
}

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  for (const method of ['info', 'warn', 'error'] as const) vi.spyOn(console, method).mockImplementation(() => {});
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, user: { id: 'g1', username: 'gk' }, session: { access_token: 'app-token' } }),
    }),
  );
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  vi.clearAllMocks();
  window.history.replaceState(null, '', '/');
});

describe('OAuthCallback', () => {
  it('exchanges the code once and keeps the signed-in user in the app', async () => {
    // A PKCE code works once; Supabase refuses a second exchange.
    auth.exchangeCodeForSession
      .mockResolvedValueOnce({ data: { session: SESSION }, error: null } as never)
      .mockResolvedValue({ data: { session: null }, error: new Error('code already used') } as never);
    renderCallback('/oauth/callback?code=abc');

    expect(await screen.findByText('app page')).toBeInTheDocument();
    await act(() => vi.advanceTimersByTimeAsync(5000));

    expect(screen.getByText('app page')).toBeInTheDocument();
    expect(auth.exchangeCodeForSession).toHaveBeenCalledTimes(1);
    expect(auth.exchangeCodeForSession).toHaveBeenCalledWith('abc');
    expect(localStorage.getItem('authToken')).toBe('app-token');
  });

  it('accepts tokens returned in the URL hash', async () => {
    auth.setSession.mockResolvedValue({ data: { session: SESSION }, error: null } as never);
    renderCallback('/oauth/callback#access_token=sb-access&refresh_token=sb-refresh');

    expect(await screen.findByText('app page')).toBeInTheDocument();
    expect(auth.setSession).toHaveBeenCalledWith({ access_token: 'sb-access', refresh_token: 'sb-refresh' });
  });

  it('sends the visitor back to login when there is no session', async () => {
    auth.getSession.mockResolvedValue({ data: { session: null }, error: null } as never);
    renderCallback('/oauth/callback');

    expect(await screen.findByText('No session found')).toBeInTheDocument();
    await act(() => vi.advanceTimersByTimeAsync(3000));
    expect(screen.getByText('login page')).toBeInTheDocument();
  });

  it('shows the backend refusal', async () => {
    auth.exchangeCodeForSession.mockResolvedValue({ data: { session: SESSION }, error: null } as never);
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, json: async () => ({ success: false, error: 'Account disabled' }) }));
    renderCallback('/oauth/callback?code=abc');

    expect(await screen.findByText('Account disabled')).toBeInTheDocument();
  });
});
