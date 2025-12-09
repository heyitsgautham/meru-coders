/**
 * Audio utility functions for recording and converting audio
 */

/**
 * Convert an audio blob to WAV format
 * @param audioBlob - The audio blob to convert
 * @returns A WAV audio blob
 */
export async function convertToWav(audioBlob: Blob): Promise<Blob> {
    const audioContext = new AudioContext();
    const arrayBuffer = await audioBlob.arrayBuffer();
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

    const wavBuffer = encodeWAV(audioBuffer);
    return new Blob([wavBuffer], { type: 'audio/wav' });
}

/**
 * Encode AudioBuffer to WAV format
 * @param audioBuffer - The AudioBuffer to encode
 * @returns ArrayBuffer containing WAV data
 */
function encodeWAV(audioBuffer: AudioBuffer): ArrayBuffer {
    const numberOfChannels = audioBuffer.numberOfChannels;
    const sampleRate = audioBuffer.sampleRate;
    const format = 1; // PCM
    const bitDepth = 16;

    // Interleave channels
    const length = audioBuffer.length * numberOfChannels * 2;
    const buffer = new ArrayBuffer(44 + length);
    const view = new DataView(buffer);

    // Write WAV header
    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + length, true);
    writeString(view, 8, 'WAVE');
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true); // fmt chunk size
    view.setUint16(20, format, true); // audio format (1 = PCM)
    view.setUint16(22, numberOfChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * numberOfChannels * bitDepth / 8, true); // byte rate
    view.setUint16(32, numberOfChannels * bitDepth / 8, true); // block align
    view.setUint16(34, bitDepth, true);
    writeString(view, 36, 'data');
    view.setUint32(40, length, true);

    // Write audio data
    const channels: Float32Array[] = [];
    for (let i = 0; i < numberOfChannels; i++) {
        channels.push(audioBuffer.getChannelData(i));
    }

    let offset = 44;
    for (let i = 0; i < audioBuffer.length; i++) {
        for (let channel = 0; channel < numberOfChannels; channel++) {
            const sample = Math.max(-1, Math.min(1, channels[channel][i]));
            view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
            offset += 2;
        }
    }

    return buffer;
}

/**
 * Write a string to a DataView
 */
function writeString(view: DataView, offset: number, string: string): void {
    for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
    }
}

/**
 * Record audio from microphone and return as WAV file
 * @param onDataAvailable - Optional callback for recording progress
 * @returns Object with start and stop functions
 */
export function createAudioRecorder(
    onDataAvailable?: (blob: Blob) => void
): {
    start: () => Promise<void>;
    stop: () => Promise<File | null>;
    isRecording: () => boolean;
} {
    let mediaRecorder: MediaRecorder | null = null;
    let audioChunks: Blob[] = [];
    let stream: MediaStream | null = null;

    const start = async (): Promise<void> => {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // Try different MIME types for broader browser support
            const mimeTypes = [
                'audio/webm;codecs=opus',
                'audio/webm',
                'audio/ogg;codecs=opus',
                'audio/mp4'
            ];

            let selectedMimeType = 'audio/webm'; // fallback
            for (const mimeType of mimeTypes) {
                if (MediaRecorder.isTypeSupported(mimeType)) {
                    selectedMimeType = mimeType;
                    console.log('Using MIME type for recording:', mimeType);
                    break;
                }
            }

            mediaRecorder = new MediaRecorder(stream, { mimeType: selectedMimeType });
            audioChunks = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                    if (onDataAvailable) {
                        onDataAvailable(event.data);
                    }
                }
            };

            mediaRecorder.start();
            console.log('Recording started');
        } catch (error) {
            console.error('Error starting recording:', error);
            throw new Error('Could not access microphone. Please ensure you have granted permission.');
        }
    };

    const stop = async (): Promise<File | null> => {
        return new Promise((resolve, reject) => {
            if (!mediaRecorder || mediaRecorder.state === 'inactive') {
                resolve(null);
                return;
            }

            mediaRecorder.onstop = async () => {
                try {
                    // Stop all tracks to release microphone
                    if (stream) {
                        stream.getTracks().forEach(track => track.stop());
                    }

                    // Create blob from recorded chunks
                    const audioBlob = new Blob(audioChunks, { type: audioChunks[0]?.type || 'audio/webm' });
                    console.log('Original recording blob size:', audioBlob.size, 'bytes');

                    // Convert to WAV format
                    console.log('Converting to WAV format...');
                    const wavBlob = await convertToWav(audioBlob);
                    console.log('WAV conversion complete. Size:', wavBlob.size, 'bytes');

                    // Create File object from WAV blob
                    const wavFile = new File([wavBlob], 'recording.wav', { type: 'audio/wav' });
                    console.log('WAV file created:', wavFile.name, wavFile.size, 'bytes');

                    resolve(wavFile);
                } catch (error) {
                    console.error('Error converting to WAV:', error);
                    reject(error);
                }
            };

            mediaRecorder.stop();
        });
    };

    const isRecording = (): boolean => {
        return mediaRecorder !== null && mediaRecorder.state === 'recording';
    };

    return { start, stop, isRecording };
}
