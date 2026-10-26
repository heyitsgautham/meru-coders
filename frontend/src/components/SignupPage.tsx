import { useState, FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import AuthLayout from './AuthLayout';
import { useAuth } from '../contexts/AuthContext';
import '../styles/auth.css';

interface SignupPayload {
  username: string;
  password: string;
  fullName?: string;
}

interface SignupPageProps {
  onSignup?: (payload: SignupPayload) => Promise<{ error?: string } | void> | { error?: string } | void;
}

export function SignupPage({ onSignup }: SignupPageProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [formError, setFormError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { signUp, startOAuth } = useAuth();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setFormError('');
    const nextErrors: { [key: string]: string } = {};

    if (!username.trim()) nextErrors.username = 'Username is required';
    if (!password) nextErrors.password = 'Password is required';
    if (password && password.length < 8) nextErrors.password = 'Password must be at least 8 characters';
    if (!confirmPassword) nextErrors.confirmPassword = 'Confirm your password';
    if (password && confirmPassword && password !== confirmPassword) nextErrors.confirmPassword = 'Passwords do not match';

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    setLoading(true);
    try {
      const result = onSignup
        ? await onSignup({ username: username.trim(), password, fullName: fullName.trim() || undefined })
        : await signUp(username.trim(), password);

      const error = result && 'error' in result ? result.error : undefined;
      if (error) {
        setFormError(error);
      } else {
        navigate('/login');
      }
    } catch (err: any) {
      setFormError(err?.message || 'Sign up failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Sign Up" subtitle="Create an account to contribute new chandas data.">
      {formError && (
        <div className="auth-alert" role="alert">
          {formError}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        <div className="auth-field">
          <label className="auth-label" htmlFor="signup-username">Username</label>
          <input
            id="signup-username"
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
          <label className="auth-label" htmlFor="signup-fullname">Full name (optional)</label>
          <input
            id="signup-fullname"
            className="auth-input"
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            autoComplete="name"
          />
        </div>

        <div className="auth-field">
          <label className="auth-label" htmlFor="signup-password">Password</label>
          <input
            id="signup-password"
            className="auth-input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            aria-invalid={Boolean(errors.password)}
            autoComplete="new-password"
          />
          {errors.password && <div className="auth-error">{errors.password}</div>}
        </div>

        <div className="auth-field">
          <label className="auth-label" htmlFor="signup-confirm">Confirm Password</label>
          <input
            id="signup-confirm"
            className="auth-input"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            aria-invalid={Boolean(errors.confirmPassword)}
            autoComplete="new-password"
          />
          {errors.confirmPassword && <div className="auth-error">{errors.confirmPassword}</div>}
        </div>

        <button className="auth-button" type="submit" disabled={loading}>
          {loading ? 'Creating account…' : 'Create account'}
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
        Sign up with Google
      </button>

      <div className="auth-footer">
        Already have an account? <Link to="/login" className="auth-link">Login</Link>
      </div>
    </AuthLayout>
  );
}

export default SignupPage;
