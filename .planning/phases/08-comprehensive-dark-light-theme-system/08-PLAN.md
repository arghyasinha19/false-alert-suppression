# Phase 8 Plan: Comprehensive Dark & Light Theme System

**Phase:** 8  
**Milestone:** v1.4 Complete UI/UX Expert Audit Implementation  
**Status:** In Progress  

## Goals

Implement a complete, production-grade Dark & Light theme system across the entire DNAC Ops Center Dashboard: CSS token architecture for dark and light surfaces, high-contrast dark mode aesthetics, an intuitive header theme toggle switch, and persistence in `localStorage`.

## Requirements Covered

- `THEME-01`: User can switch between Light and Dark themes with saved `localStorage` preference.
- `THEME-02`: System applies cohesive dark mode tokens to header backdrops, cards, tables, and dialogs.

## Design Contract Reference

- See `08-UI-SPEC.md` for complete token specifications, dark mode surface hierarchy (`#0a0e17` canvas, `#111827` surface, `#1e293b` hover/tertiary), and `.theme-toggle-btn` styling.

## Execution Waves

### Wave 1: Token Architecture & CSS Dark Mode Polish (`dashboard/src/index.css` & `dashboard/src/App.css`)

1. **Root & Dark Token Declarations (`index.css`)**:
   - Explicitly define `:root, [data-theme="light"]` and `[data-theme="dark"]` token sets.
   - Set `color-scheme: dark;` on dark mode root for native input and scrollbar adaptation.
   - Configure deep midnight canvas (`#0a0e17`), elevated card surfaces (`#111827`), high-contrast borders (`rgba(255, 255, 255, 0.08)`), crisp typography (`#f8fafc` primary, `#cbd5e1` secondary), and translucent accent tints.
2. **Component & Form Dark Mode Support (`App.css`)**:
   - Style `.theme-toggle-btn`: pill button with sun/moon icon, smooth rotation on toggle, subtle border glow, and tooltip indicator.
   - Adjust form inputs, `.filter-select`, `.search-input`, and date-time controls to ensure contrast and dark dropdown chevron indicators.
   - Ensure sticky table headers, glass cards, modal dialogs, and slide-out panels seamlessly adapt without hardcoded white backgrounds.

### Wave 2: Theme State Management & Component Integration (`dashboard/src/App.jsx`, `dashboard/src/FalseAlertMetrics.jsx`, `dashboard/src/AlertPatterns.jsx`)

3. **Persistent Theme State in `App.jsx`**:
   - Initialize theme state from `localStorage.getItem('app_theme')`, falling back to `window.matchMedia('(prefers-color-scheme: dark)')` or `'light'`.
   - Synchronize `document.documentElement.setAttribute('data-theme', theme)` and update `localStorage` on state change.
   - Add the `<button className="theme-toggle-btn">` into `.content-header-actions` next to `.live-badge`.
4. **Chart Dark Theme Adaptation**:
   - Update `TOOLTIP_STYLE` in `FalseAlertMetrics.jsx` and `AlertPatterns.jsx` to use dynamic CSS variables (`var(--bg-secondary)`, `var(--text-primary)`, `var(--card-border)`).
   - Update `CartesianGrid` stroke to `var(--card-border)`.

### Wave 3: Verification & Visual Polish

5. **Automated Verification**:
   - Run `npm run lint` in `dashboard/` to verify zero linting errors.
   - Run `npm run build` in `dashboard/` to verify clean production compilation.
   - Run `python -m pytest -q` to verify backend integrity.
6. **Live Browser Verification**:
   - Use `browser_subagent` to test `http://localhost:5173/`.
   - Verify theme toggle button exists in header and displays current mode.
   - Toggle to Dark Mode: inspect Alert Metrics, Network Operations, and Alert Patterns to verify high-contrast dark surfaces, legible text, and styled tables.
   - Open Event Detail Modal or Chat Drawer to verify dark mode dialog aesthetics.
   - Reload page to verify dark mode persists via `localStorage`.
   - Toggle back to Light Mode and verify seamless transition.
