import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SlokaChecker } from './SlokaChecker';
// Real /sloka/validate and /sloka/search responses from the Flask test client.
import fixtures from '../test/fixtures/sloka-check.json';

const RIK = 'अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजं होतारं रत्नधातमं';

function routes(byPath: Record<string, unknown>) {
  return vi.fn(async (url: string, init: RequestInit) => ({
    ok: true,
    status: 200,
    json: async () => byPath[new URL(url).pathname.replace('/api', '')],
    init,
  }));
}

const box = () => screen.getByPlaceholderText(/पेस्ट करें/);

beforeEach(() => {
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('SlokaChecker', () => {
  it('confirms an exact verse without searching further', async () => {
    const fetchMock = routes({ '/sloka/validate': fixtures.validate });
    vi.stubGlobal('fetch', fetchMock);
    render(<SlokaChecker />);

    await userEvent.type(box(), `  ${RIK} `);
    await userEvent.click(screen.getByRole('button', { name: 'Check Sloka' }));

    expect(await screen.findByText('100%')).toBeInTheDocument();
    expect(screen.getByText('Perfect!')).toBeInTheDocument();
    expect(screen.getByText('gāyatrī')).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledOnce();
    expect(JSON.parse(fetchMock.mock.calls[0][1].body as string)).toEqual({ text: RIK });
  });

  it('lists the differences in a misspelt verse', async () => {
    vi.stubGlobal('fetch', routes({ '/sloka/validate': fixtures.validate_typo }));
    render(<SlokaChecker />);

    await userEvent.type(box(), 'अग्निमीले पुरोहितम् यज्ञस्य देवमृत्विजं होतारं रत्नधातमं');
    await userEvent.keyboard('{Control>}{Enter}{/Control}');

    expect(await screen.findByText('2 Differences Found')).toBeInTheDocument();
    expect(screen.getByText('Your Input')).toBeInTheDocument();
    expect(screen.getByText('Correct Version')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Show Diff' }));
    expect(screen.getByRole('button', { name: 'Hide Diff' })).toBeInTheDocument();
  });

  it('copies the correct text', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal('fetch', routes({ '/sloka/validate': fixtures.validate }));
    render(<SlokaChecker />);
    await userEvent.type(box(), RIK);
    await userEvent.click(screen.getByRole('button', { name: 'Check Sloka' }));
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true });

    await userEvent.click(await screen.findByRole('button', { name: 'Copy' }));

    expect(writeText).toHaveBeenCalledWith(RIK);
    expect(screen.getByRole('button', { name: 'Copied!' })).toBeInTheDocument();
  });

  it('suggests close verses when nothing matches and loads the one picked', async () => {
    const fetchMock = routes({
      '/sloka/validate': { success: true, found: false, message: 'No matching sloka found' },
      '/sloka/search': fixtures.search,
    });
    vi.stubGlobal('fetch', fetchMock);
    render(<SlokaChecker />);

    await userEvent.type(box(), 'अग्निमीळे पुरोहितं');
    await userEvent.click(screen.getByRole('button', { name: 'Check Sloka' }));

    expect(await screen.findByText('Sloka Not Found')).toBeInTheDocument();
    expect(screen.getByText('No matching sloka found')).toBeInTheDocument();
    expect(JSON.parse(fetchMock.mock.calls[1][1].body as string)).toMatchObject({ threshold: 0.5, limit: 5 });

    await userEvent.click(screen.getByText('95%').closest('.suggestion-item')!);
    expect(box()).toHaveValue(fixtures.search.matches[1].original_text);
  });

  it('shows the server error and clears back to an empty box', async () => {
    vi.stubGlobal('fetch', routes({ '/sloka/validate': { success: false, error: 'Text is required' } }));
    render(<SlokaChecker />);
    await userEvent.type(box(), 'x');
    await userEvent.click(screen.getByRole('button', { name: 'Check Sloka' }));
    expect(await screen.findByText('Text is required')).toBeInTheDocument();

    await userEvent.click(screen.getByTitle('Clear'));

    expect(box()).toHaveValue('');
    expect(screen.queryByText('Text is required')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Check Sloka' })).toBeDisabled();
  });
});
