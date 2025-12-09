/**
 * Chatbot Service
 * Handles communication with the Gemini-powered multi-modal chatbot backend
 */

import axios from 'axios';
import { getAPIURL } from './api';

// Computed at request time, not module load time
const getChatbotAPI = () => `${getAPIURL()}/chatbot`;

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    confidence?: number;
    has_image?: boolean;
    has_audio?: boolean;
    image_data?: string; // base64 image data for display
    audio_data?: string; // base64 audio data for display
    ocr_text?: string;   // extracted OCR text
    persona?: string;
    meter_data?: MeterData;
    agentic_action?: string;
    type?: string;
    response_source?: 'rag' | 'ai'; // NEW: response source type
    rag_docs_used?: number; // NEW: number of RAG sources used
}

export interface MeterData {
    success: boolean;
    text: string;
    meter: string;
    meter_display: string;
    lg_pattern: string;
    gana_pattern: string;
    syllables: number;
    matra: number;
    syllable_breakdown: string[];
    found: boolean;
    fuzzy_matches: Array<[string, number]>;
}

export interface ChatRequest {
    message: string;
    conversation_id?: string;
    persona?: 'default' | 'krishna';
    image?: string; // base64 encoded
    audio?: string; // base64 encoded
}

export interface ChatResponse {
    success: boolean;
    response?: string;
    confidence?: number;
    conversation_id?: string;
    persona?: string;
    timestamp?: string;
    agentic_action?: string;
    meter_data?: MeterData;
    error?: string;
    response_source?: 'rag' | 'ai'; // NEW: response source type
    rag_docs_used?: number; // NEW: number of RAG sources used
}

export interface Conversation {
    id: string;
    message_count: number;
    last_updated: string | null;
}

export interface MeterAnalysisRequest {
    text: string;
    conversation_id?: string;
    persona?: 'default' | 'krishna';
}

export interface MeterAnalysisResponse {
    success: boolean;
    meter?: string;
    lg_pattern?: string;
    syllables?: number;
    matra?: number;
    explanation?: string;
    confidence?: number;
    conversation_id?: string;
    full_analysis?: any;
    error?: string;
}

export interface Persona {
    name: string;
    description: string;
}

export class ChatbotService {
    /**
     * Send a message to the chatbot
     */
    static async sendMessage(request: ChatRequest): Promise<ChatResponse> {
        try {
            const response = await axios.post(`${getChatbotAPI()}/chat`, request);
            return response.data;
        } catch (error: any) {
            console.error('Error sending message:', error);
            return {
                success: false,
                error: error.response?.data?.error || error.message || 'Failed to send message'
            };
        }
    }

    /**
     * Get conversation history
     */
    static async getHistory(conversationId: string): Promise<{ success: boolean; messages?: ChatMessage[]; error?: string }> {
        try {
            const response = await axios.get(`${getChatbotAPI()}/history/${conversationId}`);
            return response.data;
        } catch (error: any) {
            // Don't log 404 errors - they're expected for new conversations
            if (error?.response?.status !== 404) {
                console.error('Error fetching history:', error);
            }
            return {
                success: false,
                error: error.response?.data?.error || error.message || 'Failed to fetch history'
            };
        }
    }

    /**
     * List all conversations
     */
    static async listConversations(): Promise<{ success: boolean; conversations?: Conversation[]; error?: string }> {
        try {
            const response = await axios.get(`${getChatbotAPI()}/conversations`);
            return response.data;
        } catch (error: any) {
            console.error('Error listing conversations:', error);
            return {
                success: false,
                error: error.response?.data?.error || error.message || 'Failed to list conversations'
            };
        }
    }

    /**
     * Clear a conversation
     */
    static async clearConversation(conversationId: string): Promise<{ success: boolean; error?: string }> {
        try {
            const response = await axios.delete(`${getChatbotAPI()}/clear/${conversationId}`);
            return response.data;
        } catch (error: any) {
            console.error('Error clearing conversation:', error);
            return {
                success: false,
                error: error.response?.data?.error || error.message || 'Failed to clear conversation'
            };
        }
    }

    /**
     * Get available personas
     */
    static async getPersonas(): Promise<{ success: boolean; personas?: Record<string, Persona>; error?: string }> {
        try {
            const response = await axios.get(`${getChatbotAPI()}/personas`);
            return response.data;
        } catch (error: any) {
            console.error('Error fetching personas:', error);
            return {
                success: false,
                error: error.response?.data?.error || error.message || 'Failed to fetch personas'
            };
        }
    }

    /**
     * Analyze meter with AI explanation
     */
    static async analyzeMeter(request: MeterAnalysisRequest): Promise<MeterAnalysisResponse> {
        try {
            const response = await axios.post(`${getChatbotAPI()}/analyze-meter`, request);
            return response.data;
        } catch (error: any) {
            console.error('Error analyzing meter:', error);
            return {
                success: false,
                error: error.response?.data?.error || error.message || 'Failed to analyze meter'
            };
        }
    }

    /**
     * Convert image file to base64
     */
    static async fileToBase64(file: File): Promise<string> {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                const base64 = reader.result as string;
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }

    /**
     * Convert audio blob to base64
     */
    static async audioToBase64(blob: Blob): Promise<string> {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                const base64 = reader.result as string;
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }

    /**
     * Check chatbot health
     */
    static async healthCheck(): Promise<{ success: boolean; status?: string; error?: string }> {
        try {
            const response = await axios.get(`${getChatbotAPI()}/health`);
            return response.data;
        } catch (error: any) {
            console.error('Error checking health:', error);
            return {
                success: false,
                error: error.response?.data?.error || error.message || 'Health check failed'
            };
        }
    }
}

export default ChatbotService;
