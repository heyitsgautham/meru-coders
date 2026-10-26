import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import LGLab from './LGLab';

function renderLab() {
  return render(
    <MemoryRouter initialEntries={['/lg-lab']}>
      <Routes>
        <Route path="/lg-lab" element={<LGLab />} />
        <Route path="/" element={<p>home</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('LGLab', () => {
  it('opens on the breath rhythm tab', () => {
    renderLab();
    expect(screen.getByRole('heading', { name: 'Human Breath Rhythm' })).toBeInTheDocument();
  });

  it.each([
    ['Music & Tāla', 'Music & Time-Keeping (Tāla System)'],
    ['Mathematics', 'Mathematics: Pingala & Fibonacci'],
    ['Nature Patterns', 'Nature Loves Binary Rhythms'],
    ['Cognition', 'Cognition & Memory'],
  ])('switches to the %s tab', async (tab, heading) => {
    const user = userEvent.setup();
    renderLab();
    await user.click(screen.getByRole('button', { name: tab }));
    expect(screen.getByRole('heading', { name: heading })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Human Breath Rhythm' })).not.toBeInTheDocument();
  });

  it('shows the oral tradition notes on the cognition tab', async () => {
    const user = userEvent.setup();
    renderLab();
    await user.click(screen.getByRole('button', { name: 'Cognition' }));
    expect(screen.getByText('Resistant to corruption over generations')).toBeInTheDocument();
  });

  it('always ends with the summary of six rhythms', () => {
    renderLab();
    for (const label of ['Human Breathing', 'Musical Timing', 'Fibonacci Math', 'Universal Rhythms']) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it('goes back home', async () => {
    const user = userEvent.setup();
    renderLab();
    await user.click(screen.getByRole('button', { name: /Back to Home/ }));
    expect(screen.getByText('home')).toBeInTheDocument();
  });
});
