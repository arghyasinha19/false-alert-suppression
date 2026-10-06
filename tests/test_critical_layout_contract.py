"""
Critical Layout & Breakpoint Contract Tests (Phase 19 - UI-01)
==============================================================
Validates:
1. Fluid flexbox layout on .content-area (flex: 1, min-width: 0, max-width: 100%, no calc(100vw))
2. Table card containment (.table-card min-width: 0, overflow: hidden)
3. Explicit @media (max-width: 1100px) block with header padding compaction and grid reflow
4. Viewport-aware sidebar auto-collapse logic in App.jsx (1100px threshold)
"""

import os
import re
import pytest

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_CSS_PATH = os.path.join(project_root, "dashboard", "src", "App.css")
APP_JSX_PATH = os.path.join(project_root, "dashboard", "src", "App.jsx")


@pytest.fixture(scope="module")
def app_css_content():
    assert os.path.exists(APP_CSS_PATH), f"App.css not found at {APP_CSS_PATH}"
    with open(APP_CSS_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def app_jsx_content():
    assert os.path.exists(APP_JSX_PATH), f"App.jsx not found at {APP_JSX_PATH}"
    with open(APP_JSX_PATH, "r", encoding="utf-8") as f:
        return f.read()


def extract_media_block(css_content, query_substring):
    """Extract full content inside @media block accounting for nested braces."""
    idx = css_content.find(query_substring)
    if idx == -1:
        return None
    start = css_content.find("{", idx)
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(css_content)):
        if css_content[i] == "{":
            depth += 1
        elif css_content[i] == "}":
            depth -= 1
            if depth == 0:
                return css_content[start + 1 : i]
    return None


def test_content_area_flexbox_contract(app_css_content):
    """Verify .content-area enforces fluid flex sizing and zero min-width without rigid 100vw calc."""
    match = re.search(r"\.content-area\s*\{([^}]+)\}", app_css_content)
    assert match is not None, ".content-area CSS rule block not found in App.css"
    block = match.group(1)

    assert "flex:" in block, ".content-area must specify flex sizing"
    assert "min-width: 0" in block, ".content-area must specify min-width: 0 to prevent child blowout"
    assert "max-width: 100%" in block, ".content-area must specify max-width: 100%"
    assert "calc(100vw" not in block, ".content-area must not use rigid calc(100vw - ...) constraints"


def test_content_body_flexbox_contract(app_css_content):
    """Verify .content-body prevents horizontal overflow and bounds width properly."""
    match = re.search(r"\.content-body\s*\{([^}]+)\}", app_css_content)
    assert match is not None, ".content-body CSS rule block not found in App.css"
    block = match.group(1)

    assert "min-width: 0" in block, ".content-body must specify min-width: 0"
    assert "max-width: 100%" in block, ".content-body must specify max-width: 100%"
    assert "overflow-x: hidden" in block, ".content-body must specify overflow-x: hidden"


def test_table_card_overflow_containment(app_css_content):
    """Verify .table-card specifies min-width: 0 and overflow: hidden to isolate horizontal scrollbars."""
    match = re.search(r"\.table-card\s*\{([^}]+)\}", app_css_content)
    assert match is not None, ".table-card CSS rule block not found in App.css"
    block = match.group(1)

    assert "min-width: 0" in block, ".table-card must specify min-width: 0"
    assert "overflow: hidden" in block, ".table-card must specify overflow: hidden"


def test_1100px_media_query_contract(app_css_content):
    """Verify App.css contains @media (max-width: 1100px) with header padding compaction and grid reflow."""
    block = extract_media_block(app_css_content, "@media (max-width: 1100px)")
    assert block is not None, "@media (max-width: 1100px) block not found in App.css"

    assert ".content-header" in block, "@media (max-width: 1100px) must style .content-header"
    assert "1rem 1.25rem" in block, ".content-header must compact padding to 1rem 1.25rem (16px 20px)"
    assert ".charts-grid-3" in block, "@media (max-width: 1100px) must reflow .charts-grid-3"
    assert "grid-template-columns: 1fr" in block, ".charts-grid-3 must reflow to single column"


def test_sidebar_auto_collapse_logic(app_jsx_content):
    """Verify App.jsx includes 1100px breakpoint check and responsive resize listener for rail mode."""
    assert "1100" in app_jsx_content, "App.jsx must contain 1100px breakpoint check"
    assert "addEventListener('resize'" in app_jsx_content or "addEventListener(\"resize\"" in app_jsx_content, (
        "App.jsx must register a resize event listener"
    )
    assert "sidebarCollapsed" in app_jsx_content, "App.jsx must manage sidebarCollapsed state"
    assert "sidebar-collapse-toggle" in app_jsx_content, "App.jsx must retain manual sidebar toggle button"
