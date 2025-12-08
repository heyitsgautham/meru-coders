/**
 * ReportModal Component
 * Modal for reporting inappropriate content
 */

import { useState } from 'react';
import { X, Loader2, AlertTriangle } from 'lucide-react';
import { reportContent } from '../../services/community';

interface ReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  postId?: string;
  commentId?: string;
  userId?: string;
  type: 'post' | 'comment' | 'user';
}

const REPORT_REASONS = [
  { value: 'spam', label: 'Spam or misleading' },
  { value: 'harassment', label: 'Harassment or bullying' },
  { value: 'inappropriate', label: 'Inappropriate or offensive content' },
  { value: 'other', label: 'Other' },
] as const;

export function ReportModal({ isOpen, onClose, postId, commentId, userId, type }: ReportModalProps) {
  const [reason, setReason] = useState<string>('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!reason) {
      setError('Please select a reason');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const result = await reportContent({
        reason: reason as 'spam' | 'harassment' | 'inappropriate' | 'other',
        description: description.trim() || undefined,
        post_id: postId,
        comment_id: commentId,
        user_id: userId,
      });

      if (result.success) {
        setSubmitted(true);
        setTimeout(() => {
          onClose();
          // Reset state after close
          setTimeout(() => {
            setSubmitted(false);
            setReason('');
            setDescription('');
          }, 300);
        }, 2000);
      } else {
        setError(result.error || 'Failed to submit report');
      }
    } catch (err) {
      console.error('Failed to submit report:', err);
      setError('Failed to submit report. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && !submitting) {
      onClose();
    }
  };

  const getTitle = () => {
    switch (type) {
      case 'post': return 'Report Post';
      case 'comment': return 'Report Comment';
      case 'user': return 'Report User';
      default: return 'Report';
    }
  };

  return (
    <div className="report-modal-overlay" onClick={handleOverlayClick}>
      <div className="report-modal" onClick={e => e.stopPropagation()}>
        <div className="report-modal-header">
          <div className="report-modal-title-row">
            <AlertTriangle className="report-icon" size={20} />
            <h2 className="report-modal-title">{getTitle()}</h2>
          </div>
          <button 
            className="report-modal-close" 
            onClick={onClose}
            disabled={submitting}
          >
            <X size={20} />
          </button>
        </div>

        {submitted ? (
          <div className="report-success">
            <div className="report-success-icon">✓</div>
            <h3>Report Submitted</h3>
            <p>Thank you for helping keep our community safe.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="report-modal-form">
            {error && (
              <div className="report-modal-error">
                {error}
              </div>
            )}

            <p className="report-modal-description">
              Please select a reason for reporting this {type}. Our team will review your report.
            </p>

            <div className="report-reasons">
              {REPORT_REASONS.map(({ value, label }) => (
                <label key={value} className="report-reason">
                  <input
                    type="radio"
                    name="reason"
                    value={value}
                    checked={reason === value}
                    onChange={(e) => setReason(e.target.value)}
                    disabled={submitting}
                  />
                  <span className="report-reason-label">{label}</span>
                </label>
              ))}
            </div>

            <div className="report-modal-field">
              <label htmlFor="report-description">
                Additional details (optional)
              </label>
              <textarea
                id="report-description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Provide any additional context..."
                rows={3}
                disabled={submitting}
                className="report-modal-textarea"
              />
            </div>

            <div className="report-modal-actions">
              <button
                type="button"
                className="report-modal-cancel"
                onClick={onClose}
                disabled={submitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="report-modal-submit"
                disabled={submitting || !reason}
              >
                {submitting ? (
                  <>
                    <Loader2 className="animate-spin" size={16} />
                    Submitting...
                  </>
                ) : (
                  'Submit Report'
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
