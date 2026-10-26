// Comments on posts and replies to comments.
import type { CommentsResponse, CreateCommentInput, CreateCommentResponse, DeleteResponse, PaginationParams } from '../../types/community';
import { request } from './client';

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
