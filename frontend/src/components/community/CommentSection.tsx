/**
 * CommentSection Component
 * Phase 3: Nested/threaded comment replies support
 */

import { useState, useEffect } from 'react';
import { Send, Trash2, MessageCircle, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  getComments, 
  addComment, 
  deleteComment, 
  formatRelativeTime,
  addCommentReply,
  getCommentReplies 
} from '../../services/community';
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
        // Filter out replies (parent_id !== null) - only show top-level comments
        const topLevelComments = result.comments.filter(c => !c.parent_id);
        setComments(topLevelComments);
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

  const handleReplyAdded = (parentId: string) => {
    // Update the parent comment's reply count
    setComments(prev => prev.map(c => 
      c.id === parentId 
        ? { ...c, reply_count: (c.reply_count || 0) + 1 }
        : c
    ));
    onCommentAdded?.();
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
              postId={postId}
              isOwner={user?.id === comment.user_id}
              currentUserId={user?.id}
              onDelete={handleDelete}
              onReplyAdded={handleReplyAdded}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface CommentItemProps {
  comment: Comment;
  postId: string;
  isOwner: boolean;
  currentUserId?: string;
  onDelete: (commentId: string) => void;
  onReplyAdded: (parentId: string) => void;
  isReply?: boolean;
}

function CommentItem({ 
  comment, 
  postId, 
  isOwner, 
  currentUserId,
  onDelete, 
  onReplyAdded,
  isReply = false 
}: CommentItemProps) {
  const [showReplyInput, setShowReplyInput] = useState(false);
  const [replyContent, setReplyContent] = useState('');
  const [submittingReply, setSubmittingReply] = useState(false);
  const [showReplies, setShowReplies] = useState(false);
  const [replies, setReplies] = useState<Comment[]>([]);
  const [loadingReplies, setLoadingReplies] = useState(false);
  const [replyCount, setReplyCount] = useState(comment.reply_count || 0);

  const username = comment.users?.username || 'Anonymous';
  const initials = username.slice(0, 2).toUpperCase();

  const handleLoadReplies = async () => {
    if (loadingReplies) return;
    
    if (showReplies) {
      setShowReplies(false);
      return;
    }

    setLoadingReplies(true);
    try {
      const result = await getCommentReplies(comment.id);
      if (result.success) {
        setReplies(result.comments);
        setShowReplies(true);
      }
    } catch (error) {
      console.error('Failed to load replies:', error);
    } finally {
      setLoadingReplies(false);
    }
  };

  const handleSubmitReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!replyContent.trim() || !currentUserId) return;

    setSubmittingReply(true);
    try {
      const result = await addCommentReply(postId, comment.id, { content: replyContent.trim() });
      if (result.success) {
        setReplyContent('');
        setShowReplyInput(false);
        setReplyCount(prev => prev + 1);
        
        // Add to replies if already showing
        if (showReplies) {
          setReplies(prev => [...prev, result.comment]);
        } else {
          // Show replies after adding one
          setReplies([result.comment]);
          setShowReplies(true);
        }
        
        onReplyAdded(comment.id);
      }
    } catch (error) {
      console.error('Failed to add reply:', error);
    } finally {
      setSubmittingReply(false);
    }
  };

  const handleDeleteReply = async (replyId: string) => {
    try {
      const result = await deleteComment(replyId);
      if (result.success) {
        setReplies(prev => prev.filter(r => r.id !== replyId));
        setReplyCount(prev => Math.max(0, prev - 1));
      }
    } catch (error) {
      console.error('Failed to delete reply:', error);
    }
  };

  return (
    <div className={`comment-item ${isReply ? 'comment-reply' : ''}`}>
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

        {/* Reply actions - only for top-level comments */}
        {!isReply && (
          <div className="comment-actions">
            {currentUserId && (
              <button
                className="comment-action-btn"
                onClick={() => setShowReplyInput(!showReplyInput)}
              >
                <MessageCircle size={14} />
                Reply
              </button>
            )}
            
            {replyCount > 0 && (
              <button
                className="comment-action-btn"
                onClick={handleLoadReplies}
                disabled={loadingReplies}
              >
                {loadingReplies ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : showReplies ? (
                  <ChevronUp size={14} />
                ) : (
                  <ChevronDown size={14} />
                )}
                {replyCount} {replyCount === 1 ? 'reply' : 'replies'}
              </button>
            )}
          </div>
        )}

        {/* Reply Input */}
        {showReplyInput && (
          <form onSubmit={handleSubmitReply} className="reply-input-wrapper">
            <input
              type="text"
              value={replyContent}
              onChange={(e) => setReplyContent(e.target.value)}
              placeholder={`Reply to ${username}...`}
              className="reply-input"
              autoFocus
            />
            <button
              type="submit"
              disabled={!replyContent.trim() || submittingReply}
              className="reply-submit-btn"
            >
              {submittingReply ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
            </button>
            <button
              type="button"
              className="reply-cancel-btn"
              onClick={() => {
                setShowReplyInput(false);
                setReplyContent('');
              }}
            >
              Cancel
            </button>
          </form>
        )}

        {/* Nested Replies */}
        {showReplies && replies.length > 0 && (
          <div className="replies-list">
            {replies.map((reply) => (
              <CommentItem
                key={reply.id}
                comment={reply}
                postId={postId}
                isOwner={currentUserId === reply.user_id}
                currentUserId={currentUserId}
                onDelete={handleDeleteReply}
                onReplyAdded={onReplyAdded}
                isReply={true}
              />
            ))}
          </div>
        )}
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
