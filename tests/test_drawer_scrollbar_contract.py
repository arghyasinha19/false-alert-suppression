"""
NOC Details Drawer Scrollbar & Layout Contract Tests (Phase 16)
==============================================================
Validates:
1. Flexbox architecture on .detail-panel (height: 100vh, overflow: hidden, display: flex)
2. Scrollable container semantics on .detail-panel-body (flex: 1, min-height: 0, overflow-y: auto)
3. Dedicated, visible scrollbar styling in dark mode and light mode (DRAWER-01)
4. Anchored headers, tabs, and action bar (DRAWER-02)
5. Clean DOM sequence in NetworkOperations.jsx (DRAWER-03)
"""

import os
import re
import pytest

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_CSS_PATH = os.path.join(project_root, "dashboard", "src", "App.css")
NETWORK_OPS_PATH = os.path.join(project_root, "dashboard", "src", "NetworkOperations.jsx")


@pytest.fixture(scope="module")
def app_css_content():
    assert os.path.exists(APP_CSS_PATH), f"App.css not found at {APP_CSS_PATH}"
    with open(APP_CSS_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def network_ops_content():
    assert os.path.exists(NETWORK_OPS_PATH), f"NetworkOperations.jsx not found at {NETWORK_OPS_PATH}"
    with open(NETWORK_OPS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_detail_panel_container_flex_contract(app_css_content):
    """Verify .detail-panel is locked to viewport height with flexbox column and overflow hidden."""
    # Find .detail-panel rule block (not .detail-panel-*)
    match = re.search(r"\.detail-panel\s*\{([^}]+)\}", app_css_content)
    assert match is not None, ".detail-panel CSS rule block not found in App.css"
    block = match.group(1)

    assert "display: flex;" in block, ".detail-panel must specify display: flex"
    assert "flex-direction: column;" in block, ".detail-panel must specify flex-direction: column"
    assert "overflow: hidden;" in block, ".detail-panel outer container must have overflow: hidden"
    assert "100vh" in block, ".detail-panel must anchor to 100vh viewport height"


def test_detail_panel_body_scroll_contract(app_css_content):
    """Verify .detail-panel-body is configured as the single primary scrollable child."""
    # Check that .detail-panel-body defines flex: 1, min-height: 0, and overflow-y: auto
    match = re.search(r"\.detail-panel-body\s*\{([^}]+)\}", app_css_content)
    assert match is not None, ".detail-panel-body CSS rule block not found in App.css"
    block = match.group(1)

    assert "overflow-y: auto;" in block, ".detail-panel-body must have overflow-y: auto"
    assert "min-height: 0;" in block, ".detail-panel-body must have min-height: 0 for proper flex shrink/scroll"
    assert "flex: 1" in block or "flex-grow: 1" in block, ".detail-panel-body must expand via flex: 1"


def test_drawer_scrollbar_styling_dark_mode(app_css_content):
    """Verify dark mode (default) dedicated, high-contrast scrollbar rules are defined."""
    # Verify scrollbar-width and scrollbar-color
    assert "scrollbar-width: thin;" in app_css_content, "thin scrollbar-width required"
    assert "scrollbar-color: rgba(255, 255, 255," in app_css_content, (
        "Non-transparent scrollbar-color required for dark mode"
    )

    # Webkit scrollbar rules
    assert ".detail-panel-body::-webkit-scrollbar" in app_css_content
    assert ".detail-panel-body::-webkit-scrollbar-thumb" in app_css_content
    assert ".detail-panel-body::-webkit-scrollbar-track" in app_css_content

    # Ensure thumb is NOT transparent
    match_thumb = re.search(r"\.detail-panel-body::-webkit-scrollbar-thumb\s*\{([^}]+)\}", app_css_content)
    assert match_thumb is not None
    thumb_block = match_thumb.group(1)
    assert "rgba(255, 255, 255," in thumb_block, "Scrollbar thumb must have non-transparent white tint in dark mode"
    assert "background: transparent" not in thumb_block, "Scrollbar thumb must NOT be transparent by default"


def test_drawer_scrollbar_styling_light_mode(app_css_content):
    """Verify light mode dedicated scrollbar rules adapt with high contrast."""
    assert '[data-theme="light"] .detail-panel-body' in app_css_content
    assert '[data-theme="light"] .detail-panel-body::-webkit-scrollbar-thumb' in app_css_content

    # Check that light mode thumb uses dark tint (rgba(0, 0, 0, ...))
    match_light_thumb = re.search(
        r'\[data-theme="light"\]\s+\.detail-panel-body::-webkit-scrollbar-thumb\s*\{([^}]+)\}',
        app_css_content
    )
    assert match_light_thumb is not None, "Light mode scrollbar thumb rule not found"
    light_thumb_block = match_light_thumb.group(1)
    assert "rgba(0, 0, 0," in light_thumb_block, "Light mode scrollbar thumb must use dark tint for contrast"


def test_anchored_header_tabs_and_pinned_action_bar(app_css_content):
    """Verify header, tabs, and action bar cannot shrink away (flex-shrink: 0)."""
    # Header flex-shrink
    match_header = re.search(r"\.detail-panel-header\s*\{([^}]+)\}", app_css_content)
    assert match_header is not None
    assert "flex-shrink: 0;" in match_header.group(1), ".detail-panel-header must have flex-shrink: 0"

    # Tabs flex-shrink
    match_tabs = re.search(r"\.noc-drawer-tabs\s*\{([^}]+)\}", app_css_content)
    assert match_tabs is not None
    assert "flex-shrink: 0;" in match_tabs.group(1), ".noc-drawer-tabs must have flex-shrink: 0"

    # Action bar flex-shrink
    match_bar = re.search(r"\.noc-drawer-action-bar\s*\{([^}]+)\}", app_css_content)
    assert match_bar is not None
    assert "flex-shrink: 0;" in match_bar.group(1), ".noc-drawer-action-bar must have flex-shrink: 0"


def test_network_operations_dom_order(network_ops_content):
    """Verify NetworkOperations.jsx lays out detail-panel children in top-down sequence."""
    panel_idx = network_ops_content.find('className={`detail-panel')
    assert panel_idx != -1, "detail-panel container not found in NetworkOperations.jsx"

    header_idx = network_ops_content.find('className="detail-panel-header"', panel_idx)
    assert header_idx != -1, "detail-panel-header not found inside detail-panel"

    tabs_idx = network_ops_content.find('className="noc-drawer-tabs"', header_idx)
    assert tabs_idx != -1, "noc-drawer-tabs not found after header"

    body_idx = network_ops_content.find('className="detail-panel-body"', tabs_idx)
    assert body_idx != -1, "detail-panel-body not found after tabs"

    action_bar_idx = network_ops_content.find('className="noc-drawer-action-bar"', body_idx)
    assert action_bar_idx != -1, "noc-drawer-action-bar not found after body"

    assert panel_idx < header_idx < tabs_idx < body_idx < action_bar_idx, (
        "Drawer DOM sequence must be Header -> Tabs -> Body -> Action Bar"
    )
