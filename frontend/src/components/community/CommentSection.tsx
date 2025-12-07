/**
 * CommentSection Component
 * Elegant comments display with add/delete functionality
 */

import { useState, useEffect } from 'react';
import { Send, Trash2 } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { getComments, addComment, deleteComment, formatRelativeTime } from '../../services/community';
import type { Comment } from '../../types/community';

interface CommentSectionProps {
  postId: string;
  onCommentAdded?: () => void;
  onCommentDeleted?: () => void;
}

export function CommentSection({ postId, onCommentAdded, onCommentDeleted }: CommentSectionProps) {
  const { user } = useAuth();
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [newComment, setNewComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadComments();
  }, [postId]);

  const loadComments = async () => {
    setLoading(true);
    try {
      const result = await getComments(postId);
      if (result.success) {
        setComments(result.comments);
      }
    } catch (error) {
      console.error('Failed to load comments:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim() || !user) return;

    setSubmitting(true);
    try {
      const result = await addComment(postId, { content: newComment.trim() });
      if (result.success) {
        setComments(prev => [...prev, result.comment]);
        setNewComment('');
        onCommentAdded?.();
      }
    } catch (error) {
      console.error('Failed to add comment:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (commentId: string) => {
    try {
      const result = await deleteComment(commentId);
      if (result.success) {
        setComments(prev => prev.filter(c => c.id !== commentId));
        onCommentDeleted?.();
      }
    } catch (error) {
      console.error('Failed to delete comment:', error);
    }
  };

  const userInitials = user ? (user.username || 'U').slice(0, 2).toUpperCase() : '';

  return (
    <div className="comments-section">
      {/* Comment Input */}
      {user ? (
        <form onSubmit={handleSubmit} className="comment-input-wrapper">
          <div className="avatar avatar-sm">
            {userInitials}
          </div>
          <div className="comment-input-form">
            <input
              type="text"
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Write a comment..."
              className="comment-input"
            />
            <button
              type="submit"
              disabled={!newComment.trim() || submitting}
              className="comment-submit-btn"
            >
              <Send size={16} />
            </button>
          </div>
        </form>
      ) : (
        <p className="no-comments">
          <a href="/login" style={{ color: 'var(--community-primary)', fontWeight: 600 }}>Sign in</a> to comment
        </p>
      )}

      {/* Comments List */}
      {loading ? (
        <div className="comment-list">
          {[1, 2].map((i) => (
            <div key={i} className="comment-item">
              <div className="skeleton-avatar" style={{ width: 32, height: 32 }} />
              <div className="skeleton-content" style={{ flex: 1 }}>
                <div className="skeleton-line short" />
                <div className="skeleton-line medium" />
              </div>
            </div>
          ))}
        </div>
      ) : comments.length === 0 ? (
        <p className="no-comments">
          No comments yet. Be the first to share your thoughts!
        </p>
      ) : (
        <div className="comment-list">
          {comments.map((comment) => (
            <CommentItem
              key={comment.id}
              comment={comment}
              isOwner={user?.id === comment.user_id}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface CommentItemProps {
  comment: Comment;
  isOwner: boolean;
  onDelete: (commentId: string) => void;
}

function CommentItem({ comment, isOwner, onDelete }: CommentItemProps) {
  const username = comment.users?.username || 'Anonymous';
  const initials = username.slice(0, 2).toUpperCase();

  return (
    <div className="comment-item">
      <div className="avatar avatar-xs">
        {initials}
      </div>
      <div className="comment-item-content">
        <div className="comment-item-bubble">
          <div className="comment-item-header">
            <span className="comment-item-author">{username}</span>
            <span className="comment-item-time">{formatRelativeTime(comment.created_at)}</span>
          </div>
          <p className="comment-item-text">{comment.content}</p>
        </div>
      </div>
      {isOwner && (
        <button
          onClick={() => onDelete(comment.id)}
          className="comment-item-delete"
        >
          <Trash2 size={14} />
        </button>
      )}
    </div>
  );
}
