# Auto Subtitled

Web app that turns audio and video uploads into time-stamped subtitles users can read, edit inline, and export to SRT, VTT, or plain text.

## Architecture

pnpm monorepo with two artifacts and shared libraries.

### Artifacts

- `artifacts/subtitler` — React + Vite frontend (preview path `/`). Pages: upload/dashboard (`/`) and transcription detail (`/transcriptions/:id`). Built on shadcn/ui, wouter routing, TanStack Query, and a custom "studio slate & coral" theme defined in `src/index.css`.
- `artifacts/api-server` — Express API. Routes mounted under `/api`:
  - `GET /api/transcriptions` — list summaries
  - `GET /api/transcriptions/stats` — aggregate stats (registered before `:id`)
  - `GET /api/transcriptions/:id` — full transcription with segments
  - `POST /api/transcriptions` — multipart upload (`file` field, optional `language`); transcribes via OpenAI Whisper
  - `PATCH /api/transcriptions/:id` — update title and/or segments (recomputes word/segment counts)
  - `DELETE /api/transcriptions/:id`
- `artifacts/mockup-sandbox` — design canvas (unused for this product).

### Shared Libraries

- `lib/api-spec` — OpenAPI source of truth (`openapi.yaml`).
- `lib/api-zod` — generated Zod schemas; explicit re-exports to avoid duplicate name collisions.
- `lib/api-client-react` — generated TanStack Query hooks.
- `lib/db` — Drizzle ORM + Postgres schema. `transcriptions` table holds title, filename, mediaType, language, duration, counts, fullText, and `segments` jsonb (`SegmentRow[]`).
- `lib/integrations-openai-ai-server` — OpenAI client + `ensureCompatibleFormat` for audio normalization.

### Transcription Flow

1. User uploads file via the dropzone. Client validates 200MB cap and MIME type (`audio/*`, `video/*`).
2. `POST /api/transcriptions` receives multipart upload via `multer` memory storage.
3. Server runs `ensureCompatibleFormat`, then calls `openai.audio.transcriptions.create` with `whisper-1`, `response_format: "verbose_json"`, `timestamp_granularities: ["segment"]`.
4. Segments + metadata are persisted to Postgres and returned. The frontend navigates to the detail page.
5. Inline edits to title and segments auto-save with debounce; downloads are generated client-side as SRT/VTT/TXT blobs.

## Environment

- PostgreSQL provisioned (`DATABASE_URL`).
- OpenAI integration provisioned (`AI_INTEGRATIONS_OPENAI_BASE_URL`, `AI_INTEGRATIONS_OPENAI_API_KEY`).

## Conventions

- Don't change `info.title` in `openapi.yaml`.
- Schema changes: edit `lib/db/src/schema/*` then `pnpm --filter @workspace/db run push`.
- API contract changes: edit `lib/api-spec/openapi.yaml` then `pnpm --filter @workspace/api-spec run codegen`.
