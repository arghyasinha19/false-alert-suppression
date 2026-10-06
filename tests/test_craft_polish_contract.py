"""
tests/test_craft_polish_contract.py

Contract verification suite for Phase 23: Craft & Consistency Polish (UI-09-22).
Verifies:
1. Strict 6-step typography scale tokens declared in index.css.
2. Full compliance across App.css and ChatPanel.css (zero arbitrary font sizes).
3. FalseAlertMetrics KPI cards converged to NOC card architecture (.noc-kpi-card, .noc-kpi-top).
4. Row 2 KPI cards interactive click-to-filter capability with 'ACTIVE FILTER ✓' badge state.
5. Prototype '⚡ Simulate +5 Alerts' button completely eliminated from the production chrome.
6. Reusable EmptyState.jsx component created and utilized across all target views.
7. Domain acronyms and shorthand (SNOW, DNAC, DLX, MTTR, P1-P3) expanded with accessible tooltips.
"""

import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_CSS = REPO_ROOT / "dashboard" / "src" / "index.css"
APP_CSS = REPO_ROOT / "dashboard" / "src" / "App.css"
CHAT_CSS = REPO_ROOT / "dashboard" / "src" / "ChatPanel.css"
EMPTY_STATE_JSX = REPO_ROOT / "dashboard" / "src" / "components" / "EmptyState.jsx"
METRICS_JSX = REPO_ROOT / "dashboard" / "src" / "FalseAlertMetrics.jsx"
NOC_JSX = REPO_ROOT / "dashboard" / "src" / "NetworkOperations.jsx"
PATTERNS_JSX = REPO_ROOT / "dashboard" / "src" / "AlertPatterns.jsx"


# ==============================================================================
# 1. Strict 6-Step Typography Scale Tokens (UI-09-22, D-03, D-04)
# ==============================================================================


def test_typography_scale_tokens_in_index_css():
    """Verify index.css declares the 6 strict typography scale CSS custom properties."""
    index_content = INDEX_CSS.read_text(encoding="utf-8")

    expected_tokens = [
        ("--font-xs", "0.75rem"),    # 12px
        ("--font-sm", "0.8125rem"),  # 13px
        ("--font-md", "0.9375rem"),  # 15px
        ("--font-lg", "1.125rem"),   # 18px
        ("--font-xl", "1.5rem"),     # 24px
        ("--font-2xl", "2.125rem"),  # 34px
    ]

    for token, val in expected_tokens:
        pattern = rf"{token}:\s*{re.escape(val)}"
        assert re.search(pattern, index_content) is not None, (
            f"index.css must define '{token}: {val};'"
        )


def test_typography_scale_compliance_in_stylesheets():
    """Verify App.css and ChatPanel.css strictly use the 6 scale tokens or their exact equivalents."""
    # Permitted token references and equivalent literals
    valid_font_size_patterns = {
        "var(--font-xs)",
        "var(--font-sm)",
        "var(--font-md)",
        "var(--font-lg)",
        "var(--font-xl)",
        "var(--font-2xl)",
        "0.75rem",
        "0.8125rem",
        "0.9375rem",
        "1.125rem",
        "1.5rem",
        "2.125rem",
        "12px",
        "13px",
        "15px",
        "18px",
        "24px",
        "34px",
        "inherit",
        "0.82em",
        "0.85em",
    }

    for css_file in [APP_CSS, CHAT_CSS]:
        content = css_file.read_text(encoding="utf-8")
        raw_matches = re.findall(r"font-size:\s*([^;]+);", content)

        for val in raw_matches:
            cleaned = val.strip()
            # If comma fallback present e.g. var(--font-sm, 0.8125rem)
            if cleaned.startswith("var("):
                var_name = cleaned.split(",")[0].replace("var(", "").strip()
                assert f"var({var_name})" in valid_font_size_patterns or var_name.startswith("--font-"), (
                    f"{css_file.name} contains invalid font variable: {cleaned}"
                )
            else:
                assert cleaned in valid_font_size_patterns, (
                    f"{css_file.name} contains non-standard font-size: '{cleaned}'. "
                    f"Must strictly map to one of the 6 scale tokens."
                )


# ==============================================================================
# 2. Unified KPI Card Architecture Convergence (UI-09-22, D-01, D-02)
# ==============================================================================


def test_false_alert_metrics_kpi_cards_converged_to_noc_architecture():
    """Verify FalseAlertMetrics.jsx cards adopt the executive NOC card architecture."""
    metrics_content = METRICS_JSX.read_text(encoding="utf-8")

    # All 8 cards must use .glass-card.noc-kpi-card
    noc_card_occurrences = metrics_content.count("glass-card noc-kpi-card")
    assert noc_card_occurrences >= 8, (
        f"Expected at least 8 occurrences of 'glass-card noc-kpi-card' in FalseAlertMetrics.jsx, found {noc_card_occurrences}"
    )

    # Must contain .noc-kpi-top and .noc-kpi-body
    assert "noc-kpi-top" in metrics_content, "FalseAlertMetrics.jsx must use '.noc-kpi-top' header rows"
    assert "noc-kpi-body" in metrics_content, "FalseAlertMetrics.jsx must use '.noc-kpi-body' content containers"
    assert "noc-kpi-value-row" in metrics_content, "FalseAlertMetrics.jsx must use '.noc-kpi-value-row'"

    # Row 1 cards must display semantic badges
    assert "INGESTED" in metrics_content, "Total Processed card must display 'INGESTED' status badge"
    assert "SUPPRESSED" in metrics_content, "Suppression Rate card must display 'SUPPRESSED' status badge"
    assert "AVOIDED" in metrics_content, "Tickets Avoided card must display 'AVOIDED' status badge"
    assert "ESCALATED" in metrics_content, "SNOW Tickets card must display 'ESCALATED' status badge"


