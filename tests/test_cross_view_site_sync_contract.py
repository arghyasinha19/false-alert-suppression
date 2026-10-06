"""
Contract test suite for Milestone v2.0 Phase 26:
Cross-View Site Synchronization & Filter Alignment

Requirements covered:
- SITE-07: Selecting a site in the Regional Site Matrix automatically filters or transitions the Topology view
          to that site's LAN graph.
- SITE-08: Filtering by location in the SRE Table or multi-dimensional filter bar synchronizes with the
          Topology view's active site scope.
"""

import os
import re
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NETWORK_OPS_PATH = os.path.join(REPO_ROOT, "dashboard", "src", "NetworkOperations.jsx")
APP_CSS_PATH = os.path.join(REPO_ROOT, "dashboard", "src", "App.css")


@pytest.fixture(scope="module")
def netops_code():
    with open(NETWORK_OPS_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def app_css_code():
    with open(APP_CSS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_site_matrix_to_topology_drilldown(netops_code):
    """SITE-07: Regional Site Matrix drilldown transitions viewMode to topology with selectedSite and lan level."""
    assert "handleViewModeChange('topology')" in netops_code, "Must switch viewMode to topology"
    assert "setTopologyLevel('lan')" in netops_code, "Must set topologyLevel to 'lan'"
    assert "setSelectedSite(site.code)" in netops_code, "Must set selectedSite to the clicked site code"
    assert "noc-site-drilldown-btn" in netops_code, "Must render drilldown button on site cards"


def test_site_matrix_active_card_highlight(netops_code, app_css_code):
    """SITE-07: Site cards render active-site highlight class when selectedSite matches."""
    assert "active-site" in netops_code, "Must apply active-site class to selected site card"
    assert ".noc-site-card.active-site" in app_css_code, "App.css must style .noc-site-card.active-site"


def test_filter_bar_site_cluster_contract(netops_code):
    """SITE-08: Multi-dimensional filter bar contains dedicated Site filter cluster."""
    assert "Site:" in netops_code, "Must display 'Site:' filter cluster label"
    assert "All Sites (Global)" in netops_code, "Must provide 'All Sites (Global)' root pill"
    assert "setSelectedSite(null)" in netops_code, "Must support clearing selectedSite back to global"
    assert "setTopologyLevel('wan')" in netops_code, "Must support resetting topologyLevel to 'wan'"


def test_sre_table_interactive_location_buttons(netops_code, app_css_code):
    """SITE-08: SRE Table location cells are interactive buttons that filter site scope."""
    assert "noc-table-loc-btn" in netops_code, "Must render .noc-table-loc-btn in SRE Table"
    assert ".noc-table-loc-btn" in app_css_code, "App.css must style .noc-table-loc-btn"
    assert "setSelectedSite(siteCode)" in netops_code, "Clicking location must set selectedSite"


def test_filter_reset_clears_site_scope(netops_code):
    """SITE-08: Reset filters clears selectedSite and returns to global WAN level."""
    # Find resetAllFilters implementation block
    match = re.search(r"const resetAllFilters = \(\) => \{(.*?)\};", netops_code, re.DOTALL)
    assert match is not None, "resetAllFilters function must be defined"
    block = match.group(1)
    assert "setSelectedSite(null)" in block, "resetAllFilters must reset selectedSite to null"
    assert "setTopologyLevel('wan')" in block, "resetAllFilters must reset topologyLevel to 'wan'"


def test_table_loc_btn_touch_target_contract(app_css_code):
    """Verify .noc-table-loc-btn enforces min-height: 32px for touch accessibility."""
    assert ".noc-table-loc-btn" in app_css_code
    # check that min-height 32px is present
    match = re.search(r"\.noc-table-loc-btn\s*\{([^}]+)\}", app_css_code)
    assert match is not None
    assert "min-height: 32px" in match.group(1), "Must have min-height: 32px"
