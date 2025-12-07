/**
 * ChatBot Context
 * Manages global chatbot state, conversation history, and persona switching
 */

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import ChatbotService, { ChatMessage, ChatResponse } from '../services/chatbot';

interface ChatBotContextType {
    messages: ChatMessage[];
    conversationId: string | null;
    persona: 'default' | 'krishna';
    isOpen: boolean;
    isLoading: boolean;
    confidence: number | null;

    sendMessage: (message: string, image?: string, audio?: string) => Promise<void>;
    setPersona: (persona: 'default' | 'krishna') => void;
    toggleChatbot: () => void;
    clearConversation: () => Promise<void>;
    loadHistory: (conversationId: string) => Promise<void>;
}

const ChatBotContext = createContext<ChatBotContextType | undefined>(undefined);

export const useChatBot = () => {
    const context = useContext(ChatBotContext);
    if (!context) {
        throw new Error('useChatBot must be used within ChatBotProvider');
    }
    return context;
};

interface ChatBotProviderProps {
    children: React.ReactNode;
}

export const ChatBotProvider: React.FC<ChatBotProviderProps> = ({ children }) => {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [persona, setPersonaState] = useState<'default' | 'krishna'>('default');
    const [isOpen, setIsOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [confidence, setConfidence] = useState<number | null>(null);

    // Load conversation from localStorage on mount
    useEffect(() => {
        const savedConversationId = localStorage.getItem('chatbot_conversation_id');
        const savedPersona = localStorage.getItem('chatbot_persona') as 'default' | 'krishna' | null;

        if (savedConversationId) {
            setConversationId(savedConversationId);
            loadHistory(savedConversationId);
        }

        if (savedPersona) {
            setPersonaState(savedPersona);
        }
    }, []);

    // Save conversation ID to localStorage
    useEffect(() => {
        if (conversationId) {
            localStorage.setItem('chatbot_conversation_id', conversationId);
        }
    }, [conversationId]);

    // Save persona to localStorage
    useEffect(() => {
        localStorage.setItem('chatbot_persona', persona);
    }, [persona]);

    const sendMessage = useCallback(async (message: string, image?: string, audio?: string) => {
        if (!message.trim() && !image && !audio) return;

        setIsLoading(true);

        // Add user message immediately
        const userMessage: ChatMessage = {
            role: 'user',
            content: message,
            timestamp: new Date().toISOString(),
            has_image: !!image,
            has_audio: !!audio,
            image_data: image,  // Store image data for display
            audio_data: audio   // Store audio data for display
        };

        setMessages(prev => [...prev, userMessage]);

        try {
            const response: ChatResponse = await ChatbotService.sendMessage({
                message,
                conversation_id: conversationId || undefined,
                persona,
                image,
                audio
            });

            if (response.success && response.response) {
                // Update conversation ID if new
                if (response.conversation_id && response.conversation_id !== conversationId) {
                    setConversationId(response.conversation_id);
                }

                // Add assistant message
                const assistantMessage: ChatMessage = {
                    role: 'assistant',
                    content: response.response,
                    timestamp: response.timestamp || new Date().toISOString(),
                    confidence: response.confidence,
                    persona: response.persona,
                    meter_data: response.meter_data,
                    agentic_action: response.agentic_action
                };

                setMessages(prev => [...prev, assistantMessage]);
                setConfidence(response.confidence || null);
            } else {
                throw new Error(response.error || 'Failed to get response');
            }
        } catch (error: any) {
            console.error('Error sending message:', error);

            // Add error message
            const errorMessage: ChatMessage = {
                role: 'assistant',
                content: `I apologize, but I encountered an error: ${error.message}. Please try again.`,
                timestamp: new Date().toISOString(),
                confidence: 0
            };

            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    }, [conversationId, persona]);

    const setPersona = useCallback((newPersona: 'default' | 'krishna') => {
        setPersonaState(newPersona);

        // Only show greeting if no user messages have been sent yet
        setMessages(prev => {
            const hasUserMessages = prev.some(msg => msg.role === 'user');

            if (hasUserMessages) {
                // Middle of conversation - don't show any greeting
                return prev;
            }

            // First message - replace any existing greeting with new persona's greeting
            const greetingMessage: ChatMessage = {
                role: 'assistant',
                content: newPersona === 'krishna'
                    ? '🕉️ Namaste, dear one. I am Krishna, here to guide you through the beauty of Sanskrit prosody.'
                    : '📚 Welcome! I am your Sanskrit Prosody Expert. How may I help you understand Sanskrit meters?',
                timestamp: new Date().toISOString(),
                type: 'system'
            };

            // Remove any existing system messages and add the new greeting
            const filteredMessages = prev.filter(msg => msg.type !== 'system');
            return [...filteredMessages, greetingMessage];
        });
    }, []);

    const toggleChatbot = useCallback(() => {
        setIsOpen(prev => !prev);
    }, []);

    const clearConversation = useCallback(async () => {
        if (conversationId) {
            try {
                await ChatbotService.clearConversation(conversationId);
            } catch (error) {
                console.error('Error clearing conversation:', error);
            }
        }

        setMessages([]);
        setConversationId(null);
        setConfidence(null);
        localStorage.removeItem('chatbot_conversation_id');
    }, [conversationId]);

    const loadHistory = useCallback(async (convId: string) => {
        try {
            const response = await ChatbotService.getHistory(convId);
            if (response.success && response.messages) {
                setMessages(response.messages);
            }
        } catch (error: any) {
            // Silently handle 404 errors (conversation doesn't exist yet)
            if (error?.response?.status !== 404) {
                console.error('Error loading history:', error);
            }
        }
    }, []);

    const value: ChatBotContextType = {
        messages,
        conversationId,
        persona,
        isOpen,
        isLoading,
        confidence,
        sendMessage,
        setPersona,
        toggleChatbot,
        clearConversation,
        loadHistory
    };

    return (
        <ChatBotContext.Provider value={value}>
            {children}
        </ChatBotContext.Provider>
    );
};

export default ChatBotContext;
