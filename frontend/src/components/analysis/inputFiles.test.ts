import { describe, expect, it } from 'vitest';
import {
  MAX_UPLOAD_BYTES,
  audioIcon,
  documentIcon,
  documentTypeLabel,
  fileExtension,
  formatKilobytes,
  validateAudioFile,
  validateDocumentFile,
  validateImageFile,
} from './inputFiles';

function fileOf(name: string, type = '', size = 10): File {
  const file = new File(['x'], name, { type });
  Object.defineProperty(file, 'size', { value: size });
  return file;
}

describe('fileExtension', () => {
  it('returns the lower-case text after the last dot', () => {
    expect(fileExtension('Gita.Chapter1.DOCX')).toBe('docx');
  });

  it('returns undefined for a name without a dot', () => {
    expect(fileExtension('README')).toBeUndefined();
  });
});

describe('validateImageFile', () => {
  it('accepts an image under the size limit', () => {
    expect(validateImageFile(fileOf('verse.png', 'image/png'))).toBeNull();
  });

  it('rejects a file whose MIME type is not an image', () => {
    expect(validateImageFile(fileOf('verse.pdf', 'application/pdf'))).toBe('Please select an image file');
  });

  it('rejects an image over 10MB', () => {
    expect(validateImageFile(fileOf('big.jpg', 'image/jpeg', MAX_UPLOAD_BYTES + 1))).toBe(
      'Image size must be less than 10MB',
    );
  });

  it('accepts an image of exactly 10MB', () => {
    expect(validateImageFile(fileOf('edge.jpg', 'image/jpeg', MAX_UPLOAD_BYTES))).toBeNull();
  });
});

describe('validateDocumentFile', () => {
  it.each(['gita.docx', 'gita.txt', 'gita.TEXT'])('accepts %s', (name) => {
    expect(validateDocumentFile(fileOf(name))).toBeNull();
  });

  it.each(['gita.pdf', 'gita.doc', 'gita'])('rejects %s', (name) => {
    expect(validateDocumentFile(fileOf(name))).toBe('Please select a DOCX or TXT file');
  });

  it('rejects a document over 10MB', () => {
    expect(validateDocumentFile(fileOf('gita.txt', '', MAX_UPLOAD_BYTES + 1))).toBe(
      'File size must be less than 10MB',
    );
  });
});

describe('validateAudioFile', () => {
  it.each(['chant.wav', 'chant.mp3', 'chant.webm', 'chant.ogg', 'chant.m4a', 'chant.flac'])('accepts %s', (name) => {
    expect(validateAudioFile(fileOf(name))).toBeNull();
  });

  it('rejects an unsupported audio format', () => {
    expect(validateAudioFile(fileOf('chant.aiff'))).toBe('Please select a WAV or MP3 audio file');
  });

  it('rejects audio over 10MB', () => {
    expect(validateAudioFile(fileOf('chant.mp3', '', MAX_UPLOAD_BYTES + 1))).toBe(
      'Audio file size must be less than 10MB',
    );
  });
});

describe('display helpers', () => {
  it('formats sizes in kilobytes with one decimal', () => {
    expect(formatKilobytes(2048)).toBe('2.0 KB');
    expect(formatKilobytes(1536)).toBe('1.5 KB');
  });

  it('picks an icon per document and audio type', () => {
    expect(documentIcon('a.docx')).toBe('📝');
    expect(documentIcon('a.txt')).toBe('📃');
    expect(audioIcon('a.mp3')).toBe('🎵');
    expect(audioIcon('a.wav')).toBe('🔊');
    expect(audioIcon('a.webm')).toBe('🎤');
    expect(audioIcon('a.flac')).toBe('🎧');
  });

  it('labels the document types the backend reports', () => {
    expect(documentTypeLabel('docx')).toBe('Word Document');
    expect(documentTypeLabel('txt')).toBe('Text File');
    expect(documentTypeLabel('pdf')).toBe('Document');
  });
});
