// Community posts: feeds, a single post, creating, editing and deleting, likes and per-user lists.
import type { CreatePostInput, CreatePostResponse, DeleteResponse, LikeResponse, LikesListResponse, PaginationParams, PostsResponse, SinglePostResponse, UpdatePostInput, UpdatePostResponse } from '../../types/community';
import { request } from './client';

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

/**
 * Update a post (only owner can update)
 */
export async function updatePost(postId: string, input: UpdatePostInput): Promise<UpdatePostResponse> {
  return request<UpdatePostResponse>(`/posts/${postId}`, {
    method: 'PUT',
    body: JSON.stringify(input),
  });
}

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
