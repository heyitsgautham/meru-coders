/**
 * Word-level diff between a user's verse and the reference text, used by SlokaChecker.
 */

/* ============================================================================
   Diff Types and Utilities
   ============================================================================ */

export interface DiffSegment {
  text: string;
  type: 'equal' | 'insert' | 'delete';
}

export interface DiffResult {
  userSegments: DiffSegment[];    // For showing user's input with deletions highlighted
  correctSegments: DiffSegment[]; // For showing correct text with additions highlighted
  deletions: number;
  insertions: number;
}

// Word-based diff using Longest Common Subsequence (LCS) algorithm
export function computeWordDiff(userText: string, correctText: string): DiffResult {
  // Tokenize into words while preserving spaces and punctuation
  const tokenize = (text: string): string[] => {
    const tokens: string[] = [];
    let current = '';
    for (const char of text) {
      if (char === ' ' || char === '\n' || char === '\t') {
        if (current) {
          tokens.push(current);
          current = '';
        }
        tokens.push(char);
      } else {
        current += char;
      }
    }
    if (current) tokens.push(current);
    return tokens;
  };

  const userTokens = tokenize(userText);
  const correctTokens = tokenize(correctText);

  // Build LCS table
  const m = userTokens.length;
  const n = correctTokens.length;
  const dp: number[][] = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (userTokens[i - 1] === correctTokens[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }

  // Backtrack to find the diff
  let deletions = 0;
  let insertions = 0;

  let i = m, j = n;
  const userResult: DiffSegment[] = [];
  const correctResult: DiffSegment[] = [];

  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && userTokens[i - 1] === correctTokens[j - 1]) {
      userResult.unshift({ text: userTokens[i - 1], type: 'equal' });
      correctResult.unshift({ text: correctTokens[j - 1], type: 'equal' });
      i--;
      j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      correctResult.unshift({ text: correctTokens[j - 1], type: 'insert' });
      if (correctTokens[j - 1].trim()) insertions++;
      j--;
    } else {
      userResult.unshift({ text: userTokens[i - 1], type: 'delete' });
      if (userTokens[i - 1].trim()) deletions++;
      i--;
    }
  }

  // Merge consecutive segments of the same type
  const mergeSegments = (segments: DiffSegment[]): DiffSegment[] => {
    const merged: DiffSegment[] = [];
    for (const seg of segments) {
      if (merged.length > 0 && merged[merged.length - 1].type === seg.type) {
        merged[merged.length - 1].text += seg.text;
      } else {
        merged.push({ ...seg });
      }
    }
    return merged;
  };

  return {
    userSegments: mergeSegments(userResult),
    correctSegments: mergeSegments(correctResult),
    deletions,
    insertions
  };
}

