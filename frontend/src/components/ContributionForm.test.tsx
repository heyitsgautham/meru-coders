import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ContributionForm, { buildContributionPayload } from './ContributionForm';

const auth = vi.hoisted(() => ({ user: null as null | { id: string }, loading: false }));
vi.mock('../contexts/AuthContext', () => ({ useAuth: () => auth }));

function renderForm() {
  return render(
    <MemoryRouter initialEntries={['/contribute']}>
      <Routes>
        <Route path="/contribute" element={<ContributionForm />} />
        <Route path="/login" element={<p>login page</p>} />
        <Route path="/profile" element={<p>profile page</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

async function fillVerse() {
  await userEvent.type(screen.getByPlaceholderText(/Paste the verse here/), 'धर्मक्षेत्रे कुरुक्षेत्रे');
  await userEvent.type(screen.getByPlaceholderText('e.g., अनुष्टुभ्'), 'अनुष्टुभ्');
  await userEvent.type(screen.getByPlaceholderText(/Rigveda 1.1.1/), 'Bhagavad Gita 1.1');
}

beforeEach(() => {
  auth.user = { id: 'u1' };
  auth.loading = false;
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('buildContributionPayload', () => {
  it('names meter contributions the way the API expects', () => {
    expect(buildContributionPayload('meter', { meter_name: 'वसन्ततिलका' })).toEqual({
      contribution_type: 'meter_definition',
      data: { meter_name: 'वसन्ततिलका' },
    });
    expect(buildContributionPayload('verse', {}).contribution_type).toBe('verse');
  });
});

describe('ContributionForm', () => {
  it('sends signed-out visitors to the login page', () => {
    auth.user = null;
    renderForm();
    expect(screen.getByText('login page')).toBeInTheDocument();
  });

  it('submits a verse with the stored token, then returns to the profile', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    localStorage.setItem('authToken', 'tok');
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ success: true }) });
    vi.stubGlobal('fetch', fetchMock);
    renderForm();

    await fillVerse();
    await userEvent.click(screen.getByRole('button', { name: /submit/i }));

    expect(await screen.findByRole('status')).toHaveTextContent('Contribution submitted successfully!');
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/submit$/);
    expect(init.headers.Authorization).toBe('Bearer tok');
    expect(JSON.parse(init.body)).toEqual({
      contribution_type: 'verse',
      data: { verse_text: 'धर्मक्षेत्रे कुरुक्षेत्रे', meter: 'अनुष्टुभ्', source: 'Bhagavad Gita 1.1', notes: '' },
    });
    expect(screen.getByPlaceholderText(/Paste the verse here/)).toHaveValue('');

    await act(() => vi.advanceTimersByTimeAsync(2000));
    expect(screen.getByText('profile page')).toBeInTheDocument();
  });

  it('shows why the server refused it and keeps the input', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, json: async () => ({ success: false, error: 'Verse already exists' }) }));
    renderForm();

    await fillVerse();
    await userEvent.click(screen.getByRole('button', { name: /submit/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Verse already exists');
    expect(screen.getByPlaceholderText(/Paste the verse here/)).toHaveValue('धर्मक्षेत्रे कुरुक्षेत्रे');
  });
});
