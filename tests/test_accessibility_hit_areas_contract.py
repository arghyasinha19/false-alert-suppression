"""
tests/test_accessibility_hit_areas_contract.py

Contract verification suite for Phase 22: Accessibility & Hit Areas.
Verifies WCAG 2.1 AA hit areas (32px visual, 44x44px touch targets),
typography scale (12px min for headers/badges, 13px for data/inputs, 0 sub-12px CSS),
sidebar semantic buttons and focus rings, non-modal docked chat panel architecture,
and form labels / table captions / scope="col" / aria-sort across all dashboard views.
"""

import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_CSS = REPO_ROOT / "dashboard" / "src" / "index.css"
APP_CSS = REPO_ROOT / "dashboard" / "src" / "App.css"
CHAT_CSS = REPO_ROOT / "dashboard" / "src" / "ChatPanel.css"
APP_JSX = REPO_ROOT / "dashboard" / "src" / "App.jsx"
CHAT_JSX = REPO_ROOT / "dashboard" / "src" / "ChatPanel.jsx"
METRICS_JSX = REPO_ROOT / "dashboard" / "src" / "FalseAlertMetrics.jsx"
NOC_JSX = REPO_ROOT / "dashboard" / "src" / "NetworkOperations.jsx"
PATTERNS_JSX = REPO_ROOT / "dashboard" / "src" / "AlertPatterns.jsx"


# ==============================================================================
# 1. Hit Area Expansion & Touch Target Contract (UI-07, D-04, D-05)
# ==============================================================================


def test_hit_area_32px_minimum_in_app_css():
    """Verify App.css declares min-height: 32px for buttons, pills, search, and selects."""
    css_content = APP_CSS.read_text(encoding="utf-8")

    # Match block containing min-height: 32px
    min_height_match = re.search(
        r"([^{]+)\{\s*[^}]*min-height:\s*32px;?[^}]*\}",
        css_content,
        re.DOTALL,
    )
    assert min_height_match is not None, "App.css must contain a rule with 'min-height: 32px;'"

    matched_selectors = min_height_match.group(1)
    required_selectors = [
        ".btn",
        ".filter-btn",
        ".filter-pill",
        ".filter-search",
        ".filter-select",
        ".filter-input-datetime",
        ".datetime-action-btn",
        ".noc-view-btn",
        ".table-expand-toggle-btn",
    ]
    for sel in required_selectors:
        assert sel in matched_selectors, f"Expected selector '{sel}' in 32px min-height rule"


def test_touch_target_44px_expander_in_app_css():
    """Verify App.css defines 44x44px touch target expander for compact icons."""
    css_content = APP_CSS.read_text(encoding="utf-8")

    assert ".touch-target-expand" in css_content, "App.css must declare .touch-target-expand"
    assert "min-width: 44px" in css_content, "App.css must declare min-width: 44px"
    assert "min-height: 44px" in css_content, "App.css must declare min-height: 44px"

    # Verify compact icons included in the 44px pseudo-element expander
    compact_icons = [
        ".sidebar-collapse-toggle::before",
        ".chat-close-btn::before",
        ".demo-banner-dismiss-btn::before",
        ".table-sort-btn::before",
        ".detail-panel-close::before",
    ]
    for icon_sel in compact_icons:
        assert icon_sel in css_content, f"Expected pseudo-element '{icon_sel}' in touch target expander"


# ==============================================================================
# 2. Typography Scale & Zero Sub-12px CSS Contract (UI-07, D-06)
# ==============================================================================


def test_zero_sub_12px_css_in_stylesheets():
    """Verify zero CSS declarations exist below 12px (0.75rem or 12px) in stylesheets."""
    for stylesheet in [APP_CSS, CHAT_CSS, INDEX_CSS]:
        content = stylesheet.read_text(encoding="utf-8")
        lines = content.splitlines()

        for idx, line in enumerate(lines, 1):
            # Check rem values < 0.75rem
            rem_match = re.search(r"font-size:\s*([0-9.]+)rem;", line)
            if rem_match:
                rem_val = float(rem_match.group(1))
                assert rem_val >= 0.75, (
                    f"{stylesheet.name}:{idx} has sub-12px rem font-size: {line.strip()}"
                )

            # Check px values < 12px
            px_match = re.search(r"font-size:\s*([0-9.]+)px;", line)
            if px_match:
                px_val = float(px_match.group(1))
                assert px_val >= 12, (
                    f"{stylesheet.name}:{idx} has sub-12px px font-size: {line.strip()}"
                )


def test_table_typography_standards():
    """Verify table headers are 12px (0.75rem) uppercase and body cells are at least 13px (0.8125rem)."""
    app_css = APP_CSS.read_text(encoding="utf-8")

    # Table headers uppercase and 0.75rem
    assert ".data-table th {" in app_css
    assert ".rank-table th {" in app_css
    assert ".noc-sre-table thead th {" in app_css

    # Table body cells >= 0.8125rem
    data_table_size = re.search(r"\.data-table\s*\{[^}]*font-size:\s*([0-9.]+)rem", app_css)
    assert data_table_size and float(data_table_size.group(1)) >= 0.8125

    rank_table_size = re.search(r"\.rank-table\s*\{[^}]*font-size:\s*([0-9.]+)rem", app_css)
    assert rank_table_size and float(rank_table_size.group(1)) >= 0.8125


# ==============================================================================
# 3. Sidebar Semantic Buttons & Focus Visible Rings (UI-16, D-01, D-02)
# ==============================================================================


