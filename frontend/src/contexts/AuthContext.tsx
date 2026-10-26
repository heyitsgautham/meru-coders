import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { getAPIURL } from '../services/api';
import { isSupabaseConfigured, supabase } from '../lib/supabase';

const redactToken = (token?: string | null) =>
  token ? `${token.slice(0, 4)}...${token.slice(-4)} (len=${token.length})` : '<empty>';

interface AppUser {
  id: string;
  username: string;
  is_admin?: boolean;
  access_token?: string | null;
  refresh_token?: string | null;
  created_at?: string;
}

interface AuthResult {
  error: string | null;
}

interface AuthContextType {
  user: AppUser | null;
  isAdmin: boolean;
  loading: boolean;
  signUp: (username: string, password: string) => Promise<AuthResult>;
  signIn: (username: string, password: string) => Promise<AuthResult>;
  signInAdmin: (username: string, password: string) => Promise<AuthResult>;
  startOAuth: (provider?: string) => Promise<AuthResult>;
  completeOAuth: (accessToken: string, refreshToken?: string | null) => Promise<AuthResult>;
  signOut: () => Promise<void>;
  checkAdminStatus: () => Promise<boolean>;
  refreshToken: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AppUser | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);

  // Load stored session on mount
  useEffect(() => {
    const storedUser = typeof localStorage !== 'undefined' ? localStorage.getItem('appUser') : null;
    if (storedUser) {
      const parsed = JSON.parse(storedUser) as AppUser;
      setUser(parsed);
      setIsAdmin(!!parsed.is_admin);
      console.info('[AuthContext] Loaded stored session', {
        userId: parsed.id,
        username: parsed.username,
        isAdmin: parsed.is_admin,
      });
      // A Google session's access token lasts an hour; renew it from the stored refresh token.
      if (parsed.refresh_token && isSupabaseConfigured) {
        void refreshSessionFor(parsed);
      }
    }
    setLoading(false);
  }, []);

  // Listen for auth:expired events from API services
  useEffect(() => {
    const handleAuthExpired = (event: CustomEvent) => {
      console.warn('[AuthContext] Session expired:', event.detail?.message);
      setUser(null);
      setIsAdmin(false);
      // Optionally show a toast or redirect to login
    };

    window.addEventListener('auth:expired', handleAuthExpired as EventListener);
    return () => {
      window.removeEventListener('auth:expired', handleAuthExpired as EventListener);
    };
  }, []);

  const persistSession = (appUser: AppUser | null, token?: string | null, refresh?: string | null) => {
    if (typeof localStorage === 'undefined') return;
    if (appUser) {
      const stored = { ...appUser, access_token: token, refresh_token: refresh };
      localStorage.setItem('appUser', JSON.stringify(stored));
      if (token) localStorage.setItem('authToken', token);
      if (refresh) localStorage.setItem('refreshToken', refresh);
      console.info('[AuthContext] Persisted session', {
        userId: appUser.id,
        username: appUser.username,
        isAdmin: appUser.is_admin,
        accessToken: redactToken(token),
        refreshToken: redactToken(refresh),
      });
    } else {
      localStorage.removeItem('appUser');
      localStorage.removeItem('authToken');
      localStorage.removeItem('refreshToken');
      console.info('[AuthContext] Cleared session from storage');
    }
  };

  const handleAuthResponse = (data: any): AppUser => {
    const appUser: AppUser = {
      id: data.user?.id || '',
      username: data.user?.username || data.user?.email?.split('@')[0] || '',
      is_admin: data.user?.is_admin ?? false,
      access_token: data.session?.access_token || null,
      refresh_token: data.session?.refresh_token || null,
    };
    setUser(appUser);
    setIsAdmin(!!appUser.is_admin);
    persistSession(appUser, appUser.access_token || undefined, appUser.refresh_token || undefined);
    console.info('[AuthContext] Auth response handled', {
      userId: appUser.id,
      username: appUser.username,
      isAdmin: appUser.is_admin,
      accessToken: redactToken(appUser.access_token),
      refreshToken: redactToken(appUser.refresh_token),
    });
    return appUser;
  };

  const postJson = async (endpoint: string, payload: Record<string, any>) => {
    const res = await fetch(`${getAPIURL()}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok || data.success === false) {
      throw new Error(data.message || data.error || 'Request failed');
    }
    return data;
  };

  const signUp = async (username: string, password: string): Promise<AuthResult> => {
    try {
      const data = await postJson('/auth/signup', { username, password });
      handleAuthResponse(data);
      return { error: null };
    } catch (error) {
      console.error('Sign up error:', error);
      return { error: error instanceof Error ? error.message : 'Signup failed' };
    }
  };

  const signIn = async (username: string, password: string): Promise<AuthResult> => {
    try {
      const data = await postJson('/auth/login', { username, password });
      handleAuthResponse(data);
      return { error: null };
    } catch (error) {
      console.error('Sign in error:', error);
      return { error: error instanceof Error ? error.message : 'Login failed' };
    }
  };

  const signInAdmin = async (username: string, password: string): Promise<AuthResult> => {
    try {
      const data = await postJson('/auth/admin-login', { username, password });
      handleAuthResponse({ ...data, user: { ...data.user, is_admin: true } });
      return { error: null };
    } catch (error) {
      console.error('Admin sign in error:', error);
      return { error: error instanceof Error ? error.message : 'Admin login failed' };
    }
  };

  const checkAdminStatus = async (): Promise<boolean> => {
    setIsAdmin(!!user?.is_admin);
    return !!user?.is_admin;
  };

  const startOAuth = async (provider = 'google'): Promise<AuthResult> => {
    if (!isSupabaseConfigured) {
      return { error: 'Google sign-in is not configured on this deployment' };
    }
    try {
      const redirect_to = typeof window !== 'undefined' ? `${window.location.origin}/oauth/callback` : undefined;
      console.info('[AuthContext] Starting OAuth via supabase-js (PKCE)', {
        provider,
        redirect_to,
        apiBase: getAPIURL(),
      });

      // Use frontend Supabase client so PKCE code_verifier is stored in localStorage.
      // This avoids the "code_verifier missing" error seen when backend initiated the flow.
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: provider as 'google' | 'github' | 'azure',
        options: {
          redirectTo: redirect_to,
          skipBrowserRedirect: false,
        },
      });

      if (error) {
        console.error('[AuthContext] supabase signInWithOAuth error', error);
        return { error: error.message };
      }

      // When skipBrowserRedirect is false (default), supabase will redirect automatically.
      // If it ever returns a URL (older versions), handle it here.
      if (data?.url) {
        console.info('[AuthContext] Redirecting to provider URL (manual fallback)', { url: data.url });
        window.location.href = data.url;
      }
      return { error: null };
    } catch (error) {
      console.error('OAuth start error:', error);
      return { error: error instanceof Error ? error.message : 'Unable to start OAuth' };
    }
  };

  const completeOAuth = async (accessToken: string, refreshToken?: string | null): Promise<AuthResult> => {
    try {
      console.info('[AuthContext] Completing OAuth', {
        accessToken: redactToken(accessToken),
        refreshToken: redactToken(refreshToken),
        apiBase: getAPIURL(),
      });
      const data = await postJson('/auth/oauth/exchange', { access_token: accessToken, refresh_token: refreshToken });
      handleAuthResponse(data);
      return { error: null };
    } catch (error) {
      console.error('OAuth completion error:', error);
      return { error: error instanceof Error ? error.message : 'OAuth completion failed' };
    }
  };

  const signOut = async () => {
    persistSession(null);
    setUser(null);
    setIsAdmin(false);
  };

  // Token refresh using Supabase. It takes the user explicitly because on mount the
  // stored session is not in state yet.
  const refreshSessionFor = async (current: AppUser | null): Promise<boolean> => {
    try {
      const storedRefreshToken = current?.refresh_token || localStorage.getItem('refreshToken');
      if (!storedRefreshToken) {
        console.warn('[AuthContext] No refresh token available');
        return false;
      }

      console.info('[AuthContext] Attempting to refresh token...');
      
      // Use Supabase to refresh the session
      const { data, error } = await supabase.auth.refreshSession({
        refresh_token: storedRefreshToken
      });

      if (error || !data.session) {
        console.error('[AuthContext] Token refresh failed:', error?.message);
        // Clear invalid session
        await signOut();
        return false;
      }

      // Update the stored tokens
      const newAccessToken = data.session.access_token;
      const newRefreshToken = data.session.refresh_token;

      if (current) {
        const updatedUser = {
          ...current,
          access_token: newAccessToken,
          refresh_token: newRefreshToken,
        };
        setUser(updatedUser);
        persistSession(updatedUser, newAccessToken, newRefreshToken);
        console.info('[AuthContext] Token refreshed successfully');
        return true;
      }

      return false;
    } catch (error) {
      console.error('[AuthContext] Token refresh error:', error);
      return false;
    }
  };

  const refreshToken = () => refreshSessionFor(user);

  const value = {
    user,
    isAdmin,
    loading,
    signUp,
    signIn,
    signInAdmin,
    startOAuth,
    completeOAuth,
    signOut,
    checkAdminStatus,
    refreshToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
