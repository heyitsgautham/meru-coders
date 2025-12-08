/**
 * WebSocket Service for Real-time Notifications
 * 
 * Provides real-time communication with the backend for notifications
 * and other live updates.
 */

// Socket.IO client type definitions for manual implementation
// Using native WebSocket with Socket.IO protocol fallback

interface Notification {
  id: string;
  type: string;
  actor_id: string;
  actor?: {
    id: string;
    username: string;
    avatar_url?: string;
  };
  post_id?: string;
  comment_id?: string;
  content?: string;
  is_read: boolean;
  created_at: string;
}

type NotificationCallback = (notification: Notification) => void;
type CountCallback = (count: number) => void;
type ConnectionCallback = (connected: boolean) => void;

class WebSocketService {
  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private token: string | null = null;
  private connected = false;
  private listeners: {
    notification: NotificationCallback[];
    count: CountCallback[];
    connection: ConnectionCallback[];
  } = {
    notification: [],
    count: [],
    connection: []
  };

  /**
   * Connect to the WebSocket server
   */
  connect(token: string): void {
    if (this.socket && this.connected) {
      console.log('WebSocket already connected');
      return;
    }

    this.token = token;
    
    // Get the API URL from environment
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000';
    const wsUrl = apiUrl.replace('http://', 'ws://').replace('https://', 'wss://');
    
    try {
      // Connect using Socket.IO protocol
      this.socket = new WebSocket(`${wsUrl}/socket.io/?EIO=4&transport=websocket`);
      
      this.socket.onopen = () => {
        console.log('WebSocket connection established');
        this.connected = true;
        this.reconnectAttempts = 0;
        
        // Send authentication
        this.send('auth', { token: this.token });
        
        // Notify listeners
        this.listeners.connection.forEach(cb => cb(true));
      };

      this.socket.onmessage = (event) => {
        this.handleMessage(event.data);
      };

      this.socket.onclose = () => {
        console.log('WebSocket connection closed');
        this.connected = false;
        this.listeners.connection.forEach(cb => cb(false));
        this.attemptReconnect();
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(data: string): void {
    try {
      // Socket.IO protocol: messages are prefixed with packet type
      // 0 = connect, 2 = event, 3 = ack, 4 = error, 40 = connect (namespace), 42 = event with data
      
      if (data.startsWith('42')) {
        // Event message
        const jsonData = data.substring(2);
        const [event, payload] = JSON.parse(jsonData);
        
        switch (event) {
          case 'new_notification':
            this.listeners.notification.forEach(cb => cb(payload));
            break;
          case 'notification_count':
            this.listeners.count.forEach(cb => cb(payload.unread_count));
            break;
          case 'connected':
            console.log('Authenticated with notification server');
            break;
          case 'error':
            console.error('Server error:', payload);
            break;
        }
      } else if (data === '2') {
        // Ping - respond with pong
        this.socket?.send('3');
      } else if (data.startsWith('0')) {
        // Connection established, send auth
        this.send('auth', { token: this.token });
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error, data);
    }
  }

  /**
   * Send a message to the server
   */
  private send(event: string, data?: any): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      const message = data ? JSON.stringify([event, data]) : JSON.stringify([event]);
      this.socket.send('42' + message);
    }
  }

  /**
   * Attempt to reconnect after disconnect
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnect attempts reached');
      return;
    }

    if (!this.token) {
      console.log('No token available for reconnect');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Attempting reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      if (!this.connected && this.token) {
        this.connect(this.token);
      }
    }, delay);
  }

  /**
   * Disconnect from the WebSocket server
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
      this.connected = false;
      this.token = null;
    }
  }

  /**
   * Subscribe to new notifications
   */
  onNotification(callback: NotificationCallback): () => void {
    this.listeners.notification.push(callback);
    return () => {
      this.listeners.notification = this.listeners.notification.filter(cb => cb !== callback);
    };
  }

  /**
   * Subscribe to unread count updates
   */
  onCountUpdate(callback: CountCallback): () => void {
    this.listeners.count.push(callback);
    return () => {
      this.listeners.count = this.listeners.count.filter(cb => cb !== callback);
    };
  }

  /**
   * Subscribe to connection state changes
   */
  onConnectionChange(callback: ConnectionCallback): () => void {
    this.listeners.connection.push(callback);
    return () => {
      this.listeners.connection = this.listeners.connection.filter(cb => cb !== callback);
    };
  }

  /**
   * Mark a notification as read via WebSocket
   */
  markRead(notificationId: string): void {
    this.send('mark_read', {
      notification_id: notificationId,
      token: this.token
    });
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.connected;
  }
}

// Export singleton instance
export const websocketService = new WebSocketService();

// Export types
export type { Notification, NotificationCallback, CountCallback, ConnectionCallback };
