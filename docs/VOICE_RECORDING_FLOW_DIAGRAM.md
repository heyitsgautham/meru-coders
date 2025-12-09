# Voice Recording Flow Diagram

## Before (Failing)

```
┌─────────────┐
│   Browser   │
│ MediaRecorder│
└──────┬──────┘
       │ Records audio
       ▼
┌─────────────┐
│ WebM Blob   │
│ (compressed)│
└──────┬──────┘
       │ Direct upload
       ▼
┌─────────────┐
│   Backend   │
│   ❌ Fails   │
└─────────────┘
```

## After (Working)

```
┌─────────────────────────────────────────────────┐
│              Browser (Frontend)                  │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────┐                               │
│  │ MediaRecorder│                               │
│  │  (WebM/Opus) │                               │
│  └──────┬───────┘                               │
│         │ records                                │
│         ▼                                        │
│  ┌──────────────┐                               │
│  │  WebM Blob   │                               │
│  └──────┬───────┘                               │
│         │ convert                                │
│         ▼                                        │
│  ┌──────────────┐     Web Audio API             │
│  │ AudioContext │◄─────────────────────────────┐│
│  │decodeAudioData                              ││
│  └──────┬───────┘                              ││
│         │ decode to AudioBuffer                ││
│         ▼                                       ││
│  ┌──────────────┐                              ││
│  │ AudioBuffer  │                              ││
│  │ (PCM Float)  │                              ││
│  └──────┬───────┘                              ││
│         │ encode                                ││
│         ▼                                       ││
│  ┌──────────────┐     encodeWAV()             ││
│  │  WAV Buffer  │◄────────────────────────────┘│
│  │ (PCM 16-bit) │                               │
│  └──────┬───────┘                               │
│         │ create File                           │
│         ▼                                        │
│  ┌──────────────┐                               │
│  │recording.wav │                               │
│  │  File Object │                               │
│  └──────┬───────┘                               │
│         │                                        │
└─────────┼────────────────────────────────────────┘
          │ upload
          ▼
┌─────────────────┐
│     Backend     │
│   ✅ Success!   │
│   (ASR/TTS)     │
└─────────────────┘
```

## Detailed Conversion Process

```
Step 1: Record Audio
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
navigator.mediaDevices.getUserMedia({ audio: true })
            │
            ▼
    MediaRecorder.start()
            │
            ▼
    Collect audio chunks (WebM/Opus format)
            │
            ▼
    MediaRecorder.stop()
            │
            ▼
    Create Blob from chunks


Step 2: Convert to WAV
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Blob (WebM)
            │
            ▼
    arrayBuffer = await blob.arrayBuffer()
            │
            ▼
    AudioContext.decodeAudioData(arrayBuffer)
            │
            ▼
    AudioBuffer (Float32Array per channel)
            │
            ▼
    encodeWAV(audioBuffer)
      ├─ Write RIFF header
      ├─ Write fmt chunk (PCM info)
      ├─ Write data chunk header
      └─ Convert Float32 → Int16 samples
            │
            ▼
    ArrayBuffer (WAV format)
            │
            ▼
    Create Blob with type 'audio/wav'
            │
            ▼
    Create File object with name 'recording.wav'


Step 3: Upload and Process
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    File (recording.wav)
            │
            ▼
    FormData.append('audio_file', file)
            │
            ▼
    POST /api/audio/transcribe
            │
            ▼
    Backend receives WAV file
            │
            ▼
    IndicConformer ASR processes audio
            │
            ▼
    Returns transcribed Sanskrit text
```

## File Format Comparison

```
╔════════════════════════════════════════════════════╗
║               WebM Format (Before)                 ║
╠════════════════════════════════════════════════════╣
║ Container: WebM (Matroska)                        ║
║ Codec: Opus / Vorbis                              ║
║ Compression: Lossy                                ║
║ Size: ~500 KB per minute                          ║
║ Browser Support: Modern browsers only             ║
║ Backend Compatibility: ❌ Limited                  ║
╚════════════════════════════════════════════════════╝

                    ▼ Convert ▼

╔════════════════════════════════════════════════════╗
║                WAV Format (After)                  ║
╠════════════════════════════════════════════════════╣
║ Container: RIFF WAV                               ║
║ Codec: PCM (uncompressed)                         ║
║ Compression: None                                 ║
║ Size: ~5.5 MB per minute (mono, 48kHz)           ║
║ Browser Support: Universal                        ║
║ Backend Compatibility: ✅ Excellent                ║
╚════════════════════════════════════════════════════╝
```

