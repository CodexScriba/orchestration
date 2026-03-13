---
skill_name: skill-vitest-playwright-testing
version: "1.0"
framework: Next.js
last_verified: "2025-12-26"
always_attach: false
priority: 6
triggers:
  - vitest
  - playwright
  - @vitejs/plugin-react
  - jsdom
  - vitest.config
  - playwright.config
  - "*.test.ts"
  - "*.test.tsx"
  - tests/*.spec.ts
  - coverage
  - next/headers
  - cookies()
  - headers()
  - supabase
  - vi.mock
---

<!--
LLM INSTRUCTION: Use for repositories that run Vitest for unit/component tests and Playwright for E2E.
Keep unit tests as *.test.ts(x) and Playwright tests under tests/*.spec.ts.
Vitest must exclude tests/**; Playwright must use testDir: 'tests'.
Mock next/headers (cookies/headers) in Vitest when code depends on request scope.
Prefer mocking your own Supabase wrapper module rather than mocking @supabase/supabase-js directly.
Coverage config should include provider, reporters, include/exclude, and thresholds; run coverage via CLI flag.
-->

# Testing Stack: Vitest + Playwright (Next.js / React)

> **Target:** Next.js + React | **Last Verified:** 2025-12-26

## 1. What AI Models Get Wrong

- Mixing unit + E2E file patterns so runners pick up the wrong tests.
- Forgetting `@vitejs/plugin-react` or `jsdom` in Vitest for React DOM tests.
- Not providing a shared `vitest.setup.ts` (matchers + global mocks).
- Trying to unit-test async Server Component flows instead of using Playwright.
- Breaking request-scoped code by not mocking `next/headers` (`cookies()` / `headers()`).

## 2. Golden Rules

### ✅ DO
- **Vitest:** `*.test.ts` / `*.test.tsx` for unit/component tests.
- **Playwright:** `tests/*.spec.ts` for E2E tests.
- Ensure **Vitest excludes `tests/**`** and **Playwright uses `testDir: 'tests'`**.
- Use `vitest.setup.ts` for `@testing-library/jest-dom/vitest` and shared mocks.
- Mock `next/headers` in unit tests when server code touches cookies/headers.
- Run E2E against `build` + `start` for realism.

### ❌ DON'T
- Don’t let Vitest execute Playwright specs (keep patterns separated).
- Don’t rely on real request context in unit tests.
- Don’t unit-test full server flows that depend on Next.js runtime; prefer Playwright.

## 3. Vitest Baseline

### `vitest.config.ts`
```ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import tsconfigPaths from 'vite-tsconfig-paths';

export default defineConfig({
  plugins: [tsconfigPaths(), react()],
  test: {
    environment: 'jsdom',
    include: ['**/*.test.ts', '**/*.test.tsx'],
    exclude: ['tests/**', 'node_modules/**', '.next/**', 'dist/**'],
    setupFiles: ['./vitest.setup.ts'],
    clearMocks: true,
    restoreMocks: true,
    mockReset: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      reportsDirectory: './coverage',
      include: ['src/**/*.{ts,tsx}', 'app/**/*.{ts,tsx}'],
      exclude: [
        '**/*.test.{ts,tsx}',
        'tests/**',
        '.next/**',
        'dist/**',
        '**/*.d.ts'
      ],
      thresholds: { lines: 80, functions: 80, statements: 80, branches: 70 }
    }
  }
});
```

### `vitest.setup.ts`
```ts
import '@testing-library/jest-dom/vitest';
import { vi } from 'vitest';

const cookieStore = {
  get: vi.fn((name: string) => ({ name, value: 'cookie' })),
  getAll: vi.fn(() => []),
  set: vi.fn(),
  delete: vi.fn()
};

vi.mock('next/headers', () => ({
  cookies: vi.fn(async () => cookieStore),
  headers: vi.fn(async () => new Headers({ 'user-agent': 'vitest' }))
}));
```

## 4. Supabase Mocking Pattern

Prefer a wrapper module (example): `src/lib/supabase/client.ts` exporting a single `supabase` client.
Mock that wrapper in unit tests instead of mocking `@supabase/supabase-js` internals.

## 5. Playwright Baseline

### `playwright.config.ts`
```ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: 'tests',
  testMatch: /.*\\.spec\\.ts/,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:3000',
    trace: 'on-first-retry'
  },
  webServer: {
    command: 'npm run start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }]
});
```

## 6. Required Scripts

```json
{
  "scripts": {
    "test": "vitest",
    "test:unit": "vitest run",
    "test:coverage": "vitest run --coverage.enabled",
    "test:e2e": "npm run build && npx playwright test"
  }
}
```

## 7. Checklist

- [ ] Unit tests use `*.test.ts(x)` and exclude `tests/**`.
- [ ] E2E tests live in `tests/*.spec.ts` and Playwright uses `testDir: 'tests'`.
- [ ] `vitest.setup.ts` exists and includes jest-dom matchers.
- [ ] `next/headers` is mocked in unit tests where needed.
- [ ] Coverage has provider + reporters + include/exclude + thresholds.
- [ ] E2E runs against production build (`build` + `start`).
