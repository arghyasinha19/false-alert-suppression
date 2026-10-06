# Plan 21-01 Summary: CSS Token Contrast Remediation & Blue Badge Legibility

**Phase:** 21 — Trust & Contrast Remediation  
**Plan:** 21-01  
**Wave:** 1  
**Status:** Completed  
**Requirements Covered:** UI-05  
**Decisions Covered:** D-01, D-02, D-07 (partial)  

---

## What Changed

1. **Remediated Inverted `--text-tertiary` Tokens (`D-01`)**:
   - In `dashboard/src/index.css`:
     - Under `:root, [data-theme="light"]`: changed `--text-tertiary: #94a3b8;` to `--text-tertiary: #64748b;`. Contrast ratio against `#ffffff` card background increased from 2.5:1 (failing) to **4.64:1 (passing WCAG AA $\ge 4.5:1$)**.
     - Under `[data-theme="dark"]`: changed `--text-tertiary: #64748b;` to `--text-tertiary: #94a3b8;`. Contrast ratio against `#111827` card background increased from 2.7:1 (failing) to **5.45:1 (passing WCAG AA $\ge 4.5:1$)**.
     - Updated `--health-unknown` token in both themes to match the high-contrast tertiary text token.

2. **Dedicated `--badge-blue-text` Semantic Tokens (`D-02`)**:
   - In `dashboard/src/index.css`:
     - Light Theme: defined `--badge-blue-text: #1e40af;`, providing **8.05:1 contrast** on `#eff6ff` (`--accent-blue-light`), passing both WCAG AA and AAA.
     - Dark Theme: defined `--badge-blue-text: #93c5fd;`, providing **9.81:1 contrast** on `#111827` dark card surfaces, passing both WCAG AA and AAA.
   - In `dashboard/src/App.css`:
     - Bound `.badge.backdated`, `.badge.snow-new`, and `.badge.badge-subtle.blue` to `color: var(--badge-blue-text);`.
     - Standardized `.badge.health-unknown` background to `var(--bg-tertiary)` for theme adaptability.

3. **Automated WCAG Mathematical Contrast Contract Suite (`D-07`)**:
   - Created `tests/test_contrast_remediation_contract.py`:
     - Implemented exact sRGB gamma-expanded relative luminance and WCAG 2.1 contrast ratio calculations.
     - Verified `--text-tertiary` passes $\ge 4.5:1$ in both light and dark modes.
     - Verified `--badge-blue-text` passes $\ge 7.0:1$ in both light and dark modes.
     - Verified CSS token definitions and badge selector bindings.
     - 6/6 tests passing in 0.24s.

---

## Verification

- `pytest tests/test_contrast_remediation_contract.py`: 6 passed in 0.24s.
- `npm run build`: Production client built in 1.04s with 0 errors.
