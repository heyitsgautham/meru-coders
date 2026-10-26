/**
 * EditPostModal Component
 * Modal for editing an existing post with image upload support
 */

import { useState, useEffect, useRef } from 'react';
import { X, Loader2, Sparkles, Image, Trash2 } from 'lucide-react';
import { updatePost, uploadImage } from '../../services/community';
import type { Post } from '../../types/community';

interface EditPostModalProps {
  post: Post;
  isOpen: boolean;
  onClose: () => void;
  onPostUpdated: (post: Post) => void;
}

export function EditPostModal({ post, isOpen, onClose, onPostUpdated }: EditPostModalProps) {
  const [content, setContent] = useState(post.content);
  const [sanskritText, setSanskritText] = useState(post.sanskrit_text || '');
  const [analyzeMeter, setAnalyzeMeter] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Image state
  const [currentImageUrl, setCurrentImageUrl] = useState<string | null>(post.image_url || null);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [removeImage, setRemoveImage] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setContent(post.content);
      setSanskritText(post.sanskrit_text || '');
      setCurrentImageUrl(post.image_url || null);
      setSelectedImage(null);
      setImagePreview(null);
      setRemoveImage(false);
      setError(null);
    }
  }, [isOpen, post]);

  if (!isOpen) return null;

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
      setRemoveImage(false);
      setError(null);
    }
  };

  const handleRemoveImage = () => {
    setSelectedImage(null);
    if (imagePreview) {
      URL.revokeObjectURL(imagePreview);
    }
    setImagePreview(null);
    setRemoveImage(true);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleCancelRemoveImage = () => {
    setRemoveImage(false);
  };

  const getDisplayImageUrl = () => {
    if (imagePreview) return imagePreview;
    if (removeImage) return null;
    if (currentImageUrl) {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';
      const baseUrl = apiUrl.replace(/\/api\/?$/, '');
      if (currentImageUrl.startsWith('http')) return currentImageUrl;
      if (currentImageUrl.startsWith('/api/')) return `${baseUrl}${currentImageUrl}`;
      return `${baseUrl}/api/community${currentImageUrl}`;
    }
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!content.trim()) {
      setError('Content is required');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      // Upload new image if selected
      let newImageUrl: string | null | undefined = undefined;
      
      if (selectedImage) {
        setUploadingImage(true);
        const uploadResult = await uploadImage(selectedImage);
        if (uploadResult.success && uploadResult.url) {
          newImageUrl = uploadResult.url;
        } else {
          setError(uploadResult.error || 'Failed to upload image');
          setSaving(false);
          setUploadingImage(false);
          return;
        }
        setUploadingImage(false);
      } else if (removeImage) {
        newImageUrl = null; // Signal to remove the image
      }

      const result = await updatePost(post.id, {
        content: content.trim(),
        // An empty string tells the server to remove the verse; leaving the field out keeps the old one.
        sanskrit_text: sanskritText.trim(),
        analyze_meter: analyzeMeter,
        ...(newImageUrl !== undefined && { image_url: newImageUrl }),
      });

      if (result.success && result.post) {
        onPostUpdated(result.post);
        onClose();
      } else {
        setError(result.error || 'Failed to update post');
      }
    } catch (err) {
      console.error('Failed to update post:', err);
      setError('Failed to update post. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && !saving) {
      onClose();
    }
  };

  const displayImageUrl = getDisplayImageUrl();

  return (
    <div className="edit-modal-overlay" onClick={handleOverlayClick}>
      <div className="edit-modal" onClick={e => e.stopPropagation()}>
        <div className="edit-modal-header">
          <h2 className="edit-modal-title">Edit Post</h2>
          <button 
            className="edit-modal-close" 
            onClick={onClose}
            disabled={saving}
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="edit-modal-form">
          {error && (
            <div className="edit-modal-error">
              {error}
            </div>
          )}

          <div className="edit-modal-field">
            <label htmlFor="edit-content">Content</label>
            <textarea
              id="edit-content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="What's on your mind?"
              rows={3}
              disabled={saving}
              className="edit-modal-textarea"
            />
          </div>

          <div className="edit-modal-field">
            <label htmlFor="edit-sanskrit">
              Sanskrit Text (Optional)
              <Sparkles size={14} className="label-icon" />
            </label>
            <textarea
              id="edit-sanskrit"
              value={sanskritText}
              onChange={(e) => setSanskritText(e.target.value)}
              placeholder="Enter Sanskrit verse for meter analysis..."
              rows={3}
              disabled={saving}
              className="edit-modal-textarea sanskrit"
            />
          </div>

          {sanskritText.trim() && (
            <div className="edit-modal-checkbox">
              <input
                type="checkbox"
                id="edit-analyze"
                checked={analyzeMeter}
                onChange={(e) => setAnalyzeMeter(e.target.checked)}
                disabled={saving}
              />
              <label htmlFor="edit-analyze">
                Re-analyze meter (Chandas identification)
              </label>
            </div>
          )}

          {/* Image Section */}
          <div className="edit-modal-field">
            <label>
              Image
              <Image size={14} className="label-icon" />
            </label>
            
            {/* Hidden file input */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImageSelect}
              accept="image/*"
              style={{ display: 'none' }}
              disabled={saving}
            />

            {displayImageUrl ? (
              <div className="edit-modal-image-preview">
                <img src={displayImageUrl} alt="Post image" />
                <div className="edit-modal-image-actions">
                  <button
                    type="button"
                    className="edit-modal-image-change"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={saving}
                  >
                    <Image size={16} />
                    Change
                  </button>
                  <button
                    type="button"
                    className="edit-modal-image-remove"
                    onClick={handleRemoveImage}
                    disabled={saving}
                  >
                    <Trash2 size={16} />
                    Remove
                  </button>
                </div>
              </div>
            ) : removeImage && currentImageUrl ? (
              <div className="edit-modal-image-removed">
                <p>Image will be removed</p>
                <button
                  type="button"
                  onClick={handleCancelRemoveImage}
                  disabled={saving}
                >
                  Undo
                </button>
              </div>
            ) : (
              <button
                type="button"
                className="edit-modal-add-image"
                onClick={() => fileInputRef.current?.click()}
                disabled={saving}
              >
                <Image size={18} />
                <span>Add Image</span>
              </button>
            )}
          </div>

          <div className="edit-modal-actions">
            <button
              type="button"
              className="edit-modal-cancel"
              onClick={onClose}
              disabled={saving}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="edit-modal-save"
              disabled={saving || !content.trim()}
            >
              {uploadingImage ? (
                <>
                  <Loader2 className="animate-spin" size={16} />
                  Uploading...
                </>
              ) : saving ? (
                <>
                  <Loader2 className="animate-spin" size={16} />
                  Saving...
                </>
              ) : (
                'Save Changes'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
