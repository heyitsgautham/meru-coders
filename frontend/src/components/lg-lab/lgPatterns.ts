// Pingala's count of metres by mātrā: a laghu (L) weighs one mātrā and a guru (G) two.

/** Every L-G sequence whose mātrās add up to exactly n: those of n-1 with an L added, then those of n-2 with a G. */
export function patternsOfMatras(n: number): string[] {
  if (n < 0) return [];
  if (n === 0) return [''];
  return [...patternsOfMatras(n - 1).map((p) => p + 'L'), ...patternsOfMatras(n - 2).map((p) => p + 'G')];
}

/** How many such sequences there are: 1, 1, 2, 3, 5, 8, ... for n = 0, 1, 2, ..., so C(n) = C(n-1) + C(n-2). */
export function countPatterns(n: number): number {
  let [current, next] = [1, 1];
  for (let i = 0; i < n; i++) {
    [current, next] = [next, current + next];
  }
  return current;
}
