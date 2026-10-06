"""
Table Visibility, Scrollbars, Edge Masks & Vertical Capping Contract Tests (Phase 20 - UI-04)
=============================================================================================
Validates:
1. High-contrast 8px table scrollbars (width: 8px, height: 8px, border-radius: 6px) with slate thumbs
   and sunken tracks meeting WCAG 3:1 non-text contrast in dark & light themes.
2. 28px horizontal edge masks (::before / ::after) with pointer-events: none, z-index: 4, and bottom 8px clearance.
3. Sticky table headers (position: sticky; top: 0; backdrop-filter: blur).
4. TableScrollWrapper integration across FalseAlertMetrics, NetworkOperations, and AlertPatterns.
5. Header counter chips ("Showing X of Y") with active filter indicators.
6. SRE Details Drawer alert list capping at 5 items with progressive disclosure toggle.
"""

import os
import re
import pytest

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_CSS_PATH = os.path.join(project_root, "dashboard", "src", "index.css")
APP_CSS_PATH = os.path.join(project_root, "dashboard", "src", "App.css")
WRAPPER_JSX_PATH = os.path.join(project_root, "dashboard", "src", "components", "TableScrollWrapper.jsx")
FALSE_ALERT_JSX_PATH = os.path.join(project_root, "dashboard", "src", "FalseAlertMetrics.jsx")
NOC_JSX_PATH = os.path.join(project_root, "dashboard", "src", "NetworkOperations.jsx")
PATTERNS_JSX_PATH = os.path.join(project_root, "dashboard", "src", "AlertPatterns.jsx")


