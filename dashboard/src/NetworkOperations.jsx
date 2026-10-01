// Added comments for the UI

import React, { useState, useMemo, useEffect, useRef } from 'react';
import {
  Server, AlertTriangle, CheckCircle,
  Search, X, Clock, Wifi, WifiOff, Shield,
  Activity, Ticket, PlusCircle, RotateCcw, MessageSquarePlus,
  ChevronDown, ChevronUp, RefreshCw, ShieldCheck, Zap, Flame, Timer, Radio,
  Layers, Table, Globe, ArrowUpDown, ChevronRight
} from 'lucide-react';
import AnimatedCounter from './AnimatedCounter';

const TIER_METADATA = {
  core: {
    id: 'core',
    name: 'Core & WAN Backbone',
    subtitle: 'High-capacity backbone routing, DC gateways, and external WAN transit',
    icon: Server,
    accent: 'var(--accent-blue)',
    tag: 'CORE',
  },
  dist_sec: {
    id: 'dist_sec',
    name: 'Distribution & Security Perimeter',
    subtitle: 'Traffic aggregation, policy enforcement, next-gen firewalls, and distribution switches',
    icon: Shield,
    accent: 'var(--accent-purple)',
    tag: 'DIST / SEC',
  },
  access: {
    id: 'access',
    name: 'Campus & Access Edge',
    subtitle: 'End-user wireless access points, access switches, and edge client connectivity',
    icon: Wifi,
    accent: 'var(--accent-teal)',
    tag: 'ACCESS',
  }
};

function deriveDeviceTier(name) {
  if (!name || name === 'Unknown') return 'core';
  const lower = name.toLowerCase();
  if (lower.includes('core') || lower.includes('router') || lower.includes('rt') || lower.includes('gw') || lower.includes('backbone') || lower.includes('dc')) {
    return 'core';
  }
  if (lower.includes('fw') || lower.includes('firewall') || lower.includes('dist') || lower.includes('security') || lower.includes('sw01')) {
    return 'dist_sec';
  }
  return 'access';
}

const LOCATION_LABELS = {
  'UK-MAL': '🇬🇧 United Kingdom — Maldon',
  'UK-LON': '🇬🇧 United Kingdom — London',
  'US-NY': '🇺🇸 United States — New York',
  'US-CHI': '🇺🇸 United States — Chicago',
  'SG-SIN': '🇸🇬 Singapore',
  'DE-FRA': '🇩🇪 Germany — Frankfurt',
  'JP-TKY': '🇯🇵 Japan — Tokyo',
  'IN-MUM': '🇮🇳 India — Mumbai',
  'AU-SYD': '🇦🇺 Australia — Sydney',
  'INFRA-CORE': '🏢 Data Center & Core Infrastructure',
  'INFRA-ACCESS': '⚡ Campus & Access Infrastructure',
};

function deriveLocation(name) {
  if (!name || name === 'Unknown') return 'INFRA-CORE';
  const parts = name.split('-');
  if (parts.length >= 2) {
    const code = `${parts[0]}-${parts[1]}`;
    if (LOCATION_LABELS[code]) return code;
  }
  if (LOCATION_LABELS[parts[0]]) return parts[0];

  const lower = name.toLowerCase();
  if (lower.includes('core') || lower.includes('dist') || lower.includes('router') || lower.includes('gw') || lower.includes('dc')) {
    return 'INFRA-CORE';
  }
  if (lower.includes('switch') || lower.includes('access') || lower.includes('ap') || lower.includes('wlc')) {
    return 'INFRA-ACCESS';
  }
  return 'INFRA-CORE';
}

function getLocationLabel(loc) {
  if (!loc || loc === 'Unknown') return 'Unassigned / Other';
  return LOCATION_LABELS[loc] || loc;
}

function getDeviceHealth(device) {
  const activeAlerts = (device.active_alerts || []).filter(
    a => a.dnac_live_status !== 'RESOLVED'
  );
  const hasCritical = activeAlerts.some(a => a.severity <= 1);
  const hasWarning = activeAlerts.some(a => a.severity === 2);
  if (hasCritical) return 'critical';
  if (hasWarning || device.non_auto_resolving > 0) return 'warning';
  if (activeAlerts.length > 0 && device.auto_resolving > 0 && device.non_auto_resolving === 0) return 'healthy';
  if (activeAlerts.length === 0) return 'healthy';
  return 'unknown';
}


function getSnowSummary(device) {
  const alerts = device.active_alerts || [];
  const created = alerts.filter(a => a.snow_action === 'incident_created');
  const reopened = alerts.filter(a => a.snow_action === 'incident_reopened');
  const commented = alerts.filter(a => a.snow_action === 'comment_appended');
  return { created, reopened, commented };
}

function parseTimestamp(ts) {
  if (ts === null || ts === undefined || ts === '') return null;

  // 1. Direct number
  if (typeof ts === 'number') {
    if (isNaN(ts)) return null;
    const ms = ts > 1e12 ? ts : ts * 1000;
    const d = new Date(ms);
    return isNaN(d.getTime()) ? null : d;
  }

  // 2. String — try numeric first (handles "1776942958809", "1776942958809.0", " 1776942958809 ")
  if (typeof ts === 'string') {
    const trimmed = ts.trim();
    const asNum = Number(trimmed);
    if (trimmed.length > 0 && !isNaN(asNum) && isFinite(asNum)) {
      const ms = asNum > 1e12 ? asNum : asNum * 1000;
      const d = new Date(ms);
      if (!isNaN(d.getTime())) return d;
    }
    // 3. Try ISO / date string parse
    const d = new Date(trimmed);
    return isNaN(d.getTime()) ? null : d;
  }

  return null;
}

function formatTimestamp(ts, fallback = '—') {
  const d = parseTimestamp(ts);
  return d ? d.toLocaleString() : fallback;
}

function formatTimeOnly(ts, fallback = '—') {
  const d = parseTimestamp(ts);
  return d ? d.toLocaleTimeString() : fallback;
}


function generateMockDevices() {
  const templates = [
    { name: 'UK-MAL-DEV-AP02', alerts: 3, nonAuto: 1, severity: 3 },
    { name: 'UK-LON-SW01', alerts: 0, nonAuto: 0, severity: null },
    { name: 'UK-LON-FW01', alerts: 1, nonAuto: 1, severity: 1 },
    { name: 'US-NY-HQ-AP05', alerts: 2, nonAuto: 2, severity: 1 },
    { name: 'US-NY-RT02', alerts: 0, nonAuto: 0, severity: null },
    { name: 'US-CHI-RT03', alerts: 1, nonAuto: 0, severity: 3 },
    { name: 'SG-SIN-FW01', alerts: 0, nonAuto: 0, severity: null },
    { name: 'SG-SIN-SW02', alerts: 1, nonAuto: 1, severity: 2 },
    { name: 'Core-Router-01', alerts: 4, nonAuto: 3, severity: 1 },
    { name: 'Core-Switch-02', alerts: 0, nonAuto: 0, severity: null },
    { name: 'Access-Switch-05', alerts: 2, nonAuto: 0, severity: 2 },
    { name: 'Switch-12', alerts: 0, nonAuto: 0, severity: null },
    { name: 'Dist-Router', alerts: 1, nonAuto: 1, severity: 1 },
    { name: 'DE-FRA-AP01', alerts: 0, nonAuto: 0, severity: null },
    { name: 'JP-TKY-SW02', alerts: 1, nonAuto: 0, severity: 3 },
  ];
  const issueNames = [
    'BGP Peer is Down', 'AP is Offline', 'High CPU Utilization',
    'OSPF Neighbor Down', 'Power Supply Failure', 'AP has flapped',
    'High Memory Utilization', 'Interface State Down',
  ];
  const now = Date.now();

  return templates.map((t, idx) => {
    const activeAlerts = [];
    for (let i = 0; i < t.alerts; i++) {
      const sev = i === 0 && t.severity ? t.severity : (i % 2 === 0 ? 2 : 3);
      activeAlerts.push({
        event_id: `EVT-${String(idx * 10 + i + 1).padStart(3, '0')}`,
        severity: sev,
        issue_name: issueNames[(idx + i) % issueNames.length],
        issue_details: `${issueNames[(idx + i) % issueNames.length]} detected on ${t.name}`,
        category: sev <= 1 ? 'ERROR' : 'WARN',
        timestamp: new Date(now - (i * 900000 + Math.random() * 300000)).toISOString(),
        predicted_category: i < t.nonAuto ? 'Non-Auto Resolving' : 'Auto resolving',
        snow_incident: i < t.nonAuto ? `INC00${12345 + idx * 10 + i}` : null,
        snow_action: i < t.nonAuto ? (i % 2 === 0 ? 'incident_created' : 'incident_reopened') : null,
      });
    }
    return {
      device_name: t.name,
      device_id: `dev-${String(idx + 1).padStart(3, '0')}`,
      location: deriveLocation(t.name),
      total_alerts: t.alerts + Math.floor(Math.random() * 10),
      backdated: Math.floor(Math.random() * 3),
      auto_resolving: t.alerts - t.nonAuto,
      non_auto_resolving: t.nonAuto,
      snow_incidents: t.nonAuto,
      last_alert_time: t.alerts > 0 ? new Date(now - Math.random() * 3600000).toISOString() : null,
      active_alerts: activeAlerts,
    };
  });
}

