---
skill_name: skill-metadata-seo
version: "16.0.10"
framework: Next.js
last_verified: "2025-12-18"
always_attach: false
priority: 6
triggers:
  - metadata
  - generateMetadata
  - SEO
  - openGraph
  - og:image
  - opengraph-image
  - sitemap
  - robots
  - meta tags
---

<!--
LLM INSTRUCTION: Apply when user works on SEO, metadata, or social sharing.
generateMetadata params are PROMISES - must await them.
opengraph-image.tsx also receives async params.
Do NOT use next/head - App Router uses export const metadata or generateMetadata.
Use sitemap.ts and robots.ts for dynamic generation, not static files.
Image remotePatterns: localhost is BLOCKED by default (SSRF prevention).
-->

# Metadata & SEO

> **Target:** Next.js 16.0.10 | **React:** 19 | **Last Verified:** 2025-12-18

## 1. What AI Models Get Wrong

- **Using sync params in generateMetadata** → LLMs use `{ params: { id: string } }`. In v16, params is a Promise.
- **Using `next/head` in App Router** → LLMs suggest the old Head component. App Router uses metadata exports.
- **Sync params in ImageResponse** → LLMs forget opengraph-image.tsx also receives async params.
- **Using sitemap.xml file** → LLMs create static XML. v16 prefers sitemap.ts with dynamic generation.
- **Missing parent metadata extension** → LLMs don't await parent to extend existing metadata.

## 2. Golden Rules

### ✅ DO
- **Await params in generateMetadata** → First argument is `{ params: Promise<...> }`
- **Use `export const metadata` or `generateMetadata`** → App Router's metadata API
- **Await params in opengraph-image.tsx** → Image routes also receive async params
- **Use sitemap.ts for dynamic sitemaps** → Return `MetadataRoute.Sitemap` array
- **Await `parent` for extending metadata** → Access parent's openGraph images, etc.

### ❌ DON'T  
- **Don't use `next/head`** → Not available in App Router
- **Don't access params synchronously** → They're Promises in generateMetadata
- **Don't create static sitemap.xml** → Use sitemap.ts for dynamic generation
- **Don't forget robots.ts** → Controls crawler behavior
- **Don't use local IPs in remotePatterns** → Blocked by default for SSRF prevention

## 3. Critical Patterns

### Async generateMetadata

**❌ WRONG (v14/v15 - Hallucination Risk):**
```typescript
import type { Metadata } from 'next';

// Sync params - CRASHES in v16
export async function generateMetadata({ 
  params 
}: { 
  params: { id: string } // Wrong type
}): Promise<Metadata> {
  const product = await fetch(`https://api.example.com/products/${params.id}`); // Error
  return { title: product.name };
}
```

**✅ CORRECT (v16):**
```typescript
import type { Metadata, ResolvingMetadata } from 'next';

type Props = {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
};

export async function generateMetadata(
  { params, searchParams }: Props,
  parent: ResolvingMetadata
): Promise<Metadata> {
  // 1. Await the params
  const { id } = await params;
  
  // 2. Fetch data
  const product = await fetch(`https://api.example.com/products/${id}`)
    .then((res) => res.json());

  // 3. Extend parent metadata
  const previousImages = (await parent).openGraph?.images || [];

  return {
    title: product.title,
    description: product.description,
    openGraph: {
      images: [product.image, ...previousImages],
    },
  };
}
```
**Why:** v16's async params support PPR and streaming for metadata generation.

---

### OpenGraph Image with Async Params

**❌ WRONG (v14/v15 - Hallucination Risk):**
```typescript
// app/blog/[slug]/opengraph-image.tsx
import { ImageResponse } from 'next/og';

// Sync params - CRASHES
export default function Image({ params }: { params: { slug: string } }) {
  return new ImageResponse(
    <div>Post: {params.slug}</div>, // Error
    { width: 1200, height: 600 }
  );
}
```

**✅ CORRECT (v16):**
```typescript
// app/blog/[slug]/opengraph-image.tsx
import { ImageResponse } from 'next/og';

