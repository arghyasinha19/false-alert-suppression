import os
import re

TOPOLOGY_VIEW_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "dashboard",
    "src",
    "components",
    "TopologyGraphView.jsx"
)

NETWORK_OPERATIONS_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "dashboard",
    "src",
    "NetworkOperations.jsx"
)

APP_CSS_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "dashboard",
    "src",
    "App.css"
)


def test_node_micro_card_elements_contract():
    """GRAPH-05: Verify node micro-cards render role icons, hostnames, IPs, health dots & alert badges."""
    assert os.path.exists(TOPOLOGY_VIEW_PATH), "TopologyGraphView.jsx must exist"
    with open(TOPOLOGY_VIEW_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Role icons
    assert "renderRoleIcon" in content, "TopologyGraphView must define renderRoleIcon"
    assert "role-core" in content, "Must define core role icon"
    assert "role-dist" in content, "Must define distribution/security role icon"
    assert "role-access" in content, "Must define access role icon"

    # Hostname, IP, location
    assert "noc-node-title-text" in content, "Must define noc-node-title-text"
    assert "noc-node-subtitle-text" in content, "Must define noc-node-subtitle-text"
    assert "node.device.ip_address" in content, "Must display IP address"
    assert "node.device.location" in content, "Must display location"

    # Badges and Health indicator
    assert "noc-node-tier-pill" in content, "Must define tier pill"
    assert "noc-node-alert-pill-text" in content, "Must define alert pill text"
    assert "Nominal" in content, "Must display Nominal badge when healthy"
    assert "Alert" in content, "Must display Alert count when alerting"
    assert "noc-radar-pulse-ring" in content, "Must render radar pulse ring for critical nodes"


def test_node_selection_and_drawer_linkage():
    """GRAPH-06: Verify node selection renders glowing highlight and opens SRE drawer."""
    with open(TOPOLOGY_VIEW_PATH, "r", encoding="utf-8") as f:
        graph_content = f.read()

    with open(NETWORK_OPERATIONS_PATH, "r", encoding="utf-8") as f:
        netops_content = f.read()

    # Selection highlight
    assert "noc-node-selected-ring" in graph_content, "Must define selected glowing ring"
    assert "glow-blue" in graph_content, "Must define blue glow filter"
    assert "onSelectDevice(node.device)" in graph_content, "Clicking node must invoke onSelectDevice"

    # Drawer linkage in NetworkOperations
    assert "onSelectDevice={openDevicePanel}" in netops_content, "NetworkOperations must pass openDevicePanel"
    assert "openDevicePanel" in netops_content, "openDevicePanel must be defined"
    assert "Escape" in netops_content, "Must support Escape key to close drawer"


def test_reactive_filter_sync_and_dimming():
    """GRAPH-07: Verify full device fleet is passed and non-matches are dimmed."""
    with open(NETWORK_OPERATIONS_PATH, "r", encoding="utf-8") as f:
        netops_content = f.read()

    with open(TOPOLOGY_VIEW_PATH, "r", encoding="utf-8") as f:
        graph_content = f.read()

    # Must pass full device fleet to prevent graph fragmentation
    assert "<TopologyGraphView" in netops_content
    # devices={devices} should be passed, not devices={filteredDevices}
    match = re.search(r"<TopologyGraphView[^>]+devices=\{devices\}", netops_content)
    assert match is not None, "TopologyGraphView must receive devices={devices}"

    # Filter props passed
    assert "searchQuery={searchQuery}" in netops_content
    assert "roleFilter={roleFilter}" in netops_content
    assert "healthFilter={healthFilter}" in netops_content
    assert "onResetFilters={resetAllFilters}" in netops_content

    # Dimming logic in TopologyGraphView
    assert "isDimmed" in graph_content, "TopologyGraphView must compute isDimmed"
    assert "noc-graph-filter-badge" in graph_content, "Must render filter match badge"
    assert "Filtered:" in graph_content, "Must show filtered count"
    assert "onResetFilters" in graph_content, "Must support resetting filters"


def test_app_css_nodes_and_pulse_styling():
    """Verify App.css defines node card styling, pulse keyframes, and filter badge."""
    assert os.path.exists(APP_CSS_PATH), "App.css must exist"
    with open(APP_CSS_PATH, "r", encoding="utf-8") as f:
        css = f.read()

    assert ".noc-graph-node-card.dimmed" in css, "App.css must style dimmed nodes"
    assert ".noc-link-path.dimmed" in css, "App.css must style dimmed links"
    assert ".noc-node-card-body" in css, "App.css must style node card body"
    assert "@keyframes noc-svg-radar-pulse" in css, "App.css must define SVG radar pulse keyframes"
    assert ".noc-graph-filter-badge" in css, "App.css must style filter match badge"
    assert ".noc-graph-filter-reset-btn" in css, "App.css must style filter reset button"
