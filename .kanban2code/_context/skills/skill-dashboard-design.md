---
skill_name: skill-dashboard-design
version: "1.0"
framework: UI/UX Design
last_verified: "2026-02-17"
always_attach: false
priority: 5
triggers:
  - dashboard design
  - dashboard ui
  - dashboard layout
  - design system
  - design cheatsheet
  - icon size
  - font weight
  - border radius
  - icon stroke
  - huge_icons
  - ui design
  - frontend design
---

<!--
LLM INSTRUCTION: Apply this skill when designing or reviewing dashboard UIs.
Enforce: 14px base font, 16px base icon, 1.2px stroke width, 2 font weights max (regular + medium),
8-12px border radius, and semantic color tokens from globals. Never use semibold except in rare
emphasis cases. Prefer filled+stroke icons from huge_icons. Color values must come from design tokens.
-->

# Dashboard Design Skill

> **Domain:** Frontend UI/UX | **Style:** Dashboard / Data interfaces | **Last Verified:** 2026-02-17

## 1. What AI Models Get Wrong

- **Using too many font weights** — more than 2 (regular + medium) creates visual noise.
- **Ignoring icon stroke consistency** — mixing stroke widths breaks visual rhythm.
- **Hardcoding colors** — all color values must come from design tokens (`globals.css` / CSS custom properties).
- **Overusing large border radii** — going beyond 12px makes dashboards feel like mobile apps, not tools.
- **Using semibold or bold freely** — semibold is reserved for rare, high-signal emphasis only.
- **Scaling icons arbitrarily** — base size is 16px; deviations must be intentional and consistent.

## 2. Golden Rules

### Typography

- **Base font size:** `14px` — all body text, labels, table cells, sidebar items.
- **Only 2 weights:**
  - `regular` (400) — body text, secondary labels, descriptions.
  - `medium` (500) — headings, section titles, emphasis, interactive labels.
  - `semibold` (600) — **very rare**; only for critical callouts or KPI values that must stand out.
- Do not use `bold` (700) or `light` (300) in dashboard contexts.

### Icons

- **Library:** `huge_icons` — filled + stroke style.
- **Base size:** `16px` — default for inline icons, sidebar nav, action buttons.
- **Stroke widths (use one per context, never mix within a component):**
  - `1px` — light, decorative, background icons.
  - `1.2px` — **default**; use for all standard UI icons.
  - `1.5px` — stronger emphasis; use for primary CTAs or active state icons.
- Filled variant: use for active/selected states.
- Stroke variant: use for default/inactive states.

### Colors

- **Always use design tokens** — never hardcode hex or rgb values.
- Source: `globals.css` (or equivalent CSS custom property file for the project).
- Semantic token pattern: `--color-text-primary`, `--color-surface-muted`, `--color-border`, etc.
- Limit to 3–5 active colors per view; use muted/subtle variants for non-critical elements.

### Border Radius

- **Range: `8px` to `12px`** — no exceptions without explicit design approval.
  - `8px` — compact elements: badges, tags, small inputs, table cells.
  - `10px` — standard cards, modals, dropdowns.
  - `12px` — featured cards, hero panels, primary containers.
- Do not use `4px` (too sharp) or `16px+` (too rounded for dashboards).

## 3. Component Patterns

### Stat / KPI Card

```tsx
// Correct: medium weight for value, regular for label, 10px radius, 16px icon
<div className="rounded-[10px] p-4 bg-[var(--color-surface)]">
  <div className="flex items-center gap-2 text-[var(--color-text-secondary)] text-[14px] font-normal">
    <Icon name="chart-bar" size={16} strokeWidth={1.2} />
    <span>Total Revenue</span>
  </div>
  <p className="text-[24px] font-medium text-[var(--color-text-primary)] mt-1">$48,200</p>
</div>
```

### Sidebar Nav Item

```tsx
// Active: filled icon, medium text. Inactive: stroke icon, regular text.
<NavItem
  icon={isActive ? <FilledIcon size={16} /> : <StrokeIcon size={16} strokeWidth={1.2} />}
  label="Analytics"
  weight={isActive ? "medium" : "regular"}
/>
```

### Data Table Cell

```tsx
// 14px, regular weight, tokens for color
<td className="text-[14px] font-normal text-[var(--color-text-primary)] px-3 py-2">
  John Doe
</td>
```

## 4. ✅ DO / ❌ DON'T

### ✅ DO
- Use `14px` for all body/label text.
- Use `16px` as the default icon size.
- Use `1.2px` stroke width unless intentionally signaling emphasis.
- Use `regular` + `medium` weights only (semibold max once per page).
- Pull all colors from CSS custom properties (`var(--color-...)`).
- Use `8px`–`12px` radius range consistently per element type.
- Use `huge_icons` filled variant for active/selected states, stroke for default.

### ❌ DON'T
- Don't use `bold`, `light`, or `thin` font weights.
- Don't hardcode `#hex` or `rgb()` values; use tokens.
- Don't exceed `12px` border radius for dashboard components.
- Don't go below `8px` border radius unless for a chip/micro-badge.
- Don't mix stroke widths (`1px`, `1.2px`, `1.5px`) within the same component.
- Don't use icon sizes other than 16px without a deliberate layout reason.

## 5. Quick Reference Cheatsheet

| Token         | Value              | Notes                                 |
|---------------|--------------------|---------------------------------------|
| Font size     | `14px`             | Base for all dashboard text           |
| Font weights  | `400`, `500`       | Regular + medium; semibold = rare     |
| Icon library  | `huge_icons`       | Filled (active) + Stroke (default)    |
| Icon size     | `16px`             | Base; scale intentionally             |
| Stroke width  | `1.2px`            | Default; 1px light, 1.5px emphasis    |
| Border radius | `8px` – `12px`     | 8 compact / 10 standard / 12 featured |
| Colors        | CSS custom props   | Always via `var(--color-...)`         |

## 6. Checklist

- [ ] All text is `14px` base size.
- [ ] Only `regular` and `medium` weights used (semibold count = 0–1 per page).
- [ ] Icons are from `huge_icons`, sized at `16px`, `1.2px` stroke by default.
- [ ] Stroke variants used for inactive states, filled for active/selected.
- [ ] All colors reference CSS custom properties — no hardcoded values.
- [ ] Border radius stays within `8px`–`12px`.
- [ ] No mixed stroke widths within a single component.
