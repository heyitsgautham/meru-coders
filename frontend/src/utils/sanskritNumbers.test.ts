import { describe, expect, it } from 'vitest';
import { formatGanaForSpeech, generatePingalaScript, numberToSanskrit } from './sanskritNumbers';

describe('numberToSanskrit', () => {
  it.each([
    [8, 'अष्ट'],
    [11, 'एकादश'],
    [32, 'द्वात्रिंशत्'],
    [44, 'चतुश्चत्वारिंशत्'],
    [100, 'शतम्'],
  ])('%i is %s', (num, word) => {
    expect(numberToSanskrit(num)).toBe(word);
  });

  it('falls back to digits for numbers it does not name', () => {
    expect(numberToSanskrit(23)).toBe('23');
  });
});

describe('formatGanaForSpeech', () => {
  it('spells the gana letters in Devanagari with pauses', () => {
    expect(formatGanaForSpeech('ttj')).toBe('त-त-ज');
    expect(formatGanaForSpeech('RJS')).toBe('र-ज-स');
    expect(formatGanaForSpeech('')).toBe('');
  });
});

it('Pingala names the meter he found', () => {
  expect(generatePingalaScript('अनुष्टुभ्')).toBe('नमस्ते। अहं पिङ्गलाचार्यः। अयं छन्दः अनुष्टुभ् अस्ति।');
});
