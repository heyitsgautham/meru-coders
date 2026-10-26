import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TextToSpeech } from './TextToSpeech';

const VERSE = 'धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः';
const AUDIO = 'http://localhost:5000/api/tts/audio/a1.mp3';

function respond(body: unknown, status = 200) {
  return vi.fn().mockResolvedValue({ ok: status < 400, status, json: async () => body });
}

beforeEach(() => {
  for (const method of ['log', 'error'] as const) vi.spyOn(console, method).mockImplementation(() => {});
  vi.spyOn(HTMLMediaElement.prototype, 'load').mockImplementation(() => {});
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('TextToSpeech', () => {
  it('cannot generate speech for empty text', () => {
    render(<TextToSpeech text="   " />);
    expect(screen.getByRole('button', { name: 'Generate Speech' })).toBeDisabled();
  });

  it('asks the server for a male voice and shows the player', async () => {
    const fetchMock = respond({ success: true, audio_url: '/api/tts/audio/a1.mp3' });
    vi.stubGlobal('fetch', fetchMock);
    const { container } = render(<TextToSpeech text={VERSE} label="Listen" />);

    await userEvent.click(screen.getByRole('button', { name: 'Generate Speech' }));

    expect(await screen.findByRole('button', { name: 'Regenerate' })).toBeEnabled();
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ text: VERSE, voice: 'male' });
    expect(container.querySelector('audio')).toHaveAttribute('src', AUDIO);
  });

  it('toggles play and pause with the audio element', async () => {
    vi.stubGlobal('fetch', respond({ success: true, audio_url: '/api/tts/audio/a1.mp3' }));
    const play = vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue();
    const pause = vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => {});
    const { container } = render(<TextToSpeech text={VERSE} />);
    await userEvent.click(screen.getByRole('button', { name: 'Generate Speech' }));

    await userEvent.click(await screen.findByRole('button', { name: 'Play' }));
    expect(play).toHaveBeenCalledOnce();

    fireEvent.play(container.querySelector('audio')!);
    await userEvent.click(screen.getByRole('button', { name: 'Pause' }));
    expect(pause).toHaveBeenCalledOnce();

    fireEvent.ended(container.querySelector('audio')!);
    expect(screen.getByRole('button', { name: 'Play' })).toBeInTheDocument();
  });

  it('downloads the file with the download flag', async () => {
    vi.stubGlobal('fetch', respond({ success: true, audio_url: '/api/tts/audio/a1.mp3' }));
    const clicks: string[] = [];
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) {
      clicks.push(this.href);
    });
    render(<TextToSpeech text={VERSE} />);
    await userEvent.click(screen.getByRole('button', { name: 'Generate Speech' }));

    await userEvent.click(await screen.findByRole('button', { name: 'Download' }));

    expect(clicks).toEqual([`${AUDIO}?download=true`]);
  });

  it('shows the server error', async () => {
    vi.stubGlobal('fetch', respond({ success: false, error: 'TTS engine unavailable' }));
    render(<TextToSpeech text={VERSE} />);
    await userEvent.click(screen.getByRole('button', { name: 'Generate Speech' }));
    expect(await screen.findByText(/TTS engine unavailable/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Generate Speech' })).toBeEnabled();
  });

  it('drops the old audio when the text changes', async () => {
    vi.stubGlobal('fetch', respond({ success: true, audio_url: '/api/tts/audio/a1.mp3' }));
    const { container, rerender } = render(<TextToSpeech text={VERSE} />);
    await userEvent.click(screen.getByRole('button', { name: 'Generate Speech' }));
    await screen.findByRole('button', { name: 'Regenerate' });

    rerender(<TextToSpeech text="रामो राजमणिः" />);

    expect(container.querySelector('audio')).toBeNull();
    expect(screen.getByRole('button', { name: 'Generate Speech' })).toBeEnabled();
  });
});