@pytest.fixture(scope="module")
def index_css_content():
    assert os.path.exists(INDEX_CSS_PATH), f"index.css not found at {INDEX_CSS_PATH}"
    with open(INDEX_CSS_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def app_css_content():
    assert os.path.exists(APP_CSS_PATH), f"App.css not found at {APP_CSS_PATH}"
    with open(APP_CSS_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def wrapper_jsx_content():
    assert os.path.exists(WRAPPER_JSX_PATH), f"TableScrollWrapper.jsx not found at {WRAPPER_JSX_PATH}"
    with open(WRAPPER_JSX_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def false_alert_jsx_content():
    assert os.path.exists(FALSE_ALERT_JSX_PATH), f"FalseAlertMetrics.jsx not found at {FALSE_ALERT_JSX_PATH}"
    with open(FALSE_ALERT_JSX_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def noc_jsx_content():
    assert os.path.exists(NOC_JSX_PATH), f"NetworkOperations.jsx not found at {NOC_JSX_PATH}"
    with open(NOC_JSX_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def patterns_jsx_content():
    assert os.path.exists(PATTERNS_JSX_PATH), f"AlertPatterns.jsx not found at {PATTERNS_JSX_PATH}"
    with open(PATTERNS_JSX_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_table_scrollbar_geometry_and_contrast(index_css_content):
    """Verify high-contrast 8px table scrollbars and sunken track styling."""
    assert ".table-scroll-container::-webkit-scrollbar" in index_css_content, (
        "index.css must define scrollbar geometry for .table-scroll-container"
    )
    assert "width: 8px" in index_css_content and "height: 8px" in index_css_content, (
        "Table scrollbars must be 8px width and height"
    )
    assert "rgba(148, 163, 184, 0.45)" in index_css_content, (
        "Dark mode slate thumb must use rgba(148, 163, 184, 0.45)"
    )
    assert "rgba(100, 116, 139, 0.4" in index_css_content, (
        "Light mode slate thumb must use rgba(100, 116, 139, 0.40)"
    )
    assert "rgba(255, 255, 255, 0.04)" in index_css_content, (
        "Sunken track must use subtle rgba(255, 255, 255, 0.04) in dark theme"
    )


def test_horizontal_edge_mask_contract(app_css_content):
    """Verify 28px edge masks with bottom 8px clearance and pointer-events: none."""
    assert ".table-scroll-wrapper::before" in app_css_content, (
        "App.css must define left edge mask .table-scroll-wrapper::before"
    )
    assert ".table-scroll-wrapper::after" in app_css_content, (
        "App.css must define right edge mask .table-scroll-wrapper::after"
    )
    assert "width: 28px" in app_css_content, (
        "Edge masks must specify 28px width"
    )
    assert "bottom: 8px" in app_css_content, (
        "Edge masks must leave bottom 8px clearance for horizontal scrollbar track"
    )
    assert "pointer-events: none" in app_css_content, (
        "Edge masks must have pointer-events: none"
    )
    assert "has-overflow-left" in app_css_content and "has-overflow-right" in app_css_content, (
        "App.css must toggle mask visibility on overflow state classes"
    )


def test_sticky_headers_contract(app_css_content):
    """Verify sticky table headers lock column labels at top: 0 with backdrop blur."""
    assert "position: sticky" in app_css_content, "App.css must define sticky headers"
    assert "top: 0" in app_css_content, "Sticky headers must pin to top: 0"
    assert "backdrop-filter: blur" in app_css_content, "Sticky headers must use backdrop-filter blur"


def test_table_scroll_wrapper_component_and_integration(
    wrapper_jsx_content, false_alert_jsx_content, noc_jsx_content, patterns_jsx_content
):
    """Verify TableScrollWrapper component manages overflow and is integrated across all views."""
    assert "hasOverflowLeft" in wrapper_jsx_content and "hasOverflowRight" in wrapper_jsx_content, (
        "TableScrollWrapper must manage overflow states"
    )
    assert "TableScrollWrapper" in false_alert_jsx_content, (
        "FalseAlertMetrics.jsx must import and use TableScrollWrapper"
    )
    assert "TableScrollWrapper" in noc_jsx_content, (
        "NetworkOperations.jsx must import and use TableScrollWrapper"
    )
    assert "TableScrollWrapper" in patterns_jsx_content, (
        "AlertPatterns.jsx must import and use TableScrollWrapper"
    )


def test_header_counter_chips_and_list_capping(
    false_alert_jsx_content, noc_jsx_content, patterns_jsx_content, app_css_content
):
    """Verify header counter chips and vertical list capping with expansion toggles."""
    assert ".table-counter-chip" in app_css_content, (
        "App.css must define styling for .table-counter-chip"
    )
    assert "table-counter-chip" in false_alert_jsx_content, (
        "FalseAlertMetrics.jsx must render .table-counter-chip"
    )
    assert "table-counter-chip" in noc_jsx_content, (
        "NetworkOperations.jsx must render .table-counter-chip"
    )
    assert "table-counter-chip" in patterns_jsx_content, (
        "AlertPatterns.jsx must render .table-counter-chip"
    )
    assert "Showing " in false_alert_jsx_content, (
        "FalseAlertMetrics must contain 'Showing ' counter copy"
    )
    assert "Showing " in noc_jsx_content, (
        "NetworkOperations must contain 'Showing ' counter copy"
    )
    assert "Showing " in patterns_jsx_content, (
        "AlertPatterns must contain 'Showing ' counter copy"
    )


def test_drawer_alert_capping_contract(noc_jsx_content):
    """Verify SRE Details Drawer caps active alerts at 5 items with toggle button."""
    assert "drawerAlertsExpanded" in noc_jsx_content, (
        "NetworkOperations.jsx must manage drawerAlertsExpanded state"
    )
    assert "detail-alerts-toggle-btn" in noc_jsx_content, (
        "NetworkOperations.jsx must render .detail-alerts-toggle-btn"
    )
    assert "more alerts" in noc_jsx_content and "fewer alerts" in noc_jsx_content, (
        "Drawer must toggle between 'Show X more alerts' and 'Show fewer alerts'"
    )
