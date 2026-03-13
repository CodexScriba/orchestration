---
skill_name: skill-tailwindcss-v4
version: "4.x"
framework: Tailwind CSS
last_verified: "2025-12-26"
always_attach: false
priority: 6
triggers:
  - tailwind v4
  - tailwindcss v4
  - tailwindcss
  - "@theme"
  - "@source"
  - "@config"
  - "@tailwindcss/postcss"
  - postcss.config
  - globals.css
  - tw-animate-css
  - tailwind.config.js
---

<!--
LLM INSTRUCTION: Use for Tailwind CSS v4 (CSS-first). Prevent generating tailwind.config.js by default.
v4 entry is @import "tailwindcss"; (do not emit @tailwind base/components/utilities).
Theme tokens live in @theme as CSS custom properties; use :root only for non-Tailwind vars.
PostCSS plugin is @tailwindcss/postcss.
For extra scan sources, prefer @source in CSS over a JS config.
Only create a JS config when explicitly required; load it via @config (not auto-detected).
tw-animate-css is CSS-first; import it in CSS.
-->

# Tailwind CSS v4 (CSS-first)

> **Target:** Tailwind CSS v4 | **Last Verified:** 2025-12-26

## 1. What AI Models Get Wrong

- **Generating `tailwind.config.js` by default** (v4 is CSS-first; avoid JS config unless required).
- **Using v3 directives** (`@tailwind base/components/utilities`) instead of `@import "tailwindcss";`.
- **Putting design tokens in JS** instead of `@theme` variables.
- **Adding a `content: []` scan array** (prefer auto-detection; use `@source` when needed).
- **Using `theme()`** (prefer generated CSS variables).

## 2. Golden Rules

### ✅ DO
- Use `@import "tailwindcss";` as the Tailwind entry in `globals.css`.
- Define Tailwind tokens in `@theme { --color-...; --font-...; --breakpoint-...; }`.
- Configure PostCSS with the `@tailwindcss/postcss` plugin.
- Use `@source` in CSS for monorepo/external scan sources.
- Import `tw-animate-css` in CSS when needed.

### ❌ DON'T
- Don’t create `tailwind.config.js` unless explicitly required.
- Don’t emit `@tailwind base/components/utilities` (v3 pattern).
- Don’t use `theme()` for new code (prefer `var(--...)`).

## 3. Minimal Setup (Next.js-friendly)

### Install
```bash
npm i tailwindcss @tailwindcss/postcss postcss
```

### `postcss.config.mjs`
```js
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
```

### `app/globals.css` (or `src/app/globals.css`)
```css
@import "tailwindcss";
```

## 4. Tokens: `@theme` vs `:root`

### Tailwind tokens (generate utilities)
```css
@import "tailwindcss";

@theme {
  --color-brand-500: oklch(0.62 0.2 250);
  --font-sans: ui-sans-serif, system-ui, sans-serif;
  --breakpoint-3xl: 120rem;
  --radius-lg: 0.75rem;
}
```

### Non-Tailwind variables (do not generate utilities)
```css
:root {
  --marketing-site-max-width: 72rem;
}
```

## 5. Content Scanning

- Default: rely on v4 auto-detection.
- If you must include extra sources (monorepos/external packages), add `@source`:

```css
@import "tailwindcss";
@source "../packages/ui";
@source "../node_modules/@my-company/ui-lib";
```

## 6. Legacy Escape Hatch (only when required): `@config`

If a legacy Tailwind config is unavoidable, load it explicitly:

```css
@import "tailwindcss";
@config "../../tailwind.config.js";
```

## 7. `tw-animate-css` (Tailwind v4)

### Install
```bash
npm i -D tw-animate-css
```

### Import in CSS
```css
@import "tailwindcss";
@import "tw-animate-css";
```

### Pattern: data-state driven animations
```tsx
export function Toast({ show }: { show: boolean }) {
  return (
    <div
      data-state={show ? "show" : "hide"}
      className="
        data-[state=show]:animate-in
        data-[state=hide]:animate-out
        fade-in fade-out
        slide-in-from-top-8 slide-out-to-top-8
        duration-500
      "
    />
  );
}
```

## 8. Checklist

- [ ] No `tailwind.config.js` added unless explicitly required.
- [ ] `globals.css` uses `@import "tailwindcss";`.
- [ ] Tokens live in `@theme` (Tailwind) or `:root` (non-Tailwind).
- [ ] `postcss.config.*` uses `@tailwindcss/postcss`.
- [ ] Extra scan sources use `@source` (not `content: []`).
- [ ] `tw-animate-css` imported in CSS when used.
