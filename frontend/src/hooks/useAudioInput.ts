import { useCallback, useEffect, useRef, useState } from 'react';
import type { ChangeEvent } from 'react';
import type { SlokaValidateResponse } from '../types/api';
import { validateAudioFile } from '../components/analysis/inputFiles';
import { validateSloka } from '../services/api';
import { createAudioRecorder } from '../utils/audioUtils';
import { alertUser } from './alertUser';
import { useDropZone } from './useDropZone';
import { useExtractAudio } from './useApi';

/** A transcription is replaced by the verified verse only at this similarity or above. */
export const NORMALIZE_MIN_SIMILARITY = 0.9;

/**
 * State and actions for the Voice Input tab: record or upload chanting,
 * transcribe it, and optionally normalise the transcript against verified verses.
 */
export function useAudioInput(notify: (message: string) => void = alertUser) {
  const [audio, setAudio] = useState<File | null>(null);
  const [transcript, setTranscript] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [validation, setValidation] = useState<SlokaValidateResponse | null>(null);
  const recorderRef = useRef<ReturnType<typeof createAudioRecorder> | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { loading, error, extract: transcribe, reset: resetTranscription } = useExtractAudio();

  // Free the recording's object URL when it is replaced or the form unmounts.
  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
  }, [audioUrl]);

  const selectAudio = useCallback(
    (file: File) => {
      const problem = validateAudioFile(file);
      if (problem) {
        notify(problem);
        return;
      }
      setAudio(file);
      setTranscript(null);
      resetTranscription();
    },
    [notify, resetTranscription],
  );

  const dropZone = useDropZone(selectAudio);

  const onInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) selectAudio(file);
  };

  const extract = async () => {
    if (!audio) return;
    try {
      setTranscript(await transcribe(audio));
      setValidation(null);
    } catch (err) {
      console.error('Audio transcription failed:', err);
    }
  };

  const normalize = async () => {
    if (!transcript) return;
    setIsValidating(true);
    try {
      const result = await validateSloka(transcript);
      setValidation(result);
      if (result.found && result.original_text && result.similarity && result.similarity >= NORMALIZE_MIN_SIMILARITY) {
        setTranscript(result.original_text);
      }
    } catch (err) {
      console.error('Sloka validation failed:', err);
      notify('Failed to validate sloka. Please try again.');
    } finally {
      setIsValidating(false);
    }
  };

  const keepTranscript = () => setValidation(null);

  const remove = async () => {
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    setAudio(null);
    setTranscript(null);
    setValidation(null);
    resetTranscription();
    if (inputRef.current) inputRef.current.value = '';
    if (recorderRef.current && isRecording) {
      await recorderRef.current.stop();
      recorderRef.current = null;
      setIsRecording(false);
    }
  };

  const startRecording = async () => {
    try {
      recorderRef.current = createAudioRecorder();
      await recorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Error accessing microphone:', err);
      notify('Could not access microphone. Please ensure you have granted permission.');
      recorderRef.current = null;
    }
  };

  const stopRecording = async () => {
    try {
      if (recorderRef.current && isRecording) {
        const wavFile = await recorderRef.current.stop();
        if (wavFile) {
          if (audioUrl) URL.revokeObjectURL(audioUrl);
          setAudioUrl(URL.createObjectURL(wavFile));
          setAudio(wavFile);
          setTranscript(null);
        }
        recorderRef.current = null;
        setIsRecording(false);
      }
    } catch (err) {
      console.error('Error stopping recording:', err);
      notify('Failed to stop recording. Please try again.');
      recorderRef.current = null;
      setIsRecording(false);
    }
  };

  return {
    audio,
    transcript,
    audioUrl,
    isRecording,
    isValidating,
    validation,
    inputRef,
    loading,
    error,
    dropZone,
    onInputChange,
    extract,
    normalize,
    keepTranscript,
    remove,
    startRecording,
    stopRecording,
  };
}

export type AudioInput = ReturnType<typeof useAudioInput>;
