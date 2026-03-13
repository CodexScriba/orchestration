---
skill_name: skill-http-security-headers
version: "1.0"
framework: Next.js
last_verified: "2025-12-26"
always_attach: false
priority: 8
triggers:
  - csp
  - content-security-policy
  - security headers
  - headers()
  - next.config
  - x-frame-options
  - x-content-type-options
  - referrer-policy
  - permissions-policy
  - clickjacking
  - xss
  - nonce
  - strict-dynamic
---

<!--
LLM INSTRUCTION: Use for Next.js HTTP response header hardening.
Prefer CSP frame-ancestors over X-Frame-Options, but set both for defense-in-depth.
If using nonce-based CSP, it must be per-request (not a static next.config.ts string).
Static export (output: 'export') cannot use next.config headers(); configure at CDN/host instead.
-->

# Next.js HTTP Security Headers

> **Target:** Next.js (App Router or Pages Router) | **Last Verified:** 2025-12-26

## 1. What AI Models Get Wrong

- **Static nonce CSP in `next.config.*`** (nonces must be generated per request).
- **Allowing `unsafe-inline`/`unsafe-eval` in production**.
- **Using X-Frame-Options alone** (modern control is CSP `frame-ancestors`).
- **Forgetting static export limits** (`headers()` doesn’t apply to `output: 'export'`).
- **Over-broad allowlists** (`connect-src *`, `script-src *`) that nullify CSP.

## 2. Golden Rules

### ✅ DO
- **Set baseline security headers** via `next.config.*` `headers()` when you have a server runtime.
- **Use CSP `frame-ancestors`** to prevent clickjacking (keep XFO as legacy defense).
- **Roll out CSP using Report-Only first** if unsure what will break.
- **Generate CSP nonces per request** when you need strict CSP.

### ❌ DON'T
- **Don’t ship `unsafe-eval` in production** (dev-only if absolutely required).
- **Don’t use a single static nonce**.
- **Don’t rely on `headers()` for static export**.

## 3. Baseline Headers (Good Defaults)

Use these unless a requirement forces deviation:

- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=(), browsing-topics=()`
- `X-Frame-Options: DENY` (or `SAMEORIGIN` if you must embed yourself)
- `Content-Security-Policy: ...` (see below)

## 4. Implementing via `next.config.*` (Static Header Values)

```ts
// next.config.ts
import type { NextConfig } from 'next';

const securityHeaders = [
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  {
    key: 'Permissions-Policy',
    value: 'camera=(), microphone=(), geolocation=(), payment=(), usb=(), browsing-topics=()'
  },
  { key: 'X-Frame-Options', value: 'DENY' }
];

const nextConfig: NextConfig = {
  poweredByHeader: false,
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          ...securityHeaders,
          {
            key: 'Content-Security-Policy',
            value: "default-src 'self'; base-uri 'self'; object-src 'none'; form-action 'self'; frame-ancestors 'none'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; upgrade-insecure-requests;"
          }
        ]
      }
    ];
  }
};

export default nextConfig;
```

## 5. CSP: When to Use Nonces

Use nonce-based CSP when you need strong XSS mitigation without allowing inline scripts.

### Strict CSP shape (conceptual)

- `script-src 'self' 'nonce-<NONCE>' 'strict-dynamic'`
- `style-src 'self' 'nonce-<NONCE>'`
- keep `frame-ancestors 'none'`, `object-src 'none'`, `base-uri 'self'`, `form-action 'self'`

### Next.js pattern: generate nonce per request

```ts
// proxy.ts (example)
import { NextRequest, NextResponse } from 'next/server';

export function proxy(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64');

  const csp = `default-src 'self'; base-uri 'self'; object-src 'none'; form-action 'self'; frame-ancestors 'none'; script-src 'self' 'nonce-${nonce}' 'strict-dynamic'; style-src 'self' 'nonce-${nonce}'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; upgrade-insecure-requests;`;

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set('x-nonce', nonce);

  const response = NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set('Content-Security-Policy', csp);
  return response;
}
```

Use the nonce for third-party scripts:

```tsx
import { headers } from 'next/headers';
import Script from 'next/script';

export default async function Page() {
  const nonce = (await headers()).get('x-nonce') ?? undefined;

  return <Script src="https://example.com/script.js" nonce={nonce} />;
}
```

## 6. Static Export Caveat

If using `output: 'export'`, set headers at the hosting layer (CDN, reverse proxy). `next.config.*` `headers()` won’t apply.

## 7. Checklist

- [ ] Baseline headers set for all routes.
- [ ] CSP includes `frame-ancestors`.
- [ ] No `unsafe-eval`/`unsafe-inline` in production.
- [ ] If using nonces, they are per request and passed to scripts.
- [ ] Static export handled at CDN/host.
