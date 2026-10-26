import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { AuthProvider, useAuth } from './AuthContext';
import { supabase } from '../lib/supabase';

const flags = vi.hoisted(() => ({ supabaseConfigured: false }));
vi.mock('../lib/supabase', () => ({
  get isSupabaseConfigured() {
    return flags.supabaseConfigured;
  },
  supabase: { auth: { signInWithOAuth: vi.fn(), refreshSession: vi.fn() } },
}));

const wrapper = ({ children }: { children: ReactNode }) => <AuthProvider>{children}</AuthProvider>;

function respond(body: unknown, status = 200) {
  return vi.fn().mockResolvedValue({ ok: status < 400, status, json: async () => body });
}

const SESSION = {
  success: true,
  user: { id: 'u1', username: 'pingala', is_admin: false },
  session: { access_token: 'access', refresh_token: 'refresh' },
};

beforeEach(() => {
  for (const method of ['info', 'warn', 'error'] as const) vi.spyOn(console, method).mockImplementation(() => {});
});

afterEach(() => {
  flags.supabaseConfigured = false;
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  vi.clearAllMocks();
});

async function renderAuth() {
  const hook = renderHook(() => useAuth(), { wrapper });
  await waitFor(() => expect(hook.result.current.loading).toBe(false));
  return hook;
}

