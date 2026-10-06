"""
Contract test suite for Milestone v2.0 Phase 25:
Site-Specific LAN Topology Drill-Down & Breadcrumbs

Requirements covered:
- SITE-04: User can drill down into any site from the Global WAN map (via click or site-switcher selector)
          to view that site's local Core ↔ Distribution ↔ Access tier topology graph.
- SITE-05: User can navigate between the Global WAN overview and local site views using responsive
          breadcrumbs (Global WAN Interconnect > UK-LON (London)) with single-click return to global.
- SITE-06: User can filter devices within a site's LAN topology while preserving site boundaries and context.
"""

import os
import re
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOPOLOGY_VIEW_PATH = os.path.join(REPO_ROOT, "dashboard", "src", "components", "TopologyGraphView.jsx")
APP_CSS_PATH = os.path.join(REPO_ROOT, "dashboard", "src", "App.css")
NETWORK_OPS_PATH = os.path.join(REPO_ROOT, "dashboard", "src", "NetworkOperations.jsx")


@pytest.fixture(scope="module")
def topology_code():
    with open(TOPOLOGY_VIEW_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def app_css_code():
    with open(APP_CSS_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def netops_code():
    with open(NETWORK_OPS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_site_lan_drilldown_tier_architecture(topology_code):
    """SITE-04: Level 2 Site LAN mode renders 3-tier hierarchy (Core, Distribution, Access)."""
    assert "scopedDevices" in topology_code, "Must compute site-scoped devices when in Level 2"
    assert "CORE & WAN BACKBONE" in topology_code, "Must render Core tier lane"
    assert "DISTRIBUTION & SECURITY PERIMETER" in topology_code, "Must render Distribution tier lane"
    assert "CAMPUS & ACCESS EDGE" in topology_code, "Must render Access tier lane"
    assert "SITE LAN:" in topology_code or "SITE LAN" in topology_code, "Must display Level 2 status banner"


def test_site_switcher_selector_contract(topology_code):
    """SITE-04: Toolbar provides an accessible site switcher dropdown for direct site hopping."""
    assert "noc-site-switcher-select" in topology_code, "Must render site switcher select element"
    assert "noc-site-switcher-wrapper" in topology_code, "Must wrap site switcher in accessible container"
    assert "onSelectSite(e.target.value)" in topology_code or "onSelectSite(" in topology_code, (
        "Site switcher must invoke onSelectSite callback with chosen site code"
    )
    assert "<option" in topology_code, "Site switcher must render site option entries"


def test_responsive_breadcrumbs_contract(topology_code):
    """SITE-05: Breadcrumb trail renders parent root, chevron separator, and active site."""
    assert "noc-topology-breadcrumbs" in topology_code, "Must define .noc-topology-breadcrumbs container"
    assert "noc-topology-breadcrumb-trail" in topology_code, "Must render breadcrumb trail"
    assert "noc-breadcrumb-root" in topology_code, "Must render clickable root breadcrumb"
    assert "Global WAN Interconnect" in topology_code, "Root breadcrumb must display 'Global WAN Interconnect'"
    assert "ChevronRight" in topology_code, "Must render ChevronRight breadcrumb divider"
    assert "noc-breadcrumb-separator" in topology_code, "Must render breadcrumb separator class"
    assert "noc-breadcrumb-site" in topology_code, "Must render active site leaf breadcrumb"


def test_single_click_global_return_contract(topology_code):
    """SITE-05: Root breadcrumb and back button invoke onReturnToWan."""
    assert "onClick={onReturnToWan}" in topology_code, "Breadcrumb or back button must invoke onReturnToWan"
    assert "noc-wan-back-btn" in topology_code, "Must render .noc-wan-back-btn for single-click return"


def test_site_scoped_filtering_contract(topology_code):
    """SITE-06: Device filtering operates within site boundaries with clear scoped feedback."""
    assert "noc-graph-filter-badge" in topology_code, "Must render filter match badge"
    assert "Filtered:" in topology_code, "Must display filter match count"
    assert "onResetFilters" in topology_code, "Must support resetting filters within site scope"
    assert "devices in" in topology_code or "scopedDevices" in topology_code, (
        "Filter badge or logic must reflect site-scoped device context"
    )


def test_breadcrumbs_and_switcher_css_contract(app_css_code):
    """Verify App.css defines styling for breadcrumbs, site switcher, and touch targets."""
    assert ".noc-topology-breadcrumbs" in app_css_code, "App.css must style .noc-topology-breadcrumbs"
    assert ".noc-topology-breadcrumb-trail" in app_css_code, "App.css must style .noc-topology-breadcrumb-trail"
    assert ".noc-breadcrumb-item" in app_css_code, "App.css must style .noc-breadcrumb-item"
    assert ".noc-site-switcher-select" in app_css_code, "App.css must style .noc-site-switcher-select"
    assert "min-height: 32px" in app_css_code, "Interactive controls must enforce min-height >= 32px touch target"


def test_network_operations_site_navigation_integration(netops_code):
    """Verify NetworkOperations passes site callbacks and maintains Level 2 site state."""
    assert "onSelectSite" in netops_code, "NetworkOperations must pass onSelectSite callback"
    assert "onReturnToWan" in netops_code, "NetworkOperations must pass onReturnToWan callback"
    assert "topologyLevel" in netops_code, "NetworkOperations must pass topologyLevel state"
    assert "selectedSite" in netops_code, "NetworkOperations must pass selectedSite state"
