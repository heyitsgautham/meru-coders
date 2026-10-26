/**
 * PostCard Component
 * Desktop-optimized post display with share modal
 * Phase 2: Added Edit, Bookmark, Report functionality
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Heart, MessageCircle, Share2, Trash2, MoreHorizontal, Music, Edit2, Bookmark, Flag } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
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
import { toggleLike, deletePost, formatRelativeTime, toggleBookmark } from '../../services/community';
import type { Post } from '../../types/community';
import { CommentSection } from './CommentSection';
import { ShareModal } from './ShareModal';
import { EditPostModal } from './EditPostModal';
import { ReportModal } from './ReportModal';

interface PostCardProps {
  post: Post;
  onPostDeleted?: (postId: string) => void;
  onPostUpdated?: (post: Post) => void;
}

export function PostCard({ post, onPostDeleted, onPostUpdated }: PostCardProps) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [isLiked, setIsLiked] = useState(post.is_liked || false);
  const [likesCount, setLikesCount] = useState(post.likes_count);
  const [showComments, setShowComments] = useState(false);
  const [commentsCount, setCommentsCount] = useState(post.comments_count);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState(post.is_bookmarked || false);
  const [currentPost, setCurrentPost] = useState(post);

  const isOwner = user && (user.id === post.user_id);
  const username = currentPost.users?.username || 'Anonymous';
  const avatarInitials = username.slice(0, 2).toUpperCase();

  const handlePostClick = () => {
    navigate(`/community/post/${post.id}`);
  };

  const handleLikeToggle = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!user) return;

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

  const handleBookmarkToggle = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!user) return;

    const wasBookmarked = isBookmarked;
    setIsBookmarked(!isBookmarked);

    try {
      const result = await toggleBookmark(post.id);
      if (result.success) {
        setIsBookmarked(result.bookmarked);
      } else {
        setIsBookmarked(wasBookmarked);
      }
    } catch (error) {
      setIsBookmarked(wasBookmarked);
      console.error('Failed to toggle bookmark:', error);
    }
  };

  const handleShare = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowShareModal(true);
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

  const handlePostEdited = (updatedPost: Post) => {
    setCurrentPost(updatedPost);
    onPostUpdated?.(updatedPost);
  };

  const handleCommentAdded = () => {
    setCommentsCount(prev => prev + 1);
  };

  const handleCommentDeleted = () => {
    setCommentsCount(prev => Math.max(0, prev - 1));
  };

  const handleUserClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigate(`/community/user/${post.user_id}`);
  };

  return (
    <>
      <article className="post-card" onClick={handlePostClick} style={{ cursor: 'pointer' }}>
        <div className="post-card-inner">
          <div className="post-avatar" onClick={handleUserClick}>
            <div className="avatar avatar-lg">{avatarInitials}</div>
          </div>

          <div className="post-content-area">
            <div className="post-header">
              <div className="post-author-info" onClick={handleUserClick}>
                <span className="post-author-name">{username}</span>
                <span className="post-meta">
                  @{username.toLowerCase()} · {formatRelativeTime(currentPost.created_at)}
                  {currentPost.updated_at && currentPost.updated_at !== currentPost.created_at && (
                    <span className="edited-indicator"> · edited</span>
                  )}
                </span>
              </div>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="post-menu-btn" onClick={e => e.stopPropagation()}>
                    <MoreHorizontal size={18} />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {isOwner && (
                    <>
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowEditModal(true);
                        }}
                      >
                        <Edit2 className="mr-2 h-4 w-4" />
                        Edit Post
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        className="text-red-600"
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowDeleteDialog(true);
                        }}
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete Post
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                    </>
                  )}
                  <DropdownMenuItem
                    onClick={(e) => {
                      e.stopPropagation();
                      handleBookmarkToggle(e);
                    }}
                  >
                    <Bookmark className={`mr-2 h-4 w-4 ${isBookmarked ? 'fill-current' : ''}`} />
                    {isBookmarked ? 'Remove Bookmark' : 'Bookmark'}
                  </DropdownMenuItem>
                  {!isOwner && user && (
                    <DropdownMenuItem
                      className="text-orange-600"
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowReportModal(true);
                      }}
                    >
                      <Flag className="mr-2 h-4 w-4" />
                      Report Post
                    </DropdownMenuItem>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            <p className="post-text">{currentPost.content}</p>

            {/* Post Image */}
            {currentPost.image_url && (
              <div className="post-image-container">
                <img 
                  src={(() => {
                    const url = currentPost.image_url!;
                    // Get base URL without /api suffix
                    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';
                    const baseUrl = apiUrl.replace(/\/api\/?$/, '');
                    
                    // Handle different URL formats
                    if (url.startsWith('http://') || url.startsWith('https://')) {
                      return url; // Already absolute URL (Supabase storage)
                    }
                    if (url.startsWith('/api/community/uploads')) {
                      return `${baseUrl}${url}`; // New format: /api/community/uploads/...
                    }
                    if (url.startsWith('/uploads')) {
                      return `${baseUrl}/api/community${url}`; // Old format - add /api/community prefix
                    }
                    return `${baseUrl}${url}`; // Fallback
                  })()} 
                  alt="Post attachment" 
                  className="post-image"
                  loading="lazy"
                />
              </div>
            )}

            {currentPost.sanskrit_text && (
              <div className="post-sanskrit-box">
                <p className="post-sanskrit-text">{currentPost.sanskrit_text}</p>
                
                {currentPost.meter_analysis?.found && (
                  <div className="post-meter-analysis">
                    <span className="meter-badge meter-badge-primary">
                      <Music size={14} />
                      {currentPost.meter_analysis.meter_name}
                    </span>
                    
                    {currentPost.meter_analysis.lg_pattern && (
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <span className="meter-badge meter-badge-pattern">
                              {currentPost.meter_analysis.lg_pattern.length > 24 
                                ? currentPost.meter_analysis.lg_pattern.substring(0, 24) + '...'
                                : currentPost.meter_analysis.lg_pattern}
                            </span>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p className="font-mono">{currentPost.meter_analysis.lg_pattern}</p>
                            <p className="text-xs opacity-70">Laghu-Guru Pattern</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    )}
                    
                    {currentPost.meter_analysis.syllable_count && (
                      <span className="meter-badge meter-badge-info">
                        {currentPost.meter_analysis.syllable_count} syllables
                      </span>
                    )}
                  </div>
                )}
              </div>
            )}

            <div className="post-actions">
              <button
                className={`action-btn like ${isLiked ? 'active' : ''}`}
                onClick={handleLikeToggle}
              >
                <Heart size={18} />
                <span>{likesCount || ''}</span>
              </button>

              <button
                className="action-btn comment"
                onClick={(e) => { e.stopPropagation(); setShowComments(!showComments); }}
              >
                <MessageCircle size={18} />
                <span>{commentsCount || ''}</span>
              </button>

              <button 
                className={`action-btn bookmark ${isBookmarked ? 'active' : ''}`}
                onClick={handleBookmarkToggle}
              >
                <Bookmark size={18} />
              </button>

              <button className="action-btn share" onClick={handleShare}>
                <Share2 size={18} />
                <span>Share</span>
              </button>
            </div>

            {showComments && (
              // Clicks inside the comments belong to them, not to the card that opens the post page.
              <div onClick={e => e.stopPropagation()}>
                <CommentSection
                  postId={post.id}
                  onCommentAdded={handleCommentAdded}
                  onCommentDeleted={handleCommentDeleted}
                />
              </div>
            )}
          </div>
        </div>
      </article>

      {/* Share Modal */}
      <ShareModal 
        post={currentPost} 
        isOpen={showShareModal} 
        onClose={() => setShowShareModal(false)} 
      />

      {/* Edit Modal */}
      <EditPostModal
        post={currentPost}
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        onPostUpdated={handlePostEdited}
      />

      {/* Report Modal */}
      <ReportModal
        postId={post.id}
        type="post"
        isOpen={showReportModal}
        onClose={() => setShowReportModal(false)}
      />

      {/* Delete Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Post</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={isDeleting}
              data-variant="destructive"
            >
              {isDeleting ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
