import { useState, FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import AuthLayout from './AuthLayout';
import { useAuth } from '../contexts/AuthContext';
import '../styles/auth.css';

interface AdminLoginPayload {
  username: string;
  password: string;
}

interface AdminLoginPageProps {
  onAdminLogin?: (payload: AdminLoginPayload) => Promise<{ error?: string } | void> | { error?: string } | void;
}

export function AdminLoginPage({ onAdminLogin }: AdminLoginPageProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<{ username?: string; password?: string }>({});
  const [formError, setFormError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { signInAdmin } = useAuth();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setFormError('');

    const nextErrors: typeof errors = {};
    if (!username.trim()) nextErrors.username = 'Admin username is required';
    if (!password) nextErrors.password = 'Password is required';

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    setLoading(true);
    try {
      const result = onAdminLogin
        ? await onAdminLogin({ username: username.trim(), password })
        : await signInAdmin(username.trim(), password);

      const error = result && 'error' in result ? result.error : undefined;
      if (error) {
        setFormError(error);
      } else {
        navigate('/admin');
      }
    } catch (err: any) {
      setFormError(err?.message || 'Admin login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Admin Login"
      subtitle="Restricted area. Admin credentials required."
    >
      {formError && (
        <div className="auth-alert" role="alert">
          {formError}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        <div className="auth-field">
          <label className="auth-label" htmlFor="admin-username">Username</label>
          <input
            id="admin-username"
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
          <label className="auth-label" htmlFor="admin-password">Password</label>
          <input
            id="admin-password"
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
          {loading ? 'Logging in…' : 'Login as Admin'}
        </button>
      </form>

      <div className="auth-footer">
        Back to <Link to="/login" className="auth-link">user login</Link>
      </div>
    </AuthLayout>
  );
}

export default AdminLoginPage;
