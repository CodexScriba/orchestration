---
skill_name: skill-typescript-config
version: "16.0.10"
framework: Next.js
react_version: "19"
last_verified: "2025-12-18"
always_attach: false
priority: 6
triggers:
  - next.config
  - typescript
  - type error
  - Promise type
  - tsconfig
  - server-only
  - experimental
  - cacheComponents
  - "@types/react"
---

<!--
LLM INSTRUCTION: Apply when user has type errors or config issues.
Use next.config.ts (TypeScript) not next.config.js.
Remove experimental.serverActions - it's stable in v16.
Use cacheComponents: true instead of experimental.ppr.
All params must be typed as Promise<...> - your v14 training types are WRONG.
@types/react must be v19 for async components to work.
Use 'server-only' package to prevent accidental client imports.
moduleResolution should be "bundler" not "node".
-->

# TypeScript & Config

> **Target:** Next.js 16.0.10 | **React:** 19 | **Last Verified:** 2025-12-18

## 1. What AI Models Get Wrong

- **Using `next.config.js`** → LLMs use JavaScript config. v16 officially supports `next.config.ts` with type safety.
- **Using `experimental.serverActions`** → LLMs enable this flag. Server Actions are stable in v16, no flag needed.
- **Using `experimental.ppr`** → LLMs suggest this flag. In v16, use `cacheComponents: true` instead.
- **Wrong Promise types for props** → LLMs type params as objects. In v16, they must be `Promise<...>`.
- **Importing server-only in 'use client'** → LLMs import database modules in client files. This causes build failure.

## 2. Golden Rules

### ✅ DO
- **Use `next.config.ts`** → Typed configuration with autocomplete
- **Type params as Promises** → `params: Promise<{ slug: string }>`
- **Upgrade @types/react to v19** → Fixes async component type errors
- **Use `server-only` package** → Prevents accidental client imports
- **Set `cacheComponents: true`** → Enables 'use cache' and PPR

### ❌ DON'T  
- **Don't use `experimental.serverActions`** → Stable in v16, no flag needed
- **Don't use `experimental.ppr`** → Use `cacheComponents` instead
- **Don't import server code in 'use client' files** → Build failure
- **Don't use old @types/react** → Causes async component errors
- **Don't use `publicRuntimeConfig`** → Removed, use env variables

## 3. Critical Patterns

### Typed next.config.ts

**❌ WRONG (v14/v15 - Hallucination Risk):**
```javascript
// next.config.js - No type safety
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverActions: true, // Not needed in v16!
    ppr: true, // Wrong flag
  },
};

module.exports = nextConfig;
```

**✅ CORRECT (v16):**
```typescript
// next.config.ts - Typed configuration
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  reactStrictMode: true,
  
  // v16 Caching - replaces experimental.ppr
  cacheComponents: true,
  
  // Logging for debugging
  logging: {
    fetches: {
      fullUrl: true,
    },
  },
  
  // Optional: typed routes
  experimental: {
    typedRoutes: true,
  },
  
  // Custom cache profiles
  cacheLife: {
    'blog-posts': {
      stale: 3600,
      revalidate: 900,
      expire: 86400,
    },
  },
};

export default nextConfig;
```
**Why:** TypeScript config provides autocomplete and catches invalid options at compile time.

---

### Promise Props Type Errors

**❌ WRONG (v14/v15 - Hallucination Risk):**
```typescript
// Error: Property 'slug' does not exist on type 'Promise<...>'
interface Props {
  params: { slug: string }; // Wrong type
}

export default function Page({ params }: Props) {
  return <h1>{params.slug}</h1>; // Type error AND runtime error
}
```

**✅ CORRECT (v16):**
```typescript
// Correct Promise types
interface Props {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}

export default async function Page({ params, searchParams }: Props) {
  const { slug } = await params;
  const query = await searchParams;
  
  return <h1>{slug}</h1>;
}

// For layouts
interface LayoutProps {
  children: React.ReactNode;
  params: Promise<{ slug: string }>;
}

export default async function Layout({ children, params }: LayoutProps) {
  const { slug } = await params;
  return <div data-slug={slug}>{children}</div>;
}
```
**Why:** v16 types params as Promises to support PPR streaming architecture.

---

### Async Component Type Errors

**❌ WRONG (v14/React 18 types - Hallucination Risk):**
```typescript
// Error: 'Page' cannot be used as a JSX component
// This happens with old @types/react
export default async function Page() {
  const data = await fetch('https://api.example.com/data').then(r => r.json());
  return <div>{data.title}</div>;
}
```

**✅ CORRECT (v16/React 19 types):**
```json
// package.json - Ensure React 19 types
{
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "next": "^16.0.10"
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "typescript": "^5.0.0"
  }
}
```

```typescript
// Now async components work without errors
export default async function Page() {
  const data = await fetch('https://api.example.com/data').then(r => r.json());
  return <div>{data.title}</div>;
}
```
**Why:** React 19 types support async components natively; old v18 types don't.

---

### Server-Only Module Protection

**❌ WRONG (v14/v15 - Hallucination Risk):**
```typescript
// lib/db.ts - Can accidentally be imported in client
import { prisma } from './prisma';

export async function getUsers() {
  return prisma.user.findMany();
}

// components/UserList.tsx
'use client';
import { getUsers } from '../lib/db'; // BUILD FAILURE
```

**✅ CORRECT (v16):**
```typescript
// lib/db.ts - Protected with server-only
import 'server-only'; // Import at top of file
import { prisma } from './prisma';

export async function getUsers() {
  return prisma.user.findMany();
}

// components/UserList.tsx
'use client';
// Cannot import from db.ts - build error with clear message:
// "You're importing a component that needs server-only"

// Instead, pass data as props from Server Component
export function UserList({ users }: { users: User[] }) {
  return <ul>{users.map(u => <li key={u.id}>{u.name}</li>)}</ul>;
}
```
**Why:** `server-only` package prevents accidental imports in client bundles.

---

### Module Resolution Issues

**❌ WRONG (v14/v15 - Hallucination Risk):**
```typescript
// tsconfig.json with loose settings
{
  "compilerOptions": {
    "moduleResolution": "node", // May cause issues
    "paths": {
      "@/*": ["./src/*"] // Path doesn't match actual structure
    }
  }
}
```

**✅ CORRECT (v16):**
```json
// tsconfig.json - Correct settings for Next 16
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      { "name": "next" }
    ],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```
**Why:** `moduleResolution: "bundler"` is recommended for Next 16 with modern bundlers.

## 4. Quick Reference Table

| Feature | ❌ Don't | ✅ Do |
|---------|---------|------|
| Config File | `next.config.js` | `next.config.ts` |
| Server Actions | `experimental.serverActions` | Remove (stable) |
| PPR | `experimental.ppr` | `cacheComponents: true` |
| Params Type | `{ slug: string }` | `Promise<{ slug: string }>` |
| React Types | `@types/react@18` | `@types/react@19` |
| Server Code | Unprotected | `import 'server-only'` |
| Runtime Config | `publicRuntimeConfig` | Environment variables |
| Module Resolution | `"node"` | `"bundler"` |

## 5. Checklist Before Coding

- [ ] Using `next.config.ts` (not .js) with `NextConfig` type
- [ ] Removed `experimental.serverActions` (stable in v16)
- [ ] Using `cacheComponents: true` instead of `experimental.ppr`
- [ ] All params/searchParams typed as `Promise<...>`
- [ ] `@types/react` and `@types/react-dom` are v19
- [ ] Server-only modules import `'server-only'` at top
- [ ] `tsconfig.json` uses `moduleResolution: "bundler"`
