import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { User, LogOut, Plus, Clock } from 'lucide-react';
import { useEffect } from 'react';
import '../styles/profile-admin.css';

export default function Profile() {
  const { user, signOut, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && !user) {
      navigate('/login');
    }
  }, [user, loading, navigate]);

  const handleSignOut = async () => {
    await signOut();
    navigate('/');
  };

  const handleContribute = () => {
    navigate('/contribute');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Loading...</p>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  const username = user.username || 'User';
  const memberSince = user.created_at ? new Date(user.created_at).toLocaleDateString() : '—';

  return (
    <div className="profile-admin-page">
      <div className="page-shell">
        <div className="card">
          <div className="page-header">
            <div className="flex items-center gap-3">
              <div className="avatar-circle" aria-hidden="true">
                {username.slice(0, 2).toUpperCase()}
              </div>
              <div>
                <h1 className="page-title">Welcome, {username}</h1>
                <p className="page-subtitle">Manage your account and contributions</p>
              </div>
            </div>
            <div className="header-actions">
              <Button variant="outline" onClick={handleSignOut} className="button-secondary">
                <LogOut className="mr-2 h-4 w-4" />
                Sign Out
              </Button>
            </div>
          </div>
        </div>

        <div className="section-grid">
          <div className="card">
            <div className="card-header">
              <div>
                <h2 className="card-title">Account Information</h2>
                <p className="card-subtitle">Your basic details</p>
              </div>
            </div>
            <div className="card-body">
              <dl className="space-y-3 text-sm">
                <div>
                  <div className="small-label">Username</div>
                  <div className="text-base text-slate-900">{username}</div>
                </div>
                <div>
                  <div className="small-label">User ID</div>
                  <div className="font-mono text-xs text-slate-800 break-all">{user.id}</div>
                </div>
                <div>
                  <div className="small-label">Member Since</div>
                  <div className="text-base text-slate-900">{memberSince}</div>
                </div>
              </dl>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <div>
                <h2 className="card-title">Quick Actions</h2>
                <p className="card-subtitle">Submit new data for review</p>
              </div>
            </div>
            <div className="card-body">
              <Button onClick={handleContribute} className="button-primary w-full justify-center">
                <Plus className="h-4 w-4" />
                Contribute New Data
              </Button>
              <p className="muted text-sm">Submit new verses and meter data for review.</p>
              <Button variant="outline" className="button-ghost w-full" disabled>
                Edit Profile (coming soon)
              </Button>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Your Contributions</h2>
              <p className="card-subtitle">View and manage your submitted verses and meters.</p>
            </div>
          </div>
          <div className="card-body">
            <div className="empty-state">
              <Clock className="h-10 w-10 mx-auto mb-3 text-amber-500" />
              <div className="empty-title">No contributions yet</div>
              <div className="empty-subtext">Submit your first contribution to help grow the datasets.</div>
              <div className="mt-3">
                <Button onClick={handleContribute} className="button-primary">
                  Contribute New Data
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
