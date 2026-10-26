import { beforeEach, describe, expect, it, vi } from 'vitest';
import axios from 'axios';
import { ChatbotService } from './chatbot';

vi.mock('axios', () => ({ default: { post: vi.fn(), get: vi.fn(), delete: vi.fn() } }));

const http = vi.mocked(axios);
const BASE = 'http://localhost:5000/api/chatbot';

beforeEach(() => {
  vi.resetAllMocks();
  vi.spyOn(console, 'error').mockImplementation(() => {});
  vi.spyOn(console, 'log').mockImplementation(() => {});
});

describe('ChatbotService', () => {
  it('posts a chat message', async () => {
    http.post.mockResolvedValue({ data: { success: true, response: 'hi' } });
    expect(await ChatbotService.sendMessage({ message: 'hello' })).toEqual({ success: true, response: 'hi' });
    expect(http.post).toHaveBeenCalledWith(`${BASE}/chat`, { message: 'hello' });
  });

  it('returns the server error instead of throwing', async () => {
    http.post.mockRejectedValue({ response: { data: { error: 'Rate limited' } } });
    expect(await ChatbotService.sendMessage({ message: 'hello' })).toEqual({ success: false, error: 'Rate limited' });
  });

  it.each([
    ['getHistory', () => ChatbotService.getHistory('c1'), 'get', `${BASE}/history/c1`],
    ['listConversations', () => ChatbotService.listConversations(), 'get', `${BASE}/conversations`],
    ['clearConversation', () => ChatbotService.clearConversation('c1'), 'delete', `${BASE}/clear/c1`],
    ['getPersonas', () => ChatbotService.getPersonas(), 'get', `${BASE}/personas`],
    ['healthCheck', () => ChatbotService.healthCheck(), 'get', `${BASE}/health`],
  ] as const)('%s calls its route', async (_name, call, method, url) => {
    http[method].mockResolvedValue({ data: { success: true } });
    expect(await call()).toEqual({ success: true });
    expect(http[method]).toHaveBeenCalledWith(url);
  });

  it('reports a missing history without logging it as an error', async () => {
    http.get.mockRejectedValue({ response: { status: 404, data: { error: 'Not found' } } });
    expect(await ChatbotService.getHistory('new')).toEqual({ success: false, error: 'Not found' });
    expect(console.error).not.toHaveBeenCalled();
  });

  it('posts a meter analysis request', async () => {
    http.post.mockResolvedValue({ data: { success: true, meter: 'गायत्री' } });
    expect((await ChatbotService.analyzeMeter({ text: 'अग्निमीळे' })).meter).toBe('गायत्री');
    expect(http.post).toHaveBeenCalledWith(`${BASE}/analyze-meter`, { text: 'अग्निमीळे' });
  });

  it('reads a file as a data URL', async () => {
    const data = await ChatbotService.fileToBase64(new File(['hi'], 'a.txt', { type: 'text/plain' }));
    expect(data).toMatch(/^data:text\/plain;base64,/);
  });
});
