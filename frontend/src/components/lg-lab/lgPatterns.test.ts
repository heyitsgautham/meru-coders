import { describe, expect, it } from 'vitest';
import { countPatterns, patternsOfMatras } from './lgPatterns';

const matras = (pattern: string) => [...pattern].reduce((sum, c) => sum + (c === 'G' ? 2 : 1), 0);

describe('L-G patterns by mātrā', () => {
  it('lists the worked example on the page: five patterns of four mātrās', () => {
    expect(patternsOfMatras(4)).toEqual(['LLLL', 'GLL', 'LGL', 'LLG', 'GG']);
  });

  it('has only L for one mātrā, since a guru weighs two', () => {
    expect(patternsOfMatras(1)).toEqual(['L']);
  });

  it('counts what it lists, each pattern once and at exactly n mātrās', () => {
    for (let n = 0; n <= 10; n++) {
      const patterns = patternsOfMatras(n);
      expect(patterns).toHaveLength(countPatterns(n));
      expect(new Set(patterns).size).toBe(patterns.length);
      expect(patterns.every((p) => matras(p) === n)).toBe(true);
    }
  });

  it('follows the Fibonacci recurrence from 1, 1', () => {
    expect(Array.from({ length: 11 }, (_, n) => countPatterns(n))).toEqual([1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]);
  });
});
