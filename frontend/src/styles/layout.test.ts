import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';

const read = (path: string) => readFileSync(path, 'utf8');
const px = (css: string, selector: string, property: string, from = 0) => {
  const block = css.slice(css.indexOf(`${selector} {`, from)).split('}')[0];
  return Number(block.match(new RegExp(`\\b${property}:\\s*(\\d+)px`))?.[1]);
};

describe('fixed corner widgets', () => {
  it('keeps the Pingala popup above the chat button at every width', () => {
    const chat = read('src/components/chat/FloatingChatbot.css');
    const pingala = read('src/styles/pingala-speaker.css');
    const fabTop = px(chat, '.chatbot-fab', 'bottom') + px(chat, '.chatbot-fab', 'height');
    const phoneRules = pingala.indexOf('@media (max-width: 768px)');

    expect(px(pingala, '.pingala-speaker-container', 'bottom')).toBeGreaterThan(fabTop);
    expect(px(pingala, '.pingala-speaker-container', 'bottom', phoneRules)).toBeGreaterThan(fabTop);
  });
});

describe('results header on tablets and phones', () => {
  it('stretches only the download link, not the round close button', () => {
    const css = read('src/index.css');
    expect(css).not.toMatch(/\.results-header button[^{]*\{[^}]*width: 100%/);
    expect(css).toMatch(/\.results-header a \{[^}]*flex: 1/);
  });
});

describe('phone layouts', () => {
  it('lets the community search shrink instead of running off a 375px screen', () => {
    const css = read('src/styles/community.css');
    const phone = css.slice(css.lastIndexOf('@media (max-width: 640px)'));
    expect(phone).toMatch(/\.search-bar-container \{[^}]*width: auto;[^}]*min-width: 0;/);
  });

  it('keeps the profile avatar round when the greeting wraps', () => {
    expect(read('src/styles/profile-admin.css')).toMatch(/\.avatar-circle \{\s*flex-shrink: 0;/);
  });
});

describe('identification modes on phones', () => {
  it('sit two by two with whole-word labels', () => {
    const css = read('src/index.css');
    const phone = css.slice(css.lastIndexOf('@media (max-width: 480px)'));
    expect(phone).toMatch(/\.mode-choice-grid \{[^}]*grid-template-columns: repeat\(2, minmax\(0, 1fr\)\);/);
    expect(phone).toMatch(/\.mode-choice-grid > button \{[^}]*overflow-wrap: normal;/);
  });
});
