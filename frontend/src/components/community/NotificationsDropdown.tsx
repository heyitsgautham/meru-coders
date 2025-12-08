/**
 * NotificationsDropdown Component
 * Shows notifications in a dropdown from the header
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, Heart, MessageCircle, UserPlus, Reply, Loader2, Check } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '../ui/dropdown-menu';
import { useAuth } from '../../contexts/AuthContext';
import {
  getNotifications,
  markNotificationRead,
  markAllNotificationsRead,
} from '../../services/community';
import type { Notification } from '../../types/community';

export function NotificationsDropdown() {
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  const fetchNotifications = async () => {
    if (!user) return;
    
    try {
      setLoading(true);
      const response = await getNotifications(20);
      if (response.success) {
        setNotifications(response.notifications);
        setUnreadCount(response.unread_count);
      }
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchNotifications();
      // Poll for new notifications every 30 seconds
      const interval = setInterval(fetchNotifications, 30000);
      return () => clearInterval(interval);
    }
  }, [user]);

  // Refresh when dropdown opens
  useEffect(() => {
    if (open && user) {
      fetchNotifications();
    }
  }, [open, user]);

  const handleNotificationClick = async (notification: Notification) => {
    // Mark as read
    if (!notification.is_read) {
      try {
        await markNotificationRead(notification.id);
        setNotifications(prev =>
          prev.map(n => n.id === notification.id ? { ...n, is_read: true } : n)
        );
        setUnreadCount(prev => Math.max(0, prev - 1));
      } catch (err) {
        console.error('Failed to mark notification as read:', err);
      }
    }

    // Navigate based on type
    setOpen(false);
    if (notification.post_id) {
      navigate(`/community/post/${notification.post_id}`);
    } else if (notification.actor_id && notification.type === 'follow') {
      navigate(`/community/user/${notification.actor_id}`);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error('Failed to mark all as read:', err);
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'like':
        return <Heart className="notification-icon like" size={16} />;
      case 'comment':
        return <MessageCircle className="notification-icon comment" size={16} />;
      case 'follow':
        return <UserPlus className="notification-icon follow" size={16} />;
      case 'reply':
        return <Reply className="notification-icon reply" size={16} />;
      default:
        return <Bell className="notification-icon" size={16} />;
    }
  };

  const getNotificationText = (notification: Notification): string => {
    const actorName = notification.actor?.username || 'Someone';
    switch (notification.type) {
      case 'like':
        return `${actorName} liked your post`;
      case 'comment':
        return `${actorName} commented on your post`;
      case 'follow':
        return `${actorName} started following you`;
      case 'reply':
        return `${actorName} replied to your comment`;
      default:
        return notification.content || 'New notification';
    }
  };

  const formatTime = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m`;
    if (diffHours < 24) return `${diffHours}h`;
    if (diffDays < 7) return `${diffDays}d`;
    return date.toLocaleDateString();
  };

  if (!user) return null;

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <button className="notification-bell-btn">
          <Bell size={20} />
          {unreadCount > 0 && (
            <span className="notification-badge">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </button>
      </DropdownMenuTrigger>
      
      <DropdownMenuContent align="end" className="notifications-dropdown">
        <div className="notifications-header">
          <h3>Notifications</h3>
          {unreadCount > 0 && (
            <button className="mark-all-read-btn" onClick={handleMarkAllRead}>
              <Check size={14} />
              Mark all read
            </button>
          )}
        </div>
        
        <DropdownMenuSeparator />
        
        {loading && notifications.length === 0 ? (
          <div className="notifications-loading">
            <Loader2 className="animate-spin" size={20} />
          </div>
        ) : notifications.length === 0 ? (
          <div className="notifications-empty">
            <Bell size={24} />
            <p>No notifications yet</p>
          </div>
        ) : (
          <div className="notifications-list">
            {notifications.map(notification => (
              <DropdownMenuItem
                key={notification.id}
                className={`notification-item ${!notification.is_read ? 'unread' : ''}`}
                onClick={() => handleNotificationClick(notification)}
              >
                <div className="notification-item-icon">
                  {getNotificationIcon(notification.type)}
                </div>
                <div className="notification-item-content">
                  <p className="notification-item-text">
                    {getNotificationText(notification)}
                  </p>
                  <span className="notification-item-time">
                    {formatTime(notification.created_at)}
                  </span>
                </div>
                {!notification.is_read && (
                  <div className="notification-unread-dot" />
                )}
              </DropdownMenuItem>
            ))}
          </div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
