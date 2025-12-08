/**
 * React Hooks for Real-time Notifications
 * 
 * Provides hooks for connecting to WebSocket and receiving real-time updates.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { websocketService, Notification } from '../services/websocket';
import { useAuth } from '../contexts/AuthContext';

/**
 * Hook for managing WebSocket connection
 */
export function useWebSocket() {
  const { user } = useAuth();
  const [connected, setConnected] = useState(false);
  const tokenRef = useRef<string | null>(null);

  // Get token from user object
  const token = user?.access_token || null;
  
  // Keep token ref updated
  useEffect(() => {
    tokenRef.current = token;
  }, [token]);

  // Connect/disconnect based on auth state
  useEffect(() => {
    if (user && token) {
      websocketService.connect(token);
    } else {
      websocketService.disconnect();
    }

    return () => {
      // Don't disconnect on unmount if user is still logged in
      // The service will handle reconnection
    };
  }, [user, token]);

  // Listen to connection state
  useEffect(() => {
    const unsubscribe = websocketService.onConnectionChange(setConnected);
    return unsubscribe;
  }, []);

  return {
    connected,
    disconnect: () => websocketService.disconnect(),
    reconnect: () => tokenRef.current && websocketService.connect(tokenRef.current)
  };
}

/**
 * Hook for receiving real-time notifications
 */
export function useRealtimeNotifications(
  onNewNotification?: (notification: Notification) => void
) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  // Listen for new notifications
  useEffect(() => {
    const unsubscribe = websocketService.onNotification((notification) => {
      setNotifications(prev => [notification, ...prev]);
      onNewNotification?.(notification);
    });

    return unsubscribe;
  }, [onNewNotification]);

  // Listen for count updates
  useEffect(() => {
    const unsubscribe = websocketService.onCountUpdate(setUnreadCount);
    return unsubscribe;
  }, []);

  // Mark a notification as read
  const markAsRead = useCallback((notificationId: string) => {
    websocketService.markRead(notificationId);
    setNotifications(prev =>
      prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
  }, []);

  // Clear new notifications (for when user opens notification panel)
  const clearNew = useCallback(() => {
    setNotifications([]);
  }, []);

  return {
    newNotifications: notifications,
    unreadCount,
    markAsRead,
    clearNew
  };
}

/**
 * Hook for notification toasts/alerts
 */
export function useNotificationToast() {
  const [latestNotification, setLatestNotification] = useState<Notification | null>(null);
  const [showToast, setShowToast] = useState(false);

  useEffect(() => {
    const unsubscribe = websocketService.onNotification((notification) => {
      setLatestNotification(notification);
      setShowToast(true);

      // Auto-hide after 5 seconds
      setTimeout(() => {
        setShowToast(false);
      }, 5000);
    });

    return unsubscribe;
  }, []);

  const dismissToast = useCallback(() => {
    setShowToast(false);
  }, []);

  return {
    notification: latestNotification,
    showToast,
    dismissToast
  };
}
