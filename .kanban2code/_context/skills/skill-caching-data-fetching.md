---
skill_name: skill-caching-data-fetching
version: "16.0.10"
framework: Next.js
last_verified: "2025-12-18"
always_attach: false
priority: 8
triggers:
  - cache
  - fetch
  - revalidate
  - cacheTag
  - cacheLife
  - use cache
  - unstable_cache
  - ISR
  - PPR
  - stale data
  - performance
---

<!--
LLM INSTRUCTION: Apply when user mentions caching, data fetching, or performance.
CRITICAL CHANGE: Next.js 16 is UNCACHED BY DEFAULT. fetch() does NOT cache.
Do NOT use: unstable_cache, revalidate: 60 in fetch options.
DO use: 'use cache' directive, cacheLife() profiles, cacheTag() for invalidation.
Your v14 training assumed fetch cached by default - that's WRONG for v16.
-->

# Caching & Data Fetching

> **Target:** Next.js 16.0.10 | **React:** 19 | **Last Verified:** 2025-12-18

## 1. What AI Models Get Wrong

- **Assuming fetch caches by default** → LLMs expect v14 behavior where fetch was cached. In v16, fetch is uncached by default.
- **Using `unstable_cache`** → LLMs suggest this deprecated API. In v16, use `'use cache'` directive instead.
- **Using `revalidate: 60` in fetch options** → LLMs still use this pattern. v16 prefers `'use cache'` with `cacheLife` profiles.
- **Expecting Route Handler GET to be static** → LLMs assume GET routes cache. In v16, they're dynamic by default.
- **Trying to cache in proxy.ts** → LLMs attempt fetch caching in proxy. This is explicitly not supported.

## 2. Golden Rules

### ✅ DO
- **Use `'use cache'` directive** → Opt-in caching for functions or files
- **Use `cacheLife` profiles** → Semantic durations: `seconds`, `minutes`, `hours`, `days`, `weeks`, `max`
- **Use `cacheTag` for invalidation** → Tag cached data for targeted revalidation
- **Wrap dynamic content in `<Suspense>`** → Enables PPR static shell + streaming
- **Call `revalidateTag` after mutations** → Purge cache in Server Actions

### ❌ DON'T  
- **Don't assume fetch is cached** → v16 defaults to uncached
- **Don't use `unstable_cache`** → Deprecated, replaced by `'use cache'`
- **Don't cache in proxy.ts** → Explicitly unsupported, all fetches run every request
- **Don't use `getStaticProps` patterns** → Not available in App Router
- **Don't forget UI refresh after mutations** → Use `router.refresh()` or revalidation

## 3. Critical Patterns

### Use Cache Directive

**❌ WRONG (v14/v15 - Hallucination Risk):**
```typescript
// Assuming fetch caches automatically
export async function getProduct(id: string) {
  const res = await fetch(`https://api.example.com/products/${id}`); // Not cached in v16!
  return res.json();
}

// Or using deprecated unstable_cache
import { unstable_cache } from 'next/cache';
const getData = unstable_cache(async () => {
  return { ok: true };
}); // Deprecated
```

**✅ CORRECT (v16):**
```typescript
import { cacheLife } from 'next/cache';

export async function getProduct(id: string) {
  'use cache'; // Directive enables caching
  cacheLife('hours'); // Use semantic profile
  
  const res = await fetch(`https://api.example.com/products/${id}`);
  return res.json();
}
```
**Why:** v16 inverts caching—uncached by default, explicit opt-in required.

---

### CacheLife Profiles

**❌ WRONG (v14/v15 - Hallucination Risk):**
```typescript
// Using arbitrary seconds in fetch options
const res = await fetch(url, { 
  next: { revalidate: 3600 } // Old pattern
});
```

**✅ CORRECT (v16):**
```typescript
import { cacheLife } from 'next/cache';

export async function getMarketingData() {
  'use cache';
  cacheLife('hours'); // Built-in: seconds, minutes, hours, days, weeks, max
  
  return fetch('https://api.example.com/marketing').then(r => r.json());
}

