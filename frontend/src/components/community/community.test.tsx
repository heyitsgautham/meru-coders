import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';
import * as community from '../../services/community';
import type { Comment, Post } from '../../types/community';
import { CommentSection } from './CommentSection';
import { CreatePost } from './CreatePost';
import { PostCard } from './PostCard';
import { PostFeed } from './PostFeed';
import { ReportModal } from './ReportModal';
import { SearchBar } from './SearchBar';

const auth = vi.hoisted(() => ({ user: null as null | { id: string; username: string } }));

vi.mock('../../contexts/AuthContext', () => ({ useAuth: () => ({ user: auth.user }) }));

vi.mock('../../services/community', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../services/community')>();
  const stub = () => vi.fn().mockResolvedValue({ success: true });
  return {
    ...actual,
    addComment: stub(),
    createPost: stub(),
    deleteComment: stub(),
    getComments: vi.fn().mockResolvedValue({ success: true, comments: [] }),
    getFollowingFeed: stub(),
    getPosts: stub(),
    reportContent: stub(),
    searchPosts: stub(),
    searchUsers: stub(),
    toggleBookmark: stub(),
    toggleLike: stub(),
    uploadImage: stub(),
  };
});

const api = vi.mocked(community);

function makePost(overrides: Partial<Post> = {}): Post {
  return {
    id: 'p1',
    user_id: 'u2',
    content: 'Gita 1.1 is in anushtubh',
    created_at: new Date().toISOString(),
    likes_count: 2,
    comments_count: 1,
    users: { id: 'u2', username: 'pingala' } as Post['users'],
    ...overrides,
  };
}

function makeComment(overrides: Partial<Comment> = {}): Comment {
  return {
    id: 'c1',
    post_id: 'p1',
    user_id: 'u1',
    content: 'Eight syllables per pada',
    created_at: new Date().toISOString(),
    users: { id: 'u1', username: 'gk' } as Comment['users'],
    ...overrides,
  };
}

function Location() {
  return <output data-testid="location">{useLocation().pathname}</output>;
}

function renderAt(ui: ReactNode) {
  return render(
    <MemoryRouter initialEntries={['/community']}>
      <Routes>
        <Route path="*" element={<>{ui}<Location /></>} />
      </Routes>
    </MemoryRouter>,
  );
}

const location = () => screen.getByTestId('location').textContent;

beforeEach(() => {
  auth.user = { id: 'u1', username: 'gk' };
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
  vi.clearAllMocks();
  vi.restoreAllMocks();
});

describe('PostCard', () => {
  it('opens the post page when the card is clicked', async () => {
    renderAt(<PostCard post={makePost()} />);
    await userEvent.click(screen.getByText('Gita 1.1 is in anushtubh'));
    expect(location()).toBe('/community/post/p1');
  });

  it('opens the author profile from the name', async () => {
    renderAt(<PostCard post={makePost()} />);
    await userEvent.click(screen.getByText('pingala'));
    expect(location()).toBe('/community/user/u2');
  });

  it('stays on the feed while the reader types a comment', async () => {
    renderAt(<PostCard post={makePost()} />);
    await userEvent.click(document.querySelector('.action-btn.comment')!);
    const box = await screen.findByPlaceholderText('Write a comment...');

    await userEvent.click(box);
    await userEvent.type(box, 'Well put');

    expect(location()).toBe('/community');
    expect(box).toHaveValue('Well put');
  });

  it('counts a like at once and keeps the server answer', async () => {
    api.toggleLike.mockResolvedValue({ success: true, liked: true } as never);
    renderAt(<PostCard post={makePost()} />);
    const like = document.querySelector('.action-btn.like')!;

    await userEvent.click(like);

    expect(like).toHaveTextContent('3');
    expect(like).toHaveClass('active');
    expect(location()).toBe('/community');
  });

  it('undoes the like when the server refuses it', async () => {
    api.toggleLike.mockResolvedValue({ success: false } as never);
    renderAt(<PostCard post={makePost()} />);
    const like = document.querySelector('.action-btn.like')!;

    await userEvent.click(like);

    await waitFor(() => expect(like).toHaveTextContent('2'));
    expect(like).not.toHaveClass('active');
  });

  it('ignores likes and bookmarks from signed-out readers', async () => {
    auth.user = null;
    renderAt(<PostCard post={makePost()} />);
    await userEvent.click(document.querySelector('.action-btn.like')!);
    await userEvent.click(document.querySelector('.action-btn.bookmark')!);
    expect(api.toggleLike).not.toHaveBeenCalled();
    expect(api.toggleBookmark).not.toHaveBeenCalled();
  });

  it('rolls the bookmark back when the request fails', async () => {
    api.toggleBookmark.mockRejectedValue(new Error('offline'));
    renderAt(<PostCard post={makePost()} />);
    const bookmark = document.querySelector('.action-btn.bookmark')!;
    await userEvent.click(bookmark);
    await waitFor(() => expect(bookmark).not.toHaveClass('active'));
  });

  it('shows the meter found in the attached verse', () => {
    renderAt(
      <PostCard
        post={makePost({
          sanskrit_text: 'धर्मक्षेत्रे कुरुक्षेत्रे',
          meter_analysis: { found: true, meter_name: 'अनुष्टुभ्', syllable_count: 32 } as Post['meter_analysis'],
        })}
      />,
    );
    expect(screen.getByText('धर्मक्षेत्रे कुरुक्षेत्रे')).toBeInTheDocument();
    expect(screen.getByText('अनुष्टुभ्')).toBeInTheDocument();
    expect(screen.getByText('32 syllables')).toBeInTheDocument();
  });
});