## Component Interaction

```
┌─────────────────────────────────────────────────────┐
│             AnalysisForm.tsx                        │
│                                                     │
│  ┌────────────────────────────────────┐            │
│  │  Voice Tab UI                      │            │
│  │  • Record button                   │            │
│  │  • Stop button                     │            │
│  │  • Audio file display              │            │
│  └────────┬───────────────────────────┘            │
│           │                                         │
│           │ onClick                                 │
│           ▼                                         │
│  ┌────────────────────────────────────┐            │
│  │  startRecording() / stopRecording()│            │
│  └────────┬───────────────────────────┘            │
│           │                                         │
│           │ uses                                    │
│           ▼                                         │
└───────────┼─────────────────────────────────────────┘
            │
            │ import
            ▼
┌─────────────────────────────────────────────────────┐
│         audioUtils.ts (Utility Module)              │
│                                                     │
│  ┌────────────────────────────────────┐            │
│  │  createAudioRecorder()             │            │
│  │    ├─ start()  → Begin recording   │            │
│  │    ├─ stop()   → Convert to WAV    │            │
│  │    └─ isRecording() → Get status   │            │
│  └────────┬───────────────────────────┘            │
│           │                                         │
│           │ uses                                    │
│           ▼                                         │
│  ┌────────────────────────────────────┐            │
│  │  convertToWav()                    │            │
│  └────────┬───────────────────────────┘            │
│           │                                         │
│           │ uses                                    │
│           ▼                                         │
│  ┌────────────────────────────────────┐            │
│  │  encodeWAV()                       │            │
│  │    ├─ Write RIFF header            │            │
│  │    ├─ Write fmt chunk              │            │
│  │    ├─ Write data chunk             │            │
│  │    └─ Convert samples to Int16     │            │
│  └────────────────────────────────────┘            │
│                                                     │
└─────────────────────────────────────────────────────┘
            │
            │ returns File
            ▼
┌─────────────────────────────────────────────────────┐
│        State Management                             │
│                                                     │
│  const [selectedAudio, setSelectedAudio]           │
│                 ▼                                   │
│         recording.wav File                          │
│                 ▼                                   │
│  User clicks "Extract Text from Audio"             │
│                 ▼                                   │
│  extractTextFromAudio(selectedAudio)               │
└─────────────────────────────────────────────────────┘
            │
            │ HTTP POST
            ▼
┌─────────────────────────────────────────────────────┐
│              Backend API                            │
│   POST /api/audio/transcribe                       │
│        ├─ Receives WAV file                        │
│        ├─ IndicConformer ASR                       │
│        └─ Returns Sanskrit text                    │
└─────────────────────────────────────────────────────┘
```

## Error Handling Flow

```
┌─ Start Recording ─────────────────────────────┐
│                                                │
│  Try to access microphone                     │
│         │                                      │
│         ├─ Success ──► Start recording        │
│         │                                      │
│         └─ Error ──► Show permission alert    │
│                      Log error                │
│                                                │
└────────────────────────────────────────────────┘

┌─ Stop Recording ──────────────────────────────┐
│                                                │
│  Try to stop and convert                      │
│         │                                      │
│         ├─ Success ──► Create WAV file        │
│         │              Update UI               │
│         │                                      │
│         └─ Error ──► Show conversion alert    │
│                      Log error                │
│                      Reset state              │
│                                                │
└────────────────────────────────────────────────┘
```

## Memory Management

```
Recording Lifecycle:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Start Recording
   ├─ Request microphone access
   ├─ Create MediaRecorder
   └─ Store reference in useRef

2. During Recording
   ├─ Audio chunks collected in closure
   └─ No state updates (prevents re-renders)

3. Stop Recording
   ├─ Stop MediaRecorder
   ├─ Stop all MediaStream tracks  ← RELEASE MICROPHONE
   ├─ Convert to WAV
   ├─ Create File object
   ├─ Update state with File
   └─ Clear recorder reference

4. Cleanup / Cancel
   ├─ Stop recorder if active
   ├─ Stop all tracks
   ├─ Clear all references
   └─ Reset state

✅ No memory leaks - proper cleanup
✅ No permission issues - tracks released
✅ No multiple recordings - ref prevents overlap
```
