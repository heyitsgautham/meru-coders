import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { approveContribution, getPendingContributions, rejectContribution } from '../services/api';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Header } from './Header';
import { useOpenAppView } from '../hooks/useOpenAppView';
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from './ui/table';
import { 
  Loader2, 
  CheckCircle, 
  XCircle, 
  Shield,
  LogOut,
  Clock
} from 'lucide-react';
import '../styles/profile-admin.css';

interface Contribution {
  id: string;
  contribution_type: 'verse' | 'meter' | 'meter_definition' | string;
  data: any;
  status: string;
  submitted_at: string;
  submitted_by: string;
  users?: {
    username: string;
  };
}

export default function AdminPanel() {
  const { user, isAdmin, signOut, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [contributions, setContributions] = useState<Contribution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [viewing, setViewing] = useState<Contribution | null>(null);
  const openView = useOpenAppView();

  const previewText = (text?: string, max = 80) => {
    void text; // Mark as intentionally unused for future use
    void max;
    return '';
  };
  void previewText; // Utility function for future use

  useEffect(() => {
    if (!authLoading && (!user || !isAdmin)) {
      navigate('/admin-login');
    } else if (user && isAdmin) {
      fetchContributions();
    }
  }, [user, isAdmin, authLoading, navigate]);

  const fetchContributions = async () => {
    try {
      setLoading(true);
      const body = await getPendingContributions<Contribution>();
      setContributions(body.contributions || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (contributionId: string) => {
    try {
      setActionLoading(contributionId);
      
      await approveContribution(contributionId);

      // Refresh list
      await fetchContributions();
      setViewing(null);
    } catch (err: any) {
      alert(`Error approving contribution: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (contributionId: string) => {
    if (!confirm('Are you sure you want to reject this contribution?')) {
      return;
    }

    try {
      setActionLoading(contributionId);
      
      await rejectContribution(contributionId);

      // Refresh list
      await fetchContributions();
      setViewing(null);
    } catch (err: any) {
      alert(`Error rejecting contribution: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleSignOut = async () => {
    await signOut();
    navigate('/');
  };

  if (authLoading || loading) {
    return (
      <div className="profile-admin-page flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-[#c75b1a]" />
      </div>
    );
  }

  if (!user || !isAdmin) {
    return null;
  }

  return (
    <>
      <Header currentView={null} onViewChange={openView} />

      <div className="profile-admin-page">
        <div className="page-shell">
        <div className="page-header">
          <div>
            <h1 className="page-title">Admin Panel</h1>
            <p className="page-subtitle">Review and manage user contributions</p>
          </div>
          <div className="header-actions">
            <Button variant="outline" onClick={handleSignOut} className="button-secondary">
              <LogOut className="mr-2 h-4 w-4" />
              Sign Out
            </Button>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="flex items-center gap-3">
              <div className="avatar-circle" aria-hidden="true">
                <Shield className="h-5 w-5" />
              </div>
              <div>
                <h2 className="card-title">Access</h2>
                <p className="card-subtitle">Authenticated administrator</p>
              </div>
            </div>
            <Badge className="status-pill approved">Verified</Badge>
          </div>
          <div className="card-body">
            <div className="section-grid" style={{ marginTop: 0 }}>
              <div className="card" style={{ padding: '1rem 1.1rem' }}>
                <div className="small-label">Pending</div>
                <div className="text-3xl font-black text-slate-900">{contributions.length}</div>
                <div className="muted text-sm">Awaiting review</div>
              </div>
              <div className="card" style={{ padding: '1rem 1.1rem' }}>
                <div className="small-label">Authenticated user</div>
                <div className="text-lg font-bold text-slate-900 truncate">{user?.username}</div>
                <div className="muted text-sm">Access status: Admin verified</div>
              </div>
            </div>
          </div>
        </div>

        {error && (
          <div className="alert-bar" role="alert">
            <XCircle className="h-5 w-5" />
            Could not load contributions: {error}
          </div>
        )}

        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Pending Contributions</h2>
              <p className="card-subtitle">Review and approve or reject user submissions.</p>
            </div>
            <span className="badge-count">{contributions.length} pending</span>
          </div>
          <div className="card-body">
            {contributions.length === 0 ? (
              <div className="empty-state">
                <Clock className="h-12 w-12 mx-auto mb-3 text-amber-500" />
                <div className="empty-title">No pending contributions</div>
                <div className="empty-subtext">You’ll see new submissions here when users contribute.</div>
              </div>
            ) : (
              <div className="table-scroll">
                <Table className="list-table spaced-table">
                  <TableHeader>
                    <TableRow>
                      <TableHead className="col-user">Submitted By</TableHead>
                      <TableHead className="col-type">Type</TableHead>
                      <TableHead className="col-meter">Meter / Details</TableHead>
                      <TableHead className="col-source">Source</TableHead>
                      <TableHead className="col-actions">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {contributions.map((contrib) => (
                      <TableRow key={contrib.id} className="soft-row">
                        <TableCell className="col-user cell-pad">
                          <div className="font-medium">{contrib.users?.username || 'Unknown'}</div>
                          <div className="text-sm muted">{new Date(contrib.submitted_at).toLocaleString()}</div>
                        </TableCell>
                        <TableCell className="col-type cell-pad type-cell">
                          <div className="type-chip">{contrib.contribution_type}</div>
                        </TableCell>
                        <TableCell className="col-meter cell-pad">
                          <div className="meter-title">{contrib.data?.meter || contrib.data?.meter_name || '—'}</div>
                        </TableCell>
                        <TableCell className="col-source cell-pad">
                          <div className="text-sm notes-trunc">{contrib.data?.source || '—'}</div>
                        </TableCell>
                        <TableCell className="col-actions cell-pad text-right actions-cell">
                          <div className="action-row">
                            <Button
                              size="sm"
                              variant="outline"
                              className="btn-view"
                              onClick={() => setViewing(contrib)}
                            >
                              View
                            </Button>
                            <Button
                              size="sm"
                              variant="default"
                              className="btn-accept"
                              onClick={() => handleApprove(contrib.id)}
                              disabled={actionLoading === contrib.id}
                            >
                              {actionLoading === contrib.id ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                'Accept'
                              )}
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="btn-reject"
                              onClick={() => handleReject(contrib.id)}
                              disabled={actionLoading === contrib.id}
                            >
                              Reject
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </div>
        </div>

      {viewing && (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal-card">
            <div className="modal-header">
              <div>
                <div className="modal-eyebrow">Pending contribution</div>
                <div className="modal-title">{viewing.data?.meter || 'Verse contribution'}</div>
                <div className="modal-subtitle">User contribution from {viewing.users?.username || 'Unknown'} on {new Date(viewing.submitted_at).toLocaleString()}</div>
              </div>
              <button className="modal-close" onClick={() => setViewing(null)} aria-label="Close view">×</button>
            </div>
            <div className="modal-body">
              <div className="modal-meta">
                <div>
                  <div className="meta-label">Submitted by</div>
                  <div className="meta-value">{viewing.users?.username || 'Unknown'}</div>
                </div>
                <div>
                  <div className="meta-label">When</div>
                  <div className="meta-value">{new Date(viewing.submitted_at).toLocaleString()}</div>
                </div>
                <div>
                  <div className="meta-label">Source</div>
                  <div className="meta-value">{viewing.data?.source || '—'}</div>
                </div>
              </div>

              <div className="verse-block">
                <div className="verse-label">Verse Text</div>
                <div className="verse-text">
                  {viewing.data?.verse_text || '—'}
                </div>
              </div>

              <div className="details-grid">
                <div>
                  <div className="meta-label">Meter</div>
                  <div className="meta-value">{viewing.data?.meter || '—'}</div>
                </div>
                <div>
                  <div className="meta-label">L-G Pattern</div>
                  <div className="meta-value mono">{viewing.data?.lg_pattern || '—'}</div>
                </div>
                <div>
                  <div className="meta-label">Notes</div>
                  <div className="meta-value">{viewing.data?.notes || '—'}</div>
                </div>
              </div>
            </div>
              <div className="modal-actions">
                <span className="modal-note">This action cannot be undone.</span>
              <Button
                variant="outline"
                className="text-[#c0392b] border-[#f3c7c3]"
                onClick={() => handleReject(viewing.id)}
                disabled={actionLoading === viewing.id}
              >
                <XCircle className="mr-1 h-4 w-4" /> Reject
              </Button>
              <Button
                variant="default"
                className="bg-[#2f9e44] hover:bg-[#258a39] text-white"
                onClick={() => handleApprove(viewing.id)}
                disabled={actionLoading === viewing.id}
              >
                {actionLoading === viewing.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="mr-1 h-4 w-4" />} Accept
              </Button>
            </div>
          </div>
        </div>
      )}
        </div>
      </div>
    </>
  );
}
