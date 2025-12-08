/**
 * PostFeed Component
 * Elegant feed with posts, loading states, and infinite scroll
 * Phase 2: Added following feed support
 */

import { useState, useEffect, useCallback } from 'react';
import { Loader2, RefreshCw } from 'lucide-react';
import { PostCard } from './PostCard';
import { getPosts, getFollowingFeed } from '../../services/community';
import type { Post, FeedFilter } from '../../types/community';

interface PostFeedProps {
  filter?: FeedFilter;
  userId?: string;
  onPostUpdated?: (post: Post) => void;
}

export function PostFeed({ filter = 'all', userId, onPostUpdated }: PostFeedProps) {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const POSTS_PER_PAGE = 20;

  const loadPosts = useCallback(async (reset = false) => {
    if (reset) {
      setLoading(true);
      setError(null);
    } else {
      setLoadingMore(true);
    }

    try {
      const offset = reset ? 0 : posts.length;
      
      // Choose which feed to load based on filter
      let result;
      if (filter === 'following') {
        result = await getFollowingFeed({
          limit: POSTS_PER_PAGE,
          offset,
        });
      } else {
        result = await getPosts({
          limit: POSTS_PER_PAGE,
          offset,
          user_id: userId,
        });
      }

      if (result.success) {
        const newPosts = result.posts;
        setPosts(prev => reset ? newPosts : [...prev, ...newPosts]);
        setHasMore(newPosts.length === POSTS_PER_PAGE);
      } else {
        setError(result.error || 'Failed to load posts');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load posts');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [posts.length, userId, filter]);

  useEffect(() => {
    loadPosts(true);
  }, [filter, userId]);

  const handleRefresh = () => {
    loadPosts(true);
  };

  const handleLoadMore = () => {
    if (!loadingMore && hasMore) {
      loadPosts(false);
    }
  };

  const handlePostDeleted = (postId: string) => {
    setPosts(prev => prev.filter(p => p.id !== postId));
  };

  const handlePostUpdated = (updatedPost: Post) => {
    setPosts(prev => prev.map(p => p.id === updatedPost.id ? updatedPost : p));
    onPostUpdated?.(updatedPost);
  };

  if (loading) {
    return <PostFeedSkeleton />;
  }

  if (error) {
    return (
      <div className="error-state">
        <p className="error-state-text">{error}</p>
        <button onClick={handleRefresh} className="retry-btn">
          <RefreshCw size={16} />
          Try Again
        </button>
      </div>
    );
  }

  if (posts.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">📜</div>
        <h3 className="empty-state-title">No posts yet</h3>
        <p className="empty-state-text">
          Be the first to share something with the Sanskrit community!
        </p>
      </div>
    );
  }

  return (
    <div className="post-feed">
      {/* Refresh Header */}
      <div className="post-feed-header">
        <button
          onClick={handleRefresh}
          disabled={loading}
          className="refresh-btn"
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Posts List */}
      <div className="posts-list">
        {posts.map((post) => (
          <PostCard
            key={post.id}
            post={post}
            onPostDeleted={handlePostDeleted}
            onPostUpdated={handlePostUpdated}
          />
        ))}
      </div>

      {/* Load More / End of Feed */}
      {hasMore ? (
        <div className="load-more-container">
          <button
            onClick={handleLoadMore}
            disabled={loadingMore}
            className="load-more-btn"
          >
            {loadingMore ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Loading...
              </>
            ) : (
              'Show more'
            )}
          </button>
        </div>
      ) : posts.length > 0 ? (
        <div className="feed-end">
          <div className="feed-end-icon">🙏</div>
          <p className="feed-end-text">You've reached the end</p>
        </div>
      ) : null}
    </div>
  );
}

function PostFeedSkeleton() {
  return (
    <div className="post-feed">
      {[1, 2, 3].map((i) => (
        <div key={i} className="skeleton-post">
          <div className="skeleton-avatar" />
          <div className="skeleton-content">
            <div className="skeleton-line short" />
            <div className="skeleton-line long" />
            <div className="skeleton-line medium" />
          </div>
        </div>
      ))}
    </div>
  );
}