// Custom profiles in next.config.ts
const nextConfig: NextConfig = {
  cacheLife: {
    'marketing-pages': {
      stale: 3600,      // Serve stale up to 1 hour
      revalidate: 900,  // Check for updates every 15 mins
      expire: 86400,    // Hard expire after 1 day
    },
  },
};
```
**Why:** Semantic profiles are clearer and integrate with Next's SWR system.

---

### Tag-Based Invalidation

**❌ WRONG (v14/v15 - Hallucination Risk):**
```typescript
// Not tagging data for invalidation
async function getPosts() {
  return fetch('https://api.example.com/posts'); // No way to selectively invalidate
}
```

**✅ CORRECT (v16):**
```typescript
import { cacheTag, revalidateTag } from 'next/cache';

// Tag the cached data
async function getPosts() {
  'use cache';
  cacheTag('posts'); // Tag for invalidation
  return db.posts.findMany();
}

// Invalidate in Server Action
'use server';
export async function createPost(data: FormData) {
  await db.posts.create({
    title: String(data.get('title') ?? ''),
    body: String(data.get('body') ?? ''),
  });
  revalidateTag('posts'); // Purge cache
}
```
**Why:** Tags enable surgical cache invalidation without full revalidation.

---

### Partial Prerendering (PPR)

**❌ WRONG (v14/v15 - Hallucination Risk):**
```typescript
// No Suspense boundary - entire page becomes dynamic
export default async function Page() {
  const user = await getCurrentUser(); // Dynamic - cookies
  const products = await getProducts(); // Could be static
  
  return (
    <div>
      <UserGreeting user={user} />
      <ProductList products={products} />
    </div>
  ); // Entire page is dynamic
}
```

**✅ CORRECT (v16):**
```typescript
import { Suspense } from 'react';

export default function Page() {
  return (
    <main>
      <h1>Static Title (Instant Load)</h1>
      <ProductList /> {/* Can be cached */}
      
      <Suspense fallback={<p>Loading user...</p>}>
        <UserProfile /> {/* Dynamic - streams in */}
      </Suspense>
    </main>
  );
}
```
**Why:** PPR sends static shell immediately, streams dynamic "holes" via Suspense.

---

### Route Handler Caching

**❌ WRONG (v14/v15 - Hallucination Risk):**
```typescript
// Assuming GET is cached/static
export async function GET() {
  const data = await db.query('SELECT * FROM items');
  return Response.json(data); // Dynamic in v16!
}
```

**✅ CORRECT (v16):**
```typescript
// Explicitly set caching behavior
export const dynamic = 'force-static'; // Or use 'use cache'

export async function GET() {
  'use cache';
  cacheLife('minutes');
  
  const data = await db.query('SELECT * FROM items');
  return Response.json(data);
}
```
**Why:** GET routes are uncached by default in v16. Explicit opt-in required.

## 4. Quick Reference Table

| Feature | ❌ Don't | ✅ Do |
|---------|---------|------|
| Cache Data | Assume cached | Use `'use cache'` directive |
| Revalidation | `revalidate: 60` in fetch | `cacheLife('minutes')` |
| Old Cache API | `unstable_cache()` | `'use cache'` directive |
| Invalidation | `revalidatePath` only | `cacheTag()` + `revalidateTag()` |
| GET Routes | Assume static | Set `dynamic = 'force-static'` |
| Dynamic Data | No Suspense | Wrap in `<Suspense>` for PPR |
| Proxy.ts | Attempt caching | Move caching logic to pages |

## 5. Checklist Before Coding

- [ ] Enable `cacheComponents: true` in next.config.ts (default in 16.0.10)
- [ ] Add `'use cache'` directive to functions that should be cached
- [ ] Use semantic `cacheLife` profiles instead of raw seconds
- [ ] Tag cached data with `cacheTag()` for selective invalidation
- [ ] Call `revalidateTag()` in Server Actions after mutations
- [ ] Wrap dynamic components in `<Suspense>` for PPR benefits
