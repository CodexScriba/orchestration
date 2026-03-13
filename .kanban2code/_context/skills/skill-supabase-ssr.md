---
skill_name: skill-supabase-ssr
version: "1.0"
framework: Next.js
last_verified: "2025-12-29"
always_attach: false
priority: 8
triggers:
  - "@supabase/ssr"
  - supabase ssr
  - supabase auth
  - createServerClient
  - createBrowserClient
  - proxy.ts
  - cookies.setAll
  - next/headers
  - getUser
  - getClaims
  - getSession
  - rls
  - auth.uid()
  - "@supabase/auth-helpers-nextjs"
---

<!--
LLM INSTRUCTION: Use for Supabase Auth in Next.js App Router with @supabase/ssr.
FORBID: @supabase/auth-helpers-nextjs (deprecated; don't mix with @supabase/ssr).
Use separate clients: createBrowserClient (client components) and createServerClient (server).
Server Components may throw on setting cookies: wrap cookies.setAll in try/catch.
Use a Proxy (proxy.ts) to refresh sessions and write cookies to BOTH request and response to avoid desync.
Never rely on getSession() for server-side protection; prefer getClaims() (JWT verification) or getUser() (server revalidation).
Coordinate RLS policies with schema: policies depend on columns like user_id/tenant_id and auth.uid().
-->

# Supabase Auth (SSR) for Next.js App Router

> **Target:** Next.js + `@supabase/ssr` | **Last Verified:** 2025-12-29

## 1. What AI Models Get Wrong

- Using `@supabase/auth-helpers-nextjs` (deprecated) or mixing it with `@supabase/ssr`.
- Creating a server client as a module singleton (can bleed cookie state across requests).
- Forgetting the Proxy session refresh step (tokens drift; server components can’t reliably set cookies).
- Not updating both `request.cookies` and `response.cookies` in the Proxy.
- Trusting `getSession()` for server-side authorization decisions.

## 2. Golden Rules

### ✅ DO
- Use `@supabase/ssr` only; uninstall `@supabase/auth-helpers-nextjs`.
- Use **two clients**:
  - `createBrowserClient` for Client Components.
  - `createServerClient` for Server Components/Actions/Route Handlers with cookie plumbing.
- In Server Components, implement `cookies.getAll()` + `cookies.setAll()` and **catch `setAll` errors**.
- Use `proxy.ts` to refresh sessions early and keep cookies consistent per request.
- For server-side protection, use `getClaims()` (recommended) or `getUser()` (strongest, revalidated).

### ❌ DON'T
- Don’t trust `getSession()` in server code for protection.
- Don’t set cookies in Server Components without guarding for runtime errors.
- Don’t ship schema changes without matching RLS updates.

## 3. Minimal File Layout

```
proxy.ts                    # Root Next.js middleware entrypoint
lib/supabase/client.ts      # Browser client (createBrowserClient)
lib/supabase/server.ts      # Server client (createServerClient)
lib/supabase/proxy.ts       # Session refresh with getClaims()
```

## 4. Client Component: Browser Client

```ts
// lib/supabase/client.ts
import { createBrowserClient } from '@supabase/ssr';

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}
```

## 5. Server: Per-request Client + Cookie Safety

```ts
// lib/supabase/server.ts
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';

export function createClient() {
  const cookieStore = cookies();

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) => {
              cookieStore.set(name, value, options);
            });
          } catch {
            // Server Components can throw on cookie writes.
            // Safe to ignore IF proxy.ts refreshes sessions.
          }
        }
      }
    }
  );
}
```

## 6. Proxy Session Refresh (Required)

### Root `proxy.ts`
```ts
import type { NextRequest } from 'next/server';
import { updateSession } from '@/lib/supabase/proxy';

export async function proxy(request: NextRequest) {
  return updateSession(request);
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)'
  ]
};
```

### Session updater (`lib/supabase/proxy.ts`)
```ts
import { createServerClient } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';

export async function updateSession(request: NextRequest) {
  let response = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
          response = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) => {
            response.cookies.set(name, value, options);
          });
        }
      }
    }
  );

  // IMPORTANT: Avoid writing logic between createServerClient(...) and getClaims().
  // IMPORTANT: Don't remove getClaims(); it both validates and keeps sessions/cookies in sync.
  await supabase.auth.getClaims();

  return response;
}
```

## 7. Authorization Guidance (Server-side)

- **Never** rely on `supabase.auth.getSession()` for server protection (it reads from storage/cookies and is not a strong guarantee).
- Use `supabase.auth.getClaims()` to protect pages/user data when JWT validation is sufficient (verifies against JWKS/public keys; commonly used in middleware/proxy).
- Use `supabase.auth.getUser()` when you need the strongest server-side check (revalidated with Supabase Auth).

## 8. RLS + Schema Coordination (Security Invariant)

- RLS is the enforcement layer; without policies it is effectively default-deny.
- Policies commonly use `auth.uid()`; schema must include the columns used by policies (`user_id`, `tenant_id`, etc.).
- Ship table changes and RLS policy updates together (same PR/migration unit).

## 9. Checklist

- [ ] `@supabase/auth-helpers-nextjs` removed and not used.
- [ ] Browser code uses `createBrowserClient`.
- [ ] Server code uses per-request `createServerClient` with `getAll/setAll` cookie plumbing.
- [ ] `setAll` errors are caught in Server Components.
- [ ] `proxy.ts` refreshes sessions and updates both request and response cookies.
- [ ] Server protection uses `getClaims()` or `getUser()` (not `getSession()`).
- [ ] RLS policies and schema evolve together.
