/**
 * EditPostModal Component
 * Modal for editing an existing post
 */

import { useState, useEffect } from 'react';
import { X, Loader2, Sparkles } from 'lucide-react';
import { updatePost } from '../../services/community';
import type { Post } from '../../types/community';

interface EditPostModalProps {
  post: Post;
  isOpen: boolean;
  onClose: () => void;
  onPostUpdated: (post: Post) => void;
}

export function EditPostModal({ post, isOpen, onClose, onPostUpdated }: EditPostModalProps) {
  const [content, setContent] = useState(post.content);
  const [sanskritText, setSanskritText] = useState(post.sanskrit_text || '');
  const [analyzeMeter, setAnalyzeMeter] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setContent(post.content);
      setSanskritText(post.sanskrit_text || '');
      setError(null);
    }
  }, [isOpen, post]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!content.trim()) {
      setError('Content is required');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const result = await updatePost(post.id, {
        content: content.trim(),
        sanskrit_text: sanskritText.trim() || undefined,
        analyze_meter: analyzeMeter,
      });

      if (result.success && result.post) {
        onPostUpdated(result.post);
        onClose();
      } else {
        setError(result.error || 'Failed to update post');
      }
    } catch (err) {
      console.error('Failed to update post:', err);
      setError('Failed to update post. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && !saving) {
      onClose();
    }
  };

  return (
    <div className="edit-modal-overlay" onClick={handleOverlayClick}>
      <div className="edit-modal" onClick={e => e.stopPropagation()}>
        <div className="edit-modal-header">
          <h2 className="edit-modal-title">Edit Post</h2>
          <button 
            className="edit-modal-close" 
            onClick={onClose}
            disabled={saving}
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="edit-modal-form">
          {error && (
            <div className="edit-modal-error">
              {error}
            </div>
          )}

          <div className="edit-modal-field">
            <label htmlFor="edit-content">Content</label>
            <textarea
              id="edit-content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="What's on your mind?"
              rows={3}
              disabled={saving}
              className="edit-modal-textarea"
            />
          </div>

          <div className="edit-modal-field">
            <label htmlFor="edit-sanskrit">
              Sanskrit Text (Optional)
              <Sparkles size={14} className="label-icon" />
            </label>
            <textarea
              id="edit-sanskrit"
              value={sanskritText}
              onChange={(e) => setSanskritText(e.target.value)}
              placeholder="Enter Sanskrit verse for meter analysis..."
              rows={3}
              disabled={saving}
              className="edit-modal-textarea sanskrit"
            />
          </div>

          {sanskritText.trim() && (
            <div className="edit-modal-checkbox">
              <input
                type="checkbox"
                id="edit-analyze"
                checked={analyzeMeter}
                onChange={(e) => setAnalyzeMeter(e.target.checked)}
                disabled={saving}
              />
              <label htmlFor="edit-analyze">
                Re-analyze meter (Chandas identification)
              </label>
            </div>
          )}

          <div className="edit-modal-actions">
            <button
              type="button"
              className="edit-modal-cancel"
              onClick={onClose}
              disabled={saving}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="edit-modal-save"
              disabled={saving || !content.trim()}
            >
              {saving ? (
                <>
                  <Loader2 className="animate-spin" size={16} />
                  Saving...
                </>
              ) : (
                'Save Changes'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