def test_sidebar_semantic_buttons_and_aria_attributes():
    """Verify App.jsx uses native <button type="button"> for sidebar nav and toggle with ARIA."""
    app_jsx = APP_JSX.read_text(encoding="utf-8")

    # Sidebar nav items are buttons, not divs
    assert '<button' in app_jsx
    assert 'type="button"' in app_jsx
    assert "aria-current={activeView === item.id ? 'page' : undefined}" in app_jsx

    # Sidebar collapse toggle has aria-expanded and aria-label
    assert 'aria-expanded={!sidebarCollapsed}' in app_jsx
    assert "aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}" in app_jsx

    # Chat toggle has aria-expanded, aria-controls, and aria-label
    assert 'aria-controls="ops-assistant-panel"' in app_jsx
    assert 'aria-expanded={chatOpen}' in app_jsx

    # Global keyboard listener for Ctrl+/
    assert "(e.ctrlKey || e.metaKey) && e.key === '/'" in app_jsx


def test_accessible_focus_visible_outlines():
    """Verify App.css declares 2px solid focus visible rings with 2px offset."""
    app_css = APP_CSS.read_text(encoding="utf-8")

    assert ".sidebar-nav-item:focus-visible" in app_css
    assert "outline: 2px solid var(--accent-blue);" in app_css
    assert "outline-offset: 2px;" in app_css


# ==============================================================================
# 4. Non-Modal Docked Chat Panel Contract (UI-08, D-07, D-08, D-09, D-10)
# ==============================================================================


def test_docked_chat_panel_architecture():
    """Verify ChatPanel.jsx implements semantic <aside> region and Escape key listener."""
    chat_jsx = CHAT_JSX.read_text(encoding="utf-8")
    app_css = APP_CSS.read_text(encoding="utf-8")

    # Semantic aside landmark
    assert '<aside' in chat_jsx
    assert 'id="ops-assistant-panel"' in chat_jsx
    assert 'role="region"' in chat_jsx
    assert 'aria-label="DNAC Ops Assistant"' in chat_jsx
    assert 'className="chat-panel docked"' in chat_jsx

    # Escape key listener and trigger focus restoration
    assert "e.key === 'Escape'" in chat_jsx
    assert "triggerRef.current.focus()" in chat_jsx

    # No blocking overlay in docked mode
    assert "chat-overlay" not in chat_jsx

    # App.css insets content-area when chat is open
    assert ".app-shell.chat-open .content-area {" in app_css
    assert "margin-right: var(--chat-panel-width, 440px);" in app_css


# ==============================================================================
# 5. Form Labels, Table Captions, scope="col", and aria-sort (UI-17, D-11, D-12, D-13)
# ==============================================================================


def test_screen_reader_utility_class():
    """Verify both index.css and App.css provide the .sr-only accessible clipping class."""
    for css_file in [INDEX_CSS, APP_CSS]:
        content = css_file.read_text(encoding="utf-8")
        assert ".sr-only" in content, f"{css_file.name} must declare .sr-only"
        assert "clip: rect(0, 0, 0, 0);" in content, f"{css_file.name} .sr-only must have clip: rect"


def test_accessible_form_labels_in_views():
    """Verify all form controls have corresponding <label htmlFor="..."> elements."""
    metrics_jsx = METRICS_JSX.read_text(encoding="utf-8")
    noc_jsx = NOC_JSX.read_text(encoding="utf-8")

    # FalseAlertMetrics labels
    assert 'htmlFor="device-filter-select"' in metrics_jsx
    assert 'htmlFor="time-range-select"' in metrics_jsx
    assert 'htmlFor="custom-start-time"' in metrics_jsx
    assert 'htmlFor="custom-end-time"' in metrics_jsx
    assert 'htmlFor="matrix-search-scope"' in metrics_jsx
    assert 'htmlFor="matrix-search-input"' in metrics_jsx
    assert 'htmlFor="matrix-device-filter"' in metrics_jsx
    assert 'htmlFor="matrix-severity-filter"' in metrics_jsx
    assert 'htmlFor="matrix-outcome-filter"' in metrics_jsx
    assert 'htmlFor="matrix-snow-filter"' in metrics_jsx

    # NetworkOperations labels
    assert 'htmlFor="noc-device-search-input"' in noc_jsx
    assert 'htmlFor="noc-json-search-input"' in noc_jsx


def test_table_captions_and_header_scopes():
    """Verify all data tables include <caption className="sr-only"> and scope="col" on <th>."""
    views = [
        (METRICS_JSX, "FalseAlertMetrics"),
        (NOC_JSX, "NetworkOperations"),
        (PATTERNS_JSX, "AlertPatterns"),
    ]

    for view_path, view_name in views:
        content = view_path.read_text(encoding="utf-8")

        # Must contain sr-only caption
        assert '<caption className="sr-only">' in content, (
            f"{view_name} must contain an accessible table caption"
        )

        # Must declare scope="col" on table headers
        assert 'scope="col"' in content, (
            f"{view_name} must declare scope=\"col\" on <th> cells"
        )


def test_sortable_table_headers_aria_sort():
    """Verify sortable table headers declare aria-sort attribute."""
    metrics_jsx = METRICS_JSX.read_text(encoding="utf-8")
    noc_jsx = NOC_JSX.read_text(encoding="utf-8")

    assert "aria-sort=" in metrics_jsx, "FalseAlertMetrics must declare aria-sort on sortable headers"
    assert "aria-sort=" in noc_jsx, "NetworkOperations must declare aria-sort on sortable headers"
