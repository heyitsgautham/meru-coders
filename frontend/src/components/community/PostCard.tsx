/**
 * PostCard Component
 * Elegant post display with like, comment, and share actions
 */

import { useState } from 'react';
import { Heart, MessageCircle, Share2, Trash2, MoreHorizontal, Music } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
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
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../ui/tooltip';
import { useAuth } from '../../contexts/AuthContext';
import { toggleLike, deletePost, sharePost, formatRelativeTime } from '../../services/community';
import type { Post } from '../../types/community';
import { CommentSection } from './CommentSection';

interface PostCardProps {
  post: Post;
  onPostDeleted?: (postId: string) => void;
  onPostUpdated?: (post: Post) => void;
}

export function PostCard({ post, onPostDeleted, onPostUpdated: _onPostUpdated }: PostCardProps) {
  const { user } = useAuth();
  const [isLiked, setIsLiked] = useState(post.is_liked || false);
  const [likesCount, setLikesCount] = useState(post.likes_count);
  const [showComments, setShowComments] = useState(false);
  const [commentsCount, setCommentsCount] = useState(post.comments_count);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const isOwner = user && (user.id === post.user_id);
  const username = post.users?.username || 'Anonymous';
  const avatarInitials = username.slice(0, 2).toUpperCase();

  const handleLikeToggle = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!user) return;

    // Optimistic update
    setIsLiked(!isLiked);
    setLikesCount(prev => isLiked ? prev - 1 : prev + 1);

    try {
      const result = await toggleLike(post.id);
      if (result.success) {
        setIsLiked(result.liked);
      } else {
        setIsLiked(isLiked);
        setLikesCount(likesCount);
      }
    } catch (error) {
      setIsLiked(isLiked);
      setLikesCount(likesCount);
      console.error('Failed to toggle like:', error);
    }
  };

  const handleShare = async (e: React.MouseEvent) => {
    e.stopPropagation();
    const result = await sharePost(post);
    if (result.success && result.method === 'copy') {
      // Could show toast notification here
      console.log('Link copied to clipboard!');
    }
  };

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      const result = await deletePost(post.id);
      if (result.success) {
        onPostDeleted?.(post.id);
      }
    } catch (error) {
      console.error('Failed to delete post:', error);
    } finally {
      setIsDeleting(false);
      setShowDeleteDialog(false);
    }
  };

  const handleCommentAdded = () => {
    setCommentsCount(prev => prev + 1);
  };

  const handleCommentDeleted = () => {
    setCommentsCount(prev => Math.max(0, prev - 1));
  };

  const handleToggleComments = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowComments(!showComments);
  };

  return (
    <>
      <article className="post-card">
        <div className="post-card-inner">
          {/* Avatar */}
          <div className="post-avatar">
            <div className="avatar avatar-lg">
              {avatarInitials}
            </div>
          </div>

          {/* Content */}
          <div className="post-content-area">
            {/* Header */}
            <div className="post-header">
              <div className="post-author-info">
                <span className="post-author-name">{username}</span>
                <span className="post-meta">
                  <span className="post-meta-separator">·</span>
                  {formatRelativeTime(post.created_at)}
                </span>
              </div>

              {isOwner && (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button className="post-menu-btn" onClick={e => e.stopPropagation()}>
                      <MoreHorizontal size={18} />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem
                      className="text-red-600 focus:text-red-600"
                      onClick={() => setShowDeleteDialog(true)}
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete Post
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
            </div>

            {/* Body */}
            <div className="post-body">
              <p className="post-text">{post.content}</p>
            </div>

            {/* Sanskrit Text with Meter Analysis */}
            {post.sanskrit_text && (
              <div className="post-sanskrit-box">
                <p className="post-sanskrit-text">{post.sanskrit_text}</p>
                
                {post.meter_analysis?.found && (
                  <div className="post-meter-analysis">
                    <span className="meter-badge meter-badge-primary">
                      <Music size={14} />
                      {post.meter_analysis.meter_name}
                    </span>
                    
                    {post.meter_analysis.lg_pattern && (
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <span className="meter-badge meter-badge-pattern">
                              {post.meter_analysis.lg_pattern.length > 20 
                                ? post.meter_analysis.lg_pattern.substring(0, 20) + '...'
                                : post.meter_analysis.lg_pattern}
                            </span>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p className="font-mono text-sm">{post.meter_analysis.lg_pattern}</p>
                            <p className="text-xs mt-1 opacity-70">Laghu-Guru Pattern</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    )}
                    
                    {post.meter_analysis.syllable_count && (
                      <span className="meter-badge meter-badge-info">
                        {post.meter_analysis.syllable_count} syllables
                      </span>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="post-actions">
              <button
                className={`action-btn like ${isLiked ? 'active' : ''}`}
                onClick={handleLikeToggle}
              >
                <Heart size={18} />
                <span className="action-count">{likesCount || ''}</span>
              </button>

              <button
                className="action-btn comment"
                onClick={handleToggleComments}
              >
                <MessageCircle size={18} />
                <span className="action-count">{commentsCount || ''}</span>
              </button>

              <button
                className="action-btn share"
                onClick={handleShare}
              >
                <Share2 size={18} />
                <span>Share</span>
              </button>
            </div>

            {/* Comments Section */}
            {showComments && (
              <CommentSection
                postId={post.id}
                onCommentAdded={handleCommentAdded}
                onCommentDeleted={handleCommentDeleted}
              />
            )}
          </div>
        </div>
      </article>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Post</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this post? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={isDeleting}
              className="bg-red-600 hover:bg-red-700"
            >
              {isDeleting ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
