---
phase: 6
slug: micro-interactions-animated-counters
status: approved
shadcn_initialized: false
preset: none
created: 2026-09-30
---

# Phase 6 — UI Design Contract: Micro-Interactions & Animated Counters

> Visual and interaction contract for animated KPI counters (`0 → N`), view crossfades, and enhanced ServiceNow Ticket Details section hierarchy.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (Vanilla CSS custom design tokens) |
| Preset | not applicable |
| Component library | none (custom React components) |
| Icon library | lucide-react (`Activity`, `ShieldCheck`, `Ban`, `Ticket`, `FileText`, `PlusCircle`, `MessageSquarePlus`, `RotateCcw`, `ExternalLink`) |
| Font | Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif |
| Monospace Font | ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace |

---

## 1. Animated Counter Contract (`ANIM-01`)

- **Component:** `<AnimatedCounter value={number} duration={800} suffix={string} decimals={number} />`
- **Timing:** 800ms duration with cubic ease-out easing (`progress => 1 - Math.pow(1 - progress, 3)`).
- **Interpolation:** Animates from 0 to N on component mount; smoothly interpolates from `previousValue` to `newValue` when filters, simulations, or polls update.
- **Formatting:**
  - Standard integers: Formatted with locale comma grouping (e.g. `1,250`).
  - Decimals: Supports specified decimal places (e.g. `58.3%`).
  - Accessibility: `aria-live="polite"` with complete numeric value in `title` attribute.

---

## 2. View Crossfade Transitions (`ANIM-02`)

- **Animation:** `viewCrossfade 0.28s cubic-bezier(0.16, 1, 0.3, 1) forwards`
- **Keyframe Behavior:**
  - `0%`: `opacity: 0; transform: translateY(6px);`
  - `100%`: `opacity: 1; transform: translateY(0);`
- **Placement:** Applied to the view content wrapper in `App.jsx` keyed on `activeView` to trigger upon view switching between "Alert Metrics", "Network Operations", and "Alert Patterns".

---

## 3. ServiceNow Ticket Details Hierarchy (`STATE-02`)

- **Section Header (`.snow-section-header`):**
  - Icon badge pill: Lucide `<FileText size={16} />` with styled backdrop.
  - Section title: "ServiceNow Incident Activity" (`font-size: 0.88rem; font-weight: 700; color: var(--text-primary); text-transform: uppercase; letter-spacing: 0.04em;`).
  - Total activity badge: `<span className="snow-total-badge">N Total Records</span>` styled as a subtle neutral pill.
  - Subtle horizontal rule with gradient fade.
- **Card Accents (`.snow-detail-card`):**
  - **New Incidents Created:** Top accent border `3px solid var(--accent-blue)`, blue count badge pill.
  - **Comments Appended:** Top accent border `3px solid var(--accent-purple)`, purple count badge pill.
  - **Incidents Re-opened:** Top accent border `3px solid var(--accent-orange)`, orange count badge pill.
- **Incident Pills & Rows (`.snow-device-list li`):**
  - Hover background: `var(--bg-tertiary)` with rounded 6px corners and smooth transition.
  - Incident numbers: Monospace pill badge (`font-family: monospace; font-size: 0.74rem; font-weight: 600; padding: 0.15rem 0.5rem; border-radius: 4px; border: 1px solid rgba(37, 99, 235, 0.15);`).

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS

**Approval:** Approved 2026-09-30
