# 诗云 — Agent Guide

## Run

```bash
pip install flask waitress
python3 app.py        # Waitress on :5000, 8 threads
python3 app.py --tui  # Terminal UI mode (curses, no extra deps)
```

No tests, no CI, no linter/typecheck config.

## Architecture

| File | Role |
|------|------|
| `app.py` | Flask routes, Waitress server |
| `generator.py` | Core engine: `StreamState` (counter-based base-N), session mgmt, pause/resume, state save/load |
| `templates/index.html` | Single Jinja2 page, all logic in inline `<script>` |

## Key Classes (generator.py)

- **`StreamState`**: enumerates all combinations of `chars` up to `max_length` using a counter + indices array; position in the enumeration space is fully captured by `(current_length, indices, generated)`.
- **`_session_state`**: in-memory dict `session_id → {chars, max_length, generated, start_time, end_time, running, mode, line_length, lines_per_poem}`.
- **`_paused_states`** / **`_active_generators`**: manage pause/resume across SSE connections.

`estimate_total(chars_len, max_length)` sums `chars_len¹ + … + chars_len^max_length`, capped at 10¹⁸.

## Key API Endpoints

| Endpoint | Method | Notes |
|----------|--------|-------|
| `POST /api/start` | session_id, chars/preset, max_length, mode | Returns `{total, chars_len, max_length, mode, session_id}` |
| `GET /stream` | session_id, chars/preset, max_length, mode, line_length, lines_per_poem, resume=1 | SSE stream: enum→plain `data: combo\n\n`, poetry→`data: {"type":"poem","lines":[...],"index":N}\n\n` |
| `POST /api/pause` | session_id | Sets stop event, serializes active generator → `_paused_states` + `output/_latest_session.json` |
| `POST /api/resume` | session_id, state? | If `state` provided, injects into `_paused_states`; returns `{resume_state, …}` |
| `GET /api/stats` | session_id | `{generated, total, running, elapsed, rate, mode, line_length}` |
| `POST /api/save_state` | session_id | Saves paused state → `output/session_*.json` |
| `GET /api/latest_session` | – | Returns `{state}` from `output/_latest_session.json` |
| `GET /api/list_states` | – | Lists `output/session_*.json` with metadata |
| `POST /api/clear_latest` | – | Deletes `output/_latest_session.json` |

## Two Modes

**Enum mode** (`mode=enum`): generates ALL combinations from length 1 to max_length, streams each as plain text.

**Poetry mode** (`mode=poetry`): generates combinations at exact length = `line_length × lines_per_poem` (e.g. 5×4=20 chars). Each combination is one poem, split client-side into lines of `line_length` chars. `generated` counts poems, total = `chars^(line_length × lines_per_poem)`.

Preset `{"cjk_sample"}` = 千字文 (1000 unique CJK chars).

Preset `{"full_lns"}` = all Unicode digits, letters, symbols, and Chinese (~115k chars, built at import time).

## Refresh-Persistence Flow

1. `beforeunload` → `sendBeacon('/api/auto_save', {session_id})` → server pauses + writes `output/_latest_session.json`
2. On page load → `GET /api/latest_session` → if state exists, show restore card → user clicks "恢复" → state loaded into form, user clicks "继续" → `POST /api/resume` with `state` → `GET /stream?resume=1`
3. Pause also writes `output/_latest_session.json` automatically.

## Gotchas

- **No requirements.txt** — deps are flask + waitress, install manually.
- **`generated` vs `total`**: `generated` counts individual items (enum) or poems (poetry). `total` is always a string (JS can't safely hold >2⁵³ ints). Client uses `formatNumStr()` which returns `'过大'` for >12-digit totals.
- **`total_raw`** from `/api/estimate` and `/api/start` is the raw JS number; might be `10¹⁸+1` overflow sentinel.
- **`/api/estimate`**: for poetry mode, `max_length` param must be `line_length × lines_per_poem`, not just `line_length`.
- **`/api/save_state`** requires a paused session (won't work on a running session).
- **`output/`** directory: both output files and session state files live here. `session_*.json` = manual saves, `_latest_session.json` = auto-save for refresh recovery.
- **`PRESETS`** pre-compute `utf8_all` via `unicodedata` at import time (~155k chars, takes a few seconds).
