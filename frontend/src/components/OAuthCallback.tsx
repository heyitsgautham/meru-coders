import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../lib/supabase';
import { Loader2 } from 'lucide-react';

export default function OAuthCallback() {
  const [error, setError] = useState<string | null>(null);
  const { completeOAuth } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const handleOAuthCallback = async () => {
      try {
        // Exchange the code from URL hash for a session
        // This is needed because Supabase OAuth returns a code that needs to be exchanged
        const hashParams = new URLSearchParams(window.location.hash.substring(1));
        const accessToken = hashParams.get('access_token');
        const refreshToken = hashParams.get('refresh_token');
        
        // If we have tokens in the URL, use them directly
        if (accessToken) {
          console.log('Found tokens in URL hash, completing OAuth...');
          
          // Set the session in Supabase client
          const { data: { session }, error: sessionError } = await supabase.auth.setSession({
            access_token: accessToken,
            refresh_token: refreshToken || ''
          });

          if (sessionError) {
            console.error('Session error:', sessionError);
            setError('Failed to authenticate with Google');
            setTimeout(() => navigate('/login'), 3000);
            return;
          }

          if (!session) {
            setError('Failed to create session');
            setTimeout(() => navigate('/login'), 3000);
            return;
          }

          // Complete the OAuth flow by exchanging tokens with backend
          const { error: authError } = await completeOAuth(
            session.access_token,
            session.refresh_token
          );

          if (authError) {
            console.error('OAuth completion error:', authError);
            setError(authError);
            setTimeout(() => navigate('/login'), 3000);
            return;
          }

          // Success! Redirect to app
          navigate('/app');
          return;
        }
        
        // Fallback: try to get existing session
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();

        if (sessionError || !session) {
          console.error('No session found:', sessionError);
          setError('No session found');
          setTimeout(() => navigate('/login'), 3000);
          return;
        }

        // Complete the OAuth flow
        const { error: authError } = await completeOAuth(
          session.access_token,
          session.refresh_token
        );

        if (authError) {
          console.error('OAuth completion error:', authError);
          setError(authError);
          setTimeout(() => navigate('/login'), 3000);
          return;
        }

        // Success! Redirect to app
        navigate('/app');
      } catch (err) {
        console.error('OAuth callback error:', err);
        setError('An unexpected error occurred');
        setTimeout(() => navigate('/login'), 3000);
      }
    };

    handleOAuthCallback();
  }, [completeOAuth, navigate]);

  return (
    <div className="relative min-h-screen w-full bg-gradient-to-br from-[#faf0e2] via-[#ffe9d5] to-[#f7ddc0] text-slate-900 flex items-center justify-center px-4">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-20 -top-16 h-64 w-64 rounded-full bg-amber-200 blur-[100px] opacity-70" />
        <div className="absolute right-6 bottom-6 h-52 w-52 rounded-full bg-orange-200 blur-[90px] opacity-70" />
      </div>

      <div className="relative text-center">
        {error ? (
          <div className="space-y-4">
            <div className="text-red-600 text-xl font-semibold">
              {error}
            </div>
            <p className="text-slate-600">
              Redirecting to login page...
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <Loader2 className="h-12 w-12 animate-spin text-[#c75b1a] mx-auto" />
            <div className="text-xl font-semibold text-slate-900">
              Completing Google Sign In...
            </div>
            <p className="text-slate-600">
              Please wait while we authenticate your account
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
