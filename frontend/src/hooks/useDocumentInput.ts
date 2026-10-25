import { useCallback, useRef, useState } from 'react';
import type { ChangeEvent } from 'react';
import type { FileInfo } from '../types/api';
import { validateDocumentFile } from '../components/analysis/inputFiles';
import { alertUser } from './alertUser';
import { useDropZone } from './useDropZone';
import { useExtractFile } from './useApi';

/** State and actions for the File Upload tab: pick a DOCX or TXT file and extract its text. */
export function useDocumentInput(notify: (message: string) => void = alertUser) {
  const [file, setFile] = useState<File | null>(null);
  const [extractedText, setExtractedText] = useState<string | null>(null);
  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const { loading, error, errorDetails, extract: extractFromFile, reset: resetExtract } = useExtractFile();

  const selectFile = useCallback(
    (selected: File) => {
      const problem = validateDocumentFile(selected);
      if (problem) {
        notify(problem);
        return;
      }
      setFile(selected);
      setExtractedText(null);
      setFileInfo(null);
      resetExtract();
    },
    [notify, resetExtract],
  );

  const dropZone = useDropZone(selectFile);

  const onInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) selectFile(selected);
  };

  const remove = () => {
    setFile(null);
    setExtractedText(null);
    setFileInfo(null);
    setWarnings([]);
    resetExtract();
    if (inputRef.current) inputRef.current.value = '';
  };

  const extract = async () => {
    if (!file) return;
    try {
      const response = await extractFromFile(file);
      if (response.success && response.text) {
        setExtractedText(response.text);
        setFileInfo(response.file_info || null);
        setWarnings(response.warnings || []);
      }
    } catch (err) {
      console.error('File extraction failed:', err);
    }
  };

  return {
    file,
    extractedText,
    fileInfo,
    warnings,
    inputRef,
    loading,
    error,
    errorDetails,
    dropZone,
    onInputChange,
    remove,
    extract,
  };
}

export type DocumentInput = ReturnType<typeof useDocumentInput>;
