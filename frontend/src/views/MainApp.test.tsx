import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import * as api from '../services/api';
import { AuthProvider } from '../contexts/AuthContext';
import MainApp from './MainApp';

vi.mock('../lib/supabase', () => ({ isSupabaseConfigured: false, supabase: { auth: {} } }));
vi.mock('../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../services/api')>()),
  getAPIInfo: vi.fn(),
  getExamples: vi.fn(),
  identifyFromText: vi.fn(),
  getDatasets: vi.fn(),
  getApprovedContributions: vi.fn(),
}));
// The analysis and results views have their own tests.
vi.mock('../components/ResultsDisplay', () => ({ ResultsDisplay: () => <div data-testid="results" /> }));
vi.mock('../components/PingalaAcharyaSpeaker', () => ({ PingalaAcharyaSpeaker: () => null }));

const mocked = vi.mocked(api);

function renderApp(path = '/app') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <Routes>
          <Route path="/app" element={<MainApp />} />
          <Route path="/" element={<p>landing</p>} />
          <Route path="/lg-lab" element={<p>lab</p>} />
          <Route path="/community" element={<p>community</p>} />
          <Route path="/profile" element={<p>profile</p>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.resetAllMocks();
  for (const method of ['log', 'info', 'warn'] as const) vi.spyOn(console, method).mockImplementation(() => {});
  window.scrollTo = vi.fn();
  Element.prototype.scrollIntoView = vi.fn();
  mocked.getAPIInfo.mockResolvedValue({} as never);
  mocked.getExamples.mockResolvedValue({
    success: true,
    examples: [{ meter: 'गायत्री', lines: ['अग्निमीळे पुरोहितं', ''], mode: 'vedic' }],
  } as never);
  mocked.getDatasets.mockResolvedValue({ success: true, datasets: [], sources: [] } as never);
  mocked.getApprovedContributions.mockResolvedValue({ success: true, contributions: [] } as never);
  mocked.identifyFromText.mockResolvedValue({ success: true, result: { line: [], verse: [] } } as never);
});

describe('MainApp', () => {
  it('opens on the analyser and remembers the chosen view', async () => {
    const user = userEvent.setup();
    renderApp();
    expect(screen.getByText('Analyze Sanskrit Text')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'About' }));
    expect(localStorage.getItem('chanda_currentView')).toBe('about');
  });

  it('restores the last view', () => {
    localStorage.setItem('chanda_currentView', 'datasets');
    renderApp();
    expect(screen.getByText('Loading datasets...')).toBeInTheDocument();
  });

  it('sends a chosen example to the analyser in its mode', async () => {
    const user = userEvent.setup();
    renderApp();
    await user.click(screen.getByRole('button', { name: 'Examples' }));
    await user.click(await screen.findByText('अग्निमीळे पुरोहितं'));
    expect(screen.getByPlaceholderText(/Type or paste/)).toHaveValue('अग्निमीळे पुरोहितं');
    await user.click(screen.getByRole('button', { name: 'Identify Chanda' }));
    await waitFor(() => expect(mocked.identifyFromText).toHaveBeenCalledWith('अग्निमीळे पुरोहितं', 'verse', '', 'vedic'));
  });

  it('identifies a verse passed in the URL straight away', async () => {
    renderApp('/app?text=%E0%A4%A7%E0%A4%B0%E0%A5%8D%E0%A4%AE');
    await waitFor(() => expect(mocked.identifyFromText).toHaveBeenCalledWith('धर्म', 'verse', '', 'auto'), { timeout: 2000 });
  });

  it.each([
    ['L-G Lab', 'lab'],
    ['Community', 'community'],
  ])('header %s button leaves the analyser', async (name, page) => {
    const user = userEvent.setup();
    renderApp();
    await user.click(screen.getByRole('button', { name }));
    expect(screen.getByText(page)).toBeInTheDocument();
  });

  it('links to login when signed out and to the profile when signed in', async () => {
    const { unmount } = renderApp();
    expect(screen.getByRole('link', { name: 'Login' })).toHaveAttribute('href', '/login');
    unmount();
    localStorage.setItem('appUser', JSON.stringify({ id: 'u1', username: 'pingala' }));
    const user = userEvent.setup();
    renderApp();
    await user.click(await screen.findByRole('button', { name: 'Profile' }));
    expect(screen.getByText('profile')).toBeInTheDocument();
  });

  it('goes back to the landing page from the home icon', async () => {
    const user = userEvent.setup();
    renderApp();
    await user.click(screen.getByTitle('Back to Landing Page'));
    expect(screen.getByText('landing')).toBeInTheDocument();
  });
});
