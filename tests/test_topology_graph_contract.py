"""
NOC Interactive Network Topology Graph Contract Tests (Phase 17)
===============================================================
Validates:
1. TopologyGraphView.jsx renders an interactive SVG canvas with zoom and pan transform controls (GRAPH-01).
2. Canvas includes floating controls toolbar (Zoom In, Zoom Out, Fit, Reset) and sub-mode toggle (GRAPH-02).
3. Devices are grouped into 3 deterministic hierarchical network tiers (Core, Dist/Sec, Access) (GRAPH-03).
4. Interconnected network links (edges) use cubic bezier curves with animated traffic pulses (GRAPH-04).
5. NetworkOperations.jsx integrates TopologyGraphView with topologySubMode state.
6. App.css defines graph container, floating controls, tier lanes, and link styles for both themes.
"""

import os
import re
import pytest

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPOLOGY_GRAPH_JSX = os.path.join(project_root, "dashboard", "src", "components", "TopologyGraphView.jsx")
NETWORK_OPS_JSX = os.path.join(project_root, "dashboard", "src", "NetworkOperations.jsx")
APP_CSS = os.path.join(project_root, "dashboard", "src", "App.css")


@pytest.fixture(scope="module")
def graph_jsx_content():
    assert os.path.exists(TOPOLOGY_GRAPH_JSX), f"TopologyGraphView.jsx not found at {TOPOLOGY_GRAPH_JSX}"
    with open(TOPOLOGY_GRAPH_JSX, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def network_ops_content():
    assert os.path.exists(NETWORK_OPS_JSX), f"NetworkOperations.jsx not found at {NETWORK_OPS_JSX}"
    with open(NETWORK_OPS_JSX, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def app_css_content():
    assert os.path.exists(APP_CSS), f"App.css not found at {APP_CSS}"
    with open(APP_CSS, "r", encoding="utf-8") as f:
        return f.read()


def test_topology_graph_view_svg_canvas_contract(graph_jsx_content):
    """Verify TopologyGraphView renders an interactive SVG canvas with zoom/pan transforms."""
    assert "<svg" in graph_jsx_content, "Must contain <svg> element"
    assert "noc-topology-canvas" in graph_jsx_content, "Must have noc-topology-canvas class"
    assert "transform={`translate(${transform.x}, ${transform.y}) scale(${transform.k})`}" in graph_jsx_content or "scale(${transform.k})" in graph_jsx_content, (
        "Must apply zoom and pan transform to the main canvas group"
    )
    assert "handleWheel" in graph_jsx_content, "Must have wheel handler for mouse zoom"
    assert "onPointerDown" in graph_jsx_content, "Must support pointer drag panning"
    assert "onPointerMove" in graph_jsx_content, "Must support pointer movement"


def test_topology_graph_view_hierarchical_tiers(graph_jsx_content):
    """Verify 3-tier coordinate definition (Core, Distribution, Access)."""
    assert "TIER_METADATA" in graph_jsx_content
    assert "core" in graph_jsx_content
    assert "dist_sec" in graph_jsx_content
    assert "access" in graph_jsx_content
    assert "CORE & WAN BACKBONE" in graph_jsx_content
    assert "DISTRIBUTION & SECURITY PERIMETER" in graph_jsx_content
    assert "CAMPUS & ACCESS EDGE" in graph_jsx_content


def test_topology_graph_view_bezier_edges_and_traffic(graph_jsx_content):
    """Verify interconnected cubic bezier links and animated traffic pulses."""
    # Check cubic bezier curve syntax
    assert "M ${" in graph_jsx_content or " C " in graph_jsx_content, "Must generate cubic bezier curve paths"
    assert "<animateMotion" in graph_jsx_content, "Must use SVG animateMotion for live traffic particles"
    assert "noc-traffic-pulse" in graph_jsx_content, "Must style traffic pulse elements"
    assert "noc-link-path" in graph_jsx_content, "Must style link paths"


def test_topology_graph_floating_controls(graph_jsx_content):
    """Verify floating toolbar contains zoom in, zoom out, fit, and view switch buttons."""
    assert "noc-graph-controls-toolbar" in graph_jsx_content
    assert "handleZoomIn" in graph_jsx_content
    assert "handleZoomOut" in graph_jsx_content
    assert "handleFitToScreen" in graph_jsx_content
    assert "handleResetZoom" in graph_jsx_content
    assert "onToggleSubMode" in graph_jsx_content, "Must allow toggling between Graph and Card Grid modes"


def test_network_operations_graph_integration(network_ops_content):
    """Verify NetworkOperations.jsx imports and conditionally renders TopologyGraphView."""
    assert "import TopologyGraphView from './components/TopologyGraphView';" in network_ops_content
    assert "topologySubMode" in network_ops_content
    assert "<TopologyGraphView" in network_ops_content
    assert "noc-submode-pill-group" in network_ops_content
    assert "noc-submode-btn" in network_ops_content


def test_app_css_graph_styling(app_css_content):
    """Verify App.css defines styling rules for container, toolbar, lanes, and pulses."""
    assert ".noc-topology-graph-container" in app_css_content
    assert ".noc-graph-controls-toolbar" in app_css_content
    assert ".noc-tier-lane-bg" in app_css_content
    assert ".noc-link-path" in app_css_content
    assert ".noc-traffic-pulse" in app_css_content
    assert ".noc-submode-pill-group" in app_css_content
    assert '[data-theme="light"] .noc-graph-controls-toolbar' in app_css_content
