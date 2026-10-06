"""
tests/test_contrast_remediation_contract.py

Contract verification suite for Phase 21: Trust & Contrast Remediation.
Mathematically verifies WCAG 2.1 relative luminance and contrast ratios for
remediated color tokens, validates CSS token definitions, and checks component
bindings across light and dark modes.
"""

import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_CSS = REPO_ROOT / "dashboard" / "src" / "index.css"
APP_CSS = REPO_ROOT / "dashboard" / "src" / "App.css"
HOOK_FILE = REPO_ROOT / "dashboard" / "src" / "hooks" / "useChartTheme.js"
METRICS_FILE = REPO_ROOT / "dashboard" / "src" / "FalseAlertMetrics.jsx"
PATTERNS_FILE = REPO_ROOT / "dashboard" / "src" / "AlertPatterns.jsx"
CHAT_CHART_FILE = REPO_ROOT / "dashboard" / "src" / "ChatChart.jsx"


def hex_to_rgb(hex_code: str) -> tuple[float, float, float]:
    """Convert a 6-character hex string to RGB (0-255)."""
    hex_clean = hex_code.strip().lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join(c * 2 for c in hex_clean)
    r = int(hex_clean[0:2], 16)
    g = int(hex_clean[2:4], 16)
    b = int(hex_clean[4:6], 16)
    return r, g, b


