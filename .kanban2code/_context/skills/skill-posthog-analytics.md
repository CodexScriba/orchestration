---
skill_name: skill-posthog-analytics
version: "1.0"
framework: Next.js
last_verified: "2025-12-26"
always_attach: false
priority: 5
triggers:
  - posthog
  - posthog-js
  - posthog-node
  - "@posthog/react"
  - analytics
  - pageview
  - "$pageview"
  - "$pageleave"
  - autocapture
  - server-only
  - client-only
  - runtime = 'nodejs'
---

<!--
LLM INSTRUCTION: Use for PostHog analytics in Next.js App Router.
Strictly separate client tracking (posthog-js/@posthog/react) from server tracking (posthog-node).
Mark server analytics modules as server-only and client analytics modules as client-only to prevent cross-imports.
Server tracking must run in Node runtime (not Edge); set export const runtime = 'nodejs' where needed.
Prefer PostHog SPA pageview auto-tracking; only use manual $pageview/$pageleave when required.
Always flush server events in short-lived runtimes (flushAt: 1, flushInterval: 0, shutdown()).
-->

# PostHog Analytics (Next.js App Router)

> **Target:** Next.js App Router | **Last Verified:** 2025-12-26

## 1. What AI Models Get Wrong

- Importing `posthog-node` into client bundles (causes runtime/bundle issues).
- Using browser-only APIs on the server (“window is not defined”).
- Running server tracking in Edge runtime.
- Double-tracking pageviews (auto + manual).
- Not flushing server events in serverless/short-lived execution.

## 2. Golden Rules

### ✅ DO
- **Client:** `posthog-js` + `@posthog/react` in `'use client'` components only.
- **Server:** `posthog-node` in server-only modules only; flush events on completion.
- Enforce separation with `import 'server-only'` and optionally `import 'client-only'`.
- Prefer SPA pageview auto-tracking; standardize one approach.
- For server handlers/actions using PostHog Node SDK, ensure `export const runtime = 'nodejs'` if your project uses Edge elsewhere.

### ❌ DON'T
- Don’t import server tracking helpers in client components.
- Don’t rely on server tracking in Edge.
- Don’t mix auto and manual pageview capture without a clear reason.

## 3. Environment Variables

Client (public):

```bash
NEXT_PUBLIC_POSTHOG_KEY=phc_...
NEXT_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com
```

Server (keep separate names to avoid accidental client coupling):

```bash
POSTHOG_SERVER_KEY=phc_...
POSTHOG_SERVER_HOST=https://us.i.posthog.com
```

## 4. Client Setup (Provider)

```tsx
// app/providers.tsx
'use client';

import { useEffect } from 'react';
import posthog from 'posthog-js';
import { PostHogProvider as PHProvider } from '@posthog/react';

export function PostHogProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
      api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
    });
  }, []);

  return <PHProvider client={posthog}>{children}</PHProvider>;
}
```

Wrap in `app/layout.tsx` without forcing full client rendering (boundary is fine).

## 5. Pageview Tracking

- Prefer built-in SPA pageview auto-tracking (don’t manually capture unless you disable it).
- If manual is required:
  - disable auto (`capture_pageview: false`)
  - capture both `$pageview` and `$pageleave` (use `sendBeacon` for leave).

## 6. Server Setup (`posthog-node`)

```ts
// src/lib/posthog-server.ts
import 'server-only';
import { PostHog } from 'posthog-node';

export function PostHogServer() {
  return new PostHog(process.env.POSTHOG_SERVER_KEY!, {
    host: process.env.POSTHOG_SERVER_HOST!,
    flushAt: 1,
    flushInterval: 0
  });
}
```

Use in a route handler/action and `await posthog.shutdown()` in `finally`.

## 7. Standard Event Shape (Recommended)

- Event naming: `[object] [verb]` (e.g. `project created`, `invite sent`).
- Include these properties on all custom events:
  - `source: 'client' | 'server'`
  - `app: 'web'`
  - `router: 'app'`
  - domain IDs (`org_id`, `project_id`, etc.)

## 8. Checklist

- [ ] Client and server analytics code is split and enforced via `server-only` / `client-only`.
- [ ] Server tracking runs in Node runtime and flushes on completion.
- [ ] Pageview strategy chosen (auto vs manual) and not duplicated.
- [ ] Custom event naming and core properties standardized.
