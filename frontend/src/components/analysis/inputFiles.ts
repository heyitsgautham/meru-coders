// Upload rules for the image, document and audio tabs of the analysis form.
// Each validator returns the message shown to the user, or null when the file is accepted.

export const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;

export const DOCUMENT_EXTENSIONS = ['docx', 'txt', 'text'];
export const AUDIO_EXTENSIONS = ['wav', 'mp3', 'webm', 'ogg', 'm4a', 'flac'];

/** Lower-case extension after the last dot, or undefined for a name without one. */
export function fileExtension(filename: string): string | undefined {
  const parts = filename.split('.');
  return parts.length > 1 ? parts.pop()?.toLowerCase() : undefined;
}

export function validateImageFile(file: File): string | null {
  if (!file.type.startsWith('image/')) return 'Please select an image file';
  if (file.size > MAX_UPLOAD_BYTES) return 'Image size must be less than 10MB';
  return null;
}

export function validateDocumentFile(file: File): string | null {
  const ext = fileExtension(file.name);
  if (!ext || !DOCUMENT_EXTENSIONS.includes(ext)) return 'Please select a DOCX or TXT file';
  if (file.size > MAX_UPLOAD_BYTES) return 'File size must be less than 10MB';
  return null;
}

export function validateAudioFile(file: File): string | null {
  const ext = fileExtension(file.name);
  if (!ext || !AUDIO_EXTENSIONS.includes(ext)) return 'Please select a WAV or MP3 audio file';
  if (file.size > MAX_UPLOAD_BYTES) return 'Audio file size must be less than 10MB';
  return null;
}

/** Size in kilobytes with one decimal, as shown under an uploaded file name. */
export function formatKilobytes(bytes: number): string {
  return `${(bytes / 1024).toFixed(1)} KB`;
}

export function documentIcon(filename: string): string {
  return fileExtension(filename) === 'docx' ? '📝' : '📃';
}

export function audioIcon(filename: string): string {
  switch (fileExtension(filename)) {
    case 'mp3':
      return '🎵';
    case 'wav':
      return '🔊';
    case 'webm':
      return '🎤';
    default:
      return '🎧';
  }
}

export function documentTypeLabel(fileType: string): string {
  switch (fileType) {
    case 'docx':
      return 'Word Document';
    case 'txt':
      return 'Text File';
    default:
      return 'Document';
  }
}
