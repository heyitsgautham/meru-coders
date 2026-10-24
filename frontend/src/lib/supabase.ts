import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);

if (!isSupabaseConfigured) {
  console.warn('VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY is unset; Google sign-in is disabled');
}

// createClient throws on an empty URL, which used to stop the whole app from
// rendering on a fresh clone. A placeholder keeps the client constructible;
// startOAuth refuses to use it.
export const supabase = createClient(
  isSupabaseConfigured ? supabaseUrl : 'http://localhost:54321',
  isSupabaseConfigured ? supabaseAnonKey : 'supabase-not-configured',
  {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,
      storage: window.localStorage,
    },
  },
);
