/**
 * UserProfile Component
 * View a user's profile with their posts, followers, and following
 */

import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, Calendar, MoreHorizontal, Flag, Ban } from 'lucide-react';
import { Header } from '../Header';
import { PostCard } from './PostCard';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import { useAuth } from '../../contexts/AuthContext';
import {
  getUserProfile,
  getPosts,
  toggleFollow,
  toggleBlock,
  reportContent,
} from '../../services/community';
import type { UserProfile as UserProfileType, Post } from '../../types/community';
import type { ViewType } from '../../types/api';
import '../../styles/community.css';

const STORAGE_KEY_VIEW = 'chanda_currentView';

export function UserProfile() {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const { user: currentUser } = useAuth();
  
  const [profile, setProfile] = useState<UserProfileType | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [postsLoading, setPostsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isFollowing, setIsFollowing] = useState(false);
  const [followLoading, setFollowLoading] = useState(false);

  const currentUserId = currentUser?.id;
  const isOwnProfile = currentUserId === userId;

  useEffect(() => {
    const fetchProfile = async () => {
      if (!userId) {
        setError('User ID not found');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const response = await getUserProfile(userId);
        if (response.success && response.profile) {
          setProfile(response.profile);
          setIsFollowing(response.profile.is_following || false);
        } else {
          setError('User not found');
        }
      } catch (err) {
        console.error('Failed to fetch profile:', err);
        setError('Failed to load profile');
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [userId]);

  useEffect(() => {
    const fetchPosts = async () => {
      if (!userId) return;

      try {
        setPostsLoading(true);
        const response = await getPosts({ user_id: userId, limit: 20 });
        if (response.success) {
          setPosts(response.posts);
        }
      } catch (err) {
        console.error('Failed to fetch posts:', err);
      } finally {
        setPostsLoading(false);
      }
    };

    if (!loading && profile) {
      fetchPosts();
    }
  }, [userId, loading, profile]);

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

  const handleFollowToggle = async () => {
    if (!userId || !currentUserId || isOwnProfile) return;

    setFollowLoading(true);
    try {
      const result = await toggleFollow(userId);
      if (result.success) {
        setIsFollowing(result.following);
        setProfile(prev => prev ? {
          ...prev,
          followers_count: (prev.followers_count || 0) + (result.following ? 1 : -1)
        } : null);
      }
    } catch (err) {
      console.error('Failed to toggle follow:', err);
    } finally {
      setFollowLoading(false);
    }
  };

  const handleBlock = async () => {
    if (!userId || !currentUserId) return;
    
    try {
      const result = await toggleBlock(userId);
      if (result.success && result.blocked) {
        navigate('/community');
      }
    } catch (err) {
      console.error('Failed to block user:', err);
    }
  };

  const handleReport = async () => {
    if (!userId) return;
    
    try {
      await reportContent({
        reason: 'inappropriate',
        user_id: userId,
      });
      alert('Report submitted. Thank you for helping keep our community safe.');
    } catch (err) {
      console.error('Failed to report user:', err);
    }
  };

  const handlePostDeleted = (postId: string) => {
    setPosts(prev => prev.filter(p => p.id !== postId));
  };

  const formatJoinDate = (dateString?: string) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  };

  return (
    <div className="community-page">
      <Header currentView="community" onViewChange={handleViewChange} />

      <div className="community-content">
        <main className="community-main">
          {/* Back Button */}
          <button className="post-view-back" onClick={handleBack}>
            <ArrowLeft size={20} />
            <span>Back</span>
          </button>

          {/* Loading State */}
          {loading && (
            <div className="post-view-loading">
              <Loader2 className="animate-spin" size={32} />
              <p>Loading profile...</p>
            </div>
          )}

          {/* Error State */}
          {error && !loading && (
            <div className="post-view-error">
              <div className="empty-state-icon">😔</div>
              <h3 className="empty-state-title">{error}</h3>
              <button className="post-view-back-btn" onClick={handleBack}>
                Go to Community
              </button>
            </div>
          )}

          {/* Profile Content */}
          {profile && !loading && (
            <>
              {/* Profile Header */}
              <div className="profile-header">
                <div className="profile-header-top">
                  <div className="profile-avatar-large">
                    {profile.avatar_url ? (
                      <img src={profile.avatar_url} alt={profile.username} />
                    ) : (
                      <span>{profile.username.slice(0, 2).toUpperCase()}</span>
                    )}
                  </div>

                  <div className="profile-actions">
                    {!isOwnProfile && currentUserId && (
                      <>
                        <button
                          className={`follow-btn ${isFollowing ? 'following' : ''}`}
                          onClick={handleFollowToggle}
                          disabled={followLoading}
                        >
                          {followLoading ? (
                            <Loader2 className="animate-spin" size={16} />
                          ) : isFollowing ? (
                            'Following'
                          ) : (
                            'Follow'
                          )}
                        </button>

                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <button className="profile-menu-btn">
                              <MoreHorizontal size={20} />
                            </button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={handleReport}>
                              <Flag className="mr-2 h-4 w-4" />
                              Report User
                            </DropdownMenuItem>
                            <DropdownMenuItem className="text-red-600" onClick={handleBlock}>
                              <Ban className="mr-2 h-4 w-4" />
                              Block User
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </>
                    )}
                    
                    {isOwnProfile && (
                      <button
                        className="edit-profile-btn"
                        onClick={() => navigate('/profile')}
                      >
                        Edit Profile
                      </button>
                    )}
                  </div>
                </div>

                <div className="profile-info">
                  <h1 className="profile-username">{profile.username}</h1>
                  <p className="profile-handle">@{profile.username.toLowerCase()}</p>
                  
                  {profile.bio && (
                    <p className="profile-bio">{profile.bio}</p>
                  )}

                  <div className="profile-meta">
                    {profile.created_at && (
                      <span className="profile-meta-item">
                        <Calendar size={16} />
                        Joined {formatJoinDate(profile.created_at)}
                      </span>
                    )}
                  </div>

                  <div className="profile-stats">
                    <button className="profile-stat">
                      <span className="profile-stat-value">{profile.posts_count || 0}</span>
                      <span className="profile-stat-label">Posts</span>
                    </button>
                    <button className="profile-stat">
                      <span className="profile-stat-value">{profile.followers_count || 0}</span>
                      <span className="profile-stat-label">Followers</span>
                    </button>
                    <button className="profile-stat">
                      <span className="profile-stat-value">{profile.following_count || 0}</span>
                      <span className="profile-stat-label">Following</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* User's Posts */}
              <div className="profile-posts">
                <h2 className="profile-section-title">Posts</h2>
                
                {postsLoading ? (
                  <div className="post-view-loading">
                    <Loader2 className="animate-spin" size={24} />
                  </div>
                ) : posts.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-state-icon">📝</div>
                    <h3 className="empty-state-title">No posts yet</h3>
                    <p className="empty-state-text">
                      {isOwnProfile ? 'Share your first post!' : 'This user hasn\'t posted anything yet.'}
                    </p>
                  </div>
                ) : (
                  posts.map(post => (
                    <PostCard
                      key={post.id}
                      post={post}
                      onPostDeleted={handlePostDeleted}
                    />
                  ))
                )}
              </div>
            </>
          )}
        </main>

        {/* Right Sidebar */}
        <aside className="community-sidebar">
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
