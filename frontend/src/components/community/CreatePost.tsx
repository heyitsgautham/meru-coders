/**
 * CreatePost Component
 * Elegant post composer with Sanskrit input support
 */

import { useState } from 'react';
import { Send, Sparkles, X, BookOpen } from 'lucide-react';
import { Switch } from '../ui/switch';
import { useAuth } from '../../contexts/AuthContext';
import { createPost } from '../../services/community';
import type { Post } from '../../types/community';

interface CreatePostProps {
  onPostCreated?: (post: Post) => void;
}

export function CreatePost({ onPostCreated }: CreatePostProps) {
  const { user } = useAuth();
  const [content, setContent] = useState('');
  const [sanskritText, setSanskritText] = useState('');
  const [showSanskritInput, setShowSanskritInput] = useState(false);
  const [analyzeMeter, setAnalyzeMeter] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!user) {
    return (
      <div className="create-post-login">
        <p>
          <a href="/login">Sign in</a> to share your thoughts with the Sanskrit community
        </p>
      </div>
    );
  }

  const username = user.username || 'User';
  const avatarInitials = username.slice(0, 2).toUpperCase();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;

    setSubmitting(true);
    setError(null);

    try {
      const result = await createPost({
        content: content.trim(),
        sanskrit_text: sanskritText.trim() || undefined,
        analyze_meter: analyzeMeter,
      });

      if (result.success) {
        setContent('');
        setSanskritText('');
        setShowSanskritInput(false);
        onPostCreated?.(result.post);
      } else {
        setError(result.error || 'Failed to create post');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create post');
    } finally {
      setSubmitting(false);
    }
  };

  const toggleSanskritInput = () => {
    setShowSanskritInput(!showSanskritInput);
    if (showSanskritInput) {
      setSanskritText('');
    }
  };

  return (
    <div className="create-post-container">
      <form onSubmit={handleSubmit} className="create-post-wrapper">
        <div className="create-post-avatar">
          <div className="avatar avatar-lg">
            {avatarInitials}
          </div>
        </div>

        <div className="create-post-content">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="What's on your mind? Share a verse, thought, or insight..."
            className="create-post-textarea"
            rows={2}
          />

          {/* Sanskrit Input Panel */}
          {showSanskritInput && (
            <div className="sanskrit-input-panel">
              <div className="sanskrit-input-header">
                <div className="sanskrit-input-label">
                  <BookOpen size={16} />
                  Sanskrit Verse
                </div>
                <button
                  type="button"
                  onClick={toggleSanskritInput}
                  className="sanskrit-close-btn"
                >
                  <X size={16} />
                </button>
              </div>
              <textarea
                value={sanskritText}
                onChange={(e) => setSanskritText(e.target.value)}
                placeholder="श्लोकं लिखतु... (Enter verse in Devanagari or IAST)"
                className="sanskrit-textarea"
                rows={3}
              />
              {sanskritText.trim() && (
                <div className="sanskrit-options">
                  <Switch
                    id="analyze-meter"
                    checked={analyzeMeter}
                    onCheckedChange={setAnalyzeMeter}
                  />
                  <label htmlFor="analyze-meter">
                    Analyze chandas (meter)
                  </label>
                </div>
              )}
            </div>
          )}

          {/* Error Message */}
          {error && (
            <p className="error-message" style={{ color: '#EF4444', fontSize: '14px', marginTop: '8px' }}>
              {error}
            </p>
          )}

          {/* Actions */}
          <div className="create-post-actions">
            <div className="create-post-tools">
              <button
                type="button"
                className={`tool-btn ${showSanskritInput ? 'active' : ''}`}
                onClick={toggleSanskritInput}
              >
                <Sparkles size={18} />
                <span>Add Sanskrit</span>
              </button>
            </div>

            <button
              type="submit"
              disabled={!content.trim() || submitting}
              className="submit-btn"
            >
              {submitting ? (
                'Posting...'
              ) : (
                <>
                  <Send size={16} />
                  Post
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
