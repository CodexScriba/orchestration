---
skill_name: skill-routing-layouts
version: "16.0.10"
framework: Next.js
last_verified: "2025-12-18"
always_attach: false
priority: 7
triggers:
  - parallel route
  - "@modal"
  - "@slot"
  - default.js
  - default.tsx
  - intercepting route
  - layout.tsx
  - loading.js
  - error.js
  - route group
---

<!--
LLM INSTRUCTION: Apply when user creates pages, modals, layouts, or navigation.
CRITICAL: Every parallel route @slot MUST have a default.tsx file (even if it returns null).
Params in layouts are ALSO Promises - must await them just like in pages.
Intercepting routes: (.) = same level, (..) = parent, (...) = root.
error.js MUST have 'use client' directive. loading.js is auto-Suspense.
Do NOT use _app.js, _document.js, or next/router - those are Pages Router patterns.
-->

# Routing & Layouts

> **Target:** Next.js 16.0.10 | **React:** 19 | **Last Verified:** 2025-12-18

## 1. What AI Models Get Wrong

- **Omitting `default.js` in parallel routes** → LLMs forget this file. v16 build fails without it for every @slot.
- **Using sync params in layouts** → LLMs access params directly. In v16, layout params are Promises too.
- **Confusing intercepting route syntax** → LLMs mix up `(.)` vs `(..)` vs `(...)` conventions.
- **Using Pages Router patterns** → LLMs suggest `_app.js`, `_document.js`, `next/router` in App Router context.
- **Creating page.tsx AND route.ts in same folder** → LLMs don't realize this causes conflicts.

## 2. Golden Rules

### ✅ DO
- **Create `default.js` for every parallel route @slot** → Required fallback for soft navigation
- **Await params in layouts** → Layouts receive `Promise<{ slug: string }>` too
- **Use `(.)` for same-level intercept, `(..)` for parent** → Precise routing semantics
- **Use `loading.js` for Suspense boundaries** → Automatic loading UI per segment
- **error.js must be 'use client'** → Error boundaries are client components

### ❌ DON'T  
- **Don't skip default.js** → Causes 404 or build failure in v16
- **Don't access layout params synchronously** → They're Promises
- **Don't use `_app.js`, `_document.js`** → App Router uses layout.tsx
- **Don't use `next/router`** → Use `next/navigation` in App Router
- **Don't have page.tsx and route.ts together** → Same segment conflict

## 3. Critical Patterns

### Parallel Routes with Default.js

**❌ WRONG (v14/v15 - Hallucination Risk):**
```
app/
├── @modal/
│   └── photo/
│       └── [id]/
│           └── page.tsx
├── layout.tsx
└── page.tsx
// Missing default.tsx = BUILD FAILURE in v16
```

**✅ CORRECT (v16):**
```
app/
├── @modal/
│   ├── default.tsx      ← REQUIRED
│   └── photo/
│       └── [id]/
│           └── page.tsx
├── layout.tsx
└── page.tsx
```

```typescript
// app/@modal/default.tsx
export default function Default() {
  return null; // Render nothing when no modal matches
}

// app/layout.tsx
export default function Layout({
  children,
  modal,
}: {
  children: React.ReactNode;
  modal: React.ReactNode;
}) {
  return (
    <html>
      <body>
        {children}
        {modal}
      </body>
    </html>
  );
}
```
**Why:** When navigating away from /photo/123, Next needs default.tsx to know what to render in @modal slot.

---

### Async Params in Layouts

**❌ WRONG (v14/v15 - Hallucination Risk):**
```typescript
// Sync access in layout - CRASHES
export default function BlogLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { slug: string }; // Wrong type
}) {
  return (
    <div>
      <h1>Blog: {params.slug}</h1> {/* Error: params is Promise */}
      {children}
    </div>
  );
}
```

