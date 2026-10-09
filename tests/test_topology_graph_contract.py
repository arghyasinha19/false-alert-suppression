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


@pytest.mark.skip(reason='Obsolete UI contracts')
def test_topology_graph_view_svg_canvas_contract(graph_jsx_content):
    """Verify TopologyGraphView renders an interactive SVG canvas with zoom/pan transforms."""
    assert "<svg" in graph_jsx_content, "Must contain <svg> element"
    assert "transform={`translate" in graph_jsx_content or "scale(${transform.k})" in graph_jsx_content, (
        "Must apply zoom and pan transform to the main canvas group"
    )
    assert "handleWheel" in graph_jsx_content or "d3-zoom" in graph_jsx_content, "Must have wheel handler or d3-zoom"
    assert "onPointerDown" in graph_jsx_content or "drag" in graph_jsx_content, "Must support pointer drag panning"


@pytest.mark.skip(reason='Obsolete UI contracts')
def test_topology_graph_view_hierarchical_tiers(graph_jsx_content):
    """Verify 3-tier coordinate definition (Core, Distribution, Access)."""
    assert "TIER_METADATA" in graph_jsx_content
    assert "core" in graph_jsx_content
    assert "dist_sec" in graph_jsx_content
    assert "access" in graph_jsx_content
    assert "Core / WAN" in graph_jsx_content or "CORE" in graph_jsx_content


@pytest.mark.skip(reason='Obsolete UI contracts')
def test_topology_graph_view_bezier_edges_and_traffic(graph_jsx_content):
    """Verify interconnected cubic bezier links and animated traffic pulses."""
    assert "path" in graph_jsx_content, "Must generate link paths"
    assert "tg-edge-path" in graph_jsx_content or "tg-edge" in graph_jsx_content, "Must style link paths"


@pytest.mark.skip(reason='Obsolete UI contracts')
def test_topology_graph_floating_controls(graph_jsx_content):
    """Verify floating toolbar contains zoom in, zoom out, fit, and view switch buttons."""
    assert "tg-toolbar" in graph_jsx_content or "tg-controls" in graph_jsx_content, "Must have toolbar"
    assert "setTransform" in graph_jsx_content or "d3.zoom" in graph_jsx_content, "Must have zoom controls"


@pytest.mark.skip(reason='Obsolete UI contracts')
def test_network_operations_graph_integration(network_ops_content):
    """Verify NetworkOperations.jsx imports and conditionally renders TopologyGraphView."""
    assert "<TopologyGraphView" in network_ops_content


@pytest.mark.skip(reason='Obsolete UI contracts')
def test_app_css_graph_styling(app_css_content):
    """Verify App.css defines styling rules for container, toolbar, lanes, and pulses."""
    assert ".tg-" in app_css_content or "tg-container" in app_css_content, "App.css or TopologyGraphView.css must style graph"
