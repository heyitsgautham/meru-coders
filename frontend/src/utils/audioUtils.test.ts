import { Blob as NodeBlob } from 'node:buffer';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { convertToWav, createAudioRecorder } from './audioUtils';

// Two channels, three frames, with samples outside [-1, 1] to check clipping.
const LEFT = new Float32Array([0, 0.5, 2]);
const RIGHT = new Float32Array([-0.5, -1, -3]);

class FakeAudioContext {
  async decodeAudioData() {
    return {
      numberOfChannels: 2,
      sampleRate: 16000,
      length: 3,
      getChannelData: (channel: number) => (channel === 0 ? LEFT : RIGHT),
    };
  }
}

class FakeRecorder {
  static instances: FakeRecorder[] = [];
  static isTypeSupported = (type: string) => type === 'audio/webm';
  state = 'inactive';
  ondataavailable: ((event: { data: Blob }) => void) | null = null;
  onstop: (() => void) | null = null;
  constructor(public stream: unknown, public options: { mimeType: string }) {
    FakeRecorder.instances.push(this);
  }
  start() {
    this.state = 'recording';
  }
  stop() {
    this.state = 'inactive';
    this.ondataavailable?.({ data: new Blob(['abc'], { type: 'audio/webm' }) });
    this.ondataavailable?.({ data: new Blob([]) });
    this.onstop?.();
  }
}

const text = (view: DataView, offset: number, length: number) =>
  String.fromCharCode(...Array.from({ length }, (_, i) => view.getUint8(offset + i)));

beforeEach(() => {
  // jsdom's Blob has no arrayBuffer(), which the converter reads from.
  vi.stubGlobal('Blob', NodeBlob);
  vi.stubGlobal('AudioContext', FakeAudioContext);
  vi.stubGlobal('MediaRecorder', FakeRecorder);
  FakeRecorder.instances = [];
  vi.spyOn(console, 'log').mockImplementation(() => {});
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('convertToWav', () => {
  it('writes a 16-bit PCM header and interleaved, clipped samples', async () => {
    const wav = await convertToWav(new Blob(['x']));
    const view = new DataView(await wav.arrayBuffer());

    expect(wav.type).toBe('audio/wav');
    expect(view.byteLength).toBe(44 + 3 * 2 * 2);
    expect(text(view, 0, 4)).toBe('RIFF');
    expect(view.getUint32(4, true)).toBe(36 + 12);
    expect(text(view, 8, 8)).toBe('WAVEfmt ');
    expect(view.getUint16(20, true)).toBe(1);
    expect(view.getUint16(22, true)).toBe(2);
    expect(view.getUint32(24, true)).toBe(16000);
    expect(view.getUint32(28, true)).toBe(16000 * 2 * 2);
    expect(view.getUint16(34, true)).toBe(16);
    expect(text(view, 36, 4)).toBe('data');

    const samples = Array.from({ length: 6 }, (_, i) => view.getInt16(44 + i * 2, true));
    expect(samples).toEqual([0, -16384, 16383, -32768, 32767, -32768]);
  });
});

describe('createAudioRecorder', () => {
  it('records with the first supported type and returns a WAV file', async () => {
    const stopTrack = vi.fn();
    const stream = { getTracks: () => [{ stop: stopTrack }] };
    vi.stubGlobal('navigator', { mediaDevices: { getUserMedia: vi.fn().mockResolvedValue(stream) } });
    const onData = vi.fn();
    const recorder = createAudioRecorder(onData);

    await recorder.start();
    expect(recorder.isRecording()).toBe(true);
    expect(FakeRecorder.instances[0].options.mimeType).toBe('audio/webm');

    const file = await recorder.stop();

    expect(file?.name).toBe('recording.wav');
    expect(file?.type).toBe('audio/wav');
    expect(onData).toHaveBeenCalledOnce();
    expect(stopTrack).toHaveBeenCalledOnce();
    expect(recorder.isRecording()).toBe(false);
  });

  it('returns nothing when stopped before it started', async () => {
    expect(await createAudioRecorder().stop()).toBeNull();
  });

  it('explains a refused microphone', async () => {
    vi.stubGlobal('navigator', { mediaDevices: { getUserMedia: vi.fn().mockRejectedValue(new Error('NotAllowed')) } });
    await expect(createAudioRecorder().start()).rejects.toThrow(
      'Could not access microphone. Please ensure you have granted permission.',
    );
  });
});
