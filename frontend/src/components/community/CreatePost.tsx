/**
 * CreatePost Component
 * Elegant post composer with Sanskrit input support and image upload
 */

import { useState, useRef } from 'react';
import { Send, Sparkles, X, BookOpen, Image, Loader2 } from 'lucide-react';
import { Switch } from '../ui/switch';
import { useAuth } from '../../contexts/AuthContext';
import { createPost, uploadImage } from '../../services/community';
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
  
  // Image upload state
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [uploadingImage, setUploadingImage] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        setError('Please select an image file');
        return;
      }
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        setError('Image must be less than 5MB');
        return;
      }
      setSelectedImage(file);
      setImagePreview(URL.createObjectURL(file));
      setError(null);
    }
  };

  const removeImage = () => {
    setSelectedImage(null);
    if (imagePreview) {
      URL.revokeObjectURL(imagePreview);
    }
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;

    setSubmitting(true);
    setError(null);

    try {
      // Upload image first if selected
      let imageUrl: string | undefined;
      if (selectedImage) {
        setUploadingImage(true);
        const uploadResult = await uploadImage(selectedImage);
        if (uploadResult.success && uploadResult.url) {
          imageUrl = uploadResult.url;
        } else {
          setError(uploadResult.error || 'Failed to upload image');
          setSubmitting(false);
          setUploadingImage(false);
          return;
        }
        setUploadingImage(false);
      }

      const result = await createPost({
        content: content.trim(),
        sanskrit_text: sanskritText.trim() || undefined,
        analyze_meter: analyzeMeter,
        image_url: imageUrl,
      });

      if (result.success) {
        setContent('');
        setSanskritText('');
        setShowSanskritInput(false);
        removeImage();
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

          {/* Image Preview */}
          {imagePreview && (
            <div className="image-preview-container">
              <img src={imagePreview} alt="Preview" className="image-preview" />
              <button
                type="button"
                onClick={removeImage}
                className="image-remove-btn"
                aria-label="Remove image"
              >
                <X size={16} />
              </button>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <p className="error-message" style={{ color: '#EF4444', fontSize: '14px', marginTop: '8px' }}>
              {error}
            </p>
          )}

          {/* Hidden file input */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleImageSelect}
            accept="image/*"
            style={{ display: 'none' }}
          />

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
              <button
                type="button"
                className={`tool-btn ${selectedImage ? 'active' : ''}`}
                onClick={() => fileInputRef.current?.click()}
              >
                <Image size={18} />
                <span>Add Image</span>
              </button>
            </div>

            <button
              type="submit"
              disabled={!content.trim() || submitting || uploadingImage}
              className="submit-btn"
            >
              {uploadingImage ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Uploading...
                </>
              ) : submitting ? (
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
