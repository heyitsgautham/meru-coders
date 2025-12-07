/**
 * CommunityPage Component
 * Uses main Header navbar with centered feed layout
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Header } from '../Header';
import { CreatePost } from './CreatePost';
import { PostFeed } from './PostFeed';
import type { Post, FeedFilter } from '../../types/community';
import type { ViewType } from '../../types/api';
import '../../styles/community.css';

const STORAGE_KEY_VIEW = 'chanda_currentView';

export function CommunityPage() {
  const navigate = useNavigate();
  const [activeFilter, setActiveFilter] = useState<FeedFilter>('all');
  const [feedKey, setFeedKey] = useState(0);

  const handlePostCreated = useCallback((_post: Post) => {
    setFeedKey(prev => prev + 1);
  }, []);

  // Handle navigation to main app with selected view
  const handleViewChange = useCallback((view: ViewType) => {
    if (view === 'community') {
      // Already on community page, do nothing
      return;
    }
    // Save the view to localStorage so MainApp picks it up
    localStorage.setItem(STORAGE_KEY_VIEW, view);
    // Navigate to main app
    navigate('/app');
  }, [navigate]);

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
          {/* Page Title */}
          <div className="community-page-header">
            <h1>संस्कृत समुदाय</h1>
            <p>Sanskrit Community</p>
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
                <TabsTrigger value="following" className="community-tab" disabled>
                  Following
                </TabsTrigger>
                <TabsTrigger value="trending" className="community-tab" disabled>
                  Trending
                </TabsTrigger>
              </TabsList>
            </div>

            <TabsContent value="all">
              <CreatePost onPostCreated={handlePostCreated} />
              <PostFeed key={feedKey} filter="all" />
            </TabsContent>

            <TabsContent value="following">
              <div className="empty-state">
                <div className="empty-state-icon">👥</div>
                <h3 className="empty-state-title">Following Coming Soon</h3>
                <p className="empty-state-text">
                  Follow your favorite Sanskrit scholars to see their posts here.
                </p>
              </div>
            </TabsContent>

            <TabsContent value="trending">
              <div className="empty-state">
                <div className="empty-state-icon">🔥</div>
                <h3 className="empty-state-title">Trending Coming Soon</h3>
                <p className="empty-state-text">
                  Discover popular verses and discussions.
                </p>
              </div>
            </TabsContent>
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
