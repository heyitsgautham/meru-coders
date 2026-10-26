// The credential routes under /auth. They return the user and a session, or throw the server's message.
import { getAPIURL } from './api';

export interface AuthResponse {
  success?: boolean;
  user?: { id?: string; username?: string; email?: string; is_admin?: boolean };
  session?: { access_token?: string | null; refresh_token?: string | null };
  error?: string;
  message?: string;
}

async function postAuth(endpoint: string, payload: Record<string, unknown>): Promise<AuthResponse> {
  const res = await fetch(`${getAPIURL()}/auth${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data: AuthResponse = await res.json().catch(() => ({ error: `Request failed (HTTP ${res.status})` }));
  if (!res.ok || data.success === false) {
    throw new Error(data.message || data.error || 'Request failed');
  }
  return data;
}

export const signUpWithPassword = (username: string, password: string) => postAuth('/signup', { username, password });

export const logInWithPassword = (username: string, password: string) => postAuth('/login', { username, password });

export const logInAsAdmin = (username: string, password: string) => postAuth('/admin-login', { username, password });

export const exchangeOAuthSession = (accessToken: string, refreshToken?: string | null) =>
  postAuth('/oauth/exchange', { access_token: accessToken, refresh_token: refreshToken });
