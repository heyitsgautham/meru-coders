import { beforeEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { ChatbotService } from '../services/chatbot';
import { ChatBotProvider, useChatBot } from './ChatBotContext';

vi.mock('../services/chatbot', () => {
  const ChatbotService = { sendMessage: vi.fn(), clearConversation: vi.fn(), getHistory: vi.fn() };
  return { ChatbotService, default: ChatbotService };
});

const service = vi.mocked(ChatbotService);
const wrapper = ({ children }: { children: ReactNode }) => <ChatBotProvider>{children}</ChatBotProvider>;

beforeEach(() => {
  vi.resetAllMocks();
  vi.spyOn(console, 'error').mockImplementation(() => {});
  service.getHistory.mockResolvedValue({ success: false });
});

describe('ChatBotProvider', () => {
  it('sends a message and keeps the reply and the new conversation id', async () => {
    service.sendMessage.mockResolvedValue({ success: true, response: 'Anuṣṭubh.', conversation_id: 'c9', confidence: 0.9 });
    const { result } = renderHook(() => useChatBot(), { wrapper });

    await act(() => result.current.sendMessage('Which meter?'));

    expect(result.current.messages.map((m) => [m.role, m.content])).toEqual([
      ['user', 'Which meter?'],
      ['assistant', 'Anuṣṭubh.'],
    ]);
    expect(result.current.conversationId).toBe('c9');
    expect(result.current.confidence).toBe(0.9);
    expect(localStorage.getItem('chatbot_conversation_id')).toBe('c9');
  });

  it('ignores an empty message', async () => {
    const { result } = renderHook(() => useChatBot(), { wrapper });
    await act(() => result.current.sendMessage('   '));
    expect(service.sendMessage).not.toHaveBeenCalled();
  });

  it('turns a failed reply into an apology in the thread', async () => {
    service.sendMessage.mockResolvedValue({ success: false, error: 'quota' });
    const { result } = renderHook(() => useChatBot(), { wrapper });
    await act(() => result.current.sendMessage('hello'));
    expect(result.current.messages.at(-1)?.content).toBe('I apologize, but I encountered an error: quota. Please try again.');
    expect(result.current.isLoading).toBe(false);
  });

  it('greets in the chosen persona until the user speaks', async () => {
    const { result } = renderHook(() => useChatBot(), { wrapper });
    act(() => result.current.setPersona('krishna'));
    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].content).toContain('I am Krishna');
    act(() => result.current.setPersona('default'));
    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].content).toContain('Aacharya Pingala');
    expect(localStorage.getItem('chatbot_persona')).toBe('default');
  });

  it('restores a saved conversation from the server', async () => {
    localStorage.setItem('chatbot_conversation_id', 'saved');
    service.getHistory.mockResolvedValue({ success: true, messages: [{ role: 'user', content: 'earlier', timestamp: 't' }] });
    const { result } = renderHook(() => useChatBot(), { wrapper });
    await waitFor(() => expect(result.current.messages).toHaveLength(1));
    expect(service.getHistory).toHaveBeenCalledWith('saved');
  });

  it('clears the conversation on the server and locally', async () => {
    service.sendMessage.mockResolvedValue({ success: true, response: 'ok', conversation_id: 'c1' });
    service.clearConversation.mockResolvedValue({ success: true });
    const { result } = renderHook(() => useChatBot(), { wrapper });
    await act(() => result.current.sendMessage('hi'));
    await act(() => result.current.clearConversation());
    expect(service.clearConversation).toHaveBeenCalledWith('c1');
    expect(result.current.messages).toEqual([]);
    expect(localStorage.getItem('chatbot_conversation_id')).toBeNull();
  });

  it('opens and closes', () => {
    const { result } = renderHook(() => useChatBot(), { wrapper });
    act(() => result.current.toggleChatbot());
    expect(result.current.isOpen).toBe(true);
  });
});