describe('CreatePost', () => {
  it('asks signed-out readers to sign in', () => {
    auth.user = null;
    render(<CreatePost />);
    expect(screen.getByRole('link', { name: 'Sign in' })).toHaveAttribute('href', '/login');
  });

  it('posts the text and verse, then clears the form', async () => {
    const created = makePost({ id: 'p9' });
    api.createPost.mockResolvedValue({ success: true, post: created } as never);
    const onPostCreated = vi.fn();
    render(<CreatePost onPostCreated={onPostCreated} />);
    const box = screen.getByPlaceholderText(/What's on your mind/);
    expect(screen.getByRole('button', { name: 'Post' })).toBeDisabled();

    await userEvent.type(box, '  My first verse  ');
    await userEvent.click(screen.getByRole('button', { name: 'Add Sanskrit' }));
    await userEvent.type(screen.getByPlaceholderText(/श्लोकं लिखतु/), 'रामो राजमणिः');
    await userEvent.click(screen.getByRole('button', { name: 'Post' }));

    expect(api.createPost).toHaveBeenCalledWith({
      content: 'My first verse',
      sanskrit_text: 'रामो राजमणिः',
      analyze_meter: true,
      image_url: undefined,
    });
    expect(onPostCreated).toHaveBeenCalledWith(created);
    expect(box).toHaveValue('');
  });

  it('shows the server error and keeps the draft', async () => {
    api.createPost.mockResolvedValue({ success: false, error: 'Content is too long' } as never);
    render(<CreatePost />);
    const box = screen.getByPlaceholderText(/What's on your mind/);
    await userEvent.type(box, 'draft');
    await userEvent.click(screen.getByRole('button', { name: 'Post' }));
    expect(await screen.findByText('Content is too long')).toBeInTheDocument();
    expect(box).toHaveValue('draft');
  });

  it('uploads the image before posting and stops when the upload fails', async () => {
    vi.stubGlobal('URL', Object.assign(URL, { createObjectURL: () => 'blob:x', revokeObjectURL: () => {} }));
    api.uploadImage.mockResolvedValue({ success: false, error: 'Too large' });
    const { container } = render(<CreatePost />);
    await userEvent.type(screen.getByPlaceholderText(/What's on your mind/), 'with a picture');
    await userEvent.upload(
      container.querySelector('input[type=file]') as HTMLInputElement,
      new File(['x'], 'a.png', { type: 'image/png' }),
    );

    await userEvent.click(screen.getByRole('button', { name: 'Post' }));

    expect(await screen.findByText('Too large')).toBeInTheDocument();
    expect(api.createPost).not.toHaveBeenCalled();
    vi.unstubAllGlobals();
  });
});

describe('CommentSection', () => {
  it('lists only top-level comments', async () => {
    api.getComments.mockResolvedValue({
      success: true,
      comments: [makeComment(), makeComment({ id: 'c2', parent_id: 'c1', content: 'A reply' })],
    } as never);
    render(<CommentSection postId="p1" />);
    expect(await screen.findByText('Eight syllables per pada')).toBeInTheDocument();
    expect(screen.queryByText('A reply')).not.toBeInTheDocument();
  });

  it('adds a comment and reports it to the card', async () => {
    api.addComment.mockResolvedValue({ success: true, comment: makeComment({ id: 'c5', content: 'नमः' }) } as never);
    const onCommentAdded = vi.fn();
    render(<CommentSection postId="p1" onCommentAdded={onCommentAdded} />);
    const box = await screen.findByPlaceholderText('Write a comment...');

    await userEvent.type(box, ' नमः {Enter}');

    expect(api.addComment).toHaveBeenCalledWith('p1', { content: 'नमः' });
    expect(await screen.findByText('नमः')).toBeInTheDocument();
    expect(onCommentAdded).toHaveBeenCalledOnce();
    expect(box).toHaveValue('');
  });

  it('lets the author delete their own comment', async () => {
    api.getComments.mockResolvedValue({ success: true, comments: [makeComment()] } as never);
    const onCommentDeleted = vi.fn();
    const { container } = render(<CommentSection postId="p1" onCommentDeleted={onCommentDeleted} />);
    await screen.findByText('Eight syllables per pada');

    await userEvent.click(container.querySelector('.comment-item-delete')!);

    expect(api.deleteComment).toHaveBeenCalledWith('c1');
    await waitFor(() => expect(screen.queryByText('Eight syllables per pada')).not.toBeInTheDocument());
    expect(onCommentDeleted).toHaveBeenCalledOnce();
  });

  it('hides the box and the delete button from signed-out readers', async () => {
    auth.user = null;
    api.getComments.mockResolvedValue({ success: true, comments: [makeComment()] } as never);
    const { container } = render(<CommentSection postId="p1" />);
    await screen.findByText('Eight syllables per pada');
    expect(screen.queryByPlaceholderText('Write a comment...')).not.toBeInTheDocument();
    expect(container.querySelector('.comment-item-delete')).toBeNull();
  });
});

describe('ReportModal', () => {
  it('renders nothing while closed', () => {
    const { container } = render(<ReportModal isOpen={false} onClose={vi.fn()} type="post" />);
    expect(container).toBeEmptyDOMElement();
  });

  it('sends the reason with the reported post, then closes', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const onClose = vi.fn();
    render(<ReportModal isOpen onClose={onClose} postId="p1" type="post" />);
    expect(screen.getByRole('heading', { name: 'Report Post' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Submit Report' })).toBeDisabled();

    await userEvent.click(screen.getByLabelText('Spam or misleading'));
    await userEvent.type(screen.getByPlaceholderText(/additional context/), ' bot account ');
    await userEvent.click(screen.getByRole('button', { name: 'Submit Report' }));

    expect(api.reportContent).toHaveBeenCalledWith({
      reason: 'spam',
      description: 'bot account',
      post_id: 'p1',
      comment_id: undefined,
      user_id: undefined,
    });
    expect(await screen.findByText(/Thank you for helping/)).toBeInTheDocument();
    await act(() => vi.advanceTimersByTimeAsync(2000));
    expect(onClose).toHaveBeenCalledOnce();
    vi.useRealTimers();
  });

  it('shows the failure and stays open', async () => {
    api.reportContent.mockRejectedValue(new Error('offline'));
    const onClose = vi.fn();
    render(<ReportModal isOpen onClose={onClose} commentId="c1" type="comment" />);
    await userEvent.click(screen.getByLabelText('Other'));
    await userEvent.click(screen.getByRole('button', { name: 'Submit Report' }));
    expect(await screen.findByText('Failed to submit report. Please try again.')).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();
  });
});

describe('SearchBar', () => {
  it('lists users before posts and opens the picked result', async () => {
    api.searchUsers.mockResolvedValue({ success: true, users: [{ id: 'u7', username: 'kalidasa' }] } as never);
    api.searchPosts.mockResolvedValue({ success: true, posts: [makePost({ id: 'p3', content: 'Meghaduta uses mandakranta' })] } as never);
    renderAt(<SearchBar />);

    await userEvent.type(screen.getByPlaceholderText('Search posts or users...'), 'kali');

    const names = await screen.findAllByText(/kalidasa|Meghaduta/);
    expect(names.map(n => n.textContent)).toEqual(['kalidasa', 'Meghaduta uses mandakranta']);
    expect(api.searchUsers).toHaveBeenCalledTimes(1);
    expect(api.searchPosts).toHaveBeenCalledWith('kali', { limit: 5 });

    await userEvent.click(screen.getByText('Meghaduta uses mandakranta'));
    expect(location()).toBe('/community/post/p3');
  });

  it('says when nothing matches', async () => {
    renderAt(<SearchBar />);
    await userEvent.type(screen.getByPlaceholderText('Search posts or users...'), 'zzz');
    expect(await screen.findByText('No results found for "zzz"')).toBeInTheDocument();
  });
});

describe('PostFeed', () => {
  const page = (n: number, from = 0) => Array.from({ length: n }, (_, i) => makePost({ id: `p${from + i}`, content: `post ${from + i}` }));

  it('loads the next page from the current offset', async () => {
    api.getPosts.mockResolvedValueOnce({ success: true, posts: page(20) } as never);
    api.getPosts.mockResolvedValueOnce({ success: true, posts: page(3, 20) } as never);
    renderAt(<PostFeed userId="u2" />);

    await userEvent.click(await screen.findByRole('button', { name: 'Show more' }));

    expect(api.getPosts).toHaveBeenLastCalledWith({ limit: 20, offset: 20, user_id: 'u2' });
    expect(await screen.findByText('post 22')).toBeInTheDocument();
    expect(screen.getByText("You've reached the end")).toBeInTheDocument();
  });

  it('reads the following feed for that filter', async () => {
    api.getFollowingFeed.mockResolvedValue({ success: true, posts: [] } as never);
    renderAt(<PostFeed filter="following" />);
    expect(await screen.findByText('No posts yet')).toBeInTheDocument();
    expect(api.getPosts).not.toHaveBeenCalled();
  });

  it('offers a retry after a failed load', async () => {
    api.getPosts.mockRejectedValueOnce(new Error('Network down'));
    api.getPosts.mockResolvedValueOnce({ success: true, posts: page(1) } as never);
    renderAt(<PostFeed />);

    await userEvent.click(await screen.findByRole('button', { name: 'Try Again' }));

    expect(await screen.findByText('post 0')).toBeInTheDocument();
  });
});