describe('AuthProvider', () => {
  it('starts signed out', async () => {
    const { result } = await renderAuth();
    expect(result.current.user).toBeNull();
    expect(result.current.isAdmin).toBe(false);
  });

  it('restores a stored session', async () => {
    localStorage.setItem('appUser', JSON.stringify({ id: 'a1', username: 'admin', is_admin: true }));
    const { result } = await renderAuth();
    expect(result.current.user?.username).toBe('admin');
    expect(result.current.isAdmin).toBe(true);
  });

  it('signs in and keeps the session in localStorage', async () => {
    const fetchMock = respond(SESSION);
    vi.stubGlobal('fetch', fetchMock);
    const { result } = await renderAuth();

    let outcome;
    await act(async () => {
      outcome = await result.current.signIn('pingala', 'chandas123');
    });

    expect(outcome).toEqual({ error: null });
    expect(fetchMock.mock.calls[0][0]).toBe('http://localhost:5000/api/auth/login');
    expect(result.current.user).toMatchObject({ id: 'u1', username: 'pingala' });
    expect(localStorage.getItem('authToken')).toBe('access');
    expect(localStorage.getItem('refreshToken')).toBe('refresh');
  });

  it('returns the server message when sign-in fails', async () => {
    vi.stubGlobal('fetch', respond({ success: false, error: 'Login failed', message: 'Invalid username or password' }, 401));
    const { result } = await renderAuth();
    let outcome;
    await act(async () => {
      outcome = await result.current.signIn('pingala', 'wrong');
    });
    expect(outcome).toEqual({ error: 'Invalid username or password' });
    expect(result.current.user).toBeNull();
  });

  it('signs up through the signup route', async () => {
    const fetchMock = respond(SESSION);
    vi.stubGlobal('fetch', fetchMock);
    const { result } = await renderAuth();
    await act(async () => {
      await result.current.signUp('pingala', 'chandas123');
    });
    expect(fetchMock.mock.calls[0][0]).toBe('http://localhost:5000/api/auth/signup');
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ username: 'pingala', password: 'chandas123' });
  });

  it('marks an admin login as admin', async () => {
    vi.stubGlobal('fetch', respond({ ...SESSION, user: { id: 'a1', username: 'admin' } }));
    const { result } = await renderAuth();
    await act(async () => {
      await result.current.signInAdmin('admin', 'secret');
    });
    expect(result.current.isAdmin).toBe(true);
    expect(await result.current.checkAdminStatus()).toBe(true);
  });

  it('signs out and clears storage', async () => {
    vi.stubGlobal('fetch', respond(SESSION));
    const { result } = await renderAuth();
    await act(async () => {
      await result.current.signIn('pingala', 'chandas123');
    });
    await act(() => result.current.signOut());
    expect(result.current.user).toBeNull();
    expect(localStorage.getItem('appUser')).toBeNull();
  });

  it('drops the user when the API reports an expired session', async () => {
    vi.stubGlobal('fetch', respond(SESSION));
    const { result } = await renderAuth();
    await act(async () => {
      await result.current.signIn('pingala', 'chandas123');
    });
    act(() => {
      window.dispatchEvent(new CustomEvent('auth:expired', { detail: { message: 'expired' } }));
    });
    expect(result.current.user).toBeNull();
  });

  it('refuses Google sign-in when Supabase is not configured', async () => {
    const { result } = await renderAuth();
    expect(await result.current.startOAuth()).toEqual({ error: 'Google sign-in is not configured on this deployment' });
  });

  it('exchanges an OAuth token for a session', async () => {
    const fetchMock = respond(SESSION);
    vi.stubGlobal('fetch', fetchMock);
    const { result } = await renderAuth();
    await act(async () => {
      await result.current.completeOAuth('oauth-token', 'oauth-refresh');
    });
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ access_token: 'oauth-token', refresh_token: 'oauth-refresh' });
    expect(result.current.user?.id).toBe('u1');
  });

  describe('refreshToken', () => {
    it('reports false without a stored refresh token', async () => {
      const { result } = await renderAuth();
      expect(await result.current.refreshToken()).toBe(false);
    });

    it('stores the new tokens', async () => {
      vi.stubGlobal('fetch', respond(SESSION));
      vi.mocked(supabase.auth.refreshSession).mockResolvedValue({
        data: { session: { access_token: 'new-access', refresh_token: 'new-refresh' } },
        error: null,
      } as never);
      const { result } = await renderAuth();
      await act(async () => {
        await result.current.signIn('pingala', 'chandas123');
      });
      let refreshed;
      await act(async () => {
        refreshed = await result.current.refreshToken();
      });
      expect(refreshed).toBe(true);
      expect(localStorage.getItem('authToken')).toBe('new-access');
    });

    it('signs out when Supabase rejects the refresh', async () => {
      localStorage.setItem('refreshToken', 'stale');
      vi.mocked(supabase.auth.refreshSession).mockResolvedValue({ data: { session: null }, error: { message: 'bad' } } as never);
      const { result } = await renderAuth();
      let refreshed;
      await act(async () => {
        refreshed = await result.current.refreshToken();
      });
      expect(refreshed).toBe(false);
      expect(localStorage.getItem('refreshToken')).toBeNull();
    });

    it('renews a stored Google session when the app loads', async () => {
      flags.supabaseConfigured = true;
      localStorage.setItem(
        'appUser',
        JSON.stringify({ id: 'g1', username: 'gk', access_token: 'stale', refresh_token: 'old-refresh' }),
      );
      vi.mocked(supabase.auth.refreshSession).mockResolvedValue({
        data: { session: { access_token: 'fresh', refresh_token: 'new-refresh' } },
        error: null,
      } as never);

      const { result } = await renderAuth();

      await waitFor(() => expect(result.current.user?.access_token).toBe('fresh'));
      expect(supabase.auth.refreshSession).toHaveBeenCalledWith({ refresh_token: 'old-refresh' });
      expect(localStorage.getItem('authToken')).toBe('fresh');
      expect(localStorage.getItem('refreshToken')).toBe('new-refresh');
    });

    it('leaves password sessions alone on load', async () => {
      flags.supabaseConfigured = true;
      localStorage.setItem('appUser', JSON.stringify({ id: 'u1', username: 'gk', access_token: 'local-jwt' }));
      await renderAuth();
      expect(supabase.auth.refreshSession).not.toHaveBeenCalled();
    });
  });

  it('refuses use outside the provider', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => renderHook(() => useAuth())).toThrow('useAuth must be used within an AuthProvider');
  });
});
