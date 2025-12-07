/**
 * CommunityPage Component
 * Twitter-inspired elegant community page for Sanskrit enthusiasts
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Users } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { CreatePost } from './CreatePost';
import { PostFeed } from './PostFeed';
import type { Post, FeedFilter } from '../../types/community';
import '../../styles/community.css';

export function CommunityPage() {
  const navigate = useNavigate();
  const [activeFilter, setActiveFilter] = useState<FeedFilter>('all');
  const [feedKey, setFeedKey] = useState(0);

  const handleGoHome = () => {
    navigate('/');
  };

  const handlePostCreated = useCallback((_post: Post) => {
    setFeedKey(prev => prev + 1);
  }, []);

  return (
    <div className="community-page">
      <div className="community-container">
        {/* Header */}
        <header className="community-header">
          <div className="community-header-content">
            <div className="community-header-left">
              <button
                onClick={handleGoHome}
                className="community-back-btn"
                aria-label="Go back"
              >
                <ArrowLeft size={20} />
              </button>
              <div className="community-header-title">
                <div className="community-header-icon">
                  <Users size={20} />
                </div>
                <div className="community-header-text">
                  <h1>संस्कृत समुदाय</h1>
                  <span>Sanskrit Community</span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Tabs Navigation */}
        <Tabs 
          value={activeFilter} 
          onValueChange={(value) => setActiveFilter(value as FeedFilter)}
        >
          <div className="community-tabs-wrapper">
            <TabsList className="community-tabs-list">
              <TabsTrigger value="all" className="community-tab">
                For You
              </TabsTrigger>
              <TabsTrigger 
                value="following" 
                className="community-tab"
                disabled
                title="Coming soon"
              >
                Following
              </TabsTrigger>
              <TabsTrigger 
                value="trending" 
                className="community-tab"
                disabled
                title="Coming soon"
              >
                Trending
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="all" className="tab-content">
            {/* Create Post */}
            <CreatePost onPostCreated={handlePostCreated} />
            
            {/* Feed */}
            <PostFeed key={feedKey} filter="all" />
          </TabsContent>

          <TabsContent value="following" className="tab-content">
            <div className="empty-state">
              <div className="empty-state-icon">👥</div>
              <h3 className="empty-state-title">Following Coming Soon</h3>
              <p className="empty-state-text">
                Follow your favorite Sanskrit scholars and poets to see their posts here.
              </p>
            </div>
          </TabsContent>

          <TabsContent value="trending" className="tab-content">
            <div className="empty-state">
              <div className="empty-state-icon">🔥</div>
              <h3 className="empty-state-title">Trending Coming Soon</h3>
              <p className="empty-state-text">
                Discover the most popular verses and discussions in the community.
              </p>
            </div>
          </TabsContent>
        </Tabs>

        {/* Footer */}
        <footer className="community-footer">
          <p className="community-footer-text">
            <span className="community-footer-brand">संस्कृत समुदाय</span> • Powered by Meru Coders
            <br />
            Smart India Hackathon 2025
          </p>
        </footer>
      </div>
    </div>
  );
}

export default CommunityPage;
