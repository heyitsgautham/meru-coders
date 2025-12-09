/**
 * Pingala Acharya Speaker Component
 * Displays animated Pingala image with speech bubble explaining the identified chandas
 */

import { useState, useEffect } from 'react';
import { Volume2, VolumeX, RotateCcw, X } from 'lucide-react';
import { useTTS } from '../hooks/useApi';
import { generatePingalaScript } from '../utils/sanskritNumbers';
import type { IdentifyResponse } from '../types/api';
import '../styles/pingala-speaker.css';

interface PingalaAcharyaSpeakerProps {
  result: IdentifyResponse;
  onClose?: () => void;
}

export function PingalaAcharyaSpeaker({ result, onClose }: PingalaAcharyaSpeakerProps) {
  const [isClosing, setIsClosing] = useState(false);
  const [scriptText, setScriptText] = useState<string>('');
  const [isPlaying, setIsPlaying] = useState(false);

  const { audioUrl, loading: isLoading, error, generate: generateSpeech } = useTTS();

  // Extract meter details from result
  const getResultDetails = () => {
    if (!result?.result?.line?.[0]?.result) {
      return null;
    }

    const lineResult = result.result.line[0].result;
    
    // Extract only the primary meter name without additional info
    let meterName = lineResult.display_chanda_primary || 'अज्ञात';
    
    // Remove any parenthetical content like (indravajrā) [10.0] | त्रिष्टुभ् (पाद 1) etc.
    // Just keep the first meter name before any parentheses or brackets
    meterName = meterName.split('(')[0].trim();
    meterName = meterName.split('[')[0].trim();
    meterName = meterName.split('|')[0].trim();
    
    return {
      meterName: meterName,
      syllableCount: typeof lineResult.display_length === 'number' ? lineResult.display_length : 0,
      matraCount: typeof lineResult.display_matra === 'number' ? lineResult.display_matra : 0,
      ganaPattern: lineResult.display_gana || '',
    };
  };

  // Generate Sanskrit explanation script
  useEffect(() => {
    const details = getResultDetails();
    if (!details) return;

    const script = generatePingalaScript(details.meterName);

    setScriptText(script);

    // Auto-generate TTS immediately (no delay)
    handleGenerateSpeech(script);
  }, [result]);

  // Handle TTS generation
  const handleGenerateSpeech = async (text: string) => {
    if (!text) return;
    
    try {
      console.log('🎙️ Generating speech with MALE voice for:', text.substring(0, 50));
      await generateSpeech(text, 'male'); // Use male voice for Pingala Acharya
      console.log('✅ Speech generation completed');
    } catch (err) {
      console.error('Failed to generate speech:', err);
    }
  };

  // Handle audio playback
  const handlePlayAudio = () => {
    const audio = document.getElementById('pingala-audio') as HTMLAudioElement;
    if (audio) {
      if (isPlaying) {
        audio.pause();
        setIsPlaying(false);
      } else {
        audio.play();
        setIsPlaying(true);
      }
    }
  };

  // Handle replay
  const handleReplay = () => {
    const audio = document.getElementById('pingala-audio') as HTMLAudioElement;
    if (audio) {
      audio.currentTime = 0;
      audio.play();
      setIsPlaying(true);
    } else if (scriptText) {
      // Regenerate if audio not available
      handleGenerateSpeech(scriptText);
    }
  };

  // Handle close with animation
  const handleClose = () => {
    setIsClosing(true);
    setTimeout(() => {
      onClose?.();
    }, 400); // Match animation duration
  };

  // Monitor audio events
  useEffect(() => {
    const audio = document.getElementById('pingala-audio') as HTMLAudioElement;
    if (!audio) return;

    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleEnded = () => setIsPlaying(false);

    audio.addEventListener('play', handlePlay);
    audio.addEventListener('pause', handlePause);
    audio.addEventListener('ended', handleEnded);

    // Auto-play when audio is ready
    if (audioUrl) {
      const playAudio = async () => {
        try {
          // Ensure audio is loaded
          await audio.load();
          // Try to play
          await audio.play();
          console.log('Audio auto-playing successfully');
        } catch (err) {
          console.log('Auto-play prevented by browser:', err);
          // Browser blocked auto-play, user needs to click play
        }
      };
      playAudio();
    }

    return () => {
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('pause', handlePause);
      audio.removeEventListener('ended', handleEnded);
    };
  }, [audioUrl]);

  const details = getResultDetails();
  if (!details) return null;

  return (
    <div className={`pingala-speaker-container ${isClosing ? 'closing' : ''}`}>
      {/* Pingala Image */}
      <div className="pingala-image-container">
        <img
          src="/pingala1.jpeg"
          alt="Pingala Acharya"
          className={`pingala-image ${isPlaying ? 'speaking' : ''}`}
        />
      </div>

      {/* Speech Bubble */}
      <div className="pingala-speech-bubble-container">
        <button
          className="pingala-close-btn"
          onClick={handleClose}
          title="Close"
          aria-label="Close Pingala Acharya"
        >
          <X size={20} />
        </button>

        <div className="pingala-speech-bubble">
          {isLoading && (
            <div className="pingala-loading">
              <span>पिङ्गलाचार्यः वदति...</span>
              <div className="pingala-loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}

          {!isLoading && scriptText && (
            <>
              <p className="pingala-speech-text">{scriptText}</p>

              {/* Controls */}
              <div className="pingala-controls">
                {audioUrl && (
                  <>
                    <button
                      className={`pingala-control-btn ${isPlaying ? 'playing' : ''}`}
                      onClick={handlePlayAudio}
                      title={isPlaying ? 'Pause' : 'Play'}
                    >
                      {isPlaying ? (
                        <>
                          <VolumeX size={16} />
                          <span>रुक्यताम्</span>
                        </>
                      ) : (
                        <>
                          <Volume2 size={16} />
                          <span>श्रूयताम्</span>
                        </>
                      )}
                    </button>

                    <button
                      className="pingala-control-btn"
                      onClick={handleReplay}
                      title="Replay"
                    >
                      <RotateCcw size={16} />
                      <span>पुनः</span>
                    </button>
                  </>
                )}
              </div>

              {/* Hidden audio element */}
              {audioUrl && (
                <div className="pingala-audio-player" style={{ display: 'none' }}>
                  <audio
                    id="pingala-audio"
                    src={audioUrl}
                    preload="auto"
                    autoPlay
                  />
                </div>
              )}

              {error && (
                <p style={{ color: '#ff4444', fontSize: '14px', marginTop: '12px' }}>
                  {error}
                </p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
