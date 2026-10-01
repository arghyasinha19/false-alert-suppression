---
phase: 9
slug: executive-telemetry-health-kpi-strip
status: approved
shadcn_initialized: false
preset: none
created: 2026-10-01
---

# Phase 9 — UI Design Contract: Executive Telemetry & Health KPI Strip

> Visual and interaction design contract for the Executive Observability Telemetry Strip in Network Operations, defining layout hierarchy, styling tokens, responsive breakpoints, and micro-interactions.

---

## Design System & Tokens

| Property | Value |
| :--- | :--- |
| **Grid Layout** | `.noc-executive-strip`: 5-card layout with Hero card (`minmax(280px, 1.4fr)`) + 4 companion cards (`repeat(auto-fit, minmax(200px, 1fr))`) |
| **Hero Card Accent** | Dynamic CSS class based on SLA status (`.sla-nominal`, `.sla-degraded`, `.sla-critical`) |
| **Typography** | Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif |
| **Hero Metric Size** | `2.4rem` font size, `font-weight: 800`, with `%` suffix |
| **Companion Metric Size** | `1.75rem` font size, `font-weight: 800` |
| **Subtitles** | `0.72rem`, `color: var(--text-tertiary)`, uppercase letter-spacing `0.04em`, `font-weight: 600` |
| **Component Library** | Custom React + Vanilla CSS (No heavy UI frameworks) |
| **Icons** | `lucide-react` (`ShieldCheck`, `Activity`, `Flame`, `Zap`, `CheckCircle`, `Radio`, `Timer`, `Server`) |

---

## 1. Executive Telemetry Strip Grid (`NOC-KPI-01` to `NOC-KPI-05`)

### Container `.noc-executive-strip`
```css
.noc-executive-strip {
  display: grid;
  grid-template-columns: minmax(280px, 1.35fr) repeat(4, minmax(190px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

@media (max-width: 1400px) {
  .noc-executive-strip {
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }
}

@media (max-width: 768px) {
  .noc-executive-strip {
    grid-template-columns: 1fr;
  }
}
```

---

## 2. Card Visual Hierarchy & Tokens

### Card 1: Fleet Health Score (Hero Card)
- **Class:** `.glass-card .kpi-card .noc-hero-card`
- **Dynamic SLA Classes:**
  - `.sla-nominal`: Border accent `var(--accent-green)`, radial glow `rgba(16, 185, 129, 0.08)`, icon badge green.
  - `.sla-degraded`: Border accent `var(--accent-yellow)`, radial glow `rgba(245, 158, 11, 0.08)`, icon badge amber.
  - `.sla-critical`: Border accent `var(--accent-red)`, radial glow `rgba(239, 68, 68, 0.12)`, icon badge red.
- **Header:** Lucide `<ShieldCheck size={22} />` inside `.kpi-icon`, Title: `"Fleet Health Score"`, Status Pill: `<span className="badge health-nominal">NOMINAL</span>`.
- **Value:** `<AnimatedCounter value={fleetScore} duration={800} suffix="%" />`
- **Subtitle:** `"96.4% Operational availability"`

### Card 2: Noise Suppression Efficiency
- **Class:** `.glass-card .kpi-card .highlight-blue`
- **Header:** Lucide `<Zap size={20} />` inside `.kpi-icon.blue`, Title: `"Noise Suppression"`
- **Value:** `<AnimatedCounter value={suppressionRate} duration={800} suffix="%" decimals={1} />`
- **Subtitle:** `"Alerts filtered at edge"`

### Card 3: Active Blast Radius
- **Class:** `.glass-card .kpi-card .highlight-yellow` or `.highlight-red` (depending on degraded count)
- **Header:** Lucide `<Flame size={20} />` inside `.kpi-icon`, Title: `"Active Blast Radius"`
- **Value:** `<AnimatedCounter value={degradedDevicesCount} duration={800} />` with trailing `" Nodes"` label
- **Subtitle:** `"Affecting X / Y locations"`

### Card 4: Mean Resolution Velocity
- **Class:** `.glass-card .kpi-card .highlight-purple`
- **Header:** Lucide `<Timer size={20} />` inside `.kpi-icon.purple`, Title: `"Resolution Velocity"`
- **Value:** `"~15m"` (or animated integer with `"m"` suffix)
- **Subtitle:** `"DLX verification window"`

### Card 5: Site Resilience Index
- **Class:** `.glass-card .kpi-card .highlight-green`
- **Header:** Lucide `<Radio size={20} />` inside `.kpi-icon.green`, Title: `"Site Resilience"`
- **Value:** `"${nominalSites} / ${totalSites}"` with trailing `" Sites Nominal"` label
- **Micro-Visualization:** Inline horizontal health bar (`.noc-resilience-bar`):
  - Height: `4px`, `border-radius: 999px`, background `rgba(239, 68, 68, 0.3)`.
  - Fill: `background: var(--accent-green)`, width `${resiliencePct}%`, `transition: width 0.8s ease-out`.
- **Subtitle:** `"${resiliencePct}% regions nominal"`

---

## 3. Micro-Interactions & Animation Contract

- **Counting Animation:** On initial render and each live poll cycle (15s), values smoothly animate to their target using `<AnimatedCounter duration={800} />`.
- **Hover Micro-elevation:** Cards smoothly elevate (`transform: translateY(-2px)`, shadow intensifies `box-shadow: 0 8px 24px var(--card-glow)`).
- **Dark/Light Theme Adaptivity:** All card backgrounds use `var(--bg-card)`, borders use `var(--border-color)`, and text uses `var(--text-primary)` and `var(--text-tertiary)`.
