/**
 * Community Types for Twitter-like Sanskrit social platform
 * Phase 2: Full feature set with follows, notifications, bookmarks, etc.
 */

// User information for posts and comments
export interface CommunityUser {
  id: string;
  username: string;
  avatar_url?: string;
  bio?: string;
  followers_count?: number;
  following_count?: number;
  posts_count?: number;
  is_following?: boolean;
  is_blocked?: boolean;
}

// User profile (extended)
export interface UserProfile extends CommunityUser {
  created_at?: string;
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
  image_url?: string;
  created_at: string;
  updated_at?: string;
  likes_count: number;
  comments_count: number;
  is_liked?: boolean;
  is_bookmarked?: boolean;
  users?: CommunityUser;
}

// Comment data structure
export interface Comment {
  id: string;
  post_id: string;
  user_id: string;
  content: string;
  parent_id?: string;
  created_at: string;
  updated_at?: string;
  users?: CommunityUser;
  replies?: Comment[];
  reply_count?: number;
}

// Notification types
export type NotificationType = 'like' | 'comment' | 'follow' | 'reply' | 'mention';

// Notification data structure
export interface Notification {
  id: string;
  user_id: string;
  type: NotificationType;
  actor_id?: string;
  post_id?: string;
  comment_id?: string;
  content?: string;
  is_read: boolean;
  created_at: string;
  actor?: CommunityUser;
  post?: { id: string; content: string };
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

export interface UpdatePostResponse {
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

// Phase 2 response types
export interface FollowResponse {
  success: boolean;
  following: boolean;
  message?: string;
  error?: string;
}

export interface UsersResponse {
  success: boolean;
  users: CommunityUser[];
  count: number;
  error?: string;
}

export interface BookmarkResponse {
  success: boolean;
  bookmarked: boolean;
  message?: string;
  error?: string;
}

export interface NotificationsResponse {
  success: boolean;
  notifications: Notification[];
  unread_count: number;
  error?: string;
}

export interface ProfileResponse {
  success: boolean;
  profile: UserProfile;
  error?: string;
}

export interface SearchResponse {
  success: boolean;
  posts?: Post[];
  users?: CommunityUser[];
  count: number;
  error?: string;
}

export interface ReportResponse {
  success: boolean;
  message?: string;
  error?: string;
}

export interface BlockResponse {
  success: boolean;
  blocked: boolean;
  message?: string;
  error?: string;
}

// Create post input
export interface CreatePostInput {
  content: string;
  sanskrit_text?: string;
  analyze_meter?: boolean;
  image_url?: string;
}

// Update post input
export interface UpdatePostInput {
  content?: string;
  sanskrit_text?: string;
  analyze_meter?: boolean;
  image_url?: string | null;  // null to remove image
}

// Create comment input
export interface CreateCommentInput {
  content: string;
}

// Report input
export interface ReportInput {
  reason: 'spam' | 'harassment' | 'inappropriate' | 'other';
  description?: string;
  user_id?: string;
  post_id?: string;
  comment_id?: string;
}

// Feed filter types
export type FeedFilter = 'all' | 'following' | 'trending' | 'bookmarks';

// Pagination params
export interface PaginationParams {
  limit?: number;
  offset?: number;
}
