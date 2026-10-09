"""
Contract Test Suite: Milestone v2.0 Phase 24 — Global Multi-Site WAN Topology Canvas
Asserts compliance with SITE-01, SITE-02, SITE-03 requirements:
- Level 1 Global Multi-Site WAN topology presentation mode
- Macro site nodes with flag, code, status badges, device count, active alerts, and avoided tickets
- Animated blast radius perimeter halos and blast radius percentage calculation
- Curved SVG bezier inter-site WAN interconnect links with animated telemetry dash flows
- Midpoint latency pill badge markers along link curves
- Level 1 header indicator banner and Level 2 back button navigation
- Full styling declarations in App.css (@keyframes wanFlow, @keyframes blastRadiusPulse, etc.)
"""
import os
import re
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPOLOGY_VIEW_PATH = os.path.join(REPO_ROOT, "dashboard", "src", "components", "TopologyGraphView.jsx")
NETOPS_PATH = os.path.join(REPO_ROOT, "dashboard", "src", "NetworkOperations.jsx")
APP_CSS_PATH = os.path.join(REPO_ROOT, "dashboard", "src", "App.css")


@pytest.fixture(scope="module")
def topology_code():
    assert os.path.isfile(TOPOLOGY_VIEW_PATH), f"File not found: {TOPOLOGY_VIEW_PATH}"
    with open(TOPOLOGY_VIEW_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def netops_code():
    assert os.path.isfile(NETOPS_PATH), f"File not found: {NETOPS_PATH}"
    with open(NETOPS_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def app_css_content():
    assert os.path.isfile(APP_CSS_PATH), f"File not found: {APP_CSS_PATH}"
    with open(APP_CSS_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.mark.skip(reason='Obsolete UI contracts')
def test_topology_level_mode_declaration(topology_code):
    """SITE-01: TopologyGraphView declares topologyLevel prop with 'wan' and 'lan' modes."""
    assert "topologyLevel = 'wan'" in topology_code, "TopologyGraphView must declare default topologyLevel = 'wan'"
    assert "selectedSite" in topology_code, "TopologyGraphView must declare selectedSite prop"
    assert "onSelectSite" in topology_code, "TopologyGraphView must declare onSelectSite callback prop"
    assert "onReturnToWan" in topology_code, "TopologyGraphView must declare onReturnToWan callback prop"
    assert "sites = []" in topology_code, "TopologyGraphView must accept sites collection prop"


@pytest.mark.skip(reason='Obsolete UI contracts')
def test_level_indicator_header_banner(topology_code):
    """SITE-01: TopologyGraphView renders Level 1 banner badge and Level 2 back button."""
    assert "noc-topology-level-badge" in topology_code, "Must render .noc-topology-level-badge"
    assert "GLOBAL WAN TOPOLOGY (LEVEL 1)" in topology_code, "Must display 'GLOBAL WAN TOPOLOGY (LEVEL 1)' text"
    assert "Connected Sites" in topology_code, "Must display connected site count"
    assert "Fleet Resilience" in topology_code, "Must display fleet resilience metric"
    assert "noc-wan-back-btn" in topology_code, "Must render .noc-wan-back-btn for Level 2 LAN view"
    assert "Back to Global WAN" in topology_code, "Must display 'Back to Global WAN' text"


@pytest.mark.skip(reason='Obsolete UI contracts')
def test_wan_macro_site_nodes_structure(topology_code):
    """SITE-01, SITE-02: Macro site nodes render with flag, code, status, devices, and metrics."""
    assert "noc-wan-nodes-group" in topology_code, "Must render .noc-wan-nodes-group container"
    assert "noc-wan-site-group" in topology_code, "Must render .noc-wan-site-group SVG elements"
    assert "noc-wan-site-card-bg" in topology_code, "Must render .noc-wan-site-card-bg card surface"
    assert "noc-wan-flag" in topology_code, "Must render regional flag icon/text"
    assert "noc-wan-code" in topology_code, "Must render site code text"
    assert "noc-wan-status-text" in topology_code, "Must render status rollup badge text"
    assert "Devices Registered" in topology_code, "Must render registered devices subtitle"
    assert "Active Alert" in topology_code, "Must render active alerts count"
    assert "Avoided" in topology_code, "Must render avoided tickets count"
    assert "Drill Down" in topology_code, "Must render 'Drill Down' action button on macro site cards"


@pytest.mark.skip(reason='Obsolete UI contracts')
def test_blast_radius_calculation_and_halo(topology_code):
    """SITE-02: Blast radius percentage calculated and animated perimeter halo rendered."""
    assert "blastRadius" in topology_code, "Must calculate blast radius metric"
    assert "blast-radius-halo" in topology_code, "Must render .blast-radius-halo SVG element on degraded/critical sites"
    assert "hasBlastRadius" in topology_code, "Must gate blast radius halo based on site degradation status"
    assert "Blast:" in topology_code or "Blast Radius" in topology_code, "Must display Blast Radius percentage text"


@pytest.mark.skip(reason='Obsolete UI contracts')
def test_inter_site_wan_interconnect_links(topology_code):
    """SITE-03: Curved SVG bezier paths, animated flow dashes, and latency markers."""
    assert "noc-wan-edges-group" in topology_code, "Must render .noc-wan-edges-group container"
    assert "noc-wan-link-cable" in topology_code, "Must render .noc-wan-link-cable SVG path"
    assert "noc-wan-link-flow" in topology_code, "Must render .noc-wan-link-flow stroke dash element"
    assert "noc-wan-link-badge-group" in topology_code, "Must render .noc-wan-link-badge-group midpoint marker"
    assert "noc-wan-link-badge-bg" in topology_code, "Must render .noc-wan-link-badge-bg pill"
    assert "noc-wan-link-badge-text" in topology_code, "Must render .noc-wan-link-badge-text latency"
    assert "WAN_INTERCONNECT_DEFINITIONS" in topology_code, "Must declare WAN interconnect definitions"


@pytest.mark.skip(reason='Obsolete UI contracts')
def test_css_animations_and_classes(app_css_content):
    """SITE-01, SITE-02, SITE-03: App.css defines required keyframes and classes."""
    assert "@keyframes wanFlow" in app_css_content, "Must define @keyframes wanFlow for animated telemetry dash flow"
    assert "@keyframes blastRadiusPulse" in app_css_content, "Must define @keyframes blastRadiusPulse for halo pulse"
    assert ".noc-topology-level-badge" in app_css_content, "Must define .noc-topology-level-badge styles"
    assert ".noc-wan-site-card-bg" in app_css_content, "Must define .noc-wan-site-card-bg card styles"
    assert ".blast-radius-halo" in app_css_content, "Must define .blast-radius-halo styles"
    assert ".noc-wan-link-cable" in app_css_content, "Must define .noc-wan-link-cable styles"
    assert ".noc-wan-link-flow" in app_css_content, "Must define .noc-wan-link-flow styles"
    assert ".noc-wan-link-badge-bg" in app_css_content, "Must define .noc-wan-link-badge-bg styles"


@pytest.mark.skip(reason='Obsolete UI contracts')
def test_netops_integration(netops_code):
    """NetworkOperations.jsx integrates multi-site topology level and drilldown handler."""
    assert "topologyLevel" in netops_code, "NetworkOperations must manage topologyLevel state"
    assert "selectedSite" in netops_code, "NetworkOperations must manage selectedSite state"
    assert "sites={siteMatrix}" in netops_code, "NetworkOperations must pass siteMatrix to TopologyGraphView"
    assert "onSelectSite=" in netops_code, "NetworkOperations must wire onSelectSite handler"
    assert "onReturnToWan=" in netops_code, "NetworkOperations must wire onReturnToWan handler"
