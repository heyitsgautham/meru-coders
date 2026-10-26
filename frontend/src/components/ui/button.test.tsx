import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { render, screen } from '@testing-library/react';
import { Button } from './button';

// The Tailwind classes these components carry are not compiled into index.css,
// so styles/ui-components.css styles them by these attributes instead.
const css = readFileSync('src/styles/ui-components.css', 'utf8');

describe('Button', () => {
  it('names its variant and size for the stylesheet', () => {
    render(<Button variant="destructive" size="lg">Stop</Button>);
    const button = screen.getByRole('button', { name: 'Stop' });
    expect(button).toHaveAttribute('data-slot', 'button');
    expect(button).toHaveAttribute('data-variant', 'destructive');
    expect(button).toHaveAttribute('data-size', 'lg');
  });

  it('falls back to the default variant and size', () => {
    render(<Button>Go</Button>);
    expect(screen.getByRole('button', { name: 'Go' })).toHaveAttribute('data-variant', 'default');
  });

  it.each(['default', 'destructive', 'outline', 'secondary', 'ghost', 'link'])('has a rule for the %s variant', variant => {
    expect(css).toContain(`[data-variant="${variant}"]`);
  });

  it('places the alert dialog over the page', () => {
    expect(css).toMatch(/:where\(\[data-slot="alert-dialog-content"\]\) \{[^}]*position: fixed;[^}]*top: 50%;/);
  });
});