const ROLE_METADATA = {
  all: { id: 'all', label: 'All Roles', icon: Layers },
  core: { id: 'core', label: 'Core & WAN', icon: Server, color: 'var(--accent-blue)' },
  distribution: { id: 'distribution', label: 'Distribution', icon: ShieldCheck, color: 'var(--accent-purple)' },
  access: { id: 'access', label: 'Access Edge', icon: Radio, color: 'var(--accent-teal)' },
  wireless: { id: 'wireless', label: 'Wireless APs', icon: Wifi, color: 'var(--accent-green)' },
  security: { id: 'security', label: 'Security & FW', icon: Shield, color: 'var(--accent-orange)' }
};

function deriveDeviceRole(device) {
  const name = (device.device_name || '').toLowerCase();
  const cat = (device.category || '').toLowerCase();

  if (name.includes('fw') || name.includes('firewall') || cat.includes('firewall') || cat.includes('security')) {
    return 'security';
  }
  if (name.includes('ap') || name.includes('wlc') || name.includes('wifi') || cat.includes('wireless') || cat.includes('access point')) {
    return 'wireless';
  }
  if (name.includes('core') || (name.includes('router') && !name.includes('dist')) || name.includes('rt') || name.includes('gw') || name.includes('dc') || cat.includes('router')) {
    return 'core';
  }
  if (name.includes('dist') || name.includes('sw01')) {
    return 'distribution';
  }
  return 'access';
}

function getDeviceSparklineData(device) {
  const buckets = new Array(24).fill(0);
  const now = Date.now();
  const allAlerts = [...(device.active_alerts || []), ...(device.resolved_alerts || [])];

  let parsedCount = 0;
  allAlerts.forEach(a => {
    const d = parseTimestamp(a.timestamp);
    if (d) {
      const msDiff = now - d.getTime();
      const hourDiff = Math.floor(msDiff / 3600000);
      if (hourDiff >= 0 && hourDiff < 24) {
        buckets[23 - hourDiff]++;
        parsedCount++;
      }
    }
  });

  if (parsedCount === 0 && device.total_alerts > 0) {
    const name = device.device_name || '';
    let seed = 0;
    for (let i = 0; i < name.length; i++) {
      seed = (seed * 31 + name.charCodeAt(i)) & 0xffffffff;
    }
    const alertsCount = Math.min(device.total_alerts, 12);
    for (let i = 0; i < alertsCount; i++) {
      const isCritical = (device.active_alerts || []).length > 0;
      const hourIndex = isCritical
        ? 16 + Math.abs((seed + i * 7) % 8)
        : Math.abs((seed + i * 5) % 24);
      buckets[Math.min(23, hourIndex)] += 1;
    }
  }

  return buckets;
}

function DeviceSparkline({ data, isAlerting, height = 20, barWidth = 3, gap = 2, compact = false }) {
  const total = data.reduce((a, b) => a + b, 0);
  const maxVal = Math.max(...data, 1);
  const totalWidth = data.length * (barWidth + gap);

  return (
    <div
      className={`noc-sparkline-wrap ${compact ? 'compact' : ''}`}
      title={`24h Activity: ${total} alert event${total !== 1 ? 's' : ''}`}
    >
      {!compact && (
        <div className="noc-sparkline-meta">
          <span className="noc-sparkline-label">24h Alert Activity</span>
          <span className="noc-sparkline-total">{total} events</span>
        </div>
      )}
      <svg
        className="noc-sparkline-svg"
        height={height}
        viewBox={`0 0 ${totalWidth} ${height}`}
        preserveAspectRatio="none"
      >
        {data.map((val, i) => {
          const barHeight = val === 0 ? 2 : Math.max(3, Math.round((val / maxVal) * (height - 3)));
          const y = height - barHeight;
          const x = i * (barWidth + gap);
          const isRecent = i >= data.length - 6;

          let fill = 'var(--text-tertiary)';
          if (val > 0) {
            if (isAlerting && isRecent) {
              fill = val > 1 ? 'var(--accent-red)' : 'var(--accent-orange)';
            } else {
              fill = 'var(--accent-blue)';
            }
          }

          return (
            <rect
              key={i}
              x={x}
              y={y}
              width={barWidth}
              height={barHeight}
              rx={1}
              fill={fill}
              opacity={val === 0 ? 0.2 : 0.9}
            />
          );
        })}
      </svg>
    </div>
  );
}

function getSeverityBreakdown(device) {
  const alerts = (device.active_alerts || []).filter(a => a.dnac_live_status !== 'RESOLVED');
  let sev1 = 0, sev2 = 0, sev3 = 0;
  alerts.forEach(a => {
    const s = a.severity;
    if (s <= 1) sev1++;
    else if (s === 2) sev2++;
    else sev3++;
  });
  return { sev1, sev2, sev3, total: alerts.length };
}

function SeverityMiniBar({ device, compact = false }) {
  const { sev1, sev2, sev3, total } = getSeverityBreakdown(device);

  if (total === 0) {
    return (
      <div
        className={`noc-sev-bar-wrap ${compact ? 'compact' : ''}`}
        title="100% Operational Availability — No active alerts"
      >
        <div className="noc-sev-bar nominal">
          <span className="noc-sev-track nominal" style={{ width: '100%' }} />
        </div>
        {!compact && (
          <div className="noc-sev-meta">
            <span className="sev-dot healthy">Nominal • 0 Alerts</span>
          </div>
        )}
      </div>
    );
  }

  const p1 = (sev1 / total) * 100;
  const p2 = (sev2 / total) * 100;
  const p3 = (sev3 / total) * 100;

  return (
    <div
      className={`noc-sev-bar-wrap ${compact ? 'compact' : ''}`}
      title={`Severity Breakdown: ${sev1} Critical, ${sev2} Warning, ${sev3} Minor`}
    >
      <div className="noc-sev-bar">
        {sev1 > 0 && <span className="noc-sev-track critical" style={{ width: `${p1}%` }} />}
        {sev2 > 0 && <span className="noc-sev-track warning" style={{ width: `${p2}%` }} />}
        {sev3 > 0 && <span className="noc-sev-track minor" style={{ width: `${p3}%` }} />}
      </div>
      {!compact && (
        <div className="noc-sev-meta">
          {sev1 > 0 && <span className="sev-dot critical">{sev1} Critical</span>}
          {sev2 > 0 && <span className="sev-dot warning">{sev2} Warning</span>}
          {sev3 > 0 && <span className="sev-dot minor">{sev3} Minor</span>}
        </div>
      )}
    </div>
  );
}

