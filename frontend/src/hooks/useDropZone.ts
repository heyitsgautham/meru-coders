import { useCallback, useState } from 'react';
import type { DragEvent } from 'react';

export interface DropZoneHandlers {
  onDragOver: (e: DragEvent<HTMLDivElement>) => void;
  onDragEnter: (e: DragEvent<HTMLDivElement>) => void;
  onDragLeave: (e: DragEvent<HTMLDivElement>) => void;
  onDrop: (e: DragEvent<HTMLDivElement>) => void;
}

/**
 * Drag-and-drop state for one upload area.
 * `isDragging` stays true while the pointer moves between children of the zone,
 * and `onFile` receives the first dropped file.
 */
export function useDropZone(onFile: (file: File) => void): { isDragging: boolean; handlers: DropZoneHandlers } {
  const [isDragging, setIsDragging] = useState(false);

  const onDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const onDragEnter = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const onDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.currentTarget.contains(e.relatedTarget as Node)) return;
    setIsDragging(false);
  }, []);

  const onDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      const file = e.dataTransfer.files?.[0];
      if (file) onFile(file);
    },
    [onFile],
  );

  return { isDragging, handlers: { onDragOver, onDragEnter, onDragLeave, onDrop } };
}
