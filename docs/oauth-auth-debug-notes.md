# Google OAuth Fix Notes

## What was wrong
- OAuth flow was initiated from the backend (`/api/auth/oauth/start`). Supabase PKCE expects the **code_verifier** to live in the browser storage, but backend initiation never wrote it, so the callback failed with `invalid request: both auth code and code verifier should be non-empty`.
- Frontend callback only looked for tokens in the URL hash and then `getSession()`. In a PKCE flow Supabase returns a `?code=...` query param, so it never exchanged the code and showed "No session found".

## Fix applied
- Start OAuth **from the frontend** with `supabase.auth.signInWithOAuth` so Supabase JS stores the PKCE verifier locally. File: `frontend/src/contexts/AuthContext.tsx` (`startOAuth`).
- Handle PKCE code on callback: `exchangeCodeForSession(authCode)` before the hash/session fallback. File: `frontend/src/components/OAuthCallback.tsx`.
- Add redacted logging to trace redirects, tokens, and Supabase responses (frontend + backend `backend/auth/routes.py`).
- Import the Supabase client in `AuthContext` to avoid `supabase is not defined`.

## How to reproduce the working flow
1) Set env vars for Supabase in the frontend (e.g., `.env`):
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
   - `VITE_API_URL` (e.g., `http://localhost:5000/api`)
2) Start backend: `cd backend && python run.py` (ensure `SUPABASE_URL` and keys are set server-side too).
3) Start frontend (Vite): `cd frontend && npm run dev` (or the project’s dev command).
4) Click "Login with Google". Supabase JS redirects to Google with PKCE data stored in `localStorage`.
5) After redirect to `/oauth/callback`, the page exchanges `?code=...` via `exchangeCodeForSession`, calls the backend `/auth/oauth/exchange`, then lands on `/app`.

## Where to look for diagnostics
- Frontend console: `[AuthContext]` and `[OAuthCallback]` logs show redirect targets, redacted tokens, and code-exchange outcomes.
- Backend logs: `OAuth start request/response` and `OAuth exchange` entries confirm provider URL, token presence (redacted), Supabase `get_user`, and profile creation.

## Files touched (for reference)
- `frontend/src/contexts/AuthContext.tsx`: start OAuth via frontend supabase-js (PKCE) + import supabase + logging.
- `frontend/src/components/OAuthCallback.tsx`: handle `code` query with `exchangeCodeForSession`; keep hash/session fallback; logging.
- `backend/auth/routes.py`: added safe logging for OAuth start/exchange and profile creation.
