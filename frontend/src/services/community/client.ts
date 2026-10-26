// Shared fetch wrapper for the community API: base URL, bearer token and expired-session handling.
// Import shared API URL utility
import { getAPIURL } from '../api';

// Computed at request time, not module load time
export const getCommunityAPI = () => `${getAPIURL()}/community`;

/**
 * Handle 401 Unauthorized errors - token expired
 */
function handleUnauthorized(): void {
  // Clear expired tokens
  if (typeof localStorage !== 'undefined') {
    localStorage.removeItem('authToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('appUser');
  }

  // Dispatch a custom event that the app can listen to
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('auth:expired', {
      detail: { message: 'Session expired. Please log in again.' }
    }));
  }
}

/**
 * Make an authenticated API request
 */
export async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${getCommunityAPI()}${endpoint}`;
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('authToken') : null;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      // Handle 401 Unauthorized - token expired
      if (response.status === 401) {
        handleUnauthorized();
        throw new Error('Session expired. Please log in again.');
      }
      throw new Error(data.error || 'Request failed');
    }

    return data as T;
  } catch (error) {
    console.error('Community API Error:', error);
    throw error;
  }
}
