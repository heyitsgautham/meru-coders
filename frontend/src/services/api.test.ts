import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as api from './api';

const BASE = 'http://localhost:5000/api';

function respond(body: unknown, status = 200) {
  return vi.fn().mockResolvedValue({ ok: status < 400, status, json: async () => body });
}

function lastCall(fetchMock: ReturnType<typeof vi.fn>) {
  const [url, init] = fetchMock.mock.calls.at(-1) as [string, RequestInit];
  return { url, init };
}

beforeEach(() => {
  vi.spyOn(console, 'log').mockImplementation(() => {});
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('API base URL', () => {
  it('points at port 5000 on localhost', () => {
    expect(api.getAPIURL()).toBe(BASE);
    expect(api.getDownloadURL('r.json')).toBe(`${BASE}/download/r.json`);
    expect(api.getTTSAudioURL('a.mp3')).toBe(`${BASE}/tts/audio/a.mp3`);
  });

  it('prefers the runtime config a deployment writes into config.js', async () => {
    vi.resetModules();
    (window as typeof window & { CONFIG?: { API_URL?: string } }).CONFIG = { API_URL: 'https://api.example.org/api' };
    const fresh = await import('./api');
    expect(fresh.getAPIURL()).toBe('https://api.example.org/api');
    delete (window as typeof window & { CONFIG?: unknown }).CONFIG;
  });
});

describe('identifyFromText', () => {
  it('posts the text with its modes as JSON', async () => {
    const fetchMock = respond({ success: true });
    vi.stubGlobal('fetch', fetchMock);

    await api.identifyFromText('धर्म', 'verse', '', 'vedic');

    const { url, init } = lastCall(fetchMock);
    expect(url).toBe(`${BASE}/identify/text`);
    expect(JSON.parse(init.body as string)).toEqual({
      text: 'धर्म',
      text_mode: 'verse',
      output_scheme: null,
      identification_mode: 'vedic',
      enable_sandhi: false,
    });
  });

  it('sends the saved login token', async () => {
    localStorage.setItem('authToken', 'tok');
    const fetchMock = respond({ success: true });
    vi.stubGlobal('fetch', fetchMock);
    await api.identifyFromText('धर्म');
    expect((lastCall(fetchMock).init.headers as Record<string, string>).Authorization).toBe('Bearer tok');
  });

  it('throws the server error', async () => {
    vi.stubGlobal('fetch', respond({ error: "'text' must be a string" }, 400));
    await expect(api.identifyFromText('x')).rejects.toThrow("'text' must be a string");
  });
});

describe('uploads use the field names the backend reads', () => {
  it.each([
    ['extractTextFromImage', () => api.extractTextFromImage(new File(['x'], 'a.png')), '/ocr/extract', 'image_file'],
    ['extractTextFromFile', () => api.extractTextFromFile(new File(['x'], 'a.txt')), '/file/extract', 'file'],
    ['extractTextFromAudio', () => api.extractTextFromAudio(new File(['x'], 'a.wav')), '/audio/transcribe', 'audio_file'],
    ['identifyFromImage', () => api.identifyFromImage(new File(['x'], 'a.png')), '/identify/image', 'image_file'],
    ['identifyFromFile', () => api.identifyFromFile(new File(['x'], 'a.txt'), 'verse'), '/identify/file', 'text_file'],
  ])('%s', async (_name, call, path, field) => {
    const fetchMock = respond({ success: true });
    vi.stubGlobal('fetch', fetchMock);
    await call();
    const { url, init } = lastCall(fetchMock);
    expect(url).toBe(`${BASE}${path}`);
    expect((init.body as FormData).get(field)).toBeInstanceOf(File);
  });
});

describe('datasets and verse search', () => {
  it('builds the dataset query', async () => {
    const fetchMock = respond({ success: true });
    vi.stubGlobal('fetch', fetchMock);
    await api.getDataset('rigveda', { limit: 20, offset: 40, chandas: 'gāyatrī' });
    expect(lastCall(fetchMock).url).toBe(`${BASE}/datasets/rigveda?limit=20&offset=40&chandas=g%C4%81yatr%C4%AB`);
  });

  it('fills search defaults', async () => {
    const fetchMock = respond({ success: true });
    vi.stubGlobal('fetch', fetchMock);
    await api.searchSloka('धर्म');
    expect(JSON.parse(lastCall(fetchMock).init.body as string)).toEqual({ text: 'धर्म', threshold: 0.7, limit: 10 });
  });

  it('lists approved contributions of one type', async () => {
    const fetchMock = respond({ success: true, contributions: [], count: 0 });
    vi.stubGlobal('fetch', fetchMock);
    await api.getApprovedContributions({ type: 'verse', limit: 5 });
    expect(lastCall(fetchMock).url).toBe(`${BASE}/contributions/approved?limit=5&type=verse`);
  });
});

describe('generateTTS', () => {
  it('turns the relative audio path into a full URL on the API host', async () => {
    vi.stubGlobal('fetch', respond({ success: true, audio_url: '/api/tts/audio/x.mp3' }));
    const result = await api.generateTTS('ॐ', 'female');
    expect(result.audio_url).toBe('http://localhost:5000/api/tts/audio/x.mp3');
  });

  it('leaves a failed response alone', async () => {
    vi.stubGlobal('fetch', respond({ success: false, error: 'TTS off' }));
    expect(await api.generateTTS('ॐ')).toEqual({ success: false, error: 'TTS off' });
  });
});

it('offers the transliteration schemes the backend supports when it is unreachable', () => {
  expect(api.getDefaultSchemes().map((s) => s.value)).toEqual(['', 'devanagari', 'iast', 'itrans', 'velthuis', 'slp1', 'wx']);
});