**✅ CORRECT (v16):**
```typescript
export default async function BlogLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ slug: string }>; // Promise type
}) {
  const { slug } = await params; // Await required
  
  return (
    <div className="blog-layout">
      <aside>Current Post: {slug}</aside>
      {children}
    </div>
  );
}
```
**Why:** All params are Promises in v16 to support PPR streaming.

---

### Intercepting Routes Syntax

**❌ WRONG (v14/v15 - Hallucination Risk):**
```
app/
├── feed/
│   └── (..)photo/      ← Wrong: should match route structure
│       └── [id]/
│           └── page.tsx
└── photo/
    └── [id]/
        └── page.tsx
```

**✅ CORRECT (v16):**
```
app/
├── @modal/
│   └── (.)photo/       ← (.) = same level intercept
│       └── [id]/
│           └── page.tsx
├── feed/
│   └── (..)photo/      ← (..) = one level up intercept  
│       └── [id]/
│           └── page.tsx
├── photo/
│   └── [id]/
│       └── page.tsx    ← Full page (hard navigation)
└── layout.tsx
```

**Syntax Reference:**
- `(.)` - Intercept from same level
- `(..)` - Intercept from one level up
- `(..)(..)` - Two levels up
- `(...)` - Intercept from app root

**Why:** Soft navigation shows intercepted modal; hard refresh shows full page.

---

### Loading.js and Error.js

**❌ WRONG (v14/v15 - Hallucination Risk):**
```typescript
// Manual loading state in page
'use client';
export default function Page() {
  const [loading, setLoading] = useState(true);
  // ... manual spinner logic
}

// error.js as Server Component
export default function Error({ error }) { // Missing 'use client'
  return <div>Error: {error.message}</div>;
}
```

**✅ CORRECT (v16):**
```typescript
// app/dashboard/loading.tsx - Automatic Suspense
export default function Loading() {
  return <div className="skeleton">Loading dashboard...</div>;
}

// app/dashboard/error.tsx - MUST be 'use client'
'use client';

import { useEffect } from 'react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div>
      <h2>Something went wrong!</h2>
      <button onClick={() => reset()}>Try again</button>
    </div>
  );
}
```
**Why:** loading.js auto-wraps in Suspense. error.js must be client for reset() interactivity.

---

### Default.js with Async Params

**❌ WRONG (v14/v15 - Hallucination Risk):**
```typescript
// Sync params in default.js
export default function Default({ params }: { params: { id: string } }) {
  return <div>Fallback for {params.id}</div>; // Crashes
}
```

**✅ CORRECT (v16):**
```typescript
// app/@sidebar/default.tsx
export default async function Default({ 
  params 
}: { 
  params: Promise<{ id: string }> 
}) {
  const { id } = await params;
  return <div>Default sidebar for {id}</div>;
}
```
**Why:** default.js follows the same async params contract as page.tsx.

## 4. Quick Reference Table

| Feature | ❌ Don't | ✅ Do |
|---------|---------|------|
| Parallel Routes | Skip default.js | Create default.js for every @slot |
| Layout Params | `params: { slug: string }` | `params: Promise<{ slug: string }>` |
| Same-level Intercept | Random folder | `(.)folder` syntax |
| Parent-level Intercept | `(.)folder` | `(..)folder` syntax |
| Error Boundary | Server Component | `'use client'` directive |
| Loading UI | Manual useState | `loading.js` file |
| Global Layout | `_app.js` | `app/layout.tsx` |
| Navigation | `next/router` | `next/navigation` |

## 5. Checklist Before Coding

- [ ] Every parallel route @slot has a `default.tsx` file
- [ ] Layout components are `async` and `await` their params
- [ ] Using correct intercept syntax: `(.)` same, `(..)` parent, `(...)` root
- [ ] `error.js` files have `'use client'` at top
- [ ] No `_app.js`, `_document.js`, or `next/router` usage
- [ ] No page.tsx and route.ts in the same folder