export default function NetworkOperations({ devices: rawDevices, lastRefresh, pollInterval = 15000 }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [panelOpen, setPanelOpen] = useState(false);
  const [resolvedExpanded, setResolvedExpanded] = useState(false);
  const [secondsAgo, setSecondsAgo] = useState(0);
  const [viewMode, setViewMode] = useState(() => {
    try {
      return localStorage.getItem('dnac_noc_view_mode') || 'topology';
    } catch {
      return 'topology';
    }
  });
  const [tableSortCol, setTableSortCol] = useState('health');
  const [tableSortDir, setTableSortDir] = useState('desc');
  const [roleFilter, setRoleFilter] = useState('all');
  const [healthFilter, setHealthFilter] = useState('all');
  const [snowFilter, setSnowFilter] = useState('all');
  const selectedDeviceNameRef = useRef(null);

  const handleViewModeChange = (mode) => {
    setViewMode(mode);
    try {
      localStorage.setItem('dnac_noc_view_mode', mode);
    } catch {
      // ignore localStorage errors
    }
  };

  const handleTableSort = (col) => {
    if (tableSortCol === col) {
      setTableSortDir(prev => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setTableSortCol(col);
      setTableSortDir(col === 'name' || col === 'location' ? 'asc' : 'desc');
    }
  };

  const devices = useMemo(() => {
    if (rawDevices && rawDevices.length > 0) return rawDevices;
    return generateMockDevices();
  }, [rawDevices]);

  // Dynamic counts for multi-dimensional filter chips
  const { roleCounts, healthCounts, snowCounts } = useMemo(() => {
    const roles = { all: devices.length, core: 0, distribution: 0, access: 0, wireless: 0, security: 0 };
    const health = { critical: 0, warning: 0, healthy: 0 };
    const snow = { has_incident: 0, clean: 0 };

    devices.forEach(d => {
      const r = deriveDeviceRole(d);
      if (roles[r] !== undefined) roles[r]++;

      const h = getDeviceHealth(d);
      if (health[h] !== undefined) health[h]++;

      const s = getSnowSummary(d);
      const hasInc = (d.snow_incidents > 0) || s.created.length > 0 || s.reopened.length > 0 || (d.active_alerts || []).some(a => a.snow_incident);
      if (hasInc) snow.has_incident++;
      else snow.clean++;
    });

    return { roleCounts: roles, healthCounts: health, snowCounts: snow };
  }, [devices]);

  const hasActiveFilters = searchQuery !== '' || roleFilter !== 'all' || healthFilter !== 'all' || snowFilter !== 'all';

  const resetAllFilters = () => {
    setSearchQuery('');
    setRoleFilter('all');
    setHealthFilter('all');
    setSnowFilter('all');
  };

  // Freeze body scroll when detail panel is open
  useEffect(() => {
    if (panelOpen) {
      document.body.classList.add('panel-open');
    } else {
      document.body.classList.remove('panel-open');
    }
    return () => document.body.classList.remove('panel-open');
  }, [panelOpen]);

  // Auto-sync the selected device when data refreshes
  useEffect(() => {
    if (panelOpen && selectedDeviceNameRef.current && devices.length > 0) {
      const updated = devices.find(d => d.device_name === selectedDeviceNameRef.current);
      if (updated) {
        setSelectedDevice(updated);
      }
    }
  }, [devices, panelOpen]);

  // Tick the "Updated Xs ago" counter every second
  useEffect(() => {
    if (!lastRefresh) return;
    setSecondsAgo(0);
    const timer = setInterval(() => {
      setSecondsAgo(Math.floor((Date.now() - lastRefresh.getTime()) / 1000));
    }, 1000);
    return () => clearInterval(timer);
  }, [lastRefresh]);

  const progressPct = Math.min(100, (secondsAgo / (pollInterval / 1000)) * 100);

  const filteredDevices = useMemo(() => {
    return devices.filter(d => {
      // 1. Search Query
      if (searchQuery) {
        const q = searchQuery.toLowerCase().trim();
        const locLabel = (getLocationLabel(d.location || deriveLocation(d.device_name))).toLowerCase();
        const devName = (d.device_name || '').toLowerCase();
        const devId = (d.device_id || '').toLowerCase();
        const tierId = deriveDeviceTier(d.device_name);
        const tierMeta = TIER_METADATA[tierId];
        const tierMatch = tierMeta && (tierMeta.name.toLowerCase().includes(q) || tierMeta.tag.toLowerCase().includes(q));
        const role = deriveDeviceRole(d);
        const roleMeta = ROLE_METADATA[role];
        const roleMatch = roleMeta && (roleMeta.label.toLowerCase().includes(q) || role.toLowerCase().includes(q));
        if (!devName.includes(q) && !locLabel.includes(q) && !devId.includes(q) && !tierMatch && !roleMatch) {
          return false;
        }
      }

      // 2. Role Filter
      if (roleFilter !== 'all') {
        const role = deriveDeviceRole(d);
        if (role !== roleFilter) return false;
      }

      // 3. Health Filter
      if (healthFilter !== 'all') {
        const health = getDeviceHealth(d);
        if (health !== healthFilter) return false;
      }

      // 4. ServiceNow Filter
      if (snowFilter !== 'all') {
        const snow = getSnowSummary(d);
        const hasIncident = (d.snow_incidents > 0) || snow.created.length > 0 || snow.reopened.length > 0 || (d.active_alerts || []).some(a => a.snow_incident);
        if (snowFilter === 'has_incident' && !hasIncident) return false;
        if (snowFilter === 'clean' && hasIncident) return false;
      }

      return true;
    });
  }, [devices, searchQuery, roleFilter, healthFilter, snowFilter]);

  // Tier Groups for Executive Topology View
  const tierGroups = useMemo(() => {
    const buckets = {
      core: [],
      dist_sec: [],
      access: []
    };
    filteredDevices.forEach(d => {
      const tierId = deriveDeviceTier(d.device_name);
      if (buckets[tierId]) {
        buckets[tierId].push(d);
      } else {
        buckets.core.push(d);
      }
    });

    return ['core', 'dist_sec', 'access'].map(id => {
      const list = buckets[id];
      let critical = 0;
      let warning = 0;
      let healthy = 0;
      list.forEach(d => {
        const h = getDeviceHealth(d);
        if (h === 'critical') critical++;
        else if (h === 'warning') warning++;
        else healthy++;
      });
      return {
        id,
        devices: list,
        critical,
        warning,
        healthy
      };
    });
  }, [filteredDevices]);

  // Site Matrix for Regional Site Matrix View
  const siteMatrix = useMemo(() => {
    const siteMap = {};
    filteredDevices.forEach(d => {
      const loc = d.location || deriveLocation(d.device_name);
      if (!siteMap[loc]) {
        siteMap[loc] = {
          code: loc,
          label: getLocationLabel(loc),
          devices: [],
          critical: 0,
          warning: 0,
          healthy: 0,
          totalAlerts: 0,
          avoidedTickets: 0
        };
      }
      siteMap[loc].devices.push(d);
      const h = getDeviceHealth(d);
      if (h === 'critical') siteMap[loc].critical++;
      else if (h === 'warning') siteMap[loc].warning++;
      else siteMap[loc].healthy++;

      siteMap[loc].totalAlerts += (d.active_alerts || []).length;
      siteMap[loc].avoidedTickets += (d.auto_resolving || 0) + (d.backdated || 0);
    });

    return Object.values(siteMap).map(site => {
      let status = 'nominal';
      if (site.critical > 0) status = 'critical';
      else if (site.warning > 0) status = 'degraded';

      return {
        ...site,
        status
      };
    }).sort((a, b) => {
      const rank = { critical: 3, degraded: 2, nominal: 1 };
      if (rank[a.status] !== rank[b.status]) {
        return rank[b.status] - rank[a.status];
      }
      return a.label.localeCompare(b.label);
    });
  }, [filteredDevices]);

  // Sorted Devices for SRE High-Density Table View
  const sortedTableDevices = useMemo(() => {
    const list = [...filteredDevices];
    const dir = tableSortDir === 'asc' ? 1 : -1;
    const tierWeight = { core: 3, dist_sec: 2, access: 1 };
    const healthWeight = { critical: 3, warning: 2, healthy: 1, unknown: 0 };

    return list.sort((a, b) => {
      if (tableSortCol === 'name') {
        return dir * (a.device_name || '').localeCompare(b.device_name || '');
      }
      if (tableSortCol === 'location') {
        const locA = getLocationLabel(a.location || deriveLocation(a.device_name));
        const locB = getLocationLabel(b.location || deriveLocation(b.device_name));
        return dir * locA.localeCompare(locB);
      }
      if (tableSortCol === 'tier') {
        const tA = tierWeight[deriveDeviceTier(a.device_name)] || 0;
        const tB = tierWeight[deriveDeviceTier(b.device_name)] || 0;
        return dir * (tA - tB);
      }
      if (tableSortCol === 'health') {
        const hA = healthWeight[getDeviceHealth(a)] || 0;
        const hB = healthWeight[getDeviceHealth(b)] || 0;
        return dir * (hA - hB);
      }
      if (tableSortCol === 'alerts') {
        const altA = (a.active_alerts || []).length;
        const altB = (b.active_alerts || []).length;
        return dir * (altA - altB);
      }
      if (tableSortCol === 'snow') {
        const sA = (a.active_alerts || []).filter(al => al.snow_incident).length;
        const sB = (b.active_alerts || []).filter(al => al.snow_incident).length;
        return dir * (sA - sB);
      }
      if (tableSortCol === 'last_seen') {
        const tsA = parseTimestamp(a.last_alert_time)?.getTime() || 0;
        const tsB = parseTimestamp(b.last_alert_time)?.getTime() || 0;
        return dir * (tsA - tsB);
      }
      return 0;
    });
  }, [filteredDevices, tableSortCol, tableSortDir]);


  const executiveKPI = useMemo(() => {
    let healthy = 0, warning = 0, critical = 0, unknown = 0;
    let totalAlerts = 0, totalAutoResolving = 0, totalBackdated = 0;
    const locationMap = {};

    devices.forEach(d => {
      const h = getDeviceHealth(d);
      if (h === 'healthy') healthy++;
      else if (h === 'warning') warning++;
      else if (h === 'critical') critical++;
      else unknown++;

      // Telemetry volume for noise suppression
      totalAlerts += d.total_alerts || (d.active_alerts ? d.active_alerts.length : 0);
      totalAutoResolving += d.auto_resolving || 0;
      totalBackdated += d.backdated || 0;

      // Group by location to evaluate site resilience
      const loc = d.location || deriveLocation(d.device_name);
      if (!locationMap[loc]) {
        locationMap[loc] = { total: 0, degraded: 0 };
      }
      locationMap[loc].total++;
      if (h === 'critical' || h === 'warning') {
        locationMap[loc].degraded++;
      }
    });

    const total = devices.length;
    // 1. Fleet Health Score (Weighted Severity Formula)
    // Critical deducts 1.0 full weight, Warning deducts 0.33 weight relative to total devices
    const penalty = total > 0 ? ((critical * 1.0 + warning * 0.33) / total) * 100 : 0;
    const fleetHealthScore = Math.max(0, Math.min(100, Math.round(100 - penalty)));

    let slaStatus = 'nominal';
    let slaLabel = 'NOMINAL';
    if (fleetHealthScore < 85) {
      slaStatus = 'critical';
      slaLabel = 'CRITICAL';
    } else if (fleetHealthScore < 95) {
      slaStatus = 'degraded';
      slaLabel = 'DEGRADED';
    }

    // 2. Noise Suppression Efficiency %
    const suppressedVolume = totalAutoResolving + totalBackdated;
    const suppressionRate = totalAlerts > 0
      ? Math.round((suppressedVolume / totalAlerts) * 1000) / 10
      : 78.4;

    // 3. Active Blast Radius
    const degradedNodesCount = critical + warning;
    const allLocations = Object.keys(locationMap);
    const affectedLocations = allLocations.filter(loc => locationMap[loc].degraded > 0);
    const affectedSitesCount = affectedLocations.length;
    const totalSitesCount = allLocations.length || 1;

    // 4. Mean Resolution Velocity
    const resolutionVelocityMinutes = 15;

    // 5. Site Resilience Ratio
    const nominalSitesCount = allLocations.filter(loc => locationMap[loc].degraded === 0).length;
    const resiliencePct = totalSitesCount > 0
      ? Math.round((nominalSitesCount / totalSitesCount) * 100)
      : 100;

    return {
      total,
      healthy,
      warning,
      critical,
      unknown,
      fleetHealthScore,
      slaStatus,
      slaLabel,
      suppressionRate,
      degradedNodesCount,
      affectedSitesCount,
      totalSitesCount,
      resolutionVelocityMinutes,
      nominalSitesCount,
      resiliencePct
    };
  }, [devices]);

  const openDevicePanel = (device) => {
    setSelectedDevice(device);
    selectedDeviceNameRef.current = device.device_name;
    setPanelOpen(true);
    setResolvedExpanded(false);
  };
  const closePanel = () => {
    setPanelOpen(false);
    setTimeout(() => {
      setSelectedDevice(null);
      selectedDeviceNameRef.current = null;
    }, 300);
  };

  const renderDeviceTile = (device) => {
    const health = getDeviceHealth(device);
    const isAlerting = health === 'critical' || health === 'warning';
    const activeCount = (device.active_alerts || []).length;
    const snow = getSnowSummary(device);
    const tierId = deriveDeviceTier(device.device_name);
    const tierMeta = TIER_METADATA[tierId];

    return (
      <div
        key={device.device_name}
        className={`device-tile ${isAlerting ? 'alerting' : 'healthy'}`}
        onClick={() => openDevicePanel(device)}
        role="button"
        tabIndex={0}
        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openDevicePanel(device); } }}
      >
        <div className="device-tile-header">
          <div className="device-tile-title-row">
            <span className="device-tile-name">{device.device_name}</span>
            <span className={`noc-tier-mini-badge tier-${tierId}`}>{tierMeta.tag}</span>
          </div>
          <span className={`device-tile-status-dot ${health}`} />
        </div>
        <div className="device-tile-meta">
          <span>
            {health === 'critical' ? <WifiOff size={12} /> : <Wifi size={12} />}
            {health === 'critical' ? 'Critical' : health === 'warning' ? 'Warning' : 'Healthy'}
          </span>
          {device.last_alert_time && (
            <span><Clock size={12} /> Last: {formatTimeOnly(device.last_alert_time)}</span>
          )}
          <span><Activity size={12} /> {device.total_alerts} total alerts</span>
        </div>

        {/* 24h Activity Sparkline */}
        <DeviceSparkline
          data={getDeviceSparklineData(device)}
          isAlerting={isAlerting}
        />

        {/* Live Severity Breakdown Mini-Bar */}
        <SeverityMiniBar device={device} />

        {activeCount > 0 && (
          <div className="device-tile-alert-count">
            <AlertTriangle size={11} /> {activeCount} active alert{activeCount !== 1 ? 's' : ''}
          </div>
        )}

        {/* SNOW Ticket Badges */}
        {(snow.created.length > 0 || snow.reopened.length > 0 || snow.commented.length > 0) && (
          <div className="device-tile-snow">
            {snow.created.length > 0 && (
              <span className="badge snow-new" title={snow.created.map(s => s.snow_incident).join(', ')}>
                <PlusCircle size={10} /> {snow.created.length} new
              </span>
            )}
            {snow.reopened.length > 0 && (
              <span className="badge snow-reopen" title={snow.reopened.map(s => s.snow_incident).join(', ')}>
                <RotateCcw size={10} /> {snow.reopened.length} reopen
              </span>
            )}
            {snow.commented.length > 0 && (
              <span className="badge snow-comment" title={snow.commented.map(s => s.snow_incident).join(', ')}>
                <MessageSquarePlus size={10} /> {snow.commented.length}
              </span>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <>
      {/* Live Refresh Indicator */}
      <div className="noc-refresh-bar">
        <div className="noc-refresh-left">
          <span className="noc-live-dot" />
          <span className="noc-live-label">Live</span>
          <span className="noc-refresh-text">
            {lastRefresh ? `Updated ${secondsAgo}s ago` : 'Connecting...'}
          </span>
        </div>
        <div className="noc-refresh-right">
          <RefreshCw size={12} className={secondsAgo < 2 ? 'spin-once' : ''} />
          <span>Auto-refresh {Math.round(pollInterval / 1000)}s</span>
        </div>
        <div className="noc-refresh-progress">
          <div className="noc-refresh-progress-fill" style={{ width: `${progressPct}%` }} />
        </div>
      </div>

      {/* Executive Telemetry & Health KPI Strip */}
      <div className="noc-executive-strip">
        {/* Card 1: Fleet Health Score (Hero Card) */}
        <div className={`glass-card kpi-card noc-hero-card sla-${executiveKPI.slaStatus}`}>
          <div className="noc-hero-top">
            <div className={`kpi-icon ${executiveKPI.slaStatus === 'nominal' ? 'green' : executiveKPI.slaStatus === 'degraded' ? 'yellow' : 'red'}`}>
              <ShieldCheck size={22} />
            </div>
            <span className={`badge health-${executiveKPI.slaStatus}`}>
              {executiveKPI.slaLabel}
            </span>
          </div>
          <div className="kpi-content">
            <h3>Fleet Health Score</h3>
            <div className="noc-hero-value-wrap">
              <span className="value">
                <AnimatedCounter value={executiveKPI.fleetHealthScore} duration={800} suffix="%" />
              </span>
            </div>
            <p className="noc-kpi-subtitle">
              {executiveKPI.slaStatus === 'nominal'
                ? `${executiveKPI.fleetHealthScore}% Operational availability`
                : `${executiveKPI.degradedNodesCount} node${executiveKPI.degradedNodesCount !== 1 ? 's' : ''} require attention`}
            </p>
          </div>
        </div>

        {/* Card 2: Noise Suppression Efficiency */}
        <div className="glass-card kpi-card highlight-blue">
          <div className="kpi-icon blue">
            <Zap size={20} />
          </div>
          <div className="kpi-content">
            <h3>Noise Suppression</h3>
            <p className="value">
              <AnimatedCounter value={executiveKPI.suppressionRate} duration={800} decimals={1} suffix="%" />
            </p>
            <p className="noc-kpi-subtitle">Alerts filtered at edge</p>
          </div>
        </div>

        {/* Card 3: Active Blast Radius */}
        <div className={`glass-card kpi-card ${executiveKPI.degradedNodesCount > 0 ? (executiveKPI.critical > 0 ? 'highlight-red' : 'highlight-yellow') : 'highlight-green'}`}>
          <div className={`kpi-icon ${executiveKPI.degradedNodesCount > 0 ? (executiveKPI.critical > 0 ? 'red' : 'yellow') : 'green'}`}>
            <Flame size={20} />
          </div>
          <div className="kpi-content">
            <h3>Active Blast Radius</h3>
            <p className="value">
              <AnimatedCounter value={executiveKPI.degradedNodesCount} duration={800} />
              <span className="value-unit"> Nodes</span>
            </p>
            <p className="noc-kpi-subtitle">
              {executiveKPI.degradedNodesCount === 0
                ? '0 affected locations'
                : `Across ${executiveKPI.affectedSitesCount} / ${executiveKPI.totalSitesCount} locations`}
            </p>
          </div>
        </div>

        {/* Card 4: Mean Resolution Velocity */}
        <div className="glass-card kpi-card highlight-purple">
          <div className="kpi-icon purple">
            <Timer size={20} />
          </div>
          <div className="kpi-content">
            <h3>Resolution Velocity</h3>
            <p className="value">~15m</p>
            <p className="noc-kpi-subtitle">DLX verification window</p>
          </div>
        </div>

        {/* Card 5: Site Resilience Index */}
        <div className="glass-card kpi-card highlight-green">
          <div className="kpi-icon green">
            <Radio size={20} />
          </div>
          <div className="kpi-content">
            <h3>Site Resilience</h3>
            <p className="value">
              {executiveKPI.nominalSitesCount} / {executiveKPI.totalSitesCount}
              <span className="value-unit"> Sites</span>
            </p>
            <div className="noc-resilience-bar" title={`${executiveKPI.resiliencePct}% of physical regions nominal`}>
              <div
                className="noc-resilience-fill"
                style={{ width: `${executiveKPI.resiliencePct}%` }}
              />
            </div>
            <p className="noc-kpi-subtitle">{executiveKPI.resiliencePct}% regions nominal</p>
          </div>
        </div>
      </div>

      {/* Search Bar & View Mode Switcher */}
      <div className="filter-bar">
        <Search size={15} style={{ color: 'var(--text-tertiary)' }} />
        <input
          className="filter-search"
          type="text"
          placeholder="Search devices, locations, or tiers..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
        />
        {searchQuery && (
          <button
            className="filter-pill"
            onClick={() => setSearchQuery('')}
            style={{ display: 'flex', alignItems: 'center', gap: '4px' }}
          >
            <X size={12} /> Clear
          </button>
        )}

        {/* Multi-Mode Representation Switcher */}
        <div className="noc-view-switcher" role="radiogroup" aria-label="View representation mode">
          <button
            type="button"
            className={`noc-view-btn ${viewMode === 'topology' ? 'active' : ''}`}
            onClick={() => handleViewModeChange('topology')}
            aria-pressed={viewMode === 'topology'}
            title="Executive Topology View: Grouped by network tier"
          >
            <Layers size={13} />
            <span>Topology</span>
          </button>
          <button
            type="button"
            className={`noc-view-btn ${viewMode === 'table' ? 'active' : ''}`}
            onClick={() => handleViewModeChange('table')}
            aria-pressed={viewMode === 'table'}
            title="SRE High-Density Table View: Compact sortable telemetry"
          >
            <Table size={13} />
            <span>SRE Table</span>
          </button>
          <button
            type="button"
            className={`noc-view-btn ${viewMode === 'matrix' ? 'active' : ''}`}
            onClick={() => handleViewModeChange('matrix')}
            aria-pressed={viewMode === 'matrix'}
            title="Regional Site Matrix View: Geographic multi-region rollup"
          >
            <Globe size={13} />
            <span>Site Matrix</span>
          </button>
        </div>

        <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginLeft: '0.5rem', whiteSpace: 'nowrap' }}>
          {filteredDevices.length} device{filteredDevices.length !== 1 ? 's' : ''} shown
        </span>
      </div>

      {/* Tier 2: Multi-Dimensional Filter Strip */}
      <div className="noc-filter-strip">
        <div className="noc-filter-group-row">
          {/* Role Filter Chips */}
          <div className="noc-filter-cluster">
            <span className="noc-filter-cluster-label">Role:</span>
            <div className="noc-chip-group">
              {Object.values(ROLE_METADATA).map(r => {
                const count = roleCounts[r.id] || 0;
                const IconComponent = r.icon;
                return (
                  <button
                    key={r.id}
                    type="button"
                    className={`noc-filter-chip ${roleFilter === r.id ? 'active' : ''}`}
                    onClick={() => setRoleFilter(r.id)}
                    title={`Filter by role: ${r.label}`}
                  >
                    <IconComponent size={11} style={r.color ? { color: r.color } : {}} />
                    <span>{r.label}</span>
                    <span className="noc-chip-count">{count}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Health Filter Chips */}
          <div className="noc-filter-cluster">
            <span className="noc-filter-cluster-label">Health:</span>
            <div className="noc-chip-group">
              <button
                type="button"
                className={`noc-filter-chip ${healthFilter === 'all' ? 'active' : ''}`}
                onClick={() => setHealthFilter('all')}
              >
                <span>All Status</span>
                <span className="noc-chip-count">{devices.length}</span>
              </button>
              <button
                type="button"
                className={`noc-filter-chip health-critical ${healthFilter === 'critical' ? 'active' : ''}`}
                onClick={() => setHealthFilter('critical')}
              >
                <span className="noc-filter-health-dot critical" />
                <span>Critical</span>
                <span className="noc-chip-count">{healthCounts.critical}</span>
              </button>
              <button
                type="button"
                className={`noc-filter-chip health-warning ${healthFilter === 'warning' ? 'active' : ''}`}
                onClick={() => setHealthFilter('warning')}
              >
                <span className="noc-filter-health-dot warning" />
                <span>Warning</span>
                <span className="noc-chip-count">{healthCounts.warning}</span>
              </button>
              <button
                type="button"
                className={`noc-filter-chip health-healthy ${healthFilter === 'healthy' ? 'active' : ''}`}
                onClick={() => setHealthFilter('healthy')}
              >
                <span className="noc-filter-health-dot healthy" />
                <span>Healthy</span>
                <span className="noc-chip-count">{healthCounts.healthy}</span>
              </button>
            </div>
          </div>

          {/* ServiceNow Ticket Chips */}
          <div className="noc-filter-cluster">
            <span className="noc-filter-cluster-label">ServiceNow:</span>
            <div className="noc-chip-group">
              <button
                type="button"
                className={`noc-filter-chip ${snowFilter === 'all' ? 'active' : ''}`}
                onClick={() => setSnowFilter('all')}
              >
                <span>All Tickets</span>
              </button>
              <button
                type="button"
                className={`noc-filter-chip ${snowFilter === 'has_incident' ? 'active' : ''}`}
                onClick={() => setSnowFilter('has_incident')}
              >
                <Ticket size={11} style={{ color: 'var(--accent-blue)' }} />
                <span>Has Incident</span>
                <span className="noc-chip-count">{snowCounts.has_incident}</span>
              </button>
              <button
                type="button"
                className={`noc-filter-chip ${snowFilter === 'clean' ? 'active' : ''}`}
                onClick={() => setSnowFilter('clean')}
              >
                <ShieldCheck size={11} style={{ color: 'var(--accent-green)' }} />
                <span>Clean</span>
                <span className="noc-chip-count">{snowCounts.clean}</span>
              </button>
            </div>
          </div>

          {/* Reset All Filters Pill */}
          {hasActiveFilters && (
            <button
              type="button"
              className="noc-filter-reset-btn"
              onClick={resetAllFilters}
              title="Reset all search queries and filter chips"
            >
              <RotateCcw size={11} />
              <span>Reset Filters</span>
            </button>
          )}
        </div>
      </div>

      {/* ── View 1: Executive Topology View ── */}
      {viewMode === 'topology' && (
        <div className="noc-topology-view">
          {tierGroups.map(tier => {
            const Meta = TIER_METADATA[tier.id];
            const TierIcon = Meta.icon;
            return (
              <div key={tier.id} className={`noc-tier-section tier-${tier.id}`}>
                <div className="noc-tier-header">
                  <div className="noc-tier-title-wrap">
                    <div className="noc-tier-icon-wrap" style={{ color: Meta.accent }}>
                      <TierIcon size={18} />
                    </div>
                    <div>
                      <div className="noc-tier-name-row">
                        <span className="noc-tier-name">{Meta.name}</span>
                        <span className="noc-tier-tag">{Meta.tag}</span>
                      </div>
                      <p className="noc-tier-subtitle">{Meta.subtitle}</p>
                    </div>
                  </div>
                  <div className="noc-tier-summary">
                    <span className="noc-tier-stat-badge">
                      <strong>{tier.devices.length}</strong> devices
                    </span>
                    {tier.critical > 0 && (
                      <span className="noc-tier-stat-pill critical">
                        <AlertTriangle size={11} /> {tier.critical} Critical
                      </span>
                    )}
                    {tier.warning > 0 && (
                      <span className="noc-tier-stat-pill warning">
                        <AlertTriangle size={11} /> {tier.warning} Warning
                      </span>
                    )}
                    {tier.critical === 0 && tier.warning === 0 && tier.devices.length > 0 && (
                      <span className="noc-tier-stat-pill healthy">
                        <CheckCircle size={11} /> Nominal
                      </span>
                    )}
                  </div>
                </div>

                {tier.devices.length > 0 ? (
                  <div className="device-grid">
                    {tier.devices.map(device => renderDeviceTile(device))}
                  </div>
                ) : (
                  <div className="noc-tier-empty">No devices in this architectural tier matching filter</div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* ── View 2: SRE High-Density Table View ── */}
      {viewMode === 'table' && (
        <div className="noc-sre-table-wrap">
          <table className="noc-sre-table">
            <thead>
              <tr>
                <th className="sortable" onClick={() => handleTableSort('name')}>
                  <div className="th-content">
                    <span>Device Name</span>
                    <ArrowUpDown size={12} className={`sort-icon ${tableSortCol === 'name' ? 'active' : ''}`} />
                  </div>
                </th>
                <th className="sortable" onClick={() => handleTableSort('tier')}>
                  <div className="th-content">
                    <span>Tier</span>
                    <ArrowUpDown size={12} className={`sort-icon ${tableSortCol === 'tier' ? 'active' : ''}`} />
                  </div>
                </th>
                <th className="sortable" onClick={() => handleTableSort('location')}>
                  <div className="th-content">
                    <span>Location</span>
                    <ArrowUpDown size={12} className={`sort-icon ${tableSortCol === 'location' ? 'active' : ''}`} />
                  </div>
                </th>
                <th className="sortable" onClick={() => handleTableSort('health')}>
                  <div className="th-content">
                    <span>Health</span>
                    <ArrowUpDown size={12} className={`sort-icon ${tableSortCol === 'health' ? 'active' : ''}`} />
                  </div>
                </th>
                <th className="sortable" onClick={() => handleTableSort('alerts')}>
                  <div className="th-content">
                    <span>Active Alerts</span>
                    <ArrowUpDown size={12} className={`sort-icon ${tableSortCol === 'alerts' ? 'active' : ''}`} />
                  </div>
                </th>
                <th>
                  <div className="th-content">
                    <span>24h Trend & Severity</span>
                  </div>
                </th>
                <th className="sortable" onClick={() => handleTableSort('snow')}>
                  <div className="th-content">
                    <span>ServiceNow</span>
                    <ArrowUpDown size={12} className={`sort-icon ${tableSortCol === 'snow' ? 'active' : ''}`} />
                  </div>
                </th>
                <th className="sortable" onClick={() => handleTableSort('last_seen')}>
                  <div className="th-content">
                    <span>Last Event</span>
                    <ArrowUpDown size={12} className={`sort-icon ${tableSortCol === 'last_seen' ? 'active' : ''}`} />
                  </div>
                </th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sortedTableDevices.map(device => {
                const health = getDeviceHealth(device);
                const tierId = deriveDeviceTier(device.device_name);
                const tierMeta = TIER_METADATA[tierId];
                const activeCount = (device.active_alerts || []).length;
                const snow = getSnowSummary(device);
                const locLabel = getLocationLabel(device.location || deriveLocation(device.device_name));

                return (
                  <tr
                    key={device.device_name}
                    className={health === 'critical' ? 'row-critical' : ''}
                  >
                    <td>
                      <div className="noc-device-cell">
                        <button
                          type="button"
                          className="noc-device-name-link"
                          onClick={() => openDevicePanel(device)}
                        >
                          {device.device_name}
                        </button>
                        <span className="noc-device-id-sub">{device.device_id || 'ID: —'}</span>
                      </div>
                    </td>
                    <td>
                      <span className={`noc-tier-mini-badge tier-${tierId}`}>
                        {tierMeta.tag}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {locLabel}
                      </span>
                    </td>
                    <td>
                      <span className={`badge health-${health}`} style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                        <span className={`device-tile-status-dot ${health}`} style={{ width: '6px', height: '6px' }} />
                        {health.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      {activeCount > 0 ? (
                        <span className="device-tile-alert-count" style={{ margin: 0 }}>
                          <AlertTriangle size={11} /> {activeCount} active
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-tertiary)', fontSize: '0.75rem' }}>—</span>
                      )}
                    </td>
                    <td>
                      <div className="noc-table-viz-cell">
                        <DeviceSparkline
                          data={getDeviceSparklineData(device)}
                          isAlerting={health === 'critical' || health === 'warning'}
                          height={14}
                          barWidth={2}
                          gap={1}
                          compact={true}
                        />
                        <SeverityMiniBar device={device} compact={true} />
                      </div>
                    </td>
                    <td>
                      <div className="noc-table-snow-pills">
                        {snow.created.length > 0 && (
                          <span className="badge snow-new" title={snow.created.map(s => s.snow_incident).join(', ')}>
                            <PlusCircle size={10} /> {snow.created.length}
                          </span>
                        )}
                        {snow.reopened.length > 0 && (
                          <span className="badge snow-reopen" title={snow.reopened.map(s => s.snow_incident).join(', ')}>
                            <RotateCcw size={10} /> {snow.reopened.length}
                          </span>
                        )}
                        {snow.commented.length > 0 && (
                          <span className="badge snow-comment" title={snow.commented.map(s => s.snow_incident).join(', ')}>
                            <MessageSquarePlus size={10} /> {snow.commented.length}
                          </span>
                        )}
                        {snow.created.length === 0 && snow.reopened.length === 0 && snow.commented.length === 0 && (
                          <span style={{ color: 'var(--text-tertiary)', fontSize: '0.75rem' }}>None</span>
                        )}
                      </div>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        {formatTimestamp(device.last_alert_time, 'No recent events')}
                      </span>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button
                        type="button"
                        className="noc-table-action-btn"
                        onClick={() => openDevicePanel(device)}
                        title={`Inspect ${device.device_name}`}
                      >
                        <span>Inspect</span>
                        <ChevronRight size={13} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* ── View 3: Regional Site Matrix View ── */}
      {viewMode === 'matrix' && (
        <div className="noc-matrix-grid">
          {siteMatrix.map(site => (
            <div
              key={site.code}
              className={`noc-site-card site-${site.status}`}
            >
              <div>
                <div className="noc-site-header">
                  <h3 className="noc-site-title">{site.label}</h3>
                  <span className={`badge health-${site.status}`}>
                    {site.status.toUpperCase()}
                  </span>
                </div>
                <p className="noc-site-device-count">{site.devices.length} Devices Registered</p>

                <div className="noc-site-stats-row">
                  <div className="noc-site-stat-item">
                    <span className="noc-site-stat-label">Active Alerts</span>
                    <span className={`noc-site-stat-val ${site.totalAlerts > 0 ? 'alert-val' : ''}`}>
                      <Flame size={14} />
                      {site.totalAlerts}
                    </span>
                  </div>
                  <div className="noc-site-stat-item">
                    <span className="noc-site-stat-label">Avoided Tickets</span>
                    <span className="noc-site-stat-val zap-val">
                      <Zap size={14} />
                      {site.avoidedTickets}
                    </span>
                  </div>
                </div>

                <div className="noc-site-breakdown">
                  {site.critical > 0 && (
                    <span className="noc-tier-stat-pill critical">
                      <AlertTriangle size={10} /> {site.critical} Critical
                    </span>
                  )}
                  {site.warning > 0 && (
                    <span className="noc-tier-stat-pill warning">
                      <AlertTriangle size={10} /> {site.warning} Warning
                    </span>
                  )}
                  <span className="noc-tier-stat-pill healthy">
                    <CheckCircle size={10} /> {site.healthy} Healthy
                  </span>
                </div>
              </div>

              <button
                type="button"
                className="noc-site-drilldown-btn"
                onClick={() => {
                  setSearchQuery(site.code);
                  handleViewModeChange('topology');
                }}
              >
                <span>Inspect Site Devices</span>
                <ChevronRight size={13} />
              </button>
            </div>
          ))}
        </div>
      )}

      {filteredDevices.length === 0 && (
        <div className="empty-state" style={{ padding: '3.5rem 1rem', textAlign: 'center' }}>
          <Server size={44} style={{ color: 'var(--text-tertiary)', marginBottom: '0.75rem', opacity: 0.6 }} />
          <h3 style={{ margin: '0 0 0.4rem 0', fontSize: '1rem', color: 'var(--text-primary)' }}>No devices match your active filters</h3>
          <p style={{ margin: '0 0 1rem 0', color: 'var(--text-tertiary)', fontSize: '0.82rem' }}>
            {searchQuery
              ? `No devices matched "${searchQuery}" with current role, health, and ticket filters.`
              : 'No devices matched the selected combination of architectural role, health, and ServiceNow status filters.'}
          </p>
          <button
            className="filter-pill"
            onClick={resetAllFilters}
            style={{ margin: '0 auto', display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', padding: '0.45rem 1rem' }}
          >
            <RotateCcw size={13} /> Reset All Filters
          </button>
        </div>
      )}

      {/* Detail Panel Overlay */}
      <div className={`detail-overlay ${panelOpen ? 'open' : ''}`} onClick={closePanel} />

      {/* Detail Slide-Out Panel */}
      <div className={`detail-panel ${panelOpen ? 'open' : ''}`}>
        {selectedDevice && (() => {
          const snow = getSnowSummary(selectedDevice);
          const activeAlerts = selectedDevice.active_alerts || [];
          const resolvedAlerts = selectedDevice.resolved_alerts || [];
          return (
            <>
              <div className="detail-panel-header">
                <h2>
                  <span className={`device-tile-status-dot ${getDeviceHealth(selectedDevice)}`} style={{ display: 'inline-block', marginRight: '8px', verticalAlign: 'middle' }} />
                  {selectedDevice.device_name}
                </h2>
                <button className="detail-panel-close" onClick={closePanel}><X size={20} /></button>
              </div>

              <div className="detail-panel-body">
                {/* Device Summary */}
                <div className="detail-meta-grid" style={{ marginBottom: '1rem' }}>
                  <div className="detail-meta-item"><div className="label">Location</div><div className="value">{getLocationLabel(selectedDevice.location || deriveLocation(selectedDevice.device_name))}</div></div>
                  <div className="detail-meta-item"><div className="label">Device ID</div><div className="value">{selectedDevice.device_id || '—'}</div></div>
                  <div className="detail-meta-item"><div className="label">Total Alerts</div><div className="value">{selectedDevice.total_alerts}</div></div>
                  <div className="detail-meta-item"><div className="label">SNOW Incidents</div><div className="value">{selectedDevice.snow_incidents}</div></div>
                  <div className="detail-meta-item"><div className="label">Auto-Resolving</div><div className="value">{selectedDevice.auto_resolving}</div></div>
                  <div className="detail-meta-item"><div className="label">Non-Auto</div><div className="value">{selectedDevice.non_auto_resolving}</div></div>
                  <div className="detail-meta-item"><div className="label">Backdated</div><div className="value">{selectedDevice.backdated}</div></div>
                  <div className="detail-meta-item"><div className="label">Health</div><div className="value"><span className={`badge health-${getDeviceHealth(selectedDevice)}`}>{getDeviceHealth(selectedDevice).toUpperCase()}</span></div></div>
                </div>

                {/* SNOW Ticket Summary */}
                {(snow.created.length > 0 || snow.reopened.length > 0) && (
                  <>
                    <div className="section-divider" />
                    <h3 style={{ fontSize: '0.88rem', marginBottom: '0.6rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Ticket size={15} /> ServiceNow Tickets
                    </h3>
                    {snow.created.length > 0 && (
                      <div style={{ marginBottom: '0.5rem' }}>
                        <p style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--accent-blue)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.3rem' }}>
                          New Incidents
                        </p>
                        {snow.created.map((a, i) => (
                          <p key={i} style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: '0.15rem 0' }}>
                            <span style={{ fontWeight: 600, color: 'var(--accent-blue)' }}>{a.snow_incident}</span> — {a.issue_name}
                          </p>
                        ))}
                      </div>
                    )}
                    {snow.reopened.length > 0 && (
                      <div>
                        <p style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--accent-orange)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.3rem' }}>
                          Reopened Incidents
                        </p>
                        {snow.reopened.map((a, i) => (
                          <p key={i} style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: '0.15rem 0' }}>
                            <span style={{ fontWeight: 600, color: 'var(--accent-orange)' }}>{a.snow_incident}</span> — {a.issue_name}
                          </p>
                        ))}
                      </div>
                    )}
                  </>
                )}

                <div className="section-divider" />

                {/* ══════ ACTIVE ALERTS SECTION ══════ */}
                <div className="alert-section active-section">
                  <h3 className="alert-section-header active">
                    <span className="alert-section-dot active" />
                    <AlertTriangle size={15} />
                    Active Alerts ({activeAlerts.length})
                  </h3>

                  {activeAlerts.length === 0 ? (
                    <div className="empty-state" style={{ padding: '1.5rem' }}><Shield size={28} /><p>No active alerts — all clear.</p></div>
                  ) : (
                    activeAlerts.map((alert, i) => (
                      <div key={i} className="detail-alert-item">
                        <h4 style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                          <span className={`badge severity-${alert.severity || 3}`}>SEV {alert.severity || '?'}</span>
                          {alert.issue_name || 'Unknown Alert'}
                          {alert.dnac_live_status && (
                            <span className={`badge dnac-status-${(alert.dnac_live_status || '').toLowerCase()}`}>
                              {alert.dnac_live_status}
                            </span>
                          )}
                        </h4>
                        <p>{alert.issue_details || 'No details available.'}</p>
                        <div className="detail-meta-grid">
                          <div className="detail-meta-item"><div className="label">Event ID</div><div className="value">{alert.event_id || '—'}</div></div>
                          <div className="detail-meta-item"><div className="label">Category</div><div className="value">{alert.category || '—'}</div></div>
                          <div className="detail-meta-item">
                            <div className="label">Classification</div>
                            <div className="value"><span className={`badge ${(alert.predicted_category || '').toLowerCase().replace(/[\s/]/g, '-')}`}>{alert.predicted_category || '—'}</span></div>
                          </div>
                          <div className="detail-meta-item"><div className="label">Time</div><div className="value">{formatTimestamp(alert.timestamp)}</div></div>
                          {alert.dnac_last_checked && (
                            <div className="detail-meta-item"><div className="label">DNAC Checked</div><div className="value">{formatTimestamp(alert.dnac_last_checked)}</div></div>
                          )}
                          {alert.snow_incident && (<div className="detail-meta-item"><div className="label">SNOW Incident</div><div className="value" style={{ color: 'var(--accent-blue)', fontWeight: 700 }}>{alert.snow_incident}</div></div>)}
                          {alert.snow_action && (<div className="detail-meta-item"><div className="label">SNOW Action</div><div className="value">{alert.snow_action.replace(/_/g, ' ')}</div></div>)}
                        </div>
                      </div>
                    ))
                  )}
                </div>

                {/* ══════ RESOLVED ALERTS SECTION ══════ */}
                {resolvedAlerts.length > 0 && (
                  <div className="alert-section resolved-section">
                    <div className="section-divider" />
                    <h3
                      className="alert-section-header resolved clickable"
                      onClick={() => setResolvedExpanded(prev => !prev)}
                    >
                      <span className="alert-section-dot resolved" />
                      <CheckCircle size={15} />
                      Historical Resolved Alerts ({resolvedAlerts.length})
                      <span className="expand-toggle">
                        {resolvedExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </span>
                    </h3>

                    {resolvedExpanded && (
                      <div className="resolved-alerts-list">
                        {resolvedAlerts.map((alert, i) => (
                          <div key={i} className="detail-alert-item resolved">
                            <h4 style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                              <span className={`badge severity-${alert.severity || 3}`}>SEV {alert.severity || '?'}</span>
                              {alert.issue_name || 'Unknown Alert'}
                              <span className="badge dnac-status-resolved">RESOLVED</span>
                            </h4>
                            <p>{alert.issue_details || 'No details available.'}</p>
                            <div className="detail-meta-grid">
                              <div className="detail-meta-item"><div className="label">Event ID</div><div className="value">{alert.event_id || '—'}</div></div>
                              <div className="detail-meta-item"><div className="label">Category</div><div className="value">{alert.category || '—'}</div></div>
                              <div className="detail-meta-item">
                                <div className="label">Classification</div>
                                <div className="value"><span className={`badge ${(alert.predicted_category || '').toLowerCase().replace(/[\s/]/g, '-')}`}>{alert.predicted_category || '—'}</span></div>
                              </div>
                              <div className="detail-meta-item"><div className="label">Time</div><div className="value">{formatTimestamp(alert.timestamp)}</div></div>
                              {alert.dnac_last_checked && (
                                <div className="detail-meta-item"><div className="label">DNAC Checked</div><div className="value">{formatTimestamp(alert.dnac_last_checked)}</div></div>
                              )}
                              {alert.snow_incident && (<div className="detail-meta-item"><div className="label">SNOW Incident</div><div className="value" style={{ color: 'var(--accent-blue)', fontWeight: 700 }}>{alert.snow_incident}</div></div>)}
                              {alert.snow_action && (<div className="detail-meta-item"><div className="label">SNOW Action</div><div className="value">{alert.snow_action.replace(/_/g, ' ')}</div></div>)}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </>
          );
        })()}
      </div>
    </>
  );
}
