import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ExamplesView } from './ExamplesView';

const EXAMPLES = {
  success: true,
  examples: [
    { meter: 'गायत्री', lines: ['अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजं होतारं रत्नधातमं'], text: 'अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजं होतारं रत्नधातमं' },
  ],
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('ExamplesView', () => {
  it('labels a classical example as a verse and a daṇḍaka as a daṇḍaka', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => EXAMPLES }));
    const onSelectExample = vi.fn();
    render(<ExamplesView onSelectExample={onSelectExample} />);

    const gayatri = (await screen.findByText('गायत्री')).closest('div[class]')!.parentElement!;
    expect(within(gayatri).getByText('Analyze this verse')).toBeInTheDocument();
    expect(screen.getAllByText('Analyze this dandaka').length).toBeGreaterThan(0);

    await userEvent.click(within(gayatri).getByText('Analyze this verse'));
    expect(onSelectExample).toHaveBeenCalledWith(expect.stringContaining('अग्निमीळे'), undefined);
  });
});
