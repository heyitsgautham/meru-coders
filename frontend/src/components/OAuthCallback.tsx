import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../lib/supabase';
import { Loader2 } from 'lucide-react';

const redact = (token?: string | null) =>
  token ? `${token.slice(0, 4)}...${token.slice(-4)} (len=${token.length})` : '<empty>';

export default function OAuthCallback() {
  const [error, setError] = useState<string | null>(null);
  const { completeOAuth } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const handleOAuthCallback = async () => {
      try {
        console.info('[OAuthCallback] location', {
          hash: window.location.hash,
          search: window.location.search,
          origin: window.location.origin,
        });

        // Try hash tokens first (implicit flow)
        const hashParams = new URLSearchParams(window.location.hash.substring(1));
        const accessToken = hashParams.get('access_token');
        const refreshToken = hashParams.get('refresh_token');

        // Also check query param code (PKCE flow)
        const searchParams = new URLSearchParams(window.location.search);
        const authCode = searchParams.get('code');
        if (authCode) {
          console.info('[OAuthCallback] Found auth code in query, exchanging for session');
          const { data, error } = await supabase.auth.exchangeCodeForSession(authCode);
          if (error) {
            console.error('[OAuthCallback] exchangeCodeForSession error', error);
            setError('Failed to complete OAuth (code exchange)');
            setTimeout(() => navigate('/login'), 3000);
            return;
          }
          if (data?.session) {
            console.info('[OAuthCallback] Session obtained via code exchange', {
              userId: data.session.user?.id,
              expires_at: data.session.expires_at,
            });
            const { error: authError } = await completeOAuth(
              data.session.access_token,
              data.session.refresh_token
            );
            if (authError) {
              console.error('[OAuthCallback] OAuth completion error after code exchange', authError);
              setError(authError);
              setTimeout(() => navigate('/login'), 3000);
              return;
            }
            navigate('/app');
            return;
          }
        }
        
        // If we have tokens in the URL, use them directly
        if (accessToken) {
          console.info('[OAuthCallback] Found tokens in URL hash', {
            accessToken: redact(accessToken),
            refreshToken: redact(refreshToken),
          });
          
          // Set the session in Supabase client
          const { data: { session }, error: sessionError } = await supabase.auth.setSession({
            access_token: accessToken,
            refresh_token: refreshToken || ''
          });

          if (sessionError) {
            console.error('[OAuthCallback] Session error', sessionError);
            setError('Failed to authenticate with Google');
            setTimeout(() => navigate('/login'), 3000);
            return;
          }

          if (!session) {
            console.error('[OAuthCallback] Supabase setSession returned no session');
            setError('Failed to create session');
            setTimeout(() => navigate('/login'), 3000);
            return;
          }

          console.info('[OAuthCallback] Supabase session established', {
            expires_at: session.expires_at,
            tokenType: session.token_type,
            userId: session.user?.id,
          });

          // Complete the OAuth flow by exchanging tokens with backend
          console.info('[OAuthCallback] Calling completeOAuth', {
            accessToken: redact(session.access_token),
            refreshToken: redact(session.refresh_token),
          });
          const { error: authError } = await completeOAuth(
            session.access_token,
            session.refresh_token
          );

          if (authError) {
            console.error('[OAuthCallback] OAuth completion error', authError);
            setError(authError);
            setTimeout(() => navigate('/login'), 3000);
            return;
          }

          // Success! Redirect to app
          navigate('/app');
          return;
        }
        
        // Fallback: try to get existing session
        console.info('[OAuthCallback] No tokens in hash, attempting getSession');
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();

        if (sessionError || !session) {
          console.error('[OAuthCallback] No session found via getSession', sessionError);
          setError('No session found');
          setTimeout(() => navigate('/login'), 3000);
          return;
        }

        console.info('[OAuthCallback] Existing session found', {
          expires_at: session.expires_at,
          tokenType: session.token_type,
          userId: session.user?.id,
        });

        // Complete the OAuth flow
        console.info('[OAuthCallback] Completing OAuth with existing session', {
          accessToken: redact(session.access_token),
          refreshToken: redact(session.refresh_token),
        });
        const { error: authError } = await completeOAuth(
          session.access_token,
          session.refresh_token
        );

        if (authError) {
          console.error('[OAuthCallback] OAuth completion error (existing session)', authError);
          setError(authError);
          setTimeout(() => navigate('/login'), 3000);
          return;
        }

        // Success! Redirect to app
        navigate('/app');
      } catch (err) {
        console.error('[OAuthCallback] Unexpected error', err);
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
