import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as community from '../../services/community';
import type { Post } from '../../types/community';
import { EditPostModal } from './EditPostModal';

vi.mock('../../services/community', () => ({ updatePost: vi.fn(), uploadImage: vi.fn() }));

const api = vi.mocked(community);

const POST: Post = {
  id: 'p1',
  user_id: 'u1',
  content: 'Gita 1.1',
  sanskrit_text: 'धर्मक्षेत्रे कुरुक्षेत्रे',
  image_url: '/api/community/uploads/a.png',
  created_at: '2026-10-26T00:00:00Z',
  likes_count: 0,
  comments_count: 0,
};

function renderModal(post = POST) {
  const onClose = vi.fn();
  const onPostUpdated = vi.fn();
  render(<EditPostModal post={post} isOpen onClose={onClose} onPostUpdated={onPostUpdated} />);
  return { onClose, onPostUpdated };
}

const verse = () => screen.getByLabelText(/Sanskrit Text/);
const save = () => userEvent.click(screen.getByRole('button', { name: 'Save Changes' }));

afterEach(() => {
  vi.clearAllMocks();
  vi.restoreAllMocks();
});

describe('EditPostModal', () => {
  it('renders nothing while closed', () => {
    const { container } = render(<EditPostModal post={POST} isOpen={false} onClose={vi.fn()} onPostUpdated={vi.fn()} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('saves the edited text and hands the server copy back', async () => {
    const saved = { ...POST, content: 'Gita 1.1, the opening verse' };
    api.updatePost.mockResolvedValue({ success: true, post: saved } as never);
    const { onClose, onPostUpdated } = renderModal();

    await userEvent.type(screen.getByLabelText('Content'), ', the opening verse');
    await save();

    expect(api.updatePost).toHaveBeenCalledWith('p1', {
      content: 'Gita 1.1, the opening verse',
      sanskrit_text: 'धर्मक्षेत्रे कुरुक्षेत्रे',
      analyze_meter: true,
    });
    expect(onPostUpdated).toHaveBeenCalledWith(saved);
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('sends an empty verse when the author clears it, so the server removes it', async () => {
    api.updatePost.mockResolvedValue({ success: true, post: { ...POST, sanskrit_text: '' } } as never);
    renderModal();

    await userEvent.clear(verse());
    await save();

    expect(api.updatePost.mock.calls[0][1]).toMatchObject({ sanskrit_text: '' });
  });

  it('asks the server to drop a removed image', async () => {
    api.updatePost.mockResolvedValue({ success: true, post: POST } as never);
    renderModal();

    await userEvent.click(screen.getByRole('button', { name: /Remove/ }));
    await save();

    expect(api.updatePost.mock.calls[0][1]).toMatchObject({ image_url: null });
  });

  it('will not save empty content, and shows server errors', async () => {
    api.updatePost.mockResolvedValue({ success: false, error: 'Not your post' } as never);
    renderModal();

    await userEvent.clear(screen.getByLabelText('Content'));
    expect(screen.getByRole('button', { name: 'Save Changes' })).toBeDisabled();

    await userEvent.type(screen.getByLabelText('Content'), 'x');
    await save();
    expect(await screen.findByText('Not your post')).toBeInTheDocument();
  });
});
