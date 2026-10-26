// Display helpers for posts: relative timestamps and sharing.
import type { Post } from '../../types/community';

/**
 * Format relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return 'just now';
  if (diffMins < 60) return `${diffMins}m`;
  if (diffHours < 24) return `${diffHours}h`;
  if (diffDays < 7) return `${diffDays}d`;

  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

/**
 * Share post using Web Share API or copy to clipboard
 */
export async function sharePost(post: Post): Promise<{ success: boolean; method: 'share' | 'copy' }> {
  const shareUrl = `${window.location.origin}/community/post/${post.id}`;
  const shareText = post.sanskrit_text
    ? `${post.content}\n\n${post.sanskrit_text}`
    : post.content;

  // Try Web Share API first
  if (navigator.share) {
    try {
      await navigator.share({
        title: 'Sanskrit Community Post',
        text: shareText,
        url: shareUrl,
      });
      return { success: true, method: 'share' };
    } catch {
      // User cancelled or share failed, fall back to clipboard
    }
  }

  // Fall back to clipboard
  try {
    await navigator.clipboard.writeText(shareUrl);
    return { success: true, method: 'copy' };
  } catch (err) {
    console.error('Failed to copy to clipboard:', err);
    return { success: false, method: 'copy' };
  }
}
