import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { ChatbotService } from '../../services/chatbot';
import { ChatBotProvider } from '../../contexts/ChatBotContext';
import FloatingChatbot from './FloatingChatbot';

vi.mock('../../services/chatbot', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../services/chatbot')>();
  const ChatbotService = {
    ...actual.ChatbotService,
    sendMessage: vi.fn(),
    clearConversation: vi.fn(),
    getHistory: vi.fn(),
    fileToBase64: actual.ChatbotService.fileToBase64,
  };
  return { ...actual, ChatbotService, default: ChatbotService };
});

const service = vi.mocked(ChatbotService);

function renderChat() {
  return render(
    <MemoryRouter>
      <ChatBotProvider>
        <FloatingChatbot />
      </ChatBotProvider>
    </MemoryRouter>,
  );
}

async function openChat() {
  const user = userEvent.setup();
  renderChat();
  await user.click(screen.getByRole('button', { name: 'Open AI chatbot' }));
  return user;
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.spyOn(console, 'error').mockImplementation(() => {});
  Element.prototype.scrollIntoView = vi.fn();
  service.getHistory.mockResolvedValue({ success: false });
});

describe('FloatingChatbot', () => {
  it('starts closed and opens from the floating button', async () => {
    await openChat();
    expect(screen.getByRole('button', { name: 'Close chatbot' })).toBeInTheDocument();
  });

  it('sends the typed question with Enter and shows the answer', async () => {
    service.sendMessage.mockResolvedValue({ success: true, response: 'It is an **Anuṣṭubh**.', conversation_id: 'c1' });
    const user = await openChat();
    await user.type(screen.getByRole('textbox'), 'What meter is the Gita in?{Enter}');
    expect(await screen.findByText('What meter is the Gita in?')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('Anuṣṭubh')).toBeInTheDocument());
    expect(service.sendMessage).toHaveBeenCalledWith(expect.objectContaining({ message: 'What meter is the Gita in?' }));
    expect(screen.getByRole('textbox')).toHaveValue('');
  });

  it('does not send an empty message', async () => {
    const user = await openChat();
    await user.click(screen.getByRole('button', { name: 'Send message' }));
    expect(service.sendMessage).not.toHaveBeenCalled();
  });

  it('sends an attached image for OCR with a default prompt', async () => {
    service.sendMessage.mockResolvedValue({ success: true, response: 'Found Gāyatrī.' });
    const user = await openChat();
    const input = document.querySelector('input[type=file]') as HTMLInputElement;
    await user.upload(input, new File(['png'], 'verse.png', { type: 'image/png' }));
    expect(await screen.findByAltText('Selected')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Send message' }));
    await waitFor(() => expect(service.sendMessage).toHaveBeenCalled());
    const request = service.sendMessage.mock.calls[0][0];
    expect(request.message).toBe('Analyse the chanda');
    expect(request.image).toMatch(/^data:image\/png;base64,/);
  });

  it('switches persona and greets as Krishna', async () => {
    const user = await openChat();
    await user.click(screen.getByRole('button', { name: /Krishna/ }));
    expect(screen.getByText(/I am Krishna/)).toBeInTheDocument();
  });

  it('clears the conversation', async () => {
    service.sendMessage.mockResolvedValue({ success: true, response: 'reply', conversation_id: 'c1' });
    service.clearConversation.mockResolvedValue({ success: true });
    const user = await openChat();
    await user.type(screen.getByRole('textbox'), 'hi{Enter}');
    await screen.findByText('reply');
    await user.click(screen.getByRole('button', { name: 'Clear conversation' }));
    expect(screen.queryByText('reply')).not.toBeInTheDocument();
    expect(service.clearConversation).toHaveBeenCalledWith('c1');
  });

  it('toggles fullscreen', async () => {
    const user = await openChat();
    await user.click(screen.getByRole('button', { name: 'Enter fullscreen' }));
    expect(screen.getByRole('button', { name: 'Exit fullscreen' })).toBeInTheDocument();
  });
});