def relative_luminance(r: float, g: float, b: float) -> float:
    """Compute WCAG 2.1 relative luminance for sRGB channels."""
    channels = []
    for c in (r, g, b):
        c_norm = c / 255.0
        if c_norm <= 0.04045:
            channels.append(c_norm / 12.92)
        else:
            channels.append(((c_norm + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(hex1: str, hex2: str) -> float:
    """Calculate WCAG 2.1 contrast ratio between two hex colors."""
    l1 = relative_luminance(*hex_to_rgb(hex1))
    l2 = relative_luminance(*hex_to_rgb(hex2))
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


# ==============================================================================
# WCAG Mathematical Formula Assertions
# ==============================================================================


def test_text_tertiary_light_contrast_passes_wcag_aa():
    """Verify light mode --text-tertiary (#64748b) on white passes AA (>= 4.5:1)."""
    ratio = contrast_ratio("#64748b", "#ffffff")
    assert ratio >= 4.5, f"Light mode text-tertiary ratio {ratio:.2f} < 4.5"
    assert round(ratio, 2) >= 4.6, f"Expected ~4.64:1, got {ratio:.2f}"


def test_text_tertiary_dark_contrast_passes_wcag_aa():
    """Verify dark mode --text-tertiary (#94a3b8) on dark card (#111827) passes AA (>= 4.5:1)."""
    ratio = contrast_ratio("#94a3b8", "#111827")
    assert ratio >= 4.5, f"Dark mode text-tertiary ratio {ratio:.2f} < 4.5"
    assert round(ratio, 2) >= 5.4, f"Expected ~5.45:1, got {ratio:.2f}"


def test_badge_blue_text_light_contrast_passes_wcag_aaa():
    """Verify light mode --badge-blue-text (#1e40af) on --accent-blue-light (#eff6ff) passes AAA (>= 7.0:1)."""
    ratio = contrast_ratio("#1e40af", "#eff6ff")
    assert ratio >= 7.0, f"Light mode badge text ratio {ratio:.2f} < 7.0"
    assert round(ratio, 2) >= 8.0, f"Expected ~8.05:1, got {ratio:.2f}"


def test_badge_blue_text_dark_contrast_passes_wcag_aaa():
    """Verify dark mode --badge-blue-text (#93c5fd) on dark card (#111827) passes AAA (>= 7.0:1)."""
    ratio = contrast_ratio("#93c5fd", "#111827")
    assert ratio >= 7.0, f"Dark mode badge text ratio {ratio:.2f} < 7.0"
    assert round(ratio, 2) >= 9.8, f"Expected ~9.81:1, got {ratio:.2f}"


# ==============================================================================
# CSS Token Declarations in index.css
# ==============================================================================


def test_index_css_token_definitions():
    """Verify index.css declares remediated tokens in both light and dark themes."""
    content = INDEX_CSS.read_text(encoding="utf-8")

    # Light mode checks (:root or [data-theme="light"])
    light_match = re.search(r':root,\s*\[data-theme="light"\]\s*\{([^}]+)\}', content)
    assert light_match is not None, "Could not find light theme block in index.css"
    light_body = light_match.group(1)

    assert re.search(r"--text-tertiary:\s*#64748b;", light_body), (
        "Light theme must set --text-tertiary to #64748b"
    )
    assert re.search(r"--badge-blue-text:\s*#1e40af;", light_body), (
        "Light theme must set --badge-blue-text to #1e40af"
    )
    assert re.search(r"--health-unknown:\s*#64748b;", light_body), (
        "Light theme must set --health-unknown to #64748b"
    )

    # Dark mode checks ([data-theme="dark"])
    dark_match = re.search(r'\[data-theme="dark"\]\s*\{([^}]+)\}', content)
    assert dark_match is not None, "Could not find dark theme block in index.css"
    dark_body = dark_match.group(1)

    assert re.search(r"--text-tertiary:\s*#94a3b8;", dark_body), (
        "Dark theme must set --text-tertiary to #94a3b8"
    )
    assert re.search(r"--badge-blue-text:\s*#93c5fd;", dark_body), (
        "Dark theme must set --badge-blue-text to #93c5fd"
    )
    assert re.search(r"--health-unknown:\s*#94a3b8;", dark_body), (
        "Dark theme must set --health-unknown to #94a3b8"
    )


# ==============================================================================
# Badge Color Rules in App.css
# ==============================================================================


def test_app_css_badge_color_bindings():
    """Verify App.css binds blue status badges to var(--badge-blue-text)."""
    content = APP_CSS.read_text(encoding="utf-8")

    assert re.search(r"\.badge\.backdated\s*\{[^}]*color:\s*var\(--badge-blue-text\)", content), (
        ".badge.backdated must use color: var(--badge-blue-text)"
    )
    assert re.search(r"\.badge\.snow-new\s*\{[^}]*color:\s*var\(--badge-blue-text\)", content), (
        ".badge.snow-new must use color: var(--badge-blue-text)"
    )
    assert re.search(r"\.badge\.badge-subtle\.blue\s*\{[^}]*color:\s*var\(--badge-blue-text\)", content), (
        ".badge.badge-subtle.blue must use color: var(--badge-blue-text)"
    )


# ==============================================================================
# Dynamic Chart Theme Contract (UI-06)
# ==============================================================================


def test_use_chart_theme_hook_structure():
    """Verify useChartTheme.js exists, exports hook, and sets up MutationObserver."""
    assert HOOK_FILE.exists(), f"Missing hook file: {HOOK_FILE}"
    content = HOOK_FILE.read_text(encoding="utf-8")

    assert "export function useChartTheme" in content or "export default useChartTheme" in content, (
        "useChartTheme.js must export useChartTheme"
    )
    assert "MutationObserver" in content, "Hook must use MutationObserver to watch theme changes"
    assert "attributeFilter: ['data-theme']" in content or 'data-theme' in content, (
        "Hook must observe data-theme attribute"
    )
    assert "tooltipStyle:" in content, "Hook must return tooltipStyle"
    assert "legendStyle:" in content, "Hook must return legendStyle"
    assert "colors:" in content, "Hook must return colors object"
    assert "axis:" in content, "Hook must return axis object"
    assert "grid:" in content, "Hook must return grid object"


def test_false_alert_metrics_chart_theme_binding():
    """Verify FalseAlertMetrics.jsx imports and binds useChartTheme for charts."""
    content = METRICS_FILE.read_text(encoding="utf-8")

    assert "useChartTheme" in content, "FalseAlertMetrics must import useChartTheme"
    assert "const chartTheme = useChartTheme();" in content, (
        "FalseAlertMetrics must invoke useChartTheme()"
    )
    assert "chartTheme.colors.primary" in content, "AreaChart must bind primary color to chartTheme"
    assert "chartTheme.colors.success" in content, "AreaChart must bind success color to chartTheme"
    assert "chartTheme.colors.danger" in content, "AreaChart must bind danger color to chartTheme"
    assert "chartTheme.axis.stroke" in content, "XAxis/YAxis must bind stroke to chartTheme.axis.stroke"
    assert "chartTheme.axis.tickFill" in content, "XAxis/YAxis must bind tick to chartTheme.axis.tickFill"
    assert "chartTheme.tooltipStyle" in content, "RechartsTooltip must bind contentStyle to chartTheme.tooltipStyle"


def test_alert_patterns_chart_theme_binding():
    """Verify AlertPatterns.jsx imports and binds useChartTheme for ComposedChart."""
    content = PATTERNS_FILE.read_text(encoding="utf-8")

    assert "useChartTheme" in content, "AlertPatterns must import useChartTheme"
    assert "useChartTheme()" in content, "AlertPatterns must invoke useChartTheme()"
    assert "chartTheme.colors.primary" in content, "ComposedChart must bind primary color to chartTheme"
    assert "chartTheme.axis.stroke" in content, "ComposedChart XAxis/YAxis must bind to chartTheme.axis.stroke"
    assert "chartTheme.axis.tickFill" in content, "ComposedChart XAxis/YAxis must bind to chartTheme.axis.tickFill"
    assert "chartTheme.tooltipStyle" in content, "ComposedChart Tooltip must bind to chartTheme.tooltipStyle"


def test_chat_chart_theme_binding():
    """Verify ChatChart.jsx imports and binds useChartTheme for chat charts."""
    content = CHAT_CHART_FILE.read_text(encoding="utf-8")

    assert "useChartTheme" in content, "ChatChart must import useChartTheme"
    assert "useChartTheme()" in content, "ChatChart must invoke useChartTheme()"
    assert "chartTheme.axis.stroke" in content, "ZoomableChart must bind axis stroke to chartTheme.axis.stroke"
    assert "chartTheme.tooltipStyle" in content, "ZoomableChart must bind Tooltip to chartTheme.tooltipStyle"

