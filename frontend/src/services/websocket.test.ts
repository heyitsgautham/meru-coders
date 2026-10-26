import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// A server-side stand-in that speaks Engine.IO 4 / Socket.IO 5 frames.
class FakeSocket {
  static OPEN = 1;
  static last: FakeSocket;
  readyState = 0;
  sent: string[] = [];
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: ((error: unknown) => void) | null = null;
  constructor(public url: string) {
    FakeSocket.last = this;
  }
  send(frame: string) {
    this.sent.push(frame);
  }
  close() {
    this.readyState = 3;
    this.onclose?.();
  }
  open() {
    this.readyState = FakeSocket.OPEN;
    this.onopen?.();
    this.receive('0{"sid":"s1","upgrades":[],"pingInterval":25000,"pingTimeout":60000}');
  }
  receive(data: string) {
    this.onmessage?.({ data });
  }
}

async function freshService(apiUrl?: string) {
  vi.resetModules();
  vi.stubEnv('VITE_API_URL', apiUrl ?? '');
  const { websocketService } = await import('./websocket');
  return websocketService;
}

beforeEach(() => {
  vi.stubGlobal('WebSocket', FakeSocket);
  for (const method of ['log', 'warn', 'error'] as const) vi.spyOn(console, method).mockImplementation(() => {});
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('websocketService', () => {
  it('connects to the server root even when the API URL ends in /api', async () => {
    const service = await freshService('https://meru.example/api');
    service.connect('tok');
    expect(FakeSocket.last.url).toBe('wss://meru.example/socket.io/?EIO=4&transport=websocket');
  });

  it('joins the namespace with the token, as the server connect handler expects', async () => {
    const service = await freshService();
    service.connect('tok');
    FakeSocket.last.open();
    expect(FakeSocket.last.sent).toEqual(['40{"token":"tok"}']);
  });

  it('reports a live connection only once the server accepts the token', async () => {
    const service = await freshService();
    const states: boolean[] = [];
    service.onConnectionChange(state => states.push(state));
    service.connect('tok');

    FakeSocket.last.open();
    expect(service.isConnected()).toBe(false);

    FakeSocket.last.receive('40{"sid":"n1"}');
    expect(service.isConnected()).toBe(true);
    expect(states).toEqual([true]);
  });

  it('stays offline when the server refuses the token', async () => {
    const service = await freshService();
    service.connect('expired');
    FakeSocket.last.open();
    FakeSocket.last.receive('44{"message":"Connection rejected by server"}');
    expect(service.isConnected()).toBe(false);
  });

  it('delivers pushed notifications and unread counts', async () => {
    const service = await freshService();
    const notifications = vi.fn();
    const counts = vi.fn();
    service.onNotification(notifications);
    const stopCounts = service.onCountUpdate(counts);
    service.connect('tok');
    FakeSocket.last.open();
    FakeSocket.last.receive('40{"sid":"n1"}');

    FakeSocket.last.receive('42["new_notification",{"id":"n9","type":"like"}]');
    FakeSocket.last.receive('42["notification_count",{"unread_count":4}]');
    stopCounts();
    FakeSocket.last.receive('42["notification_count",{"unread_count":5}]');

    expect(notifications).toHaveBeenCalledWith({ id: 'n9', type: 'like' });
    expect(counts.mock.calls).toEqual([[4]]);
  });

  it('answers pings and sends mark_read with the token', async () => {
    const service = await freshService();
    service.connect('tok');
    FakeSocket.last.open();
    FakeSocket.last.receive('40{"sid":"n1"}');

    FakeSocket.last.receive('2');
    service.markRead('n9');

    expect(FakeSocket.last.sent.slice(1)).toEqual(['3', '42["mark_read",{"notification_id":"n9","token":"tok"}]']);
  });

  it('retries with a growing delay after the connection drops', async () => {
    vi.useFakeTimers();
    const service = await freshService();
    service.connect('tok');
    const first = FakeSocket.last;
    first.open();
    first.receive('40{"sid":"n1"}');

    first.close();
    expect(service.isConnected()).toBe(false);
    vi.advanceTimersByTime(999);
    expect(FakeSocket.last).toBe(first);
    vi.advanceTimersByTime(1);
    expect(FakeSocket.last).not.toBe(first);
  });

  it('does not reconnect after a deliberate disconnect', async () => {
    vi.useFakeTimers();
    const service = await freshService();
    service.connect('tok');
    const first = FakeSocket.last;
    first.open();
    service.disconnect();
    vi.advanceTimersByTime(60_000);
    expect(FakeSocket.last).toBe(first);
  });
});
