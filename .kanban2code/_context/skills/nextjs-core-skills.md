---
skill_name: nextjs-core-skills
version: "16.0.10"
framework: Next.js
react_version: "19"
last_verified: "2025-12-18"
always_attach: true
priority: 10
triggers:
  - nextjs
  - next.js
  - app router
  - react 19
  - params
  - cookies
  - headers
  - middleware
  - proxy.ts
---

<!--
LLM INSTRUCTION: This is a CORE skill file for Next.js 16.0.10.
ALWAYS apply these rules when generating Next.js code.
Your training data likely contains v14/v15 patterns - OVERRIDE them with v16 patterns below.
Key breaking changes: async params, proxy.ts, useActionState, uncached-by-default.
When you see ❌ WRONG, that's what you might hallucinate. Use ✅ CORRECT instead.
-->

# Next.js 16 Core Skills

> **Target:** Next.js 16.0.10 | **React:** 19 | **Last Verified:** 2025-12-18

## 1. What AI Models Get Wrong

- **Synchronous params access** → LLMs generate `Page({ params }: { params: { slug: string } })` because training data from v14 used sync access. In v16, params is a Promise.
- **Using `middleware.ts`** → LLMs create middleware.ts because it existed in v14/15. In v16, it's deprecated in favor of `proxy.ts`.
- **Assuming fetch is cached** → LLMs expect fetch to cache by default (v14 behavior). In v16, all fetches are uncached by default.
- **Using `useFormState`** → LLMs import from 'react-dom' using React 18 patterns. React 19 renames this to `useActionState`.
- **Omitting `default.js` in parallel routes** → LLMs forget this file, causing build failures in v16 which strictly requires it for all @slots.

## 2. Golden Rules

### ✅ DO
- **Await all dynamic APIs** → `params`, `searchParams`, `cookies()`, `headers()` are Promises in v16
- **Use `proxy.ts` for request interception** → Replaces middleware.ts, runs on Node.js by default
- **Keep components Server by default** → Only add `'use client'` for interactivity (state, events, browser APIs)
- **Create `default.js` for every parallel route slot** → Required fallback for soft navigation
- **Use `useActionState` from 'react'** → React 19's replacement for useFormState

### ❌ DON'T  
- **Don't access params synchronously** → Causes runtime crash: "params is a Promise"
- **Don't use `middleware.ts`** → Deprecated, use proxy.ts instead
- **Don't use `useFormState` from 'react-dom'** → Renamed to useActionState in React 19
- **Don't assume fetch caches** → v16 is uncached by default, opt-in with `'use cache'`
- **Don't use `getServerSideProps`/`getStaticProps`** → Don't exist in App Router

## 3. Critical Patterns

### Async Params in Page Components

**❌ WRONG (v14/v15 - Hallucination Risk):**
```typescript
// Sync access causes runtime crash in v16
export default function Page({ params }: { params: { slug: string } }) {
  return <h1>{params.slug}</h1>; // Error: params is a Promise
}
```

**✅ CORRECT (v16):**
```typescript
// Await the Promise props
interface Props {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}

export default async function Page(props: Props) {
  const params = await props.params;
  const searchParams = await props.searchParams;
  return <h1>{params.slug}</h1>;
}
```
**Why:** v16's Partial Prerendering requires async access to support streaming dynamic content.

---

### Async Cookies and Headers

**❌ WRONG (v14/v15 - Hallucination Risk):**
```typescript
// Sync access returns Promise object, not data
import { cookies, headers } from 'next/headers';

export default function Page() {
  const cookieStore = cookies(); // Wrong: returns Promise
  const token = cookieStore.get('token'); // undefined
}
```

**✅ CORRECT (v16):**
```typescript
import { cookies, headers } from 'next/headers';

export default async function Page() {
  const cookieStore = await cookies();
  const token = cookieStore.get('auth-token');
  
  const headerList = await headers();
  const userAgent = headerList.get('user-agent');
}
```
**Why:** Request APIs are async to support Edge runtime and streaming.

---

### Proxy.ts Instead of Middleware

**❌ WRONG (v14/v15 - Hallucination Risk):**
```typescript
// middleware.ts - DEPRECATED
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  return NextResponse.next();
}
```

**✅ CORRECT (v16):**
```typescript
// proxy.ts - at project root or src/
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export async function proxy(request: NextRequest) {
  const url = request.nextUrl;
  
  if (url.pathname === '/old') {
    url.pathname = '/new';
    return NextResponse.redirect(url);
  }
  
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```
**Why:** Renamed for clarity—it's a proxy/interception layer, not middleware chain. Runs on Node.js by default.

---

### React 19 Form Pattern

**❌ WRONG (v14/React 18 - Hallucination Risk):**
```typescript
'use client';
import { useFormState } from 'react-dom'; // Wrong import

export function Form() {
  const [state, action] = useFormState(submitAction, null);
}
```

**✅ CORRECT (v16/React 19):**
```typescript
'use client';
import { useActionState } from 'react'; // Correct import

export function Form() {
  const [state, formAction, isPending] = useActionState(submitAction, null);
  
  return (
    <form action={formAction}>
      <input name="email" />
      <button disabled={isPending}>Submit</button>
      {state?.error && <p>{state.error}</p>}
    </form>
  );
}
```
**Why:** React 19 renamed useFormState to useActionState and added isPending.

---

### Parallel Routes Default.js

**❌ WRONG (v14/v15 - Hallucination Risk):**
```
app/
├── @modal/
│   └── login/
│       └── page.tsx
└── layout.tsx
// Missing default.tsx causes 404 on soft navigation!
```

**✅ CORRECT (v16):**
```
app/
├── @modal/
│   ├── default.tsx  ← REQUIRED
│   └── login/
│       └── page.tsx
└── layout.tsx
```

```typescript
// app/@modal/default.tsx
export default function Default() {
  return null; // Render nothing when no modal active
}
```
**Why:** v16 strictly requires default.js as fallback when slot has no matching route during soft navigation.

## 4. Quick Reference Table

| Feature | ❌ Don't | ✅ Do |
|---------|---------|------|
| Params | `{ params: { id: string } }` | `{ params: Promise<{ id: string }> }` |
| Cookies | `const c = cookies()` | `const c = await cookies()` |
| Headers | `const h = headers()` | `const h = await headers()` |
| Middleware | `middleware.ts` | `proxy.ts` |
| Form State | `useFormState` from 'react-dom' | `useActionState` from 'react' |
| Caching | Assume cached by default | Use `'use cache'` explicitly |
| Parallel Routes | Skip default.js | Create default.js for every @slot |
| Config | `next.config.js` | `next.config.ts` (typed) |

## 5. Checklist Before Coding

- [ ] Verify Next.js version is 16.x and React 19 in package.json
- [ ] All `params` and `searchParams` props typed as `Promise<...>` and awaited
- [ ] All `cookies()` and `headers()` calls have `await`
- [ ] Using `proxy.ts` not `middleware.ts` for request interception
- [ ] Every parallel route @slot has a `default.tsx` file
- [ ] Using `useActionState` not `useFormState` for forms
