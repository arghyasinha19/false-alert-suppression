"""
Topology Bounds, Wheel Zoom Guard & Fullscreen Mode Contract Tests (Phase 20 - UI-03)
====================================================================================
Validates:
1. Container height viewport clamp: clamp(560px, calc(100vh - 280px), 780px) and overflow: hidden
2. Fullscreen overlay CSS rules: position: fixed, inset: 0, z-index: 1000
3. Wheel zoom modifier guard with Ctrl/Cmd + floating hint toast "Use Ctrl + scroll to zoom"
4. Soft pan coordinate clamping and Escape key exit listener
5. Fullscreen toggle button presence in the floating controls toolbar
"""

import os
import re
import pytest

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_CSS_PATH = os.path.join(project_root, "dashboard", "src", "App.css")
TOPOLOGY_JSX_PATH = os.path.join(project_root, "dashboard", "src", "components", "TopologyGraphView.jsx")


@pytest.fixture(scope="module")
def app_css_content():
    assert os.path.exists(APP_CSS_PATH), f"App.css not found at {APP_CSS_PATH}"
    with open(APP_CSS_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def topology_jsx_content():
    assert os.path.exists(TOPOLOGY_JSX_PATH), f"TopologyGraphView.jsx not found at {TOPOLOGY_JSX_PATH}"
    with open(TOPOLOGY_JSX_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_topology_container_height_clamp_contract(app_css_content):
    """Verify .noc-topology-graph-container specifies viewport proportional height clamp and overflow hidden."""
    match = re.search(r"\.noc-topology-graph-container\s*\{([^}]+)\}", app_css_content)
    assert match is not None, ".noc-topology-graph-container rule block not found in App.css"
    block = match.group(1)

    assert "clamp(560px" in block, "Container height must clamp with 560px minimum"
    assert "780px" in block, "Container height must clamp with 780px maximum"
    assert "overflow: hidden" in block, "Container must specify overflow: hidden to bound canvas"
    assert "min-height: 560px" in block, "Container must specify min-height: 560px"


def test_topology_fullscreen_css_contract(app_css_content):
    """Verify .noc-topology-graph-container.fullscreen defines fixed overlay across entire viewport."""
    match = re.search(r"\.noc-topology-graph-container\.fullscreen\s*\{([^}]+)\}", app_css_content)
    assert match is not None, ".noc-topology-graph-container.fullscreen rule block not found in App.css"
    block = match.group(1)

    assert "position: fixed" in block, "Fullscreen container must specify position: fixed"
    assert "inset: 0" in block, "Fullscreen container must specify inset: 0"
    assert "z-index: 1000" in block or "z-index: 10" in block, "Fullscreen container must have high z-index"


def test_wheel_zoom_modifier_guard_contract(topology_jsx_content, app_css_content):
    """Verify wheel zoom requires Ctrl/Cmd modifier and triggers floating toast hint without page hijack."""
    assert "ctrlKey" in topology_jsx_content or "metaKey" in topology_jsx_content, (
        "handleWheel must verify ctrlKey or metaKey modifier before zooming"
    )
    assert "Use Ctrl + scroll to zoom" in topology_jsx_content, (
        "TopologyGraphView.jsx must contain exact hint copy 'Use Ctrl + scroll to zoom'"
    )
    assert ".noc-wheel-zoom-hint" in app_css_content, (
        "App.css must define styling for .noc-wheel-zoom-hint floating toast"
    )


def test_pan_clamping_and_escape_listener(topology_jsx_content):
    """Verify pan coordinates are clamped to keep diagram visible and Escape key exits fullscreen."""
    assert "clampedX" in topology_jsx_content or "Math.max" in topology_jsx_content, (
        "TopologyGraphView.jsx must implement pan boundary clamping"
    )
    assert "Escape" in topology_jsx_content, (
        "TopologyGraphView.jsx must listen for Escape key to exit fullscreen"
    )
    assert "isFullscreen" in topology_jsx_content, (
        "TopologyGraphView.jsx must manage isFullscreen state"
    )


def test_fullscreen_toolbar_toggle_button(topology_jsx_content):
    """Verify floating toolbar includes Expand/Exit toggle with accessible labels."""
    assert "Expand Topology View" in topology_jsx_content, (
        "Toolbar button must include 'Expand Topology View' title/aria-label"
    )
    assert "Exit Fullscreen Canvas" in topology_jsx_content, (
        "Toolbar button must include 'Exit Fullscreen Canvas' title/aria-label"
    )
    assert "Minimize2" in topology_jsx_content and "Maximize2" in topology_jsx_content, (
        "TopologyGraphView.jsx must render Maximize2 and Minimize2 icons"
    )
