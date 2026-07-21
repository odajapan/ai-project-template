---
paths:
  - "web/**"
---

# Web Workspace Rules (TypeScript)

`web/` is an optional TypeScript workspace (dashboards, UIs). It only
exists in some downstream projects.

## Conventions

- TypeScript with `strict: true` — no `any` without a justifying comment
- Package manager: **pnpm** by convention; if the project already has a
  `package-lock.json` or `yarn.lock`, follow that lockfile's tool instead
- Keep components small and single-purpose; colocate tests with sources

## Commands

Run from `web/`:

```bash
pnpm install          # install dependencies
pnpm lint             # ESLint
pnpm typecheck        # tsc --noEmit
pnpm test             # unit tests
pnpm build            # production build
```

`make check` does **not** cover `web/` — run lint + typecheck + test
before committing any `web/` change.

## Never commit

- `node_modules/`, build output (`dist/`, `.next/`, etc.)
- `.env.local` or any file containing secrets — client-side code must
  never embed API keys; calls that need a key go through a backend

## Testing

- Unit tests colocated with sources; no real network calls
- Mock API clients at the boundary, same policy as the Python side
