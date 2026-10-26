/**
 * CommunityPage Component
 * Phase 2: Full feature set with search, following, trending, bookmarks
 */

import { useState, useCallback, useEffect } from 'react';
import { Bookmark } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Header } from '../Header';
import { useOpenAppView } from '../../hooks/useOpenAppView';
import { CreatePost } from './CreatePost';
import { PostFeed } from './PostFeed';
import { PostCard } from './PostCard';
import { SearchBar } from './SearchBar';
import { NotificationsDropdown } from './NotificationsDropdown';
import { getTrendingPosts, getBookmarkedPosts } from '../../services/community';
import type { Post, FeedFilter } from '../../types/community';
import { useAuth } from '../../contexts/AuthContext';
import '../../styles/community.css';

export function CommunityPage() {
  const { user } = useAuth();
  const [activeFilter, setActiveFilter] = useState<FeedFilter>('all');
  const [feedKey, setFeedKey] = useState(0);
  const [trendingPosts, setTrendingPosts] = useState<Post[]>([]);
  const [bookmarkedPosts, setBookmarkedPosts] = useState<Post[]>([]);
  const [loadingTrending, setLoadingTrending] = useState(false);
  const [loadingBookmarks, setLoadingBookmarks] = useState(false);

  const handlePostCreated = useCallback((_post: Post) => {
    setFeedKey(prev => prev + 1);
  }, []);

  const handleViewChange = useOpenAppView();

  // Load trending posts when tab changes
  useEffect(() => {
    if (activeFilter === 'trending' && trendingPosts.length === 0) {
      setLoadingTrending(true);
      getTrendingPosts({ limit: 20 }).then((result: { success: boolean; posts?: Post[] }) => {
        if (result.success && result.posts) {
          setTrendingPosts(result.posts);
        }
        setLoadingTrending(false);
      });
    }
  }, [activeFilter, trendingPosts.length]);

  // Load bookmarked posts when tab changes
  useEffect(() => {
    if (activeFilter === 'bookmarks' && user && bookmarkedPosts.length === 0) {
      setLoadingBookmarks(true);
      getBookmarkedPosts().then((result: { success: boolean; posts?: Post[] }) => {
        if (result.success && result.posts) {
          setBookmarkedPosts(result.posts);
        }
        setLoadingBookmarks(false);
      });
    }
  }, [activeFilter, user, bookmarkedPosts.length]);

  const handlePostDeleted = (postId: string) => {
    setTrendingPosts(prev => prev.filter(p => p.id !== postId));
    setBookmarkedPosts(prev => prev.filter(p => p.id !== postId));
  };

  const handlePostUpdated = (updatedPost: Post) => {
    setTrendingPosts(prev => prev.map(p => p.id === updatedPost.id ? updatedPost : p));
    setBookmarkedPosts(prev => prev.map(p => p.id === updatedPost.id ? updatedPost : p));
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
        {/* Main Feed Column */}
        <main className="community-main">
          {/* Page Title with Search */}
          <div className="community-page-header">
            <div className="community-header-top">
              <div>
                <h1>संस्कृत समुदाय</h1>
                <p>Sanskrit Community</p>
              </div>
              <div className="community-header-actions">
                <SearchBar />
                {user && <NotificationsDropdown />}
              </div>
            </div>
          </div>

          {/* Tabs */}
          <Tabs 
            value={activeFilter} 
            onValueChange={(value) => setActiveFilter(value as FeedFilter)}
          >
            <div className="community-tabs-wrapper">
              <TabsList className="community-tabs-list">
                <TabsTrigger value="all" className="community-tab">
                  For You
                </TabsTrigger>
                <TabsTrigger value="following" className="community-tab">
                  Following
                </TabsTrigger>
                <TabsTrigger value="trending" className="community-tab">
                  Trending
                </TabsTrigger>
                {user && (
                  <TabsTrigger value="bookmarks" className="community-tab">
                    <Bookmark size={16} className="mr-1" />
                    Saved
                  </TabsTrigger>
                )}
              </TabsList>
            </div>

            <TabsContent value="all">
              <CreatePost onPostCreated={handlePostCreated} />
              <PostFeed key={feedKey} filter="all" />
            </TabsContent>

            <TabsContent value="following">
              {user ? (
                <>
                  <CreatePost onPostCreated={handlePostCreated} />
                  <PostFeed key={`following-${feedKey}`} filter="following" />
                </>
              ) : (
                <div className="empty-state">
                  <div className="empty-state-icon">👥</div>
                  <h3 className="empty-state-title">Sign in to see following</h3>
                  <p className="empty-state-text">
                    Follow Sanskrit scholars to see their posts here.
                  </p>
                </div>
              )}
            </TabsContent>

            <TabsContent value="trending">
              {loadingTrending ? (
                <div className="loading-state">
                  <div className="loading-spinner"></div>
                  <p>Loading trending posts...</p>
                </div>
              ) : trendingPosts.length > 0 ? (
                <div className="post-list">
                  {trendingPosts.map(post => (
                    <PostCard
                      key={post.id}
                      post={post}
                      onPostDeleted={handlePostDeleted}
                      onPostUpdated={handlePostUpdated}
                    />
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <div className="empty-state-icon">🔥</div>
                  <h3 className="empty-state-title">No trending posts yet</h3>
                  <p className="empty-state-text">
                    Popular verses and discussions will appear here.
                  </p>
                </div>
              )}
            </TabsContent>

            {user && (
              <TabsContent value="bookmarks">
                {loadingBookmarks ? (
                  <div className="loading-state">
                    <div className="loading-spinner"></div>
                    <p>Loading your bookmarks...</p>
                  </div>
                ) : bookmarkedPosts.length > 0 ? (
                  <div className="post-list">
                    {bookmarkedPosts.map(post => (
                      <PostCard
                        key={post.id}
                        post={post}
                        onPostDeleted={handlePostDeleted}
                        onPostUpdated={handlePostUpdated}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">
                    <div className="empty-state-icon">📚</div>
                    <h3 className="empty-state-title">No saved posts</h3>
                    <p className="empty-state-text">
                      Bookmark posts to save them for later.
                    </p>
                  </div>
                )}
              </TabsContent>
            )}
          </Tabs>
        </main>

        {/* Right Sidebar - Info Widgets */}
        <aside className="community-sidebar">
          <div className="sidebar-widget">
            <h2 className="sidebar-widget-title">What's Happening</h2>
            <div className="sidebar-widget-item">
              <div className="sidebar-widget-item-title">📚 Chandas Analysis</div>
              <div className="sidebar-widget-item-desc">
                Analyze Sanskrit verses and identify their meters instantly
              </div>
            </div>
            <div className="sidebar-widget-item">
              <div className="sidebar-widget-item-title">🎯 SIH 2025</div>
              <div className="sidebar-widget-item-desc">
                Meru Coders - Smart India Hackathon Grand Finale
              </div>
            </div>
            <div className="sidebar-widget-item">
              <div className="sidebar-widget-item-title">🕉️ Vedic Meters</div>
              <div className="sidebar-widget-item-desc">
                Explore Gayatri, Anushtubh, Trishtubh and more
              </div>
            </div>
          </div>

          <div className="sidebar-widget">
            <h2 className="sidebar-widget-title">Learn Chandas</h2>
            <a href="/" className="sidebar-widget-link">
              Try the Analyzer →
              <span>Paste any Sanskrit verse to identify its meter</span>
            </a>
          </div>

          <div className="sidebar-footer">
            <p>© 2025 Meru Coders · SIH 2025</p>
          </div>
        </aside>
      </div>
    </div>
  );
}

export default CommunityPage;
