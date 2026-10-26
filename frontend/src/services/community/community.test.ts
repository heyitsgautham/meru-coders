import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as community from './index';
import type { Post } from '../../types/community';

const BASE = 'http://localhost:5000/api/community';

function respond(body: unknown, status = 200) {
  return vi.fn().mockResolvedValue({ ok: status < 400, status, json: async () => body });
}

function lastCall(fetchMock: ReturnType<typeof vi.fn>) {
  const [url, init] = fetchMock.mock.calls.at(-1) as [string, RequestInit];
  return { url, init, headers: init.headers as Record<string, string> };
}

beforeEach(() => {
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('request', () => {
  it('sends the stored token as a bearer header', async () => {
    localStorage.setItem('authToken', 'tok');
    const fetchMock = respond({ success: true, posts: [] });
    vi.stubGlobal('fetch', fetchMock);

    await community.getPosts({ limit: 5, offset: 10, user_id: 'u1' });

    const { url, headers } = lastCall(fetchMock);
    expect(url).toBe(`${BASE}/posts?limit=5&offset=10&user_id=u1`);
    expect(headers.Authorization).toBe('Bearer tok');
    expect(headers['Content-Type']).toBe('application/json');
  });

  it('omits the header and the query string when there is nothing to send', async () => {
    const fetchMock = respond({ success: true });
    vi.stubGlobal('fetch', fetchMock);
    await community.getPosts();
    const { url, headers } = lastCall(fetchMock);
    expect(url).toBe(`${BASE}/posts`);
    expect(headers.Authorization).toBeUndefined();
  });

  it('raises the server error message', async () => {
    vi.stubGlobal('fetch', respond({ error: 'Content is required' }, 400));
    await expect(community.createPost({ content: '' })).rejects.toThrow('Content is required');
  });

  it('clears the session and announces it on a 401', async () => {
    localStorage.setItem('authToken', 'old');
    localStorage.setItem('appUser', '{}');
    const expired = vi.fn();
    window.addEventListener('auth:expired', expired);
    vi.stubGlobal('fetch', respond({ error: 'expired' }, 401));

    await expect(community.toggleLike('p1')).rejects.toThrow('Session expired. Please log in again.');

    expect(localStorage.getItem('authToken')).toBeNull();
    expect(localStorage.getItem('appUser')).toBeNull();
    expect(expired).toHaveBeenCalledOnce();
    window.removeEventListener('auth:expired', expired);
  });
});

describe('endpoints', () => {
  it.each([
    ['createPost', () => community.createPost({ content: 'नमः' }), '/posts', 'POST', { content: 'नमः' }],
    ['deletePost', () => community.deletePost('p1'), '/posts/p1', 'DELETE', undefined],
    ['updatePost', () => community.updatePost('p1', { content: 'x' }), '/posts/p1', 'PUT', { content: 'x' }],
    ['addComment', () => community.addComment('p1', { content: 'c' }), '/posts/p1/comments', 'POST', { content: 'c' }],
    ['deleteComment', () => community.deleteComment('c1'), '/comments/c1', 'DELETE', undefined],
    ['toggleFollow', () => community.toggleFollow('u2'), '/users/u2/follow', 'POST', undefined],
    ['toggleBookmark', () => community.toggleBookmark('p1'), '/posts/p1/bookmark', 'POST', undefined],
    ['toggleBlock', () => community.toggleBlock('u2'), '/users/u2/block', 'POST', undefined],
    ['markAllNotificationsRead', () => community.markAllNotificationsRead(), '/notifications/read-all', 'POST', undefined],
    [
      'handleReport',
      () => community.handleReport('r1', 'dismiss', 'spam'),
      '/admin/reports/r1/action',
      'POST',
      { action: 'dismiss', notes: 'spam' },
    ],
  ])('%s calls its route', async (_name, call, path, method, body) => {
    const fetchMock = respond({ success: true });
    vi.stubGlobal('fetch', fetchMock);
    await call();
    const { url, init } = lastCall(fetchMock);
    expect(url).toBe(`${BASE}${path}`);
    expect(init.method).toBe(method);
    expect(init.body ? JSON.parse(init.body as string) : undefined).toEqual(body);
  });

  it.each([
    ['searchPosts', () => community.searchPosts('gita', { limit: 3 }), '/search/posts?q=gita&limit=3'],
    ['getReports', () => community.getReports('reviewed', 20), '/admin/reports?status=reviewed&limit=20'],
    ['getFollowingFeed', () => community.getFollowingFeed({ offset: 20 }), '/feed/following?offset=20'],
    ['getModerationStats', () => community.getModerationStats(), '/admin/stats'],
  ])('%s builds its query', async (_name, call, path) => {
    const fetchMock = respond({ success: true });
    vi.stubGlobal('fetch', fetchMock);
    await call();
    expect(lastCall(fetchMock).url).toBe(`${BASE}${path}`);
  });
});

describe('uploadImage', () => {
  it('posts multipart data without a JSON content type', async () => {
    localStorage.setItem('authToken', 'tok');
    const fetchMock = respond({ success: true, url: '/uploads/a.png' });
    vi.stubGlobal('fetch', fetchMock);

    const result = await community.uploadImage(new File(['x'], 'a.png', { type: 'image/png' }));

    const { url, init, headers } = lastCall(fetchMock);
    expect(result.url).toBe('/uploads/a.png');
    expect(url).toBe(`${BASE}/upload/image`);
    expect(init.body).toBeInstanceOf(FormData);
    expect(headers['Content-Type']).toBeUndefined();
  });

  it('returns the failure instead of throwing', async () => {
    vi.stubGlobal('fetch', respond({ error: 'Too large' }, 413));
    expect(await community.uploadImage(new File(['x'], 'a.png'))).toEqual({ success: false, error: 'Too large' });
  });
});

describe('formatRelativeTime', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-10-26T12:00:00Z'));
  });
  afterEach(() => vi.useRealTimers());

  it.each([
    ['2026-10-26T11:59:30Z', 'just now'],
    ['2026-10-26T11:15:00Z', '45m'],
    ['2026-10-26T07:00:00Z', '5h'],
    ['2026-10-23T12:00:00Z', '3d'],
    ['2026-09-01T12:00:00Z', 'Sep 1'],
  ])('%s reads as %s', (date, expected) => {
    expect(community.formatRelativeTime(date)).toBe(expected);
  });
});

describe('sharePost', () => {
  const post = { id: 'p9', content: 'Gita 1.1', sanskrit_text: 'धर्मक्षेत्रे' } as Post;

  it('uses the Web Share API when the browser has it', async () => {
    const share = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal('navigator', { share });
    expect(await community.sharePost(post)).toEqual({ success: true, method: 'share' });
    expect(share.mock.calls[0][0].text).toBe('Gita 1.1\n\nधर्मक्षेत्रे');
  });

  it('copies the link when sharing is unavailable', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal('navigator', { clipboard: { writeText } });
    expect(await community.sharePost(post)).toEqual({ success: true, method: 'copy' });
    expect(writeText).toHaveBeenCalledWith(`${window.location.origin}/community/post/p9`);
  });
});
