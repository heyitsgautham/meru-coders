/**
 * Community API Service
 * Handles all community-related API calls (posts, likes, comments, follows, etc.)
 * Phase 2: Full feature set
 */

import type {
  Post,
  PostsResponse,
  SinglePostResponse,
  CreatePostResponse,
  UpdatePostResponse,
  DeleteResponse,
  LikeResponse,
  LikesListResponse,
  CommentsResponse,
  CreateCommentResponse,
  CreatePostInput,
  UpdatePostInput,
  CreateCommentInput,
  PaginationParams,
  FollowResponse,
  UsersResponse,
  BookmarkResponse,
  NotificationsResponse,
  ProfileResponse,
  SearchResponse,
  ReportResponse,
  BlockResponse,
  ReportInput,
} from '../types/community';

// Get API URL from environment or use default
const getAPIBaseURL = (): string => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  if (typeof window !== 'undefined' &&
    window.location.hostname !== 'localhost' &&
    window.location.hostname !== '127.0.0.1') {
    const win = window as typeof window & { CONFIG?: { API_URL?: string } };
    if (win.CONFIG?.API_URL) {
      return win.CONFIG.API_URL;
    }
    return 'http://localhost:5000/api';
  }

  return 'http://localhost:5000/api';
};

const API_BASE_URL = getAPIBaseURL();
const COMMUNITY_API = `${API_BASE_URL}/community`;

/**
 * Handle 401 Unauthorized errors - token expired
 */
function handleUnauthorized(): void {
  // Clear expired tokens
  if (typeof localStorage !== 'undefined') {
    localStorage.removeItem('authToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('appUser');
  }
  
  // Dispatch a custom event that the app can listen to
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('auth:expired', { 
      detail: { message: 'Session expired. Please log in again.' } 
    }));
  }
}

/**
 * Make an authenticated API request
 */
