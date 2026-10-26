// Image upload for posts; sent as multipart form data rather than JSON.
import { getCommunityAPI } from './client';

export interface ImageUploadResponse {
  success: boolean;
  url?: string;
  error?: string;
}

/**
 * Upload an image for a post
 */
export async function uploadImage(file: File): Promise<ImageUploadResponse> {
  const url = `${getCommunityAPI()}/upload/image`;
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('authToken') : null;

  const formData = new FormData();
  formData.append('image', file);

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Upload failed');
    }

    return data as ImageUploadResponse;
  } catch (error) {
    console.error('Image upload error:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Upload failed' };
  }
}
