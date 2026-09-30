---
phase: 8
slug: comprehensive-dark-light-theme-system
status: approved
shadcn_initialized: false
preset: none
created: 2026-09-30
---

# Phase 8 — UI Design Contract: Comprehensive Dark & Light Theme System

> Visual and interaction contract for system-wide dark and light mode tokens, header theme toggle switch, high-contrast dark surfaces, and persistent theme state.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (Vanilla CSS custom design tokens) |
| Preset | not applicable |
| Component library | none (custom React components) |
| Icon library | lucide-react (`Sun`, `Moon`, `Monitor`) |
| Font | Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif |
| Monospace Font | ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace |

---

## 1. Theme Token Architecture (`THEME-01`, `THEME-02`)

### Light Mode (Default `:root`, `[data-theme="light"]`)
```css
:root, [data-theme="light"] {
  --bg-color: #f0f2f5;
  --bg-secondary: #ffffff;
  --bg-tertiary: #f8f9fb;
  --sidebar-bg: #ffffff;
  --card-bg: #ffffff;
  --card-bg-solid: #ffffff;
  --card-border: rgba(0, 0, 0, 0.06);
  --card-border-hover: rgba(0, 0, 0, 0.12);
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-tertiary: #94a3b8;
  color-scheme: light;
}
```

### Dark Mode (`[data-theme="dark"]`)
```css
[data-theme="dark"] {
  --bg-color: #0a0e17;
  --bg-secondary: #111827;
  --bg-tertiary: #1e293b;
  --sidebar-bg: #0d131f;
  --card-bg: #111827;
  --card-bg-solid: #111827;
  --card-border: rgba(255, 255, 255, 0.08);
  --card-border-hover: rgba(255, 255, 255, 0.16);
  --text-primary: #f8fafc;
  --text-secondary: #cbd5e1;
  --text-tertiary: #64748b;

  --accent-blue-light: rgba(37, 99, 235, 0.18);
  --accent-green-light: rgba(5, 150, 105, 0.18);
  --accent-red-light: rgba(220, 38, 38, 0.18);
  --accent-yellow-light: rgba(217, 119, 6, 0.18);
  --accent-purple-light: rgba(124, 58, 237, 0.18);
  --accent-cyan-light: rgba(8, 145, 178, 0.18);
  --accent-teal-light: rgba(13, 148, 136, 0.18);
  --accent-orange-light: rgba(234, 88, 12, 0.18);
  --accent-indigo-light: rgba(79, 70, 229, 0.18);

  --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.4);
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.5), 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.6), 0 2px 4px -1px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.7), 0 4px 6px -2px rgba(0, 0, 0, 0.5);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.8), 0 10px 10px -5px rgba(0, 0, 0, 0.6);
  color-scheme: dark;
}
```

---

## 2. Header Theme Toggle Switch (`THEME-01`)

- **Placement**: Top-right header action bar (`.content-header-actions`), situated beside the Live status badge.
- **Button Styling (`.theme-toggle-btn`)**:
  - Compact glassmorphic pill button: `height: 32px; padding: 0 0.75rem; border-radius: 999px;`
  - Border: `1px solid var(--card-border);`
  - Background: `var(--bg-tertiary);`
  - Icon: `<Sun size={15} />` with amber glow in Dark mode, `<Moon size={15} />` in Light mode.
  - Text label: "Light" / "Dark" in `font-size: 0.75rem; font-weight: 600; color: var(--text-secondary);`
  - Hover state: `border-color: var(--accent-blue); color: var(--text-primary); background: var(--accent-blue-light);`
  - Transition: smooth rotation on icon (`transform: rotate(180deg)`) on toggle.

---

## 3. Surface & Component Adaptivity (`THEME-02`)

1. **Header & Sidebar**:
   - Translucent glassmorphism with `backdrop-filter: blur(16px); background: var(--bg-secondary);`
   - Sidebar brand and status divider lines adapt cleanly with `var(--card-border)`.
2. **Glass Cards & Metric Tiles**:
   - `background: var(--card-bg);` with `border: 1px solid var(--card-border);`
   - Dark mode provides deep charcoal/navy card elevation against midnight canvas (`#0a0e17`).
3. **Tables**:
   - Sticky headers retain `background: var(--bg-secondary);` with `backdrop-filter: blur(8px);`
   - Row hover transitions smoothly to `var(--bg-tertiary);`
4. **Form Controls & Inputs**:
   - Dropdown selects, text inputs, and datetime-local pickers adopt `background: var(--bg-secondary); color: var(--text-primary); border-color: var(--card-border);`
   - Dark select dropdown arrow SVG adapted for dark backgrounds.
5. **Recharts Tooltips & Grids**:
   - Tooltip popup styled with `var(--bg-secondary)`, `var(--text-primary)`, and `var(--card-border)`.
   - CartesianGrid stroke configured with `var(--card-border)`.

---

## 4. State Persistence

- Initial state priority:
  1. `localStorage.getItem('app_theme')`
  2. System preference `window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'`
  3. Default: `'light'`
- Theme applied via `document.documentElement.setAttribute('data-theme', theme)` and persisted upon each toggle.

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS

**Approval:** Approved 2026-09-30
