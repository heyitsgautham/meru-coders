/**
 * Floating Chatbot Component
 * A multi-modal AI chatbot with persona switching using assistant-ui
 */

import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, Mic, Image as ImageIcon, Trash2, Sparkles, X, Send, Maximize2, Minimize2 } from 'lucide-react';
import { useChatBot } from '../../contexts/ChatBotContext';
import ReactMarkdown from 'react-markdown';
import { createAudioRecorder } from '../../utils/audioUtils';
import './FloatingChatbot.css';

const FloatingChatbot: React.FC = () => {
  const {
    messages,
    persona,
    isOpen,
    isLoading,
    confidence,
    sendMessage,
    setPersona,
    toggleChatbot,
    clearConversation
  } = useChatBot();

  const [inputMessage, setInputMessage] = useState('');
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const audioRecorderRef = useRef<ReturnType<typeof createAudioRecorder> | null>(null);
  const shouldAutoScrollRef = useRef(true);

  // Auto-scroll to bottom only when user sends a message, not during AI response
  useEffect(() => {
    // Only auto-scroll if the last message is from the user
    if (messages.length > 0 && shouldAutoScrollRef.current) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.role === 'user') {
        // User just sent a message - scroll to bottom
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }
      // Don't auto-scroll for assistant messages - let user read from top
    }
  }, [messages]);

  // Cleanup audio URL on unmount or when audio changes
  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  const handleSendMessage = async () => {
    // Auto-add a default prompt if image is selected but no message
    const messageToSend = inputMessage.trim() ||
      (selectedImage ? 'Analyse the chanda' : '');

    if (!messageToSend && !selectedImage && !audioFile) return;

    let imageBase64: string | undefined;
    let audioBase64: string | undefined;

    // Convert image to base64
    if (selectedImage) {
      imageBase64 = await fileToBase64(selectedImage);
    }

    // Convert audio to base64
    if (audioFile) {
      audioBase64 = await fileToBase64(audioFile);
    }

    // Reset input IMMEDIATELY to clear preview
    setInputMessage('');
    setSelectedImage(null);
    setImagePreview(null);
    // Revoke audio URL to free memory
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    setAudioFile(null);

    // Send message after clearing UI
    await sendMessage(messageToSend, imageBase64, audioBase64);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedImage(file);
      const reader = new FileReader();
      reader.onload = (event) => {
        setImagePreview(event.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleStartRecording = async () => {
    try {
      audioRecorderRef.current = createAudioRecorder();
      await audioRecorderRef.current.start();
      setIsRecording(true);
      console.log('Chatbot recording started - will save as WAV');
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Failed to access microphone. Please check permissions.');
      audioRecorderRef.current = null;
    }
  };

  const handleStopRecording = async () => {
    try {
      if (audioRecorderRef.current && isRecording) {
        console.log('Chatbot stopping recording and converting to WAV...');
        const wavFile = await audioRecorderRef.current.stop();
        if (wavFile) {
          console.log('Chatbot WAV file created:', wavFile.name, wavFile.size, 'bytes');
          // Revoke old URL if exists
          if (audioUrl) {
            URL.revokeObjectURL(audioUrl);
          }
          // Create new URL for playback
          const url = URL.createObjectURL(wavFile);
          setAudioUrl(url);
          setAudioFile(wavFile);
        }
        audioRecorderRef.current = null;
        setIsRecording(false);
      }
    } catch (error) {
      console.error('Error stopping recording:', error);
      alert('Failed to stop recording. Please try again.');
      audioRecorderRef.current = null;
      setIsRecording(false);
    }
  };

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  if (!isOpen) {
    return (
      <button
        onClick={toggleChatbot}
        className="chatbot-fab"
        aria-label="Open AI chatbot"
        title="Ask AI about Sanskrit prosody"
      >
        <MessageCircle size={28} strokeWidth={2.5} />
      </button>
    );
  }

  return (
    <div className={`chatbot-container ${isFullscreen ? 'chatbot-fullscreen' : ''}`}>
      {/* Header */}
      <div className="chatbot-header">
        <div className="chatbot-header-content">
          <div className="chatbot-persona-icon">
            {persona === 'krishna' ? '🕉️' : '📚'}
          </div>
          <div className="chatbot-header-text">
            <h3 className="chatbot-title">
              {persona === 'krishna' ? 'Krishna' : 'Chandas Expert'}
            </h3>
            <p className="chatbot-subtitle">Multi-modal AI Assistant</p>
          </div>
        </div>
        <div className="chatbot-header-actions">
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="chatbot-action-btn"
            aria-label={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
            title={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
          >
            {isFullscreen ? <Minimize2 size={20} /> : <Maximize2 size={20} />}
          </button>
          <button
            onClick={toggleChatbot}
            className="chatbot-action-btn"
            aria-label="Close chatbot"
          >
            <X size={20} />
          </button>
        </div>
      </div>

      {/* Persona Switcher */}
      <div className="chatbot-persona-switcher">
        <button
          onClick={() => setPersona('default')}
          className={`persona-btn ${persona === 'default' ? 'active' : ''}`}
        >
          <span className="persona-icon">📚</span>
          <span>Expert</span>
        </button>
        <button
          onClick={() => setPersona('krishna')}
          className={`persona-btn ${persona === 'krishna' ? 'active' : ''}`}
        >
          <span className="persona-icon">🕉️</span>
          <span>Krishna</span>
        </button>
        <button
          onClick={clearConversation}
          className="clear-btn"
          aria-label="Clear conversation"
          title="Clear conversation"
        >
          <Trash2 size={16} />
        </button>
      </div>

      {/* Messages */}
      <div className="chatbot-messages">
        {messages.length === 0 && (
          <div className="chatbot-empty-state">
            <Sparkles className="empty-icon" size={48} />
            <p className="empty-title">Ask me anything about Sanskrit prosody!</p>
            <p className="empty-subtitle">Supports text, images, and voice input</p>
          </div>
        )}

        {messages.map((msg, index) => (
          <div
            key={index}
            className={`message ${msg.role === 'user' ? 'message-user' : 'message-assistant'}`}
          >
            <div className="message-content">
              {/* Display Image if Available (for user messages) */}
              {msg.role === 'user' && msg.image_data && (
                <div className="message-image-container">
                  <img
                    src={msg.image_data}
                    alt="Uploaded content"
                    className="message-image"
                  />
                  {msg.ocr_text && (
                    <div className="ocr-text-badge">
                      📄 OCR Extracted
                    </div>
                  )}
                </div>
              )}

              <div className="markdown-content">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>

              {msg.confidence !== undefined && msg.confidence !== null && (
                <div className="message-confidence">
                  Confidence: {(msg.confidence * 100).toFixed(0)}%
                  {msg.agentic_action && (
                    <span className="agentic-badge" title="Powered by Chandas Algorithm">
                      🤖 Agentic
                    </span>
                  )}
                </div>
              )}

              <div className="message-timestamp">
                {new Date(msg.timestamp).toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message message-assistant">
            <div className="message-content loading-indicator">
              <div className="typing-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Image Preview */}
      {imagePreview && (
        <div className="image-preview-container">
          <div className="image-preview-hint">
            📷 Image will be processed with OCR - Press Send to analyze
          </div>
          <img src={imagePreview} alt="Selected" className="image-preview" />
          <button
            onClick={() => {
              setSelectedImage(null);
              setImagePreview(null);
            }}
            className="image-preview-close"
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Audio Recording Indicator */}
      {audioFile && (
        <div className="audio-indicator" style={{ flexDirection: 'column', gap: '8px', alignItems: 'stretch' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Mic size={16} className="audio-icon" />
              <span>Audio recorded ({audioFile.name})</span>
            </div>
            <button
              onClick={() => {
                if (audioUrl) {
                  URL.revokeObjectURL(audioUrl);
                  setAudioUrl(null);
                }
                setAudioFile(null);
              }}
              className="audio-remove"
            >
              <X size={16} />
            </button>
          </div>
          {audioUrl && (
            <audio
              controls
              src={audioUrl}
              style={{
                width: '100%',
                height: '32px',
                borderRadius: '4px'
              }}
            >
              Your browser does not support the audio element.
            </audio>
          )}
        </div>
      )}

      {/* Input */}
      <div className="chatbot-input-container">
        <div className="chatbot-input-wrapper">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleImageSelect}
            accept="image/*"
            className="hidden"
          />

          <div className="input-icons-stack">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="input-action-btn"
              aria-label="Upload image"
              title="Upload image"
            >
              <ImageIcon size={20} />
            </button>

            <button
              onClick={isRecording ? handleStopRecording : handleStartRecording}
              className={`input-action-btn ${isRecording ? 'recording' : ''}`}
              aria-label={isRecording ? 'Stop recording' : 'Start recording'}
              title={isRecording ? 'Stop recording' : 'Start voice recording'}
            >
              <Mic size={20} />
            </button>
          </div>

          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              selectedImage
                ? "Optional: Add a question (default: 'Analyse the chanda')"
                : "Ask about chandas, meters, or upload an image..."
            }
            className="chatbot-textarea"
            rows={3}
            disabled={isLoading}
          />

          <button
            onClick={handleSendMessage}
            disabled={isLoading}
            className="send-btn"
            aria-label="Send message"
            title={selectedImage && !inputMessage.trim() ? "Will extract text via OCR and analyze chanda" : "Send message"}
          >
            <Send size={20} />
          </button>
        </div>

        {confidence !== null && (
          <div className="last-confidence">
            Last response confidence: {(confidence * 100).toFixed(0)}%
          </div>
        )}
      </div>
    </div>
  );
};

export default FloatingChatbot;
