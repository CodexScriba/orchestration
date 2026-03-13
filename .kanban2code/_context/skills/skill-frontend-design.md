---
skill_name: skill-frontend-design
version: "1.0"
framework: Frontend UI/UX
last_verified: "2026-02-17"
always_attach: false
priority: 4
triggers:
  - frontend design
  - web design
  - ui design
  - landing page
  - component design
  - page design
  - beautiful ui
  - modern design
  - design skill
  - aesthetic
  - visual design
  - creative ui
  - polished ui
  - production-grade ui
  - distinctive design
---

<!--
LLM INSTRUCTION: Use this skill when the user asks to build web components, pages, artifacts,
posters, or applications with high design quality. This skill guides creation of distinctive,
production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Implement real
working code with exceptional attention to aesthetic details and creative choices.
The user primarily works with Tailwind CSS + shadcn/ui but expects designs that transcend
typical component library defaults. Push beyond stock shadcn patterns into genuinely modern,
memorable interfaces.
-->

# Frontend Design Skill

> **Domain:** Frontend UI/UX Design | **Stack:** Tailwind CSS, shadcn/ui, React | **Last Verified:** 2026-02-17

## 1. What AI Models Get Wrong

- **Defaulting to generic aesthetics** — Inter font, purple gradients on white, predictable card grids. This is "AI slop."
- **Treating shadcn as a ceiling** — shadcn is a foundation, not a finished design. Override tokens, extend components, break the defaults.
- **Using safe, committee-approved palettes** — timid color distributions with no dominant voice.
- **Ignoring motion entirely** — or sprinkling random transitions without choreography.
- **Symmetric, predictable layouts** — centered hero, 3-column features grid, footer. Every AI output looks identical.
- **Skipping atmosphere** — flat solid backgrounds with no depth, texture, or visual interest.
- **Converging on the same fonts** — Space Grotesk, Inter, Roboto appear in nearly every AI-generated UI.

## 2. Design Thinking Process

Before writing any code, commit to a direction:

### Step 1: Context
- **Purpose** — What problem does this interface solve? Who uses it?
- **Tone** — Commit to a distinct aesthetic direction. Starting points (not limits):
  - Brutally minimal / Swiss precision
  - Maximalist chaos / information-dense
  - Luxury / refined / editorial
  - Lo-fi / zine / raw
  - Dark / moody / cinematic
  - Soft / pastel / dreamy
  - Retro-futuristic / synthwave
  - Organic / natural / handcrafted
  - Art deco / geometric / structured
  - Playful / whimsical / toy-like
  - Industrial / utilitarian / blueprint
- **Constraints** — Framework, performance budget, accessibility requirements.

### Step 2: Differentiation
Ask: *What makes this UNFORGETTABLE? What is the one thing someone will remember?*

### Step 3: Execute with conviction
Bold maximalism and refined minimalism both work. The key is **intentionality, not intensity**. Every detail must serve the chosen direction.

## 3. Aesthetics Guidelines

### Typography

Typography carries the design's singular voice. It is the most impactful design decision.

**Rules:**
- **Never default** to Arial, Inter, Roboto, system stacks, or Space Grotesk. These signal default thinking.
- **Choose fonts with personality** — the typeface should be inseparable from the aesthetic direction.
- **Display type should be expressive**, even risky. Body text should be legible and refined.
- **Pair like actors in a scene** — a bold display font with a quiet body font creates tension and hierarchy.
- **Work the full typographic range** — size, weight, letter-spacing, text-transform, line-height all contribute.

**Font discovery sources:**
- Google Fonts (filter by category + trending)
- Fontshare (free, high-quality variable fonts)
- Fontsource (npm-installable, tree-shakable)

**Pairing examples (vary every time — never repeat across projects):**
- Display: `Clash Display` / Body: `Satoshi`
- Display: `Cabinet Grotesk` / Body: `General Sans`
- Display: `Playfair Display` / Body: `Source Serif 4`
- Display: `Syne` / Body: `Work Sans`
- Display: `Space Mono` / Body: `IBM Plex Sans`

### Color & Theme

Commit to a cohesive position. Palettes must take a stance.

