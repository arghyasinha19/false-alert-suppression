"""
Connection State Machine, Resiliency & Mock Demarcation Contract Tests (Phase 19 - UI-02)
========================================================================================
Validates:
1. Tri-state connection machine ('connected', 'stale', 'offline') in App.jsx (D-05)
2. Strict payload validation with Array.isArray for alerts and devices (D-08, D-15)
3. Freezing of lastSuccessfulSync on fetch failure without false-positive refreshes (D-06)
4. Progressive backoff retry calculation (10s -> 20s -> 60s) (D-13)
5. Window focus listener and manual Reconnect API controls (D-14)
6. Header mock data demarcation chip and dismissible demo mode banner (D-09, D-12)
7. Propagation of connection status to NetworkOperations and .noc-refresh-bar (D-07)
8. SRE drawer offline provenance banner and Poll DNAC button disabling (D-10)
9. CSS styling contracts for tri-state dots, badges, chips, and banners
"""

import os
import re
import pytest

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_JSX_PATH = os.path.join(project_root, "dashboard", "src", "App.jsx")
NETWORK_OPS_PATH = os.path.join(project_root, "dashboard", "src", "NetworkOperations.jsx")
APP_CSS_PATH = os.path.join(project_root, "dashboard", "src", "App.css")


@pytest.fixture(scope="module")
def app_jsx_content():
    assert os.path.exists(APP_JSX_PATH), f"App.jsx not found at {APP_JSX_PATH}"
    with open(APP_JSX_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def network_ops_content():
    assert os.path.exists(NETWORK_OPS_PATH), f"NetworkOperations.jsx not found at {NETWORK_OPS_PATH}"
    with open(NETWORK_OPS_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def app_css_content():
    assert os.path.exists(APP_CSS_PATH), f"App.css not found at {APP_CSS_PATH}"
    with open(APP_CSS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_connection_state_tri_state_model(app_jsx_content):
    """Verify App.jsx implements tri-state transitions ('connected', 'stale', 'offline')."""
    assert "'connected'" in app_jsx_content, "App.jsx must reference 'connected' status"
    assert "'stale'" in app_jsx_content, "App.jsx must reference 'stale' status"
    assert "'offline'" in app_jsx_content, "App.jsx must reference 'offline' status"
    assert "consecutiveFailures" in app_jsx_content, "App.jsx must track consecutive failure counts"


def test_payload_validation_logic(app_jsx_content):
    """Verify App.jsx performs strict Array.isArray validation on API payloads."""
    assert "Array.isArray(alertsRes?.alerts)" in app_jsx_content, (
        "App.jsx must validate alertsRes?.alerts as an array"
    )
    assert "Array.isArray(devicesRes?.devices)" in app_jsx_content, (
        "App.jsx must validate devicesRes?.devices as an array"
    )


def test_refresh_timestamp_freezing(app_jsx_content):
    """Verify lastSuccessfulSync only updates on success and is frozen on failure."""
    assert "lastSuccessfulSync: attemptTime" in app_jsx_content, (
        "lastSuccessfulSync must be assigned only upon successful fetch"
    )
    # Ensure error handler does not overwrite lastSuccessfulSync with new Date()
    catch_block_match = re.search(r"catch\s*\([^\)]*\)\s*\{([^}]+(?:\{[^}]+\}[^}]+)*)\}", app_jsx_content)
    assert catch_block_match is not None, "fetchData catch block not found in App.jsx"
    catch_block = catch_block_match.group(1)
    assert "lastSuccessfulSync: attemptTime" not in catch_block, (
        "catch block must NOT update lastSuccessfulSync to attemptTime"
    )
    assert "lastSuccessfulSync: new Date()" not in catch_block, (
        "catch block must NOT update lastSuccessfulSync to new Date()"
    )


def test_progressive_backoff_and_focus_triggers(app_jsx_content):
    """Verify adaptive retry backoff (10s, 20s, 60s) and window focus reconnection."""
    assert "10000" in app_jsx_content, "App.jsx must include 10s initial failure backoff"
    assert "20000" in app_jsx_content, "App.jsx must include 20s second failure backoff"
    assert "60000" in app_jsx_content, "App.jsx must include 60s cap for 3+ failures"
    assert "addEventListener('focus'" in app_jsx_content or 'addEventListener("focus"' in app_jsx_content, (
        "App.jsx must register window focus listener for reconnect re-checks"
    )


def test_mock_data_demarcation_and_banner(app_jsx_content, app_css_content):
    """Verify App.jsx renders Mock / Seed Data chip, dismissible demo banner, and CSS rules."""
    assert "mock-data-chip" in app_jsx_content, "App.jsx must render mock-data-chip"
    assert "Mock / Seed Data" in app_jsx_content, "App.jsx must contain 'Mock / Seed Data' text"
    assert "demo-mode-banner" in app_jsx_content, "App.jsx must render demo-mode-banner"
    assert "Reconnect API" in app_jsx_content, "App.jsx must provide 'Reconnect API' action"

    # CSS assertions
    assert ".mock-data-chip" in app_css_content, "App.css must style .mock-data-chip"
    assert ".demo-mode-banner" in app_css_content, "App.css must style .demo-mode-banner"
    assert ".live-badge.connected" in app_css_content, "App.css must style .live-badge.connected"
    assert ".live-badge.stale" in app_css_content, "App.css must style .live-badge.stale"
    assert ".live-badge.offline" in app_css_content, "App.css must style .live-badge.offline"


def test_noc_refresh_bar_prop_synchronization(network_ops_content, app_jsx_content):
    """Verify NetworkOperations receives connectionStatus prop and styles .noc-refresh-bar."""
    assert "connectionStatus" in network_ops_content, (
        "NetworkOperations must accept connectionStatus prop"
    )
    assert "noc-refresh-bar ${connectionStatus}" in network_ops_content, (
        "NetworkOperations must assign connectionStatus class to .noc-refresh-bar"
    )
    assert "noc-live-dot ${connectionStatus}" in network_ops_content, (
        "NetworkOperations must assign connectionStatus class to .noc-live-dot"
    )
    assert "connectionStatus={connectionState.status}" in app_jsx_content, (
        "App.jsx must pass connectionStatus prop to child components"
    )


def test_sre_drawer_offline_handling(network_ops_content):
    """Verify SRE drawer handles offline status by rendering simulated notice and disabling poll button."""
    assert "Simulated Device Profile" in network_ops_content, (
        "NetworkOperations must render 'Simulated Device Profile' banner when offline"
    )
    assert "connectionStatus === 'offline'" in network_ops_content, (
        "NetworkOperations must check for offline connectionStatus"
    )
    assert "Backend API offline" in network_ops_content, (
        "NetworkOperations must provide 'Backend API offline' tooltip"
    )
