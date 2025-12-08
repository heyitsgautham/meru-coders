/**
 * Community API Service
 * Handles all community-related API calls (posts, likes, comments)
 */

import type {
  Post,
  PostsResponse,
  SinglePostResponse,
  CreatePostResponse,
  DeleteResponse,
  LikeResponse,
  LikesListResponse,
  CommentsResponse,
  CreateCommentResponse,
  CreatePostInput,
  CreateCommentInput,
  PaginationParams,
} from '../types/community';

// Import shared API URL utility
import { getAPIURL } from './api';

// Computed at request time, not module load time
const getCommunityAPI = () => `${getAPIURL()}/community`;

/**
 * Make an authenticated API request
 */
async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${getCommunityAPI()}${endpoint}`;
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
      throw new Error(data.error || 'Request failed');
    }

    return data as T;
  } catch (error) {
    console.error('Community API Error:', error);
    throw error;
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
