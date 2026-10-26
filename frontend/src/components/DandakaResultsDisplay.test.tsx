import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { render, screen } from '@testing-library/react';
import { DandakaResultsDisplay } from './DandakaResultsDisplay';
import type { DandakaModeResult } from '../types/api';
// A real /identify/dandaka response from the Flask test client (Gita 1.1).
import recorded from '../test/fixtures/identify-dandaka.json';

const gita = recorded.result as unknown as DandakaModeResult;

describe('DandakaResultsDisplay', () => {
  it('shows the overall class with its range, the totals and every unit', () => {
    render(<DandakaResultsDisplay result={gita} />);

    const banner = screen.getByRole('heading', { name: 'Saṃkīrṇa-daṇḍakam' }).parentElement!;
    expect(banner).toHaveClass('dandaka-banner', 'dandaka-tone-blue');
    expect(banner).toHaveTextContent('≤26 akṣaras per unit');
    expect(screen.getByText('Total Akṣaras').nextSibling).toHaveTextContent('32');
    expect(screen.getByText('Density', { selector: 'p' }).nextSibling).toHaveTextContent('31.2%');
    expect(screen.getAllByRole('row')).toHaveLength(3);
  });

  it('describes a Rājaśyāmalā stotram without a metre', () => {
    render(
      <DandakaResultsDisplay
        result={{
          mode: 'dandaka',
          text_type: 'rajashyamala-stotram',
          rajashyamala: {
            is_rajashyamala: true,
            confidence: 0.82,
            title_match: true,
            structure_type: 'invocation-list',
            matched_keywords: ['śyāmalā'],
            semantic_markers: ['mātaṅgī'],
          },
        } as DandakaModeResult}
      />,
    );

    expect(screen.getByText('Rājaśyāmalā Stotram Identified')).toBeInTheDocument();
    expect(screen.getByText('82%')).toBeInTheDocument();
    expect(screen.getByText('INVOCATION LIST')).toBeInTheDocument();
    expect(screen.queryByText('Final classification')).not.toBeInTheDocument();
  });

  it('is styled by rules the stylesheet defines', () => {
    const css = readFileSync('src/styles/dandaka.css', 'utf8');
    for (const name of ['dandaka-banner', 'dandaka-stat__value', 'dandaka-table', 'dandaka-badge', 'dandaka-tone-blue']) {
      expect(css).toContain(`.${name} {`);
    }
  });
});
