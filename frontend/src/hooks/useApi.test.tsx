import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import * as api from '../services/api';
import {
  useAPIInfo,
  useExamples,
  useExtractAudio,
  useExtractFile,
  useExtractText,
  useIdentifyText,
  useSchemes,
  useTTS,
} from './useApi';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    getSchemes: vi.fn(),
    getExamples: vi.fn(),
    getAPIInfo: vi.fn(),
    identifyFromText: vi.fn(),
    extractTextFromImage: vi.fn(),
    extractTextFromAudio: vi.fn(),
    extractTextFromFile: vi.fn(),
    generateTTS: vi.fn(),
  };
});

const mocked = vi.mocked(api);

beforeEach(() => {
  vi.resetAllMocks();
  for (const method of ['log', 'warn', 'error'] as const) vi.spyOn(console, method).mockImplementation(() => {});
});

afterEach(() => vi.restoreAllMocks());

describe('useSchemes', () => {
  it('starts with the built-in list and replaces it with the server list', async () => {
    mocked.getSchemes.mockResolvedValue({ success: true, schemes: [{ value: 'iast', label: 'IAST' }] } as never);
    const { result } = renderHook(() => useSchemes());
    expect(result.current.schemes).toEqual(api.getDefaultSchemes());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.schemes).toEqual([{ value: 'iast', label: 'IAST' }]);
  });

  it('keeps the built-in list when the server is down', async () => {
    mocked.getSchemes.mockRejectedValue(new Error('offline'));
    const { result } = renderHook(() => useSchemes());
    await waitFor(() => expect(result.current.error).toBe('offline'));
    expect(result.current.schemes).toEqual(api.getDefaultSchemes());
  });
});

describe('useExamples', () => {
  it('loads once', async () => {
    mocked.getExamples.mockResolvedValue({ success: true, examples: [{ meter: 'गायत्री', text: 'x' }] } as never);
    const { result } = renderHook(() => useExamples());
    await act(() => result.current.loadExamples());
    await act(() => result.current.loadExamples());
    expect(result.current.examples).toHaveLength(1);
    expect(mocked.getExamples).toHaveBeenCalledTimes(1);
  });

  it('reports an unsuccessful answer', async () => {
    mocked.getExamples.mockResolvedValue({ success: false } as never);
    const { result } = renderHook(() => useExamples());
    await act(() => result.current.loadExamples());
    expect(result.current.error).toBe('No examples available');
  });
});

describe('useAPIInfo', () => {
  it('records the OCR engines the server offers', async () => {
    mocked.getAPIInfo.mockResolvedValue({ ocr_available: { tesseract: false, cloud_vision: true } } as never);
    const { result } = renderHook(() => useAPIInfo());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.connected).toBe(true);
    expect(result.current.ocrAvailable).toEqual({ tesseract: false, cloud_vision: true });
  });

  it('marks the backend as disconnected when it does not answer', async () => {
    mocked.getAPIInfo.mockRejectedValue(new Error('offline'));
    const { result } = renderHook(() => useAPIInfo());
    await waitFor(() => expect(result.current.connected).toBe(false));
  });
});

describe('useIdentifyText', () => {
  it('stores the result and passes every argument through', async () => {
    mocked.identifyFromText.mockResolvedValue({ success: true } as never);
    const { result } = renderHook(() => useIdentifyText());
    await act(() => result.current.identify('धर्म', 'verse', '', 'vedic'));
    expect(mocked.identifyFromText).toHaveBeenCalledWith('धर्म', 'verse', '', 'vedic');
    expect(result.current.result).toEqual({ success: true });
  });

  it('keeps the error and rethrows it', async () => {
    mocked.identifyFromText.mockRejectedValue(new Error('Rate limit exceeded'));
    const { result } = renderHook(() => useIdentifyText());
    await act(async () => {
      await expect(result.current.identify('x')).rejects.toThrow('Rate limit exceeded');
    });
    expect(result.current.error).toBe('Rate limit exceeded');
    act(() => result.current.reset());
    expect(result.current.error).toBeNull();
  });
});

describe('extraction hooks', () => {
  it('useExtractText returns the OCR text', async () => {
    mocked.extractTextFromImage.mockResolvedValue({ success: true, text: 'धर्म' } as never);
    const { result } = renderHook(() => useExtractText());
    await act(async () => {
      expect(await result.current.extract(new File(['x'], 'a.png'))).toBe('धर्म');
    });
    expect(result.current.text).toBe('धर्म');
  });

  it('useExtractAudio turns an unsuccessful answer into an error', async () => {
    mocked.extractTextFromAudio.mockResolvedValue({ success: false, error: 'ASR offline' } as never);
    const { result } = renderHook(() => useExtractAudio());
    await act(async () => {
      await expect(result.current.extract(new File(['x'], 'a.wav'))).rejects.toThrow('ASR offline');
    });
    expect(result.current.error).toBe('ASR offline');
  });

  it('useExtractFile keeps the file details of a success', async () => {
    mocked.extractTextFromFile.mockResolvedValue({ success: true, text: 'x', file_info: { file_type: 'txt' } } as never);
    const { result } = renderHook(() => useExtractFile());
    await act(() => result.current.extract(new File(['x'], 'a.txt')));
    expect(result.current.fileInfo).toEqual({ file_type: 'txt' });
  });

  it('useExtractFile reports a server rejection with its code and details', async () => {
    mocked.extractTextFromFile.mockResolvedValue({
      success: false,
      error: 'Unsupported',
      error_code: 'VALIDATION_ERROR',
      details: 'DOCX or TXT only',
    } as never);
    const { result } = renderHook(() => useExtractFile());
    await act(async () => {
      await expect(result.current.extract(new File(['x'], 'a.pdf'))).rejects.toThrow('Unsupported');
    });
    expect([result.current.error, result.current.errorCode, result.current.errorDetails]).toEqual([
      'Unsupported',
      'VALIDATION_ERROR',
      'DOCX or TXT only',
    ]);
  });
});

describe('useExtractFile after a failure', () => {
  it('shows the second of two failures in a row', async () => {
    const { result } = renderHook(() => useExtractFile());
    mocked.extractTextFromFile.mockRejectedValueOnce(new Error('first failure'));
    await act(async () => {
      await expect(result.current.extract(new File(['x'], 'a.txt'))).rejects.toThrow();
    });
    mocked.extractTextFromFile.mockRejectedValueOnce(new Error('second failure'));
    await act(async () => {
      await expect(result.current.extract(new File(['x'], 'a.txt'))).rejects.toThrow();
    });
    expect(result.current.error).toBe('second failure');
  });
});

describe('useTTS', () => {
  it('exposes the audio URL', async () => {
    mocked.generateTTS.mockResolvedValue({ success: true, audio_url: 'http://x/a.mp3' });
    const { result } = renderHook(() => useTTS());
    await act(() => result.current.generate('ॐ'));
    expect(result.current.audioUrl).toBe('http://x/a.mp3');
  });

  it('turns a failed generation into an error', async () => {
    mocked.generateTTS.mockResolvedValue({ success: false, error: 'TTS off' });
    const { result } = renderHook(() => useTTS());
    await act(async () => {
      await expect(result.current.generate('ॐ')).rejects.toThrow('TTS off');
    });
    expect(result.current.error).toBe('TTS off');
  });
});