**Rules:**
- Lead with a **dominant color**, punctuate with **sharp accents**.
- Avoid timid, evenly-distributed palettes where every color gets equal weight.
- Use **CSS custom properties** for all color values (Tailwind `@theme` tokens or `globals.css`).
- Bold + saturated, moody + restrained, or high-contrast + minimal — pick one and commit.
- Dark themes are not just "invert the colors" — they need their own palette with adjusted saturation and contrast.

**Tailwind + shadcn approach:**
```css
/* Override shadcn defaults in globals.css — don't just use the stock theme */
@theme {
  --color-accent: oklch(0.72 0.18 145);
  --color-surface: oklch(0.14 0.01 260);
  --color-surface-raised: oklch(0.18 0.01 260);
  --color-text-primary: oklch(0.95 0 0);
  --color-text-muted: oklch(0.55 0.01 260);
  --color-border: oklch(0.25 0.01 260);
}
```

### Motion & Animation

Motion should feel choreographed, not scattered.

**Rules:**
- **One well-orchestrated page load** with staggered reveals (`animation-delay`) creates more delight than random micro-interactions.
- **CSS-only first** — use `@keyframes`, `transition`, `animation-delay` for HTML/CSS projects.
- **Motion library (framer-motion)** for React when orchestration or gesture-based interaction is needed.
- **Scroll-triggered animations** — use `IntersectionObserver` or motion's `whileInView`.
- **Hover states that surprise** — not just `opacity: 0.8`. Think scale, translate, color shift, blur, clip-path reveals.

**Stagger pattern (Tailwind + CSS):**
```css
.stagger-in > * {
  opacity: 0;
  transform: translateY(12px);
  animation: fadeUp 0.5s ease-out forwards;
}
.stagger-in > *:nth-child(1) { animation-delay: 0ms; }
.stagger-in > *:nth-child(2) { animation-delay: 80ms; }
.stagger-in > *:nth-child(3) { animation-delay: 160ms; }
.stagger-in > *:nth-child(4) { animation-delay: 240ms; }

@keyframes fadeUp {
  to { opacity: 1; transform: translateY(0); }
}
```

### Spatial Composition & Layout

Break expectations. Layouts should have a point of view.

**Techniques:**
- **Asymmetry** — off-center hero text, unequal column splits (40/60, 30/70).
- **Overlap and z-depth** — elements layered with negative margins, `z-index`, absolute positioning.
- **Diagonal flow** — skewed sections, rotated elements, angled dividers.
- **Grid-breaking elements** — items that bleed outside their container or span unexpected areas.
- **Dramatic scale jumps** — 120px display heading next to 14px body. Not gradual — dramatic.
- **Full-bleed moments** — edge-to-edge images, color blocks, or sections.
- **Generous negative space OR controlled density** — both are valid, but commit to one.

### Backgrounds & Visual Depth

Flat solid backgrounds are the hallmark of generic AI output. Create atmosphere.

**Techniques:**
- Gradient meshes and multi-stop radial gradients
- Noise and grain overlays (`background-image: url("data:image/svg+xml,...")` or CSS `filter`)
- Geometric patterns (CSS `repeating-linear-gradient`, SVG patterns)
- Layered transparencies and glassmorphism (`backdrop-filter: blur()`)
- Dramatic or soft shadows and glows (`box-shadow` layering, colored shadows)
- Decorative borders, `clip-path` shapes, SVG masks
- Print-inspired textures: halftone, duotone, stipple
- Knockout typography (text as mask over images/gradients)

**Grain overlay (reusable):**
```css
.grain::after {
  content: '';
  position: fixed;
  inset: 0;
  opacity: 0.04;
  pointer-events: none;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
}
```

## 4. Tailwind + shadcn: Beyond Defaults

shadcn/ui provides unstyled primitives. The design layer is your responsibility.

### Override, don't accept
```tsx
// WRONG: stock shadcn button
<Button variant="default">Submit</Button>

// RIGHT: designed button with intent
<Button
  className="bg-[var(--color-accent)] text-black font-medium tracking-tight
             rounded-[10px] px-6 py-3 text-[15px]
             hover:brightness-110 hover:scale-[1.02]
             active:scale-[0.98] transition-all duration-150"
>
  Submit
</Button>
```

