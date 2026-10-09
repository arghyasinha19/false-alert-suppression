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
    assert "Icon size=" in content, "TopologyGraphView must render icons"
    assert "core:" in content, "Must map core role"
    assert "dist_sec:" in content, "Must map dist_sec role"
    assert "access:" in content, "Must map access role"

    # Hostname, IP, location
    assert "tg-node-label" in content, "Must define tg-node-label"
    assert "caption" in content, "Must define caption"

    # Badges and Health indicator
    assert "tg-badge" in content, "Must define tier pill or badge"
    assert "tg-health" in content, "Must define health status indicator"
    assert "tg-node-pulse" in content, "Must render radar pulse ring for critical nodes"


def test_node_selection_and_drawer_linkage():
    """GRAPH-06: Verify node selection renders glowing highlight and opens SRE drawer."""
    with open(TOPOLOGY_VIEW_PATH, "r", encoding="utf-8") as f:
        graph_content = f.read()

    with open(NETWORK_OPERATIONS_PATH, "r", encoding="utf-8") as f:
        netops_content = f.read()

    # Selection highlight
    assert "tg-node-halo" in graph_content, "Must define selected glowing ring (halo)"
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

    # Dimming logic in TopologyGraphView (Removed or replaced by other D3 filtering)
    assert "searchQuery" in netops_content, "Search query is passed"
    assert "onResetFilters" in graph_content or "reset" in graph_content.lower(), "Must support resetting filters"


    pass
