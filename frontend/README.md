# Meru Coders frontend

The React and TypeScript client for the meter identification API in `../backend`.
It is built with Vite and served by nginx in the Docker image.

## Run it

Node 20 is what CI and the Docker image use.

```bash
npm ci
npm run dev        # http://localhost:8080, expects the backend on http://localhost:5000
```

Meter analysis needs only the backend.
Sign-in, the community feed and contributions also need Supabase, set up as below.

## Configuration

Copy `.env.example` to `.env`.
Every variable is optional.

| Variable | Used for |
|---|---|
| `VITE_API_URL` | API base, such as `http://localhost:5000/api` |
| `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` | Google sign-in through Supabase; without them the Google button explains that it is off |

`src/services/api.ts` picks the API base in this order.

1. `VITE_API_URL`, fixed at build time.
2. `window.CONFIG.API_URL` from `config.js`, which the Docker image serves uncached so one build can point at any backend.
3. `http://localhost:5000/api` when the page runs on localhost.
4. Port 5000 on the page's own host, for testing from a phone on the same network.

The notification socket connects to the same host with `/api` removed, since Socket.IO is served from the server root.

## Scripts

| Command | What it does |
|---|---|
| `npm run dev` | Vite dev server on port 8080 |
| `npm run build` | Type-checks, then writes the production bundle to `build/` |
| `npm run preview` | Serves `build/` locally |
| `npm run lint` | ESLint over `src/` |
| `npm run typecheck` | `tsc --noEmit` |
| `npm test` | Vitest, once |
| `npm run test:coverage` | Vitest with the coverage floor in `vitest.config.ts`; CI runs this one |

## Layout

```
src/
├── App.tsx                 routes
├── views/                  MainApp (the analyzer) and LandingPage, with landing/ sections
├── pages/LGLab.tsx         the L-G Lab, with its sections in components/lg-lab/
├── components/
│   ├── analysis/           input tabs for text, image, document and voice, and mode selection
│   ├── results/            the meter result cards and their confidence wording
│   ├── datasets/           dataset browser parts
│   ├── community/          feed, posts, comments, notifications and moderation
│   ├── chat/               the floating Pingala chatbot
│   └── ui/                 the shadcn/ui primitives the app uses
├── hooks/                  state for each input tab, the dataset browser, API calls and notifications
├── services/               API, chatbot and community clients, and the notification socket
├── contexts/               AuthContext (session, sign-in, OAuth) and ChatBotContext
├── styles/                 page stylesheets
└── test/                   Vitest setup and recorded API responses
```

Components and contexts reach the network only through `services/`; none of them calls `fetch` directly.

## Styling

`src/index.css` is a precompiled Tailwind build, not a Tailwind source file.
A utility class that build does not contain has no effect.
The build's spacing utilities sit in `@layer utilities`, under the file's own unlayered `* { margin: 0; padding: 0 }` reset, so `p-4`, `mx-auto` and the rest do nothing either.
Recompiling Tailwind restyles most screens, so it is left alone until someone redesigns on purpose.

The L-G Lab is styled almost entirely with Tailwind classes, so it gets its own compiled stylesheet.
`npm run css:lg-lab` compiles the classes its files use into `src/styles/lg-lab-utilities.css`, with every rule scoped to `:where(.lg-lab-page)` so no other page changes.
`src/styles/lg-lab-utilities.test.ts` fails when an L-G Lab class changes and the file was not regenerated.

`styles/ui-components.css` styles the shadcn Button and AlertDialog by their `data-slot`, `data-variant` and `data-size` attributes, because their Tailwind classes are among the missing ones.
Its selectors use `:where()`, so a class passed by the caller still wins.

## Tests

Tests sit next to the code they cover as `*.test.ts` or `*.test.tsx` and run under jsdom.
Network calls are stubbed with `vi.stubGlobal('fetch', ...)`.
Where a test needs a realistic response, it loads one recorded from the Flask test client in `src/test/fixtures/`.

On Node 25 and later, `vitest.config.ts` starts workers with `--no-experimental-webstorage`.
Node's own `localStorage` global would otherwise hide the jsdom one.
