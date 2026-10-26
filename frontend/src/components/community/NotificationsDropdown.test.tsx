import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import * as community from '../../services/community';
import { NotificationsDropdown } from './NotificationsDropdown';

const auth = vi.hoisted(() => ({ user: null as null | { id: string; access_token: string } }));
vi.mock('../../contexts/AuthContext', () => ({ useAuth: () => ({ user: auth.user }) }));

vi.mock('../../services/community', () => ({
  getNotifications: vi.fn(),
  markNotificationRead: vi.fn(),
  markAllNotificationsRead: vi.fn(),
}));

// A stand-in for the socket service that lets a test push events.
const socket = vi.hoisted(() => {
  const listeners = { notification: new Set<(n: unknown) => void>(), connection: new Set<(c: boolean) => void>() };
  const on = <T,>(set: Set<T>) => (cb: T) => {
    set.add(cb);
    return () => set.delete(cb);
  };
  return {
    listeners,
    service: {
      connect: vi.fn(),
      disconnect: vi.fn(),
      markRead: vi.fn(),
      onNotification: on(listeners.notification),
      onConnectionChange: on(listeners.connection),
      onCountUpdate: () => () => {},
    },
  };
});
vi.mock('../../services/websocket', () => ({ websocketService: socket.service }));

const api = vi.mocked(community);

function renderBell() {
  return render(
    <MemoryRouter>
      <NotificationsDropdown />
    </MemoryRouter>,
  );
}

const bell = () => document.querySelector('.notification-bell-btn')!;

beforeEach(() => {
  auth.user = { id: 'u1', access_token: 'tok' };
  api.getNotifications.mockResolvedValue({ success: true, notifications: [], unread_count: 3 });
});

afterEach(() => {
  vi.clearAllMocks();
});

describe('NotificationsDropdown', () => {
  it('stays hidden for signed-out visitors', () => {
    auth.user = null;
    const { container } = renderBell();
    expect(container).toBeEmptyDOMElement();
    expect(api.getNotifications).not.toHaveBeenCalled();
  });

  it('connects with the login token and shows the unread count', async () => {
    renderBell();
    expect(socket.service.connect).toHaveBeenCalledWith('tok');
    await waitFor(() => expect(bell()).toHaveTextContent('3'));
    expect(screen.getByTitle('Polling mode')).toBeInTheDocument();
  });

  it('marks the bell live once the socket is accepted', async () => {
    renderBell();
    act(() => socket.listeners.connection.forEach(cb => cb(true)));
    expect(await screen.findByTitle('Real-time connected')).toBeInTheDocument();
  });

  it('counts a pushed notification and announces it', async () => {
    renderBell();
    await waitFor(() => expect(bell()).toHaveTextContent('3'));

    act(() =>
      socket.listeners.notification.forEach(cb =>
        cb({ id: 'n1', type: 'like', actor: { username: 'kalidasa' }, is_read: false, created_at: new Date().toISOString() }),
      ),
    );

    expect(bell()).toHaveTextContent('4');
    expect(screen.getByText('kalidasa liked your post')).toBeInTheDocument();
  });

  it('caps the badge at 99+', async () => {
    api.getNotifications.mockResolvedValue({ success: true, notifications: [], unread_count: 250 });
    renderBell();
    await waitFor(() => expect(bell()).toHaveTextContent('99+'));
  });
});
