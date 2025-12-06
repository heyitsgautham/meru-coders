# Multimodal AI Chatbot Integration Plan

This plan integrates the ShlokaYug-style multimodal chatbot into **meru-coders** (primary web app). The chatbot will be a floating widget (bottom-right FAB) that expands into a panel (~70% height) with text, voice, and image inputs, persona toggle, and conversation history. Backend will proxy to Gemini using the existing keys in the root `.env` (GEMINI_API_KEY_*).

## Scope & Placement
- **App**: meru-coders frontend (Vite/React/TS). Chandas-game can embed later but reuse the same backend endpoint.
- **UI Placement**: Floating button at bottom-right on all pages; click → slide-up panel anchored bottom-right.
- **Backends**: New Flask blueprint `/api/chat` (in `backend/api/chat.py`). Uses Gemini via `GEMINI_API_KEY_*` from root `.env`.

## High-Level Architecture
1. **Frontend**: React widget with `ChatBotContext` managing messages, persona, loading, input modes. Service `chat.ts` calls `/api/chat`.
2. **Backend**: Flask blueprint `chat.py` accepts text/voice/image, persona, conversation_history; calls Gemini; returns `{response, confidence, input_detected, sources?, suggestions?}`.
3. **Data Flow**:
   - User opens widget → sends message via `chatService.send({ input_type, persona, message|audio|image, conversation_history })`.
   - Backend proxies to Gemini with system prompt (persona), optional STT/OCR hooks, returns response.
   - UI renders bot message with confidence badge, sources, suggestion chips; history persisted to localStorage (optional future: sync server-side).

## Backend Tasks (Flask)
- [ ] Add file `backend/api/chat.py` with blueprint `chat_bp` mounted at `/api/chat`.
- [ ] Endpoints:
  - `POST /api/chat` (multipart or JSON): fields `input_type` (`text|voice|image`), `persona` (`default|krishna`), `message` (text), `audio` (file), `image` (file), `conversation_history` (JSON array of `{role, content, timestamp}`), optional `metadata`.
  - Optional (later): `GET/POST /api/chat/history` for auth’d users.
- [ ] Logic:
  - Validate input_type; for `voice`, run STT (stub for now); for `image`, run OCR (stub for now).
  - Build Gemini prompt: system prompt varies by persona; include concise instructions to answer as a chandas tutor; include prior history.
  - Call Gemini with one of the `GEMINI_API_KEY_*` loaded from env (rotate if desired).
  - Return JSON: `{response: str, confidence: float (0-1), input_detected: 'text|voice|image', sources: [str]?, suggestions: [str]?}`.
- [ ] Config:
  - Load env via existing settings; ensure `GEMINI_API_KEY_*` available; choose primary key (e.g., `GEMINI_API_KEY_1`).
  - CORS: allow frontend origin (Vite dev 5173 or configured).
- [ ] Error handling: return `{response: friendly message, confidence: 0, error: details}` with 502/500 codes.

## Frontend Tasks (React/Vite)
- [ ] Add `.env.example` entry `VITE_CHAT_API_URL=http://localhost:5000/api/chat`.
- [ ] Create `src/services/chat.ts`:
  - `sendChat({ inputType, persona, message?, audioFile?, imageFile?, history })` → POST to `VITE_CHAT_API_URL` with FormData (for audio/image) or JSON (text only).
  - Normalize response to `{role: 'assistant', content, confidence, sources?, suggestions?, inputDetected}`.
- [ ] Create `src/context/ChatBotContext.tsx`:
  - State: `messages`, `persona`, `loading`.
  - Methods: `sendMessage(payload)`, `setPersona`, `clearHistory`.
  - Persistence: localStorage key `chatbot_history` (and persona).
- [ ] Create UI `src/components/chat/FloatingChatbot.tsx`:
  - Collapsed FAB bottom-right (z-index high; icon + label “Chat”).
  - Expanded panel bottom-right (width ~380–420px, height ~70vh): header with persona toggle (Default/Krishna), minimize, clear button; body scroll with bubbles; footer input bar.
  - Input bar: text box + send; mic button (MediaRecorder) for voice; image upload (file input). Disable send while loading.
  - Messages: user/bot bubbles, timestamp, confidence pill, sources list, suggestion chips (click sends).
  - Loading: animated dots bubble while awaiting response.
- [ ] Wire into app shell (e.g., `src/main.tsx` or layout): wrap app in `ChatBotProvider`, render `<FloatingChatbot />` once globally.

## UI/UX Spec
- **Button**: Circular FAB, bottom-right offset 24–32px, color accent, shadow; expands on click.
- **Panel**: Card with subtle border, drop shadow; rounded corners; backdrop blur optional.
- **Animations**: Spring slide-up/down for panel; fade/scale for FAB; typing dots for loading.
- **Personas**: Toggle pills (Default / Krishna) in header; avatar/icon changes accordingly.
- **Accessibility**: Escape closes panel; focus trap inside panel; aria labels on buttons.

## API Contract
- **Request (text JSON)**:
  ```json
  {
    "input_type": "text",
    "persona": "default",
    "message": "Explain Anushtubh",
    "conversation_history": [{"role":"user","content":"Hi"}]
  }
  ```
- **Request (multipart for voice/image)**:
  - Fields: `input_type=voice|image`, `persona`, `conversation_history` (stringified JSON), `audio` or `image` file, optional `message`.
- **Response**:
  ```json
  {
    "response": "Anuṣṭubh is 4×8 syllables...",
    "confidence": 0.82,
    "input_detected": "text",
    "sources": ["Pingala Chandas"],
    "suggestions": ["Show an example", "Test me with a verse"]
  }
  ```

## Env & Secrets
- Frontend: add `VITE_CHAT_API_URL` to `.env.local` or `.env.example`.
- Backend: use `GEMINI_API_KEY_*` from root `.env`; do NOT expose to frontend.

## Rollout Plan
1. Backend: implement `chat.py`, mount in `backend/app.py` (or equivalent), enable CORS.
2. Frontend: add service, context, component; wire provider and global render.
3. Manual QA: text → response; voice (basic); image (stub); persona toggle; loading/disable states.
4. Polish: add suggestions, sources rendering, error toasts.
5. Optional: history sync endpoints + auth guard.

## Future (After Chatbot)
- Embed same widget inside Chandas-game (learn/); reuse `ChatBotContext` and `chatService`.
- Add STT/OCR pipelines if needed; add rate limit/backoff.
- Add analytics and feedback collection per message.
