---
phase: 4
slug: network-operations-responsive-redesign
status: approved
shadcn_initialized: false
preset: none
created: 2026-09-30
---

# Phase 4 — UI Design Contract: Network Operations Responsive Redesign

> Visual and interaction contract for Network Operations multi-column layout, device card responsive grid, and clean location grouping.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (Vanilla CSS custom design tokens) |
| Preset | not applicable |
| Component library | none (custom React components) |
| Icon library | lucide-react |
| Font | Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif |

---

## Layout & Responsive Grid

| Element | CSS Grid / Flex Definition | Viewport Adaptation |
|---------|----------------------------|---------------------|
| Device Grid (`.device-grid`) | `display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1rem;` | 3 cols at >1400px, 2 cols at 900–1400px, 1 col below 768px |
| Health Summary KPI Grid (`.noc-summary-grid`) | `display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem;` | 4 cols on desktop, 2 cols on mobile |
| Location Header (`.location-header`) | `display: flex; align-items: center; gap: 0.5rem; border-bottom: 1px solid var(--card-border);` | Flex wrap enabled on narrow screens |
| Filter Bar (`.filter-bar`) | `display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap;` | Full width, search input min-width 260px |

---

## Spacing Scale

Declared values (must be multiples of 4):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Icon-text gaps, inline pill padding |
| sm | 8px | Button padding, tag spacing |
| md | 16px | Card padding, grid gap (`1rem`) |
| lg | 24px | Section bottom margins (`1.5rem`) |
| xl | 32px | Main content body horizontal padding |
| 2xl | 48px | Empty state top/bottom padding |
| 3xl | 64px | Page boundary spacing |

---

## Typography

| Role | Size | Weight | Line Height | Font Family |
|------|------|--------|-------------|-------------|
| Device Tile Title | 14px (0.88rem) | 700 (Bold) | 1.2 | Inter |
| Location Header Title | 15px (0.95rem) | 700 (Bold) | 1.25 | Inter |
| Telemetry Meta | 12px (0.75rem) | 500 (Medium) | 1.4 | Inter |
| Status Badge | 11px (0.68rem) | 700 (Bold) | 1.0 | Inter |
| Empty State | 13px (0.82rem) | 500 (Medium) | 1.4 | Inter |

---

## Color & Contrast

| Role | Value | Usage |
|------|-------|-------|
| Background (`--bg-primary`) | `#f8fafc` | Page canvas surface |
| Card Background (`--bg-secondary`) | `#ffffff` | Device tiles, KPI summary cards |
| Card Border (`--card-border`) | `rgba(226, 232, 240, 0.8)` | Subtle tile outlines |
| Text Primary (`--text-primary`) | `#0f172a` | Device names, section headings |
| Text Secondary (`--text-secondary`) | `#475569` | Telemetry values, timestamps |
| Text Tertiary (`--text-tertiary`) | `#94a3b8` | Labels, counters, search placeholders |
| Accent Blue (`--accent-blue`) | `#2563eb` | Geographic location icons, focus outlines |
| Accent Green (`--accent-green`) | `#059669` | Healthy status badges & dots |
| Accent Red (`--accent-red`) | `#dc2626` | Critical status badges & alert borders |
| Accent Yellow (`--accent-yellow`) | `#d97706` | Warning status badges |

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Search Placeholder | "Search devices or locations..." |
| Filter Counter | "{N} devices shown" |
| Empty State Title | "No devices match your search." |
| Empty State Subtitle | "Try adjusting your search query or clear the filter." |
| Geographic Header | "{Country Flag} {Country} — {City}" (e.g. "🇬🇧 United Kingdom — London") |
| Infrastructure Header | "{Group Name}" (e.g. "Core Distribution", "Branch Firewalls") |
| Active Alert Badge | "{N} active alert{s}" |

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS

**Approval:** Approved 2026-09-30
