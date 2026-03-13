---
skill_name: skill-next-intl
version: "3.x"
framework: Next.js
last_verified: "2025-12-26"
always_attach: false
priority: 7
triggers:
  - next-intl
  - i18n
  - internationalization
  - locale
  - locales
  - translations
  - NextIntlClientProvider
  - setRequestLocale
  - defineRouting
  - createNavigation
  - getRequestConfig
---

<!--
LLM INSTRUCTION: Use for Next.js App Router i18n with next-intl.
CRITICAL: In Next.js 16, params are Promises in layouts/pages. Always await.
CRITICAL: In async server components, use getTranslations (async) from next-intl/server. NEVER use useTranslations hook in async functions.
useTranslations hook is ONLY for client components ('use client').
Always call setRequestLocale(locale) in every layout/page that uses params.
Use NextIntlClientProvider in the root locale layout.
Use createNavigation() wrappers; never use next/link or next/navigation directly for localized routes.
Do NOT use next-intl/client or createSharedPathnamesNavigation (deprecated).
-->

# next-intl (Next.js 16 App Router)

> **Target:** Next.js 16 | **Last Verified:** 2025-12-26

## 1. What AI Models Get Wrong

- **Sync params access** → Next.js 16 params are Promises; sync destructuring breaks.
- **Missing setRequestLocale** → causes dynamic rendering errors or wrong locale.
- **Using useTranslations in async server components** → hooks can't be called in async functions; use `getTranslations` from `next-intl/server` instead.
- **Using next/link** → bypasses localized pathnames.
- **No NextIntlClientProvider** → client hooks fail.
- **Missing matcher for unprefixed routes** → localePrefix: 'as-needed' breaks.

## 2. Golden Rules

### ✅ DO
- **Type params as Promise** and `await` them in layouts/pages.
- **Call setRequestLocale(locale)** before any server-side translations.
- **Use `getTranslations` from `next-intl/server`** in async server components (pages/layouts).
- **Use `useTranslations` from `next-intl`** only in client components (`'use client'`).
- **Wrap with NextIntlClientProvider** in `[locale]/layout.tsx`.
- **Use createNavigation wrappers** for Link/redirect/useRouter/usePathname.
- **Validate locale** with hasLocale and fallback to defaultLocale.

### ❌ DON'T
- **Don't destructure params synchronously** (`{ params: { locale } }`).
- **Don't use `useTranslations` in async server components** → use `getTranslations` instead.
- **Don't import from next-intl/client** (deprecated).
- **Don't use createSharedPathnamesNavigation** (superseded).
- **Don't use next/link or next/navigation directly** for localized routes.

## 3. Minimal Setup (Files)

```
src/
├── i18n/
│   ├── routing.ts
│   ├── navigation.ts
│   └── request.ts
proxy.ts
└── app/[locale]/layout.tsx
messages/
└── en.json
```

## 4. Core Patterns

### Routing (`src/i18n/routing.ts`)
```ts
import { defineRouting } from 'next-intl/routing';

export const routing = defineRouting({
  locales: ['en', 'es'],
  defaultLocale: 'en',
  localePrefix: 'as-needed',
  pathnames: {
    '/': '/',
    '/about': { en: '/about', es: '/acerca-de' }
  }
} as const);

export type Locale = (typeof routing.locales)[number];
```

### Navigation (`src/i18n/navigation.ts`)
```ts
import { createNavigation } from 'next-intl/navigation';
import { routing } from './routing';

export const { Link, redirect, usePathname, useRouter, getPathname } =
  createNavigation(routing);
```

### Request Config (`src/i18n/request.ts`)
```ts
import { getRequestConfig } from 'next-intl/server';
import { hasLocale } from 'next-intl';
import { routing } from './routing';

export default getRequestConfig(async ({ requestLocale }) => {
  const requested = await requestLocale;
  const locale = hasLocale(routing.locales, requested)
    ? requested
    : routing.defaultLocale;

  return {
    locale,
    messages: (await import(`../../messages/${locale}.json`)).default
  };
});
```

### Proxy (`proxy.ts`) — compose with other request interceptors
If you also use Supabase SSR (`@supabase/ssr`), run both i18n + session refresh in **one** `proxy.ts`.

```ts
import type { NextRequest } from 'next/server';
import createIntlMiddleware from 'next-intl/middleware';
import { routing } from '@/i18n/routing';
import { updateSession } from '@/lib/supabase/proxy';

const handleI18n = createIntlMiddleware(routing);

export async function proxy(request: NextRequest) {
  // 1) Refresh Supabase session (may set cookies)
  const sessionResponse = await updateSession(request);

  // 2) Apply i18n routing (may rewrite/redirect)
  const i18nResponse = handleI18n(request);

  // 3) Merge cookies into the final response
  for (const cookie of sessionResponse.cookies.getAll()) {
    i18nResponse.cookies.set(cookie);
  }

  return i18nResponse;
}

export const config = {
  matcher: ['/((?!api|trpc|_next|_vercel|.*\\..*).*)']
};
```

### Locale Layout (`src/app/[locale]/layout.tsx`)
```tsx
import { NextIntlClientProvider, hasLocale } from 'next-intl';
import { getMessages, setRequestLocale } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { routing } from '@/i18n/routing';

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) notFound();

  setRequestLocale(locale);
  const messages = await getMessages();

  return (
    <html lang={locale}>
      <body>
        <NextIntlClientProvider messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
```

### Server Component Page (`app/[locale]/page.tsx`)
```tsx
import { getTranslations, setRequestLocale } from 'next-intl/server';

export default async function HomePage({
  params
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  const t = await getTranslations('HomePage');
  return <h1>{t('title')}</h1>;
}
```

> **Note:** Use `getTranslations` (async) in server components. Use `useTranslations` (hook) only in client components.

### Client Component (`'use client'`)
```tsx
'use client';

import { useTranslations } from 'next-intl';
import { Link, usePathname, useRouter } from '@/i18n/navigation';

export default function Navigation() {
  const t = useTranslations('Nav');
  const pathname = usePathname();
  const router = useRouter();

  return (
    <nav>
      <Link href="/about">{t('about')}</Link>
      <button onClick={() => router.push('/contact')}>{t('contact')}</button>
    </nav>
  );
}
```

## 5. Checklist

- [ ] Params typed as `Promise` and awaited in layouts/pages.
- [ ] `setRequestLocale(locale)` called before server translations.
- [ ] `NextIntlClientProvider` wraps app under `[locale]/layout.tsx`.
- [ ] Navigation uses `@/i18n/navigation` wrappers.
- [ ] Proxy matcher includes unprefixed routes.
