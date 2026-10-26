import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import * as community from '../../services/community';
import { PostView } from './PostView';

vi.mock('../../contexts/AuthContext', () => ({ useAuth: () => ({ user: { id: 'u1', username: 'gk' }, isAdmin: false }) }));
vi.mock('../../services/community', async importOriginal => ({
  ...(await importOriginal<typeof import('../../services/community')>()),
  getPost: vi.fn(),
  deletePost: vi.fn(),
}));

const api = vi.mocked(community);
const POST = {
  id: 'p1',
  user_id: 'u1',
  content: 'My verse about anushtubh',
  created_at: new Date().toISOString(),
  likes_count: 0,
  comments_count: 0,
  users: { id: 'u1', username: 'gk' },
};

function renderPost() {
  render(
    <MemoryRouter initialEntries={['/community/post/p1']}>
      <Routes>
        <Route path="/community/post/:postId" element={<PostView />} />
        <Route path="/community" element={<p>community feed</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

afterEach(() => vi.clearAllMocks());

describe('PostView', () => {
  it('shows the post from the link', async () => {
    api.getPost.mockResolvedValue({ success: true, post: POST } as never);
    renderPost();
    expect(await screen.findByText('My verse about anushtubh')).toBeInTheDocument();
    expect(api.getPost).toHaveBeenCalledWith('p1');
  });

  it('returns to the feed once the author deletes the post', async () => {
    api.getPost.mockResolvedValue({ success: true, post: POST } as never);
    api.deletePost.mockResolvedValue({ success: true } as never);
    renderPost();
    await screen.findByText('My verse about anushtubh');

    await userEvent.click(document.querySelector('.post-menu-btn')!);
    await userEvent.click(await screen.findByRole('menuitem', { name: 'Delete Post' }));
    await userEvent.click(await screen.findByRole('button', { name: 'Delete' }));

    expect(api.deletePost).toHaveBeenCalledWith('p1');
    expect(await screen.findByText('community feed')).toBeInTheDocument();
  });

  it('says when the post is gone', async () => {
    api.getPost.mockResolvedValue({ success: false, error: 'Post not found' } as never);
    renderPost();
    expect(await screen.findByText('Post not found')).toBeInTheDocument();
  });
});
