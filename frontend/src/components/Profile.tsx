import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { LogOut, Plus, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { useEffect, useState } from 'react';
import * as api from '../services/api';
import { Header } from './Header';
import type { ViewType } from '../types/api';
import '../styles/profile-admin.css';

export default function Profile() {
  const { user, signOut, loading } = useAuth();
  const navigate = useNavigate();
  const [contributions, setContributions] = useState<any[]>([]);
  const [contributionsLoading, setContributionsLoading] = useState(false);
  const [currentView, setCurrentView] = useState<ViewType>('home');

  useEffect(() => {
    if (!loading && !user) {
      navigate('/login');
    }
  }, [user, loading, navigate]);

  useEffect(() => {
    if (user) {
      loadContributions();
    }
  }, [user]);

  const loadContributions = async () => {
    try {
      setContributionsLoading(true);
      const response = await api.getMyContributions();
      if (response.success && response.contributions) {
        setContributions(response.contributions);
      }
    } catch (err) {
      console.error('Failed to load contributions:', err);
    } finally {
      setContributionsLoading(false);
    }
  };

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
    <>
      <Header 
        currentView={currentView}
        onViewChange={(view) => {
          setCurrentView(view);
          navigate('/app');
        }}
      />

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
            {contributionsLoading ? (
              <div className="text-center py-8">
                <Clock className="h-8 w-8 animate-spin mx-auto mb-2 text-amber-600" />
                <p className="text-sm text-slate-600">Loading contributions...</p>
              </div>
            ) : contributions.length === 0 ? (
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
            ) : (
              <div className="space-y-3">
                {contributions.map((contrib) => (
                  <div
                    key={contrib.id}
                    className="flex items-start gap-3 p-4 bg-white rounded-lg border border-slate-200 hover:border-amber-300 transition-colors"
                  >
                    <div className="flex-shrink-0 mt-1">
                      {contrib.status === 'approved' && (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      )}
                      {contrib.status === 'rejected' && (
                        <XCircle className="h-5 w-5 text-red-600" />
                      )}
                      {contrib.status === 'pending' && (
                        <AlertCircle className="h-5 w-5 text-amber-600" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-semibold text-slate-900">
                          {contrib.contribution_type === 'verse' ? 'Verse' : 'Meter Definition'}
                        </span>
                        <span
                          className={
                            contrib.status === 'approved'
                              ? 'px-2 py-0.5 text-xs font-medium rounded-full bg-green-100 text-green-700'
                              : contrib.status === 'rejected'
                              ? 'px-2 py-0.5 text-xs font-medium rounded-full bg-red-100 text-red-700'
                              : 'px-2 py-0.5 text-xs font-medium rounded-full bg-amber-100 text-amber-700'
                          }
                        >
                          {contrib.status.charAt(0).toUpperCase() + contrib.status.slice(1)}
                        </span>
                      </div>
                      {contrib.contribution_type === 'verse' && contrib.data?.verse_text && (
                        <p className="text-sm text-slate-700 mb-1 line-clamp-2">
                          {contrib.data.verse_text}
                        </p>
                      )}
                      {contrib.data?.meter_name && (
                        <p className="text-xs text-slate-600">
                          Meter: <span className="font-medium">{contrib.data.meter_name}</span>
                        </p>
                      )}
                      <p className="text-xs text-slate-500 mt-1">
                        Submitted {new Date(contrib.created_at).toLocaleDateString()}
                      </p>
                      {contrib.review_notes && (
                        <p className="text-xs text-slate-600 mt-2 italic">
                          Note: {contrib.review_notes}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
    </>
  );
}
