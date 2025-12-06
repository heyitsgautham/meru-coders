import { describe, it, expect } from 'vitest';
import { buildContributionPayload } from './ContributionForm';

describe('buildContributionPayload', () => {
  it('maps verse contributions to contribution_type verse', () => {
    const payload = buildContributionPayload('verse', { verse_text: 'x', meter: 'm' });
    expect(payload.contribution_type).toBe('verse');
    expect(payload.data).toEqual({ verse_text: 'x', meter: 'm' });
  });

  it('maps meter contributions to contribution_type meter_definition', () => {
    const payload = buildContributionPayload('meter', { meter_name: 'Anushtubh' });
    expect(payload.contribution_type).toBe('meter_definition');
    expect(payload.data).toEqual({ meter_name: 'Anushtubh' });
  });
});