async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${COMMUNITY_API}${endpoint}`;
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('authToken') : null;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      // Handle 401 Unauthorized - token expired
      if (response.status === 401) {
        handleUnauthorized();
        throw new Error('Session expired. Please log in again.');
      }
      throw new Error(data.error || 'Request failed');
    }

    return data as T;
  } catch (error) {
    console.error('Community API Error:', error);
    throw error;
  }
}

// ==================== IMAGE UPLOAD ====================

export interface ImageUploadResponse {
  success: boolean;
  url?: string;
  error?: string;
}

/**
 * Upload an image for a post
 */
export async function uploadImage(file: File): Promise<ImageUploadResponse> {
  const url = `${COMMUNITY_API}/upload/image`;
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('authToken') : null;

  const formData = new FormData();
  formData.append('image', file);

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Upload failed');
    }

    return data as ImageUploadResponse;
  } catch (error) {
    console.error('Image upload error:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Upload failed' };
  }
}

// ==================== POSTS ====================

/**
 * Get posts feed (chronological order)
 */
export async function getPosts(params: PaginationParams & { user_id?: string } = {}): Promise<PostsResponse> {
  const searchParams = new URLSearchParams();
  if (params.limit) searchParams.set('limit', params.limit.toString());
  if (params.offset) searchParams.set('offset', params.offset.toString());
  if (params.user_id) searchParams.set('user_id', params.user_id);

  const query = searchParams.toString();
  return request<PostsResponse>(`/posts${query ? `?${query}` : ''}`);
}

/**
 * Get following feed (posts from users you follow)
 */
export async function getFollowingFeed(params: PaginationParams = {}): Promise<PostsResponse> {
  const searchParams = new URLSearchParams();
  if (params.limit) searchParams.set('limit', params.limit.toString());
  if (params.offset) searchParams.set('offset', params.offset.toString());

  const query = searchParams.toString();
  return request<PostsResponse>(`/feed/following${query ? `?${query}` : ''}`);
}

/**
 * Get a single post by ID
 */
export async function getPost(postId: string): Promise<SinglePostResponse> {
  return request<SinglePostResponse>(`/posts/${postId}`);
}

/**
 * Create a new post
 */
export async function createPost(input: CreatePostInput): Promise<CreatePostResponse> {
  return request<CreatePostResponse>('/posts', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

/**
 * Delete a post (only owner can delete)
 */
export async function deletePost(postId: string): Promise<DeleteResponse> {
  return request<DeleteResponse>(`/posts/${postId}`, {
    method: 'DELETE',
  });
}

// ==================== LIKES ====================

/**
 * Toggle like on a post
 */
export async function toggleLike(postId: string): Promise<LikeResponse> {
  return request<LikeResponse>(`/posts/${postId}/like`, {
    method: 'POST',
  });
}

/**
 * Get users who liked a post
 */
export async function getPostLikes(postId: string, limit?: number): Promise<LikesListResponse> {
  const query = limit ? `?limit=${limit}` : '';
  return request<LikesListResponse>(`/posts/${postId}/likes${query}`);
}

// ==================== COMMENTS ====================

/**
 * Get comments for a post
 */
export async function getComments(postId: string, params: PaginationParams = {}): Promise<CommentsResponse> {
  const searchParams = new URLSearchParams();
  if (params.limit) searchParams.set('limit', params.limit.toString());
  if (params.offset) searchParams.set('offset', params.offset.toString());

  const query = searchParams.toString();
  return request<CommentsResponse>(`/posts/${postId}/comments${query ? `?${query}` : ''}`);
}

/**
 * Add a comment to a post
 */
export async function addComment(postId: string, input: CreateCommentInput): Promise<CreateCommentResponse> {
  return request<CreateCommentResponse>(`/posts/${postId}/comments`, {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

/**
 * Delete a comment (only owner can delete)
 */
export async function deleteComment(commentId: string): Promise<DeleteResponse> {
  return request<DeleteResponse>(`/comments/${commentId}`, {
    method: 'DELETE',
  });
}

// ==================== USER ACTIVITY ====================

/**
 * Get posts by a specific user
 */
export async function getUserPosts(userId: string, params: PaginationParams = {}): Promise<PostsResponse> {
  const searchParams = new URLSearchParams();
  if (params.limit) searchParams.set('limit', params.limit.toString());
  if (params.offset) searchParams.set('offset', params.offset.toString());

  const query = searchParams.toString();
  return request<PostsResponse>(`/users/${userId}/posts${query ? `?${query}` : ''}`);
}

/**
 * Get posts liked by a user
 */
export async function getUserLikedPosts(userId: string, params: PaginationParams = {}): Promise<PostsResponse> {
  const searchParams = new URLSearchParams();
  if (params.limit) searchParams.set('limit', params.limit.toString());
  if (params.offset) searchParams.set('offset', params.offset.toString());

  const query = searchParams.toString();
  return request<PostsResponse>(`/users/${userId}/liked${query ? `?${query}` : ''}`);
}

// ==================== CURRENT USER ACTIVITY ====================

/**
 * Get current user's posts
 */
export async function getMyPosts(params: PaginationParams = {}): Promise<PostsResponse> {
  const searchParams = new URLSearchParams();
  if (params.limit) searchParams.set('limit', params.limit.toString());
  if (params.offset) searchParams.set('offset', params.offset.toString());

  const query = searchParams.toString();
  return request<PostsResponse>(`/me/posts${query ? `?${query}` : ''}`);
}

/**
 * Get current user's liked posts
 */
export async function getMyLikedPosts(params: PaginationParams = {}): Promise<PostsResponse> {
  const searchParams = new URLSearchParams();
  if (params.limit) searchParams.set('limit', params.limit.toString());
  if (params.offset) searchParams.set('offset', params.offset.toString());

  const query = searchParams.toString();
  return request<PostsResponse>(`/me/liked${query ? `?${query}` : ''}`);
}

// ==================== HELPERS ====================

/**
 * Format relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return 'just now';
  if (diffMins < 60) return `${diffMins}m`;
  if (diffHours < 24) return `${diffHours}h`;
  if (diffDays < 7) return `${diffDays}d`;

  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

/**
 * Share post using Web Share API or copy to clipboard
 */
export async function sharePost(post: Post): Promise<{ success: boolean; method: 'share' | 'copy' }> {
  const shareUrl = `${window.location.origin}/community/post/${post.id}`;
  const shareText = post.sanskrit_text
    ? `${post.content}\n\n${post.sanskrit_text}`
    : post.content;

  // Try Web Share API first
  if (navigator.share) {
    try {
      await navigator.share({
        title: 'Sanskrit Community Post',
        text: shareText,
        url: shareUrl,
      });
      return { success: true, method: 'share' };
    } catch (err) {
      // User cancelled or share failed, fall back to clipboard
    }
  }

  // Fall back to clipboard
  try {
    await navigator.clipboard.writeText(shareUrl);
    return { success: true, method: 'copy' };
  } catch (err) {
    console.error('Failed to copy to clipboard:', err);
    return { success: false, method: 'copy' };
  }
}

// ==================== PHASE 2: EDIT POST ====================

/**
 * Update a post (only owner can update)
 */
export async function updatePost(postId: string, input: UpdatePostInput): Promise<UpdatePostResponse> {
  return request<UpdatePostResponse>(`/posts/${postId}`, {
    method: 'PUT',
    body: JSON.stringify(input),
  });
}

// ==================== PHASE 2: FOLLOWS ====================

/**
 * Toggle follow on a user
 */
export async function toggleFollow(userId: string): Promise<FollowResponse> {
  return request<FollowResponse>(`/users/${userId}/follow`, {
    method: 'POST',
  });
}

/**
 * Get followers of a user
 */
export async function getFollowers(userId: string, params: PaginationParams = {}): Promise<UsersResponse> {
  const searchParams = new URLSearchParams();
  if (params.limit) searchParams.set('limit', params.limit.toString());
  if (params.offset) searchParams.set('offset', params.offset.toString());
  const query = searchParams.toString();
  return request<UsersResponse>(`/users/${userId}/followers${query ? `?${query}` : ''}`);
}

/**
 * Get users that a user follows
 */
export async function getFollowing(userId: string, params: PaginationParams = {}): Promise<UsersResponse> {
  const searchParams = new URLSearchParams();
  if (params.limit) searchParams.set('limit', params.limit.toString());
  if (params.offset) searchParams.set('offset', params.offset.toString());
  const query = searchParams.toString();
  return request<UsersResponse>(`/users/${userId}/following${query ? `?${query}` : ''}`);
}

// ==================== PHASE 2: TRENDING ====================

/**
 * Get trending posts
 */
export async function getTrendingPosts(params: PaginationParams = {}): Promise<PostsResponse> {
  const searchParams = new URLSearchParams();
  if (params.limit) searchParams.set('limit', params.limit.toString());
  if (params.offset) searchParams.set('offset', params.offset.toString());
  const query = searchParams.toString();
  return request<PostsResponse>(`/feed/trending${query ? `?${query}` : ''}`);
}

// ==================== PHASE 2: BOOKMARKS ====================

/**
 * Toggle bookmark on a post
 */
export async function toggleBookmark(postId: string): Promise<BookmarkResponse> {
  return request<BookmarkResponse>(`/posts/${postId}/bookmark`, {
    method: 'POST',
  });
}

/**
 * Get bookmarked posts
 */
export async function getBookmarkedPosts(params: PaginationParams = {}): Promise<PostsResponse> {
  const searchParams = new URLSearchParams();
  if (params.limit) searchParams.set('limit', params.limit.toString());
  if (params.offset) searchParams.set('offset', params.offset.toString());
  const query = searchParams.toString();
  return request<PostsResponse>(`/me/bookmarks${query ? `?${query}` : ''}`);
}

// ==================== PHASE 2: SEARCH ====================

/**
 * Search posts
 */
export async function searchPosts(query: string, params: PaginationParams = {}): Promise<SearchResponse> {
  const searchParams = new URLSearchParams();
  searchParams.set('q', query);
  if (params.limit) searchParams.set('limit', params.limit.toString());
  if (params.offset) searchParams.set('offset', params.offset.toString());
  return request<SearchResponse>(`/search/posts?${searchParams.toString()}`);
}

/**
 * Search users
 */
export async function searchUsers(query: string, limit?: number): Promise<UsersResponse> {
  const searchParams = new URLSearchParams();
  searchParams.set('q', query);
  if (limit) searchParams.set('limit', limit.toString());
  return request<UsersResponse>(`/search/users?${searchParams.toString()}`);
}

// ==================== PHASE 2: NOTIFICATIONS ====================

/**
 * Get notifications
 */
export async function getNotifications(limit?: number, unreadOnly?: boolean): Promise<NotificationsResponse> {
  const searchParams = new URLSearchParams();
  if (limit) searchParams.set('limit', limit.toString());
  if (unreadOnly) searchParams.set('unread', 'true');
  const query = searchParams.toString();
  return request<NotificationsResponse>(`/notifications${query ? `?${query}` : ''}`);
}

/**
 * Mark notification as read
 */
export async function markNotificationRead(notificationId: string): Promise<DeleteResponse> {
  return request<DeleteResponse>(`/notifications/${notificationId}/read`, {
    method: 'POST',
  });
}

/**
 * Mark all notifications as read
 */
export async function markAllNotificationsRead(): Promise<DeleteResponse> {
  return request<DeleteResponse>('/notifications/read-all', {
    method: 'POST',
  });
}

// ==================== PHASE 2: USER PROFILES ====================

/**
 * Get user profile
 */
export async function getUserProfile(userId: string): Promise<ProfileResponse> {
  return request<ProfileResponse>(`/users/${userId}/profile`);
}

/**
 * Update current user's profile
 */
export async function updateMyProfile(data: { bio?: string; avatar_url?: string }): Promise<DeleteResponse> {
  return request<DeleteResponse>('/me/profile', {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

// ==================== PHASE 2: REPORTS & BLOCKS ====================

/**
 * Report content
 */
export async function reportContent(input: ReportInput): Promise<ReportResponse> {
  return request<ReportResponse>('/reports', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

/**
 * Toggle block on a user
 */
export async function toggleBlock(userId: string): Promise<BlockResponse> {
  return request<BlockResponse>(`/users/${userId}/block`, {
    method: 'POST',
  });
}

/**
 * Get blocked users
 */
export async function getBlockedUsers(): Promise<UsersResponse> {
  return request<UsersResponse>('/me/blocked');
}

// ==================== PHASE 2: COMMENT REPLIES ====================

/**
 * Add a reply to a comment
 */
export async function addCommentReply(postId: string, commentId: string, input: CreateCommentInput): Promise<CreateCommentResponse> {
  return request<CreateCommentResponse>(`/posts/${postId}/comments/${commentId}/replies`, {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

/**
 * Get replies to a comment
 */
export async function getCommentReplies(commentId: string, limit?: number): Promise<CommentsResponse> {
  const query = limit ? `?limit=${limit}` : '';
  return request<CommentsResponse>(`/comments/${commentId}/replies${query}`);
}

// ==================== PHASE 3: ADMIN MODERATION ====================

export interface Report {
  id: string;
  reporter_id: string;
  reported_user_id?: string;
  post_id?: string;
  comment_id?: string;
  reason: string;
  description?: string;
  status: 'pending' | 'resolved' | 'dismissed';
  created_at: string;
  reviewed_at?: string;
  reviewed_by?: string;
  admin_notes?: string;
  action_taken?: string;
  reporter?: { id: string; username: string; avatar_url?: string };
  reported_user?: { id: string; username: string; avatar_url?: string };
  post?: { id: string; content: string; user_id: string };
  comment?: { id: string; content: string; user_id: string };
}

export interface ReportsResponse {
  success: boolean;
  reports: Report[];
  count: number;
  error?: string;
}

export interface ModerationStats {
  reports: {
    pending: number;
    resolved: number;
    dismissed: number;
    total: number;
  };
  users: {
    total: number;
    banned: number;
  };
  posts: {
    total: number;
  };
}

export interface ModerationStatsResponse {
  success: boolean;
  stats: ModerationStats;
  error?: string;
}

export interface ActionResponse {
  success: boolean;
  message?: string;
  error?: string;
}

/**
 * Get all reports (admin only)
 */
export async function getReports(status: string = 'pending', limit?: number): Promise<ReportsResponse> {
  const searchParams = new URLSearchParams();
  searchParams.set('status', status);
  if (limit) searchParams.set('limit', limit.toString());
  return request<ReportsResponse>(`/admin/reports?${searchParams.toString()}`);
}

/**
 * Take action on a report (admin only)
 */
export async function handleReport(
  reportId: string, 
  action: 'dismiss' | 'delete_content' | 'warn_user' | 'ban_user',
  notes?: string
): Promise<ActionResponse> {
  return request<ActionResponse>(`/admin/reports/${reportId}/action`, {
    method: 'POST',
    body: JSON.stringify({ action, notes }),
  });
}

/**
 * Get moderation statistics (admin only)
 */
export async function getModerationStats(): Promise<ModerationStatsResponse> {
  return request<ModerationStatsResponse>('/admin/stats');
}
