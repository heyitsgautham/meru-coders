/**
 * useApi Hook
 * Custom hooks for API calls with loading and error states
 */

import { useState, useEffect, useCallback } from 'react';
import * as api from '../services/api';
import type {
  SchemeOption,
  Example,
  IdentifyResponse,
  AnalysisMode,
  OCRAvailability,
  OCRExtractResponse,
} from '../types/api';

// Hook for loading schemes
export function useSchemes() {
  const [schemes, setSchemes] = useState<SchemeOption[]>(api.getDefaultSchemes());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function loadSchemes() {
      try {
        const response = await api.getSchemes();
        if (mounted && response.success && response.schemes) {
          setSchemes(response.schemes);
        }
      } catch (err) {
        if (mounted) {
          console.warn('Failed to load schemes, using defaults');
          setError(err instanceof Error ? err.message : 'Failed to load schemes');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadSchemes();
    return () => { mounted = false; };
  }, []);

  return { schemes, loading, error };
}

// Hook for loading examples
export function useExamples() {
  const [examples, setExamples] = useState<Example[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const loadExamples = useCallback(async () => {
    if (loaded) return;
    
    setLoading(true);
    setError(null);

    try {
      const response = await api.getExamples();
      if (response.success && response.examples) {
        setExamples(response.examples);
        setLoaded(true);
      } else {
        setError('No examples available');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load examples');
    } finally {
      setLoading(false);
    }
  }, [loaded]);

  return { examples, loading, error, loadExamples, loaded };
}

// Hook for checking API connection and OCR availability
export function useAPIInfo() {
  const [ocrAvailable, setOcrAvailable] = useState<OCRAvailability>({ tesseract: true, cloud_vision: false });
  const [connected, setConnected] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    async function checkAPI() {
      try {
        const response = await api.getAPIInfo();
        if (mounted) {
          if (response.ocr_available) {
            setOcrAvailable(response.ocr_available);
          }
          setConnected(true);
        }
      } catch (err) {
        if (mounted) {
          console.warn('Could not connect to API:', err);
          setConnected(false);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    checkAPI();
    return () => { mounted = false; };
  }, []);

  return { ocrAvailable, connected, loading };
}

// Hook for text identification
export function useIdentifyText() {
  const [result, setResult] = useState<IdentifyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const identify = useCallback(async (
    text: string,
    mode: AnalysisMode = 'line',
    outputScheme: string = ''
  ) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await api.identifyFromText(text, mode, outputScheme);
      setResult(response);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Analysis failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { result, loading, error, identify, reset };
}

// Hook for image identification
export function useIdentifyImage() {
  const [result, setResult] = useState<IdentifyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const identify = useCallback(async (
    file: File,
    mode: AnalysisMode = 'line',
    outputScheme: string = ''
  ) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await api.identifyFromImage(file, mode, outputScheme);
      setResult(response);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Analysis failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { result, loading, error, identify, reset };
}

// Hook for OCR text extraction only (no analysis)
export function useExtractText() {
  const [text, setText] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const extract = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);
    setText(null);

    try {
      const response = await api.extractTextFromImage(file);
      if (response.success && response.text !== undefined) {
        setText(response.text);
        return response.text;
      } else {
        throw new Error(response.error || 'OCR extraction failed');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'OCR extraction failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setText(null);
    setError(null);
  }, []);

  return { text, loading, error, extract, reset };
}

// Hook for file identification
export function useIdentifyFile() {
  const [result, setResult] = useState<IdentifyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const identify = useCallback(async (
    file: File,
    mode: AnalysisMode = 'line',
    outputScheme: string = ''
  ) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await api.identifyFromFile(file, mode, outputScheme);
      setResult(response);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Analysis failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { result, loading, error, identify, reset };
}
