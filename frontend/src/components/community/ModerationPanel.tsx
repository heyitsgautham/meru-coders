/**
 * ModerationPanel Component
 * Admin panel for reviewing and acting on reported content
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Trash2,
  Ban,
  AlertCircle,
  Loader2,
  RefreshCw,
  MessageSquare,
  FileText,
  User
} from 'lucide-react';
import { Header } from '../Header';
import { useOpenAppView } from '../../hooks/useOpenAppView';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../ui/alert-dialog';
import { useAuth } from '../../contexts/AuthContext';
import {
  getReports,
  handleReport,
  getModerationStats,
  type Report,
  type ModerationStats
} from '../../services/community';
import { formatRelativeTime } from '../../services/community';
import '../../styles/moderation.css';

type ReportStatus = 'pending' | 'resolved' | 'dismissed' | 'all';
type ReportAction = 'dismiss' | 'delete_content' | 'warn_user' | 'ban_user';

export function ModerationPanel() {
  const { user, isAdmin } = useAuth();
  const navigate = useNavigate();

  const [reports, setReports] = useState<Report[]>([]);
  const [stats, setStats] = useState<ModerationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<ReportStatus>('pending');
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [showActionDialog, setShowActionDialog] = useState(false);
  const [pendingAction, setPendingAction] = useState<{ report: Report; action: ReportAction } | null>(null);
  const [actionNotes, setActionNotes] = useState('');

  useEffect(() => {
    if (!user || !isAdmin) {
      navigate('/admin-login');
      return;
    }
    loadData();
  }, [user, isAdmin, navigate]);

  useEffect(() => {
    if (user && isAdmin) {
      loadReports();
    }
  }, [statusFilter, user, isAdmin]);

  const loadData = async () => {
    setLoading(true);
    await Promise.all([loadReports(), loadStats()]);
    setLoading(false);
  };

  const loadReports = async () => {
    try {
      const result = await getReports(statusFilter, 50);
      if (result.success) {
        setReports(result.reports);
      }
    } catch (error) {
      console.error('Failed to load reports:', error);
    }
  };

  const loadStats = async () => {
    try {
      const result = await getModerationStats();
      if (result.success) {
        setStats(result.stats);
      }
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleViewChange = useOpenAppView();

  const confirmAction = (report: Report, action: ReportAction) => {
    setPendingAction({ report, action });
    setActionNotes('');
    setShowActionDialog(true);
  };

  const executeAction = async () => {
    if (!pendingAction) return;

    const { report, action } = pendingAction;
    setActionLoading(report.id);
    setShowActionDialog(false);

    try {
      const result = await handleReport(report.id, action, actionNotes || undefined);
      if (result.success) {
        // Remove from list or update status
        setReports(prev => prev.filter(r => r.id !== report.id));
        await loadStats();
      } else {
        console.error('Action failed:', result.error);
      }
    } catch (error) {
      console.error('Failed to execute action:', error);
    } finally {
      setActionLoading(null);
      setPendingAction(null);
    }
  };

  const getActionLabel = (action: ReportAction): string => {
    switch (action) {
      case 'dismiss': return 'Dismiss Report';
      case 'delete_content': return 'Delete Content';
      case 'warn_user': return 'Warn User';
      case 'ban_user': return 'Ban User';
      default: return action;
    }
  };

  const getActionDescription = (action: ReportAction): string => {
    switch (action) {
      case 'dismiss': return 'This will mark the report as dismissed with no action taken.';
      case 'delete_content': return 'This will permanently delete the reported content.';
      case 'warn_user': return 'This will send a warning notification to the user.';
      case 'ban_user': return 'This will permanently ban the user from the platform.';
      default: return '';
    }
  };

  const getReasonBadgeColor = (reason: string): string => {
    switch (reason) {
      case 'spam': return 'bg-yellow-100 text-yellow-800';
      case 'harassment': return 'bg-red-100 text-red-800';
      case 'inappropriate': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="moderation-page">
        <Header currentView={null} onViewChange={handleViewChange} />
        <div className="moderation-loading">
          <Loader2 className="animate-spin" size={32} />
          <p>Loading moderation panel...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="moderation-page">
      <Header currentView={null} onViewChange={handleViewChange} />

      <div className="moderation-container">
        <div className="moderation-header">
          <div>
            <h1>Moderation Panel</h1>
            <p>Review and manage reported content</p>
          </div>
          <Button onClick={loadData} variant="outline">
            <RefreshCw size={16} className="mr-2" />
            Refresh
          </Button>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="moderation-stats">
            <div className="stat-card stat-pending">
              <AlertTriangle size={24} />
              <div className="stat-content">
                <span className="stat-value">{stats.reports.pending}</span>
                <span className="stat-label">Pending Reports</span>
              </div>
            </div>
            <div className="stat-card stat-resolved">
              <CheckCircle size={24} />
              <div className="stat-content">
                <span className="stat-value">{stats.reports.resolved}</span>
                <span className="stat-label">Resolved</span>
              </div>
            </div>
            <div className="stat-card stat-users">
              <User size={24} />
              <div className="stat-content">
                <span className="stat-value">{stats.users.total}</span>
                <span className="stat-label">Total Users</span>
              </div>
            </div>
            <div className="stat-card stat-banned">
              <Ban size={24} />
              <div className="stat-content">
                <span className="stat-value">{stats.users.banned}</span>
                <span className="stat-label">Banned Users</span>
              </div>
            </div>
          </div>
        )}

        {/* Filter Tabs */}
        <div className="moderation-tabs">
          {(['pending', 'resolved', 'dismissed', 'all'] as ReportStatus[]).map(status => (
            <button
              key={status}
              className={`moderation-tab ${statusFilter === status ? 'active' : ''}`}
              onClick={() => setStatusFilter(status)}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
              {status === 'pending' && stats && stats.reports.pending > 0 && (
                <span className="tab-badge">{stats.reports.pending}</span>
              )}
            </button>
          ))}
        </div>

        {/* Reports List */}
        <div className="reports-list">
          {reports.length === 0 ? (
            <div className="no-reports">
              <CheckCircle size={48} />
              <h3>No {statusFilter} reports</h3>
              <p>
                {statusFilter === 'pending'
                  ? 'Great! There are no reports waiting for review.'
                  : `No reports with status "${statusFilter}" found.`}
              </p>
            </div>
          ) : (
            reports.map(report => (
              <div
                key={report.id}
                className={`report-card ${selectedReport?.id === report.id ? 'selected' : ''}`}
                onClick={() => setSelectedReport(selectedReport?.id === report.id ? null : report)}
              >
                <div className="report-header">
                  <div className="report-meta">
                    <Badge className={getReasonBadgeColor(report.reason)}>
                      {report.reason}
                    </Badge>
                    <span className="report-time">{formatRelativeTime(report.created_at)}</span>
                  </div>
                  <div className="report-type">
                    {report.post_id && <FileText size={16} />}
                    {report.comment_id && <MessageSquare size={16} />}
                    {report.reported_user_id && !report.post_id && !report.comment_id && <User size={16} />}
                  </div>
                </div>

                <div className="report-content">
                  <div className="report-users">
                    <span className="report-label">Reporter:</span>
                    <span className="report-username">{report.reporter?.username || 'Unknown'}</span>
                    {report.reported_user && (
                      <>
                        <span className="report-arrow">→</span>
                        <span className="report-label">Reported:</span>
                        <span className="report-username">{report.reported_user.username}</span>
                      </>
                    )}
                  </div>

                  {report.description && (
                    <p className="report-description">{report.description}</p>
                  )}

                  {/* Show reported content preview */}
                  {report.post && (
                    <div className="reported-content">
                      <span className="content-label">Post content:</span>
                      <p className="content-preview">
                        {report.post.content.length > 200
                          ? report.post.content.substring(0, 200) + '...'
                          : report.post.content}
                      </p>
                    </div>
                  )}

                  {report.comment && (
                    <div className="reported-content">
                      <span className="content-label">Comment:</span>
                      <p className="content-preview">{report.comment.content}</p>
                    </div>
                  )}
                </div>

                {/* Action Buttons - show when selected and pending */}
                {selectedReport?.id === report.id && report.status === 'pending' && (
                  <div className="report-actions">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => { e.stopPropagation(); confirmAction(report, 'dismiss'); }}
                      disabled={actionLoading === report.id}
                    >
                      <XCircle size={14} className="mr-1" />
                      Dismiss
                    </Button>

                    {(report.post_id || report.comment_id) && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-orange-600"
                        onClick={(e) => { e.stopPropagation(); confirmAction(report, 'delete_content'); }}
                        disabled={actionLoading === report.id}
                      >
                        <Trash2 size={14} className="mr-1" />
                        Delete Content
                      </Button>
                    )}

                    {report.reported_user_id && (
                      <>
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-yellow-600"
                          onClick={(e) => { e.stopPropagation(); confirmAction(report, 'warn_user'); }}
                          disabled={actionLoading === report.id}
                        >
                          <AlertCircle size={14} className="mr-1" />
                          Warn User
                        </Button>

                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={(e) => { e.stopPropagation(); confirmAction(report, 'ban_user'); }}
                          disabled={actionLoading === report.id}
                        >
                          <Ban size={14} className="mr-1" />
                          Ban User
                        </Button>
                      </>
                    )}

                    {actionLoading === report.id && (
                      <Loader2 className="animate-spin ml-2" size={16} />
                    )}
                  </div>
                )}

                {/* Show action taken for resolved/dismissed */}
                {report.status !== 'pending' && report.action_taken && (
                  <div className="report-resolution">
                    <span className="resolution-label">Action taken:</span>
                    <Badge variant="outline">{report.action_taken.replace('_', ' ')}</Badge>
                    {report.admin_notes && (
                      <p className="resolution-notes">{report.admin_notes}</p>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Action Confirmation Dialog */}
      <AlertDialog open={showActionDialog} onOpenChange={setShowActionDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {pendingAction && getActionLabel(pendingAction.action)}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {pendingAction && getActionDescription(pendingAction.action)}
            </AlertDialogDescription>
          </AlertDialogHeader>

          <div className="action-notes-input">
            <label htmlFor="action-notes">Notes (optional):</label>
            <textarea
              id="action-notes"
              value={actionNotes}
              onChange={(e) => setActionNotes(e.target.value)}
              placeholder="Add notes about this action..."
              rows={3}
            />
          </div>

          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setPendingAction(null)}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction onClick={executeAction}>
              Confirm
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

export default ModerationPanel;
