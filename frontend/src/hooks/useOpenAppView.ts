import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import type { ViewType } from '../types/api';

/** MainApp restores its view from this key on load. */
export const STORAGE_KEY_VIEW = 'chanda_currentView';

/**
 * Header navigation for pages outside MainApp (profile, admin, community): open the chosen
 * view in /app. Navigating without storing the view first would reopen whichever view was last used.
 */
export function useOpenAppView() {
  const navigate = useNavigate();
  return useCallback(
    (view: ViewType) => {
      if (view === 'community') {
        navigate('/community');
        return;
      }
      try {
        localStorage.setItem(STORAGE_KEY_VIEW, view);
      } catch {
        // Storage can be blocked; /app then opens on its default view.
      }
      navigate('/app');
    },
    [navigate],
  );
}