export const runtime = 'edge';
export const alt = 'Blog post image';
export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

export default async function Image({ 
  params 
}: { 
  params: Promise<{ slug: string }> 
}) {
  const { slug } = await params;
  
  // Optionally fetch post data
  const post = await fetch(`https://api.example.com/posts/${slug}`)
    .then(r => r.json());
  
  return new ImageResponse(
    (
      <div
        style={{
          fontSize: 48,
          background: 'linear-gradient(to bottom, #1a1a2e, #16213e)',
          color: 'white',
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {post.title}
      </div>
    ),
    { ...size }
  );
}
```
**Why:** Image routes follow the same async params pattern as pages.

---

### Dynamic Sitemap

**❌ WRONG (v14/v15 - Hallucination Risk):**
```xml
<!-- public/sitemap.xml - Static, outdated -->
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/</loc>
  </url>
</urlset>
```

**✅ CORRECT (v16):**
```typescript
// app/sitemap.ts
import { MetadataRoute } from 'next';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const posts = await fetch('https://api.example.com/posts')
    .then(r => r.json());

  const postUrls = posts.map((post: { slug: string; updatedAt: string }) => ({
    url: `https://example.com/blog/${post.slug}`,
    lastModified: new Date(post.updatedAt),
    changeFrequency: 'weekly' as const,
    priority: 0.8,
  }));

  return [
    {
      url: 'https://example.com',
      lastModified: new Date(),
      changeFrequency: 'yearly',
      priority: 1,
    },
    {
      url: 'https://example.com/about',
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.5,
    },
    ...postUrls,
  ];
}
```
**Why:** sitemap.ts generates dynamic XML at request time with fresh data.

---

### Robots.ts

**❌ WRONG (v14/v15 - Hallucination Risk):**
```
# public/robots.txt - Static file
User-agent: *
Disallow: /admin
```

**✅ CORRECT (v16):**
```typescript
// app/robots.ts
import { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://example.com';
  
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: ['/admin/', '/api/', '/private/'],
      },
      {
        userAgent: 'Googlebot',
        allow: '/',
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
    host: baseUrl,
  };
}
```
**Why:** robots.ts allows dynamic rules and environment-based URLs.

---

### Image Remote Patterns Security

**❌ WRONG (v14/v15 - Hallucination Risk):**
```typescript
// next.config.ts
const config = {
  images: {
    remotePatterns: [
      { hostname: 'localhost' }, // Blocked for SSRF prevention
      { hostname: '127.0.0.1' }, // Blocked
    ],
  },
};
```

**✅ CORRECT (v16):**
```typescript
// next.config.ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'assets.example.com',
        pathname: '/images/**',
      },
      {
        protocol: 'https',
        hostname: '*.cloudinary.com',
      },
    ],
    // Only for development - NOT production
    // dangerouslyAllowLocalIP: true,
  },
};

export default nextConfig;
```
**Why:** v16 blocks loopback IPs by default to prevent SSRF attacks.

## 4. Quick Reference Table

| Feature | ❌ Don't | ✅ Do |
|---------|---------|------|
| Head Tags | `import Head from 'next/head'` | `export const metadata` or `generateMetadata` |
| Metadata Params | `params: { id: string }` | `params: Promise<{ id: string }>` |
| OG Image Params | Sync access | `await params` in async function |
| Sitemap | Static `sitemap.xml` | Dynamic `sitemap.ts` |
| Robots | Static `robots.txt` | Dynamic `robots.ts` |
| Local Images | `localhost` in remotePatterns | Only production domains |
| Parent Metadata | Ignore parent | `await parent` to extend |

## 5. Checklist Before Coding

- [ ] `generateMetadata` function awaits its `params` argument
- [ ] `opengraph-image.tsx` is async and awaits params  
- [ ] Using `export const metadata` or `generateMetadata` (not next/head)
- [ ] `sitemap.ts` returns `MetadataRoute.Sitemap` array
- [ ] `robots.ts` returns `MetadataRoute.Robots` object
- [ ] Image `remotePatterns` only includes production domains (no localhost)
