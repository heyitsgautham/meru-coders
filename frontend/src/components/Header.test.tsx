import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { Header } from './Header';
import { STORAGE_KEY_VIEW, useOpenAppView } from '../hooks/useOpenAppView';

vi.mock('../contexts/AuthContext', () => ({ useAuth: () => ({ user: { id: 'u1' }, isAdmin: false }) }));

function Where() {
  return <output data-testid="where">{useLocation().pathname}</output>;
}

// A standalone page as Profile, AdminPanel and the community pages render it.
function StandalonePage() {
  return <Header currentView={null} onViewChange={useOpenAppView()} />;
}

function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="*" element={<><StandalonePage /><Where /></>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('Header on pages outside the analyzer', () => {
  it('marks Profile, not Home, as the current page', () => {
    renderAt('/profile');
    expect(screen.getByRole('button', { name: 'Profile' })).toHaveClass('active');
    expect(screen.getByRole('button', { name: 'Home' })).not.toHaveClass('active');
  });

  it('opens the view that was clicked', async () => {
    localStorage.setItem(STORAGE_KEY_VIEW, 'home');
    renderAt('/profile');

    await userEvent.click(screen.getByRole('button', { name: 'Datasets' }));

    expect(localStorage.getItem(STORAGE_KEY_VIEW)).toBe('datasets');
    expect(screen.getByTestId('where')).toHaveTextContent('/app');
  });

  it('sends Community to its own page', async () => {
    renderAt('/admin');
    await userEvent.click(screen.getByRole('button', { name: 'Community' }));
    expect(screen.getByTestId('where')).toHaveTextContent('/community');
  });
});
