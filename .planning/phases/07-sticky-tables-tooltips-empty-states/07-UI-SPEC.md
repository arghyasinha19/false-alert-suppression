---
phase: 7
slug: sticky-tables-tooltips-empty-states
status: approved
shadcn_initialized: false
preset: none
created: 2026-09-30
---

# Phase 7 — UI Design Contract: Sticky Tables, Tooltips & Empty States

> Visual and interaction contract for sticky table headers, robust cell truncation with hover tooltips, and illustrated empty states for zero-match filters.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (Vanilla CSS custom design tokens) |
| Preset | not applicable |
| Component library | none (custom React components) |
| Icon library | lucide-react (`SearchX`, `FilterX`, `ServerOff`, `RotateCcw`, `Info`, `Layers`) |
| Font | Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif |
| Monospace Font | ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace |

---

## 1. Sticky Table Headers (`TABLE-01`)

- **Traceability Matrix (`.data-table th`) & Device Ranking (`.rank-table th`):**
  - `position: sticky; top: 0;`
  - `background: var(--bg-secondary);`
  - `z-index: 10;`
  - `box-shadow: 0 1px 0 var(--card-border);`
  - `backdrop-filter: blur(8px);`
- **Table Containers:**
  - Traceability Matrix: `max-height: 480px; overflow-y: auto; overflow-x: auto;`
  - Device Ranking: `max-height: 440px; overflow-y: auto; overflow-x: auto;`

---

## 2. Cell Truncation & Hover Tooltips (`TABLE-02`)

- **Text Truncation:**
  - `overflow: hidden; text-overflow: ellipsis; white-space: nowrap;`
- **Tooltips on Truncated Content:**
  - Event ID: Full event ID in `title`
  - Device Name: Full hostname and filter hint in `title`
  - Issue Name: Full descriptive issue text in `title`
  - Timestamp: Complete ISO / localized date-time in `title`
  - Classification: Predicted class + confidence percentage in `title`
  - ServiceNow: Complete action and ticket reference in `title`
- **Header Tooltips:**
  - Clear explanations for all Device Ranking metric columns (Rank, Device, Total Alerts, Genuine Alerts, False/Suppressed, Auto-Resolving, Uncertain, SNOW Created, SNOW Reopened, Volume).

---

## 3. Rich Empty States (`STATE-01`)

- **Component Structure (`.table-empty-state`):**
  - Container: Centered flex column with `padding: 3rem 1.5rem;`
  - Icon badge: 44x44px circular backdrop (`background: rgba(37, 99, 235, 0.08); color: var(--accent-blue);`) containing `SearchX` or `FilterX`.
  - Headline: `font-size: 0.95rem; font-weight: 700; color: var(--text-primary); margin: 0.75rem 0 0.35rem;`
  - Body: `font-size: 0.82rem; color: var(--text-secondary); max-width: 420px; line-height: 1.5; margin: 0 0 1rem;`
  - Action Button: Pill button with `RotateCcw` icon (`padding: 0.4rem 0.9rem; font-size: 0.78rem; font-weight: 600; border-radius: 6px;`) allowing instant reset of active filters.

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS

**Approval:** Approved 2026-09-30
