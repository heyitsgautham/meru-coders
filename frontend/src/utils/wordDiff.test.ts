import { describe, expect, it } from 'vitest';
import { computeWordDiff } from './wordDiff';

const join = (segments: { text: string }[]) => segments.map((s) => s.text).join('');

describe('computeWordDiff', () => {
  it('reports no edits for identical verses', () => {
    const verse = 'अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजं';
    const diff = computeWordDiff(verse, verse);
    expect(diff.deletions).toBe(0);
    expect(diff.insertions).toBe(0);
    expect(diff.userSegments.every((s) => s.type === 'equal')).toBe(true);
  });

  it('marks a misspelt word as a deletion on the user side and an insertion on the reference side', () => {
    const diff = computeWordDiff('अग्निमीळे पुरोहितम यज्ञस्य', 'अग्निमीळे पुरोहितं यज्ञस्य');
    expect(diff.deletions).toBeGreaterThan(0);
    expect(diff.insertions).toBeGreaterThan(0);
    expect(diff.userSegments.filter((s) => s.type === 'delete').map((s) => s.text.trim())).toContain('पुरोहितम');
    expect(diff.correctSegments.filter((s) => s.type === 'insert').map((s) => s.text.trim())).toContain('पुरोहितं');
  });

  it('keeps every character of both texts in the segments', () => {
    const user = 'राम सीता';
    const correct = 'राम लक्ष्मण सीता';
    const diff = computeWordDiff(user, correct);
    expect(join(diff.userSegments).replace(/\s+/g, ' ').trim()).toBe(user);
    expect(join(diff.correctSegments).replace(/\s+/g, ' ').trim()).toBe(correct);
  });
});
