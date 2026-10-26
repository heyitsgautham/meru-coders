// Follows, bookmarks, search, notifications, profiles and blocks.
import type { BlockResponse, BookmarkResponse, DeleteResponse, FollowResponse, NotificationsResponse, PaginationParams, PostsResponse, ProfileResponse, SearchResponse, UsersResponse } from '../../types/community';
import { request } from './client';

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
