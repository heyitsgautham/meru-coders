/**
 * PostView Component
 * Displays a single post by ID (for permalink sharing)
 */

import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { Header } from '../Header';
import { PostCard } from './PostCard';
import type { Post } from '../../types/community';
import type { ViewType } from '../../types/api';
import { getPost } from '../../services/community';
import '../../styles/community.css';

const STORAGE_KEY_VIEW = 'chanda_currentView';

export function PostView() {
  const { postId } = useParams<{ postId: string }>();
  const navigate = useNavigate();
  const [post, setPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPost = async () => {
      if (!postId) {
        setError('Post ID not found');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const response = await getPost(postId);
        if (response.success && response.post) {
          setPost(response.post);
          setError(null);
        } else {
          setError('Post not found');
        }
      } catch (err) {
        console.error('Failed to fetch post:', err);
        setError('Post not found or has been deleted');
      } finally {
        setLoading(false);
      }
    };

    fetchPost();
  }, [postId]);

  // Handle navigation to main app with selected view
  const handleViewChange = useCallback((view: ViewType) => {
    if (view === 'community') {
      navigate('/community');
      return;
    }
    localStorage.setItem(STORAGE_KEY_VIEW, view);
    navigate('/app');
  }, [navigate]);

  const handleBack = () => {
    navigate('/community');
  };

  const handlePostUpdated = (updatedPost: Post) => {
    setPost(updatedPost);
  };

  return (
    <div className="community-page">
      {/* Main Header/Navbar */}
      <Header 
        currentView="community" 
        onViewChange={handleViewChange} 
      />

      {/* Page Content */}
      <div className="community-content">
        {/* Main Content Column */}
        <main className="community-main">
          {/* Back Button */}
          <button className="post-view-back" onClick={handleBack}>
            <ArrowLeft size={20} />
            <span>Back to Community</span>
          </button>

          {/* Loading State */}
          {loading && (
            <div className="post-view-loading">
              <Loader2 className="animate-spin" size={32} />
              <p>Loading post...</p>
            </div>
          )}

          {/* Error State */}
          {error && !loading && (
            <div className="post-view-error">
              <div className="empty-state-icon">😔</div>
              <h3 className="empty-state-title">{error}</h3>
              <p className="empty-state-text">
                The post you're looking for might have been removed or doesn't exist.
              </p>
              <button className="post-view-back-btn" onClick={handleBack}>
                Go to Community
              </button>
            </div>
          )}

          {/* Post Content */}
          {post && !loading && (
            <div className="post-view-content">
              <PostCard 
                post={post} 
                onPostUpdated={handlePostUpdated}
              />
            </div>
          )}
        </main>

        {/* Right Sidebar */}
        <aside className="community-sidebar">
          <div className="sidebar-card">
            <h3 className="sidebar-card-title">Share this post</h3>
            <p className="sidebar-card-text">
              You're viewing a shared post from the Sanskrit Community.
            </p>
          </div>

          <div className="sidebar-card">
            <h3 className="sidebar-card-title">Learn Chandas</h3>
            <a href="/app" className="sidebar-link">Try the Analyzer →</a>
            <p className="sidebar-card-text">
              Paste any Sanskrit verse to identify its meter
            </p>
          </div>

          <div className="sidebar-footer">
            © 2025 Meru Coders · SIH 2025
          </div>
        </aside>
      </div>
    </div>
  );
}