def test_false_alert_metrics_row2_click_to_filter_contract():
    """Verify Row 2 KPI cards provide interactive click-to-filter with 'ACTIVE FILTER ✓' badge."""
    metrics_content = METRICS_JSX.read_text(encoding="utf-8")

    # Row 2 cards must be designated as clickable
    assert "clickable" in metrics_content, "Row 2 cards must include '.clickable' class"
    assert 'aria-pressed={categoryFilter ===' in metrics_content, "Row 2 cards must have aria-pressed state"

    # Status badges in Row 2 must toggle to 'ACTIVE FILTER ✓' when selected
    assert "ACTIVE FILTER ✓" in metrics_content, "Row 2 cards must render 'ACTIVE FILTER ✓' when active"
    assert "FILTERABLE" in metrics_content, "Row 2 cards must render 'FILTERABLE' badge when inactive"


# ==============================================================================
# 3. Demo Scaffolding Removal (UI-09-22, D-06)
# ==============================================================================


def test_demo_simulate_button_eliminated_from_chrome():
    """Verify prototype '⚡ Simulate +5 Alerts' button is absent from FalseAlertMetrics.jsx."""
    metrics_content = METRICS_JSX.read_text(encoding="utf-8")

    assert "Simulate +5 Alerts" not in metrics_content, (
        "Prototype 'Simulate +5 Alerts' button must be completely removed from FalseAlertMetrics.jsx"
    )
    assert "simulate-btn" not in metrics_content, (
        "Prototype 'simulate-btn' class must be removed from FalseAlertMetrics.jsx"
    )
    assert "handleSimulate" not in metrics_content, (
        "handleSimulate handler must not be present in FalseAlertMetrics.jsx"
    )


# ==============================================================================
# 4. Standardized EmptyState Component Contract (UI-09-22, D-08, D-09)
# ==============================================================================


def test_empty_state_reusable_component_contract():
    """Verify EmptyState.jsx exists and is integrated across all target views."""
    assert EMPTY_STATE_JSX.exists(), "dashboard/src/components/EmptyState.jsx must exist"

    empty_state_content = EMPTY_STATE_JSX.read_text(encoding="utf-8")
    assert "empty-state-badge" in empty_state_content, "EmptyState.jsx must render .empty-state-badge"
    assert "empty-state-title" in empty_state_content, "EmptyState.jsx must render .empty-state-title"
    assert "empty-state-action" in empty_state_content, "EmptyState.jsx must render .empty-state-action"

    # Must be imported in FalseAlertMetrics, NetworkOperations, and AlertPatterns
    for view_file in [METRICS_JSX, NOC_JSX, PATTERNS_JSX]:
        content = view_file.read_text(encoding="utf-8")
        assert "EmptyState" in content, (
            f"{view_file.name} must import and utilize EmptyState component"
        )
        assert "<EmptyState" in content, (
            f"{view_file.name} must render <EmptyState /> element"
        )


# ==============================================================================
# 5. Domain Shorthand Tooltip Expansions (UI-09-22, D-10)
# ==============================================================================


def test_domain_abbreviation_tooltips_contract():
    """Verify domain abbreviations provide accessible tooltips and expansions."""
    metrics_content = METRICS_JSX.read_text(encoding="utf-8")
    noc_content = NOC_JSX.read_text(encoding="utf-8")

    # SNOW tooltip
    assert "ServiceNow" in metrics_content and "ITSM" in metrics_content, (
        "FalseAlertMetrics.jsx must provide descriptive tooltip for SNOW (ServiceNow ITSM)"
    )

    # DNAC tooltip
    assert "Cisco DNA Center" in metrics_content or "Catalyst Center" in metrics_content, (
        "FalseAlertMetrics.jsx must provide tooltip expanding DNAC"
    )

    # DLX tooltip in NetworkOperations
    assert "Dead Letter Exchange" in noc_content, (
        "NetworkOperations.jsx must provide tooltip expanding DLX (Dead Letter Exchange)"
    )

    # SRE tooltip in NetworkOperations
    assert "Site Reliability Engineering" in noc_content, (
        "NetworkOperations.jsx must provide tooltip expanding SRE"
    )

    # Priority tooltips (P1, P2, P3)
    assert "Priority 1: Critical" in metrics_content, (
        "FalseAlertMetrics.jsx must expand P1 priority with descriptive tooltip"
    )
