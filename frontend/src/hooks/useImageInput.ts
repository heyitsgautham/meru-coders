import { useCallback, useRef, useState } from 'react';
import type { ChangeEvent } from 'react';
import { validateImageFile } from '../components/analysis/inputFiles';
import { useDropZone } from './useDropZone';
import { useExtractText } from './useApi';
import { alertUser } from './alertUser';

/** State and actions for the Image OCR tab: pick an image, preview it, extract its text. */
export function useImageInput(notify: (message: string) => void = alertUser) {
  const [image, setImage] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [extractedText, setExtractedText] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { loading, error, extract: extractFromImage } = useExtractText();

  const selectImage = useCallback(
    (file: File) => {
      const problem = validateImageFile(file);
      if (problem) {
        notify(problem);
        return;
      }
      setImage(file);
      setExtractedText(null);
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target?.result as string);
      reader.readAsDataURL(file);
    },
    [notify],
  );

  const dropZone = useDropZone(selectImage);

  const onInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) selectImage(file);
  };

  const remove = () => {
    setImage(null);
    setPreview(null);
    setExtractedText(null);
    // Reset the input so choosing the same file again fires a change event.
    if (inputRef.current) inputRef.current.value = '';
  };

  const extract = async () => {
    if (!image) return;
    try {
      setExtractedText(await extractFromImage(image));
    } catch (err) {
      console.error('OCR extraction failed:', err);
    }
  };

  return { image, preview, extractedText, inputRef, loading, error, dropZone, onInputChange, remove, extract };
}

export type ImageInput = ReturnType<typeof useImageInput>;
