import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { LandingPage } from './LandingPage';
import { FEATURES, METER_CATEGORIES, TRUSTED_SOURCES } from './landing/landingContent';

function renderAt(path = '/') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/app" element={<p>analyser</p>} />
        <Route path="/lg-lab" element={<p>lg lab</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('LandingPage', () => {
  it.each(['Get Started', 'Launch Application Launch'])('opens the analyser from "%s"', async (name) => {
    const user = userEvent.setup();
    renderAt();
    await user.click(screen.getByRole('button', { name }));
    expect(screen.getByText('analyser')).toBeInTheDocument();
  });

  it('opens the analyser from the closing call to action', async () => {
    const user = userEvent.setup();
    const { container } = renderAt();
    await user.click(container.querySelector('.landing-cta-btn') as HTMLElement);
    expect(screen.getByText('analyser')).toBeInTheDocument();
  });

  it('opens the L-G Laboratory', async () => {
    const user = userEvent.setup();
    renderAt();
    await user.click(screen.getByRole('button', { name: 'Explore L-G Lab' }));
    expect(screen.getByText('lg lab')).toBeInTheDocument();
  });

  it('links Learn More to the What is Chandas section', () => {
    const { container } = renderAt();
    expect(screen.getByRole('link', { name: 'Learn More' })).toHaveAttribute('href', '#what-is-chandas');
    expect(container.querySelector('#what-is-chandas')).toHaveTextContent('What is Chandas?');
  });

  it('shows every feature, meter category and source', () => {
    renderAt();
    for (const feature of FEATURES) expect(screen.getByText(feature.title)).toBeInTheDocument();
    for (const category of METER_CATEGORIES) {
      expect(screen.getByText(category.name)).toBeInTheDocument();
      expect(screen.getByText(String(category.count))).toBeInTheDocument();
    }
    for (const source of TRUSTED_SOURCES) expect(screen.getByRole('img', { name: source.title })).toBeInTheDocument();
  });

  it('darkens a launch button while hovered and restores it after', () => {
    renderAt();
    const button = screen.getByRole('button', { name: 'Get Started' });
    fireEvent.mouseOver(button);
    expect(button.style.backgroundColor).toBe('rgb(179, 77, 18)');
    fireEvent.mouseOut(button);
    expect(button.style.backgroundColor).toBe('rgb(199, 91, 26)');
  });

  it('lifts a source card while hovered', () => {
    renderAt();
    const card = screen.getByRole('img', { name: 'Rig Veda' }).closest('div')?.parentElement as HTMLElement;
    fireEvent.mouseOver(card);
    expect(card.style.transform).toBe('translateY(-4px)');
    fireEvent.mouseOut(card);
    expect(card.style.transform).toBe('translateY(0)');
  });

  it('paints the L-G Laboratory call-out with its peach gradient', () => {
    renderAt();
    expect(screen.getByTestId('lg-lab-highlight').style.background).toContain('linear-gradient');
  });
});
