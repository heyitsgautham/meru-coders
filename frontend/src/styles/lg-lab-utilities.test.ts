import { describe, expect, it } from 'vitest';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';

describe('lg-lab-utilities.css', () => {
  it('is what scripts/lg-lab-utilities.mjs generates from the current L-G Lab sources', () => {
    // Exits non-zero, and so throws, when a class was added or removed without regenerating.
    expect(() => execFileSync('node', ['scripts/lg-lab-utilities.mjs', '--check'], { stdio: 'pipe' })).not.toThrow();
  });

  it('scopes every class rule to the L-G Lab page', () => {
    const css = readFileSync('src/styles/lg-lab-utilities.css', 'utf8');
    const rules = css.split('\n').filter((line) => /^\s*[.:].*\{$/.test(line));
    expect(rules.length).toBeGreaterThan(100);
    expect(rules.filter((rule) => !rule.trim().startsWith(':where(.lg-lab-page)'))).toEqual([]);
  });
});