### Extend component variants
Create project-specific variants via `cva` or className overrides that match your aesthetic:
```tsx
const buttonVariants = cva(
  "inline-flex items-center justify-center transition-all duration-150 font-medium tracking-tight",
  {
    variants: {
      intent: {
        primary: "bg-[var(--color-accent)] text-black rounded-[10px] hover:brightness-110",
        ghost: "bg-transparent text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-raised)]",
        danger: "bg-red-500/10 text-red-400 hover:bg-red-500/20 rounded-[10px]",
      },
      size: {
        sm: "text-[13px] px-3 py-1.5 rounded-[8px]",
        md: "text-[15px] px-5 py-2.5 rounded-[10px]",
        lg: "text-[17px] px-7 py-3.5 rounded-[12px]",
      },
    },
    defaultVariants: { intent: "primary", size: "md" },
  }
);
```

### Theme token overrides
Always customize the shadcn theme tokens in `globals.css` — the default theme is intentionally neutral:
```css
@layer base {
  :root {
    /* Replace with your aesthetic's palette */
    --background: 0 0% 4%;
    --foreground: 0 0% 95%;
    --card: 0 0% 7%;
    --primary: 145 60% 45%;
    --primary-foreground: 0 0% 2%;
    --muted: 0 0% 12%;
    --muted-foreground: 0 0% 50%;
    --border: 0 0% 14%;
    --radius: 0.625rem;
  }
}
```

## 5. DO / DON'T

### DO
- Choose a bold aesthetic direction and execute every detail in service of it.
- Pick distinctive, characterful fonts — different for every project.
- Lead with a dominant color; use accents sparingly but decisively.
- Choreograph motion — staggered load, purposeful hover, scroll-triggered reveals.
- Create visual depth with gradients, noise, shadows, layered elements.
- Override shadcn defaults aggressively — tokens, spacing, radius, components.
- Use asymmetric layouts, dramatic scale contrasts, and intentional negative space.
- Vary between light/dark themes, different aesthetics — no two projects should look the same.

### DON'T
- Don't use Inter, Roboto, Arial, Space Grotesk, or system font stacks.
- Don't use purple-gradient-on-white or any palette that screams "AI generated this."
- Don't accept stock shadcn themes without customization.
- Don't create symmetric, predictable layouts (centered hero > 3-col grid > CTA > footer).
- Don't add `opacity: 0.8` hover states as your only interaction.
- Don't use flat solid backgrounds with no depth or texture.
- Don't scatter random micro-interactions — choreograph motion intentionally.
- Don't converge on familiar choices across projects — actively explore the full range.

## 6. Implementation Complexity Matching

Match code complexity to the aesthetic vision:

| Direction | Code Approach |
|-----------|---------------|
| Maximalist / chaos | Elaborate keyframes, layered pseudo-elements, SVG animations, complex gradients, multiple overlapping elements |
| Refined / minimal | Precise spacing, perfect typography scale, subtle transitions, restraint in every detail, fewer elements but each one perfect |
| Editorial / magazine | CSS Grid with named areas, art-directed image placement, pull quotes, typographic hierarchy with 4+ size steps |
| Dark / moody | Colored shadows, glow effects, grain overlays, deep layered backgrounds, selective light sources |
| Retro-futuristic | Custom fonts, scanline effects, neon glows, CRT curvature, monospace accents |

Excellence comes from executing the vision well — not from adding more effects.

## 7. Checklist

- [ ] Aesthetic direction chosen and stated before coding.
- [ ] Fonts are distinctive and project-specific (not Inter/Roboto/Arial/Space Grotesk).
- [ ] Color palette takes a clear position — dominant + accent, via CSS tokens.
- [ ] shadcn theme tokens overridden in `globals.css` to match the direction.
- [ ] Layout has a point of view — asymmetry, scale contrast, or intentional density.
- [ ] Motion is choreographed — staggered load, purposeful hover/scroll interactions.
- [ ] Backgrounds have depth — gradients, noise, patterns, or layered effects.
- [ ] No generic "AI slop" patterns (purple gradients, symmetric grids, stock components).
- [ ] Implementation complexity matches the aesthetic ambition.
- [ ] The design is memorable — someone could describe what makes it unique.
