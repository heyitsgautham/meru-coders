/**
 * Community Types for Twitter-like Sanskrit social platform
 */

// User information for posts and comments
export interface CommunityUser {
  id: string;
  username: string;
  avatar_url?: string;
}

// Meter analysis result from Chanda
export interface MeterAnalysis {
  meter_name?: string;
  lg_pattern?: string;
  syllable_count?: number;
  matra_count?: number;
  gana_pattern?: string;
  found: boolean;
  error?: string;
}

// Post data structure
export interface Post {
  id: string;
  user_id: string;
  content: string;
  sanskrit_text?: string;
  meter_analysis?: MeterAnalysis;
  created_at: string;
  updated_at?: string;
  likes_count: number;
  comments_count: number;
  is_liked?: boolean;
  users?: CommunityUser;
}

// Comment data structure
export interface Comment {
  id: string;
  post_id: string;
  user_id: string;
  content: string;
  created_at: string;
  updated_at?: string;
  users?: CommunityUser;
}

// API response types
export interface PostsResponse {
  success: boolean;
  posts: Post[];
  count: number;
  error?: string;
}

export interface SinglePostResponse {
  success: boolean;
  post: Post;
  error?: string;
}

export interface CreatePostResponse {
  success: boolean;
  post: Post;
  message?: string;
  error?: string;
}

export interface DeleteResponse {
  success: boolean;
  message?: string;
  error?: string;
}

export interface LikeResponse {
  success: boolean;
  liked: boolean;
  message?: string;
  error?: string;
}

export interface LikesListResponse {
  success: boolean;
  users: CommunityUser[];
  count: number;
  error?: string;
}

export interface CommentsResponse {
  success: boolean;
  comments: Comment[];
  count: number;
  error?: string;
}

export interface CreateCommentResponse {
  success: boolean;
  comment: Comment;
  message?: string;
  error?: string;
}

// Create post input
export interface CreatePostInput {
  content: string;
  sanskrit_text?: string;
  analyze_meter?: boolean;
}

// Create comment input
export interface CreateCommentInput {
  content: string;
}

// Feed filter types (for future use)
export type FeedFilter = 'all' | 'following' | 'trending';

// Pagination params
export interface PaginationParams {
  limit?: number;
  offset?: number;
}
