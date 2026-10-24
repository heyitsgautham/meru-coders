#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket Module for Real-time Notifications

Provides real-time notification updates to connected clients
using Flask-SocketIO.
"""

import logging

import jwt
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room

logger = logging.getLogger(__name__)

# Global SocketIO instance (initialized in app.py)
socketio = None


def init_socketio(app):
    """
    Initialize SocketIO with the Flask app.
    
    Args:
        app: Flask application instance
        
    Returns:
        SocketIO: Configured SocketIO instance
    """
    global socketio

    socketio = SocketIO(
        app,
        cors_allowed_origins=app.config.get('CORS_ORIGINS', '*'),
        async_mode='threading',  # Use threading instead of eventlet for compatibility
        logger=True,
        engineio_logger=True,
        ping_timeout=60,
        ping_interval=25
    )

    # Register event handlers
    register_handlers()

    app.logger.info("Flask-SocketIO initialized successfully")
    return socketio


def get_socketio():
    """Get the global SocketIO instance."""
    global socketio
    return socketio


def verify_socket_token(token):
    """
    Verify JWT token for WebSocket authentication.
    
    Args:
        token: JWT token string
        
    Returns:
        dict: User data if valid, None otherwise
    """
    try:
        from backend.config import settings

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=['HS256']
        )
        return {'id': payload.get('sub'), 'email': payload.get('email')}
    except jwt.ExpiredSignatureError:
        logger.warning("WebSocket auth: Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"WebSocket auth: Invalid token - {e}")
        return None


def register_handlers():
    """Register all WebSocket event handlers."""
    global socketio

    @socketio.on('connect')
    def handle_connect(auth=None):
        """Handle client connection."""
        logger.info(f"WebSocket client connecting: {request.sid}")

        # Check for auth token
        token = None
        if auth and isinstance(auth, dict):
            token = auth.get('token')

        if not token:
            logger.warning("WebSocket connection rejected: No auth token")
            return False  # Reject connection

        # Verify token
        user = verify_socket_token(token)
        if not user:
            logger.warning("WebSocket connection rejected: Invalid token")
            return False

        # Join user's personal room for targeted notifications
        user_id = user['id']
        join_room(f"user_{user_id}")

        logger.info(f"WebSocket client connected: user {user_id}, sid {request.sid}")

        # Send connection confirmation
        emit('connected', {
            'message': 'Connected to notification server',
            'user_id': user_id
        })

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        logger.info(f"WebSocket client disconnected: {request.sid}")

    @socketio.on('subscribe_notifications')
    def handle_subscribe(data):
        """Subscribe to notification updates."""
        token = data.get('token')
        if not token:
            emit('error', {'message': 'Authentication required'})
            return

        user = verify_socket_token(token)
        if not user:
            emit('error', {'message': 'Invalid authentication'})
            return

        user_id = user['id']
        join_room(f"notifications_{user_id}")

        emit('subscribed', {
            'channel': 'notifications',
            'user_id': user_id
        })
        logger.info(f"User {user_id} subscribed to notifications")

    @socketio.on('unsubscribe_notifications')
    def handle_unsubscribe(data):
        """Unsubscribe from notification updates."""
        token = data.get('token')
        if token:
            user = verify_socket_token(token)
            if user:
                leave_room(f"notifications_{user['id']}")
                emit('unsubscribed', {'channel': 'notifications'})

    @socketio.on('mark_read')
    def handle_mark_read(data):
        """Handle marking notification as read via WebSocket."""
        token = data.get('token')
        notification_id = data.get('notification_id')

        if not token or not notification_id:
            emit('error', {'message': 'Missing required fields'})
            return

        user = verify_socket_token(token)
        if not user:
            emit('error', {'message': 'Invalid authentication'})
            return

        try:
            from backend.models.community import CommunityModel
            community_model = CommunityModel()

            result = community_model.mark_notification_read(notification_id, user['id'])
            if result.get('success'):
                emit('notification_read', {
                    'notification_id': notification_id,
                    'success': True
                })
            else:
                emit('error', {'message': result.get('error', 'Failed to mark as read')})
        except Exception as e:
            logger.error(f"Error marking notification read: {e}")
            emit('error', {'message': str(e)})

    @socketio.on('ping')
    def handle_ping():
        """Handle ping/keepalive."""
        emit('pong')


def send_notification_to_user(user_id: str, notification: dict):
    """
    Send a real-time notification to a specific user.
    
    Args:
        user_id: Target user's ID
        notification: Notification data to send
    """
    global socketio

    if socketio is None:
        logger.warning("SocketIO not initialized, cannot send notification")
        return

    try:
        # Emit to user's personal room
        socketio.emit(
            'new_notification',
            notification,
            room=f"user_{user_id}"
        )
        logger.info(f"Sent real-time notification to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send notification to user {user_id}: {e}")


def broadcast_notification(notification: dict, room: str = None):
    """
    Broadcast a notification to all connected clients or a specific room.
    
    Args:
        notification: Notification data to send
        room: Optional room to broadcast to (None = all clients)
    """
    global socketio

    if socketio is None:
        logger.warning("SocketIO not initialized, cannot broadcast")
        return

    try:
        if room:
            socketio.emit('notification', notification, room=room)
        else:
            socketio.emit('notification', notification)
        logger.info(f"Broadcast notification to room: {room or 'all'}")
    except Exception as e:
        logger.error(f"Failed to broadcast notification: {e}")


def emit_notification_count(user_id: str, count: int):
    """
    Send updated unread notification count to a user.
    
    Args:
        user_id: Target user's ID
        count: New unread count
    """
    global socketio

    if socketio is None:
        return

    try:
        socketio.emit(
            'notification_count',
            {'unread_count': count},
            room=f"user_{user_id}"
        )
    except Exception as e:
        logger.error(f"Failed to send notification count: {e}")
