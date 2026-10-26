import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import AdminPanel from './AdminPanel';

const auth = vi.hoisted(() => ({
  user: { id: 'a1', username: 'admin', is_admin: true } as null | object,
  isAdmin: true,
  loading: false,
  signOut: vi.fn(),
}));
vi.mock('../contexts/AuthContext', () => ({ useAuth: () => auth }));

const PENDING = {
  id: 'c7',
  contribution_type: 'verse',
  data: { verse_text: 'धर्मक्षेत्रे कुरुक्षेत्रे', meter: 'अनुष्टुभ्', source: 'Gita 1.1' },
  status: 'pending',
  submitted_at: '2026-10-26T00:00:00Z',
  submitted_by: 'u1',
  users: { username: 'panini' },
};

// Answers like the Flask app: only the routes it registers exist.
function server() {
  return vi.fn(async (url: string, init: RequestInit = {}) => {
    const path = new URL(url).pathname;
    const routes: Record<string, unknown> = {
      'GET /api/contributions/admin/pending': { success: true, contributions: [PENDING] },
      'POST /api/contributions/admin/approve/c7': { success: true },
      'POST /api/contributions/admin/reject/c7': { success: true },
    };
    const body = routes[`${init.method ?? 'GET'} ${path}`];
    return body
      ? { ok: true, status: 200, json: async () => body }
      : { ok: false, status: 404, json: async () => JSON.parse('<!doctype html>') };
  });
}

function renderPanel() {
  return render(
    <MemoryRouter initialEntries={['/admin']}>
      <Routes>
        <Route path="/admin" element={<AdminPanel />} />
        <Route path="/admin-login" element={<p>admin login</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  auth.user = { id: 'a1', username: 'admin', is_admin: true };
  auth.isAdmin = true;
  localStorage.setItem('authToken', 'admin-token');
  vi.spyOn(window, 'alert').mockImplementation(() => {});
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('AdminPanel', () => {
  it('sends non-admins to the admin login', () => {
    auth.isAdmin = false;
    renderPanel();
    expect(screen.getByText('admin login')).toBeInTheDocument();
  });

  it('loads the pending queue with the admin token', async () => {
    const fetchMock = server();
    vi.stubGlobal('fetch', fetchMock);
    renderPanel();

    expect(await screen.findByText('panini')).toBeInTheDocument();
    expect(fetchMock.mock.calls[0][1].headers).toMatchObject({ Authorization: 'Bearer admin-token' });
  });

  it('approves a contribution and reloads the queue', async () => {
    const fetchMock = server();
    vi.stubGlobal('fetch', fetchMock);
    renderPanel();
    const row = (await screen.findByText('panini')).closest('tr')!;

    await userEvent.click(within(row).getByRole('button', { name: 'Accept' }));

    const calls = fetchMock.mock.calls.map(([url, init]) => `${init?.method ?? 'GET'} ${new URL(url).pathname}`);
    expect(calls).toEqual([
      'GET /api/contributions/admin/pending',
      'POST /api/contributions/admin/approve/c7',
      'GET /api/contributions/admin/pending',
    ]);
    expect(window.alert).not.toHaveBeenCalled();
  });

  it('rejects after confirmation', async () => {
    const fetchMock = server();
    vi.stubGlobal('fetch', fetchMock);
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    renderPanel();
    const row = (await screen.findByText('panini')).closest('tr')!;

    await userEvent.click(within(row).getByRole('button', { name: 'Reject' }));

    expect(fetchMock.mock.calls.some(([url]) => url.endsWith('/api/contributions/admin/reject/c7'))).toBe(true);
    expect(window.alert).not.toHaveBeenCalled();
  });
});
