import { describe, expect, it } from 'vitest';
import type { IdentifyResponse } from '../../types/api';
import { ACTIVE_TAB_STORAGE_KEY, MODE_INFO, foundMeter, readSavedTab } from './analysisModes';

const storageWith = (value: string | null) => ({ getItem: (key: string) => (key === ACTIVE_TAB_STORAGE_KEY ? value : null) });

describe('readSavedTab', () => {
  it.each(['text', 'image', 'file', 'voice'])('restores the saved %s tab', (tab) => {
    expect(readSavedTab(storageWith(tab))).toBe(tab);
  });

  it('falls back to the text tab when nothing is saved', () => {
    expect(readSavedTab(storageWith(null))).toBe('text');
  });

  it('falls back to the text tab for a value from an older version', () => {
    expect(readSavedTab(storageWith('pdf'))).toBe('text');
  });
});

describe('foundMeter', () => {
  const withFound = (found: boolean, success = true) =>
    ({ success, result: { line: [{ result: { found } }] } }) as unknown as IdentifyResponse;

  it('is true when the first line found a meter', () => {
    expect(foundMeter(withFound(true))).toBe(true);
  });

  it('is false when the first line found nothing', () => {
    expect(foundMeter(withFound(false))).toBe(false);
  });

  it('is false for an unsuccessful or missing response', () => {
    expect(foundMeter(withFound(true, false))).toBe(false);
    expect(foundMeter(null)).toBe(false);
    expect(foundMeter({ success: true } as IdentifyResponse)).toBe(false);
  });
});

describe('MODE_INFO', () => {
  it('lists the four identification modes in display order', () => {
    expect(Object.keys(MODE_INFO)).toEqual(['auto', 'vedic', 'classical', 'dandaka']);
  });
});
