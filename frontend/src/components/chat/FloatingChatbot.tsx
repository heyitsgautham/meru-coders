/**
 * Floating Chatbot Component
 * A multi-modal AI chatbot with persona switching using assistant-ui
 */

import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, Mic, Image as ImageIcon, Trash2, Sparkles, X, Send } from 'lucide-react';
import { useChatBot } from '../../contexts/ChatBotContext';
import ReactMarkdown from 'react-markdown';
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
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
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

  const handleSendMessage = async () => {
    // Auto-add a default prompt if image is selected but no message
    const messageToSend = inputMessage.trim() ||
      (selectedImage ? 'Analyse the chanda' : '');

    if (!messageToSend && !selectedImage && !audioBlob) return;

    let imageBase64: string | undefined;
    let audioBase64: string | undefined;

    // Convert image to base64
    if (selectedImage) {
      imageBase64 = await fileToBase64(selectedImage);
    }

    // Convert audio to base64
    if (audioBlob) {
      audioBase64 = await blobToBase64(audioBlob);
    }

    // Reset input IMMEDIATELY to clear preview
    setInputMessage('');
    setSelectedImage(null);
    setImagePreview(null);
    setAudioBlob(null);

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
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Determine the best supported MIME type for audio recording
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
          console.log('Using MIME type:', mimeType);
          break;
        }
      }

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: selectedMimeType
      });
      mediaRecorderRef.current = mediaRecorder;

      const chunks: Blob[] = [];
      mediaRecorder.ondataavailable = (e) => {
        chunks.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: selectedMimeType });
        setAudioBlob(blob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Failed to access microphone. Please check permissions.');
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
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

  const blobToBase64 = (blob: Blob): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
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
    <div className="chatbot-container">
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
        <button
          onClick={toggleChatbot}
          className="chatbot-close-btn"
          aria-label="Close chatbot"
        >
          <X size={20} />
        </button>
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
      {audioBlob && (
        <div className="audio-indicator">
          <Mic size={16} className="audio-icon" />
          <span>Audio recorded</span>
          <button onClick={() => setAudioBlob(null)} className="audio-remove">
            <X size={16} />
          </button>
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
