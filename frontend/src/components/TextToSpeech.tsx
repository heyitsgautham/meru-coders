/**
 * TextToSpeech Component
 * Provides Sanskrit text-to-speech functionality with elegant UI
 */

import { useState, useRef, useEffect } from 'react';
import { Volume2, VolumeX, Loader2, Download } from 'lucide-react';
import { useTTS } from '../hooks/useApi';

interface TextToSpeechProps {
  text: string;
  label?: string;
}

export function TextToSpeech({ text, label = "Listen to this verse" }: TextToSpeechProps) {
  const { audioUrl, loading, error, generate, reset } = useTTS();
  const [voice, setVoice] = useState<'male' | 'female'>('male');
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  // Reset audio when text changes
  useEffect(() => {
    reset();
    setIsPlaying(false);
  }, [text, reset]);

  // Reset audio when voice changes to allow regeneration
  const handleVoiceChange = (newVoice: 'male' | 'female') => {
    setVoice(newVoice);
    if (audioUrl) {
      // Reset to allow regeneration with new voice
      reset();
      setIsPlaying(false);
    }
  };

  // Handle audio playback state
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleEnded = () => setIsPlaying(false);
    const handleError = (e: Event) => {
      console.error('Audio playback error:', e);
      setIsPlaying(false);
    };
    const handleLoadedData = () => {
      console.log('Audio loaded successfully:', audioUrl);
    };

    audio.addEventListener('play', handlePlay);
    audio.addEventListener('pause', handlePause);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('error', handleError);
    audio.addEventListener('loadeddata', handleLoadedData);

    // Force reload when URL changes
    if (audioUrl) {
      audio.load();
    }

    return () => {
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('pause', handlePause);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('error', handleError);
      audio.removeEventListener('loadeddata', handleLoadedData);
    };
  }, [audioUrl]);

  const handleGenerate = async () => {
    if (!text.trim()) return;

    // Reset playing state before generating new audio
    setIsPlaying(false);

    console.log('🎤 Generating TTS for text:', text.substring(0, 50) + '...');
    console.log('🎤 Selected voice:', voice);

    try {
      const result = await generate(text, voice);
      console.log('🎤 TTS Generation result:', result);
      if (result.audio_url) {
        console.log('✅ Audio URL received:', result.audio_url);
      }
    } catch (err) {
      console.error('❌ TTS generation failed:', err);
    }
  };

  const handlePlay = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
    }
  };

  const handleDownload = () => {
    if (audioUrl && audioRef.current) {
      const a = document.createElement('a');
      a.href = audioUrl;
      a.download = 'sanskrit_recitation.mp3';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  };

  return (
    <div className="tts-container">
      <style>{`
        .tts-container {
          background: linear-gradient(135deg, #fff5e6 0%, #ffe8cc 100%);
          border: 2px solid #ff9933;
          border-radius: 16px;
          padding: 20px;
          margin: 20px 0;
          box-shadow: 0 4px 12px rgba(255, 153, 51, 0.15);
        }

        .tts-header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 16px;
          color: #bf360c;
          font-weight: 600;
          font-size: 16px;
        }

        .tts-header svg {
          color: #ff9933;
          flex-shrink: 0;
        }

        .tts-controls {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
          align-items: center;
        }

        .tts-voice-selector {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background: white;
          border: 2px solid #ffcc80;
          border-radius: 8px;
          font-size: 14px;
          color: #bf360c;
        }

        .tts-voice-selector label {
          font-weight: 500;
          margin-right: 4px;
        }

        .tts-voice-selector select {
          border: none;
          background: transparent;
          color: #bf360c;
          font-weight: 600;
          cursor: pointer;
          outline: none;
          font-size: 14px;
        }

        .tts-button {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 16px;
          border: none;
          border-radius: 8px;
          font-weight: 600;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.2s ease;
          color: white;
        }

        .tts-button-primary {
          background: linear-gradient(135deg, #ff9933 0%, #ff6600 100%);
          box-shadow: 0 2px 8px rgba(255, 153, 51, 0.3);
        }

        .tts-button-primary:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(255, 153, 51, 0.4);
        }

        .tts-button-secondary {
          background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
          box-shadow: 0 2px 8px rgba(33, 150, 243, 0.3);
        }

        .tts-button-secondary:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(33, 150, 243, 0.4);
        }

        .tts-button-success {
          background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
          box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
        }

        .tts-button-success:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
        }

        .tts-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
          transform: none;
        }

        .tts-button svg {
          width: 18px;
          height: 18px;
        }

        .tts-audio-player {
          margin-top: 12px;
          padding: 12px;
          background: white;
          border-radius: 8px;
          border: 2px solid #ffcc80;
        }

        .tts-audio-player audio {
          width: 100%;
          height: 40px;
        }

        .tts-error {
          margin-top: 12px;
          padding: 12px;
          background: #ffebee;
          border: 1px solid #ef5350;
          border-radius: 8px;
          color: #c62828;
          font-size: 14px;
        }

        .tts-sanskrit-text {
          font-family: 'Noto Sans Devanagari', 'Noto Serif Devanagari', sans-serif;
          font-size: 18px;
          line-height: 1.8;
          color: #4a148c;
          margin: 12px 0;
          padding: 12px;
          background: rgba(255, 255, 255, 0.6);
          border-radius: 8px;
          border-left: 4px solid #ff9933;
        }

        @media (max-width: 640px) {
          .tts-controls {
            flex-direction: column;
            align-items: stretch;
          }

          .tts-button {
            width: 100%;
            justify-content: center;
          }

          .tts-voice-selector {
            width: 100%;
            justify-content: space-between;
          }
        }
      `}</style>

      <div className="tts-header">
        <Volume2 size={24} />
        <span>{label}</span>
      </div>

      <div className="tts-sanskrit-text">
        {text}
      </div>

      <div className="tts-controls">
        <div className="tts-voice-selector">
          <label htmlFor="voice-select">🎤 Voice:</label>
          <select
            id="voice-select"
            value={voice}
            onChange={(e) => handleVoiceChange(e.target.value as 'male' | 'female')}
            disabled={loading}
          >
            <option value="male">👨 Male</option>
            <option value="female">👩 Female</option>
          </select>
        </div>

        {!audioUrl ? (
          <button
            onClick={handleGenerate}
            disabled={loading || !text.trim()}
            className="tts-button tts-button-primary"
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Volume2 />
                Generate Speech
              </>
            )}
          </button>
        ) : (
          <>
            <button
              onClick={handleGenerate}
              disabled={loading}
              className="tts-button tts-button-primary"
              title="Regenerate with selected voice"
            >
              {loading ? (
                <>
                  <Loader2 className="animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Volume2 />
                  Regenerate
                </>
              )}
            </button>
            <button
              onClick={handlePlay}
              disabled={!audioUrl || loading}
              className="tts-button tts-button-success"
            >
              {isPlaying ? (
                <>
                  <VolumeX />
                  Pause
                </>
              ) : (
                <>
                  <Volume2 />
                  Play
                </>
              )}
            </button>
            <button
              onClick={handleDownload}
              disabled={!audioUrl || loading}
              className="tts-button tts-button-secondary"
            >
              <Download />
              Download
            </button>
          </>
        )}
      </div>

      {audioUrl && (
        <div className="tts-audio-player">
          <audio
            key={audioUrl}
            ref={audioRef}
            src={audioUrl}
            controls
            preload="auto"
            onError={(e) => console.error('Audio element error:', e)}
            onLoadedData={() => console.log('Audio data loaded')}
          />
        </div>
      )}

      {error && (
        <div className="tts-error">
          ⚠️ {error}
        </div>
      )}
    </div>
  );
}
