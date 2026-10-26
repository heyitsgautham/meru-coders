import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import CombinatoricsCalculator from './CombinatoricsCalculator';
import FibonacciVisualizer from './FibonacciVisualizer';

describe('CombinatoricsCalculator', () => {
  it('agrees with its own table for every length', () => {
    render(<CombinatoricsCalculator />);
    const slider = screen.getByRole('slider');
    for (const [n, expected] of [[1, '1'], [4, '5'], [5, '8'], [10, '89']] as const) {
      fireEvent.change(slider, { target: { value: String(n) } });
      expect(screen.getByText('Total Combinations').nextSibling).toHaveTextContent(expected);
      expect(screen.getByText(`Fibonacci F(${n})`).nextSibling).toHaveTextContent(expected);
      expect(screen.getByText(/Confirmed!/)).toBeInTheDocument();
    }
    expect(screen.getByText('with F(0) = 1, F(1) = 1')).toBeInTheDocument();
  });
});

describe('FibonacciVisualizer', () => {
  it('offers only L at one mātrā', () => {
    render(<FibonacciVisualizer />);
    fireEvent.change(screen.getByRole('slider'), { target: { value: '1' } });
    expect(screen.getByText('All possible L-G patterns (1 total):')).toBeInTheDocument();
  });

  it('charts 1, 2, 3, 5, 8 patterns for one to five mātrās', () => {
    const { container } = render(<FibonacciVisualizer />);
    const bars = [...container.querySelectorAll('[data-testid="fib-bar"]')].map((bar) => bar.textContent);
    expect(bars).toEqual(['1', '2', '3', '5', '8', '13', '21', '34']);
  });
});
