import { useState, FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import AuthLayout from './AuthLayout';
import { useAuth } from '../contexts/AuthContext';
import '../styles/auth.css';

interface LoginPayload {
  username: string;
  password: string;
}

interface LoginPageProps {
  onLogin?: (payload: LoginPayload) => Promise<{ error?: string } | void> | { error?: string } | void;
}

export function LoginPage({ onLogin }: LoginPageProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<{ username?: string; password?: string }>({});
  const [formError, setFormError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { signIn, startOAuth } = useAuth();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setFormError('');

    const nextErrors: typeof errors = {};
    if (!username.trim()) nextErrors.username = 'Username is required';
    if (!password) nextErrors.password = 'Password is required';

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    setLoading(true);
    try {
      const result = onLogin
        ? await onLogin({ username: username.trim(), password })
        : await signIn(username.trim(), password);

      const error = result && 'error' in result ? result.error : undefined;
      if (error) {
        setFormError(error);
      } else {
        navigate('/profile');
      }
    } catch (err: any) {
      setFormError(err?.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Login" subtitle="Welcome back! Please login to continue">
      {formError && (
        <div className="auth-alert" role="alert">
          {formError}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        <div className="auth-field">
          <label className="auth-label" htmlFor="login-username">Username</label>
          <input
            id="login-username"
            className="auth-input"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            aria-invalid={Boolean(errors.username)}
            autoComplete="username"
          />
          {errors.username && <div className="auth-error">{errors.username}</div>}
        </div>

        <div className="auth-field">
          <label className="auth-label" htmlFor="login-password">Password</label>
          <input
            id="login-password"
            className="auth-input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            aria-invalid={Boolean(errors.password)}
            autoComplete="current-password"
          />
          {errors.password && <div className="auth-error">{errors.password}</div>}
        </div>

        <button className="auth-button" type="submit" disabled={loading}>
          {loading ? 'Logging in…' : 'Login'}
        </button>
      </form>

      <div className="auth-divider">
        <span>or continue with</span>
      </div>

      <button 
        type="button"
        className="auth-button-google"
        onClick={async () => {
          setFormError('');
          const { error } = await startOAuth('google');
          if (error) setFormError(error);
        }}
        disabled={loading}
      >
        <svg className="google-icon" viewBox="0 0 24 24" width="20" height="20">
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
        </svg>
        Sign in with Google
      </button>

      <div className="auth-footer">
        <div>Don’t have an account? <Link to="/signup" className="auth-link">Sign up</Link></div>
        <div className="auth-hint">Admin? <Link to="/admin-login" className="auth-link">Admin Login</Link></div>
      </div>
    </AuthLayout>
  );
}

export default LoginPage;
