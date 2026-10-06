import React, { useState, useRef, useMemo, useEffect, useCallback } from 'react';
import {
  ZoomIn, ZoomOut, Maximize2, Minimize2, RotateCcw,
  LayoutGrid, Server, Shield, Wifi,
  Activity, Move, Layers, Globe, ArrowLeft, Zap,
  AlertTriangle, CheckCircle, ExternalLink, ShieldAlert,
  ChevronRight
} from 'lucide-react';

const SITE_METADATA = {
  'UK-LON': { flag: '🇬🇧', name: 'United Kingdom — London', shortName: 'London Core DC' },
  'UK-MAL': { flag: '🇬🇧', name: 'United Kingdom — Malmesbury', shortName: 'Malmesbury Campus' },
  'DE-FRA': { flag: '🇩🇪', name: 'Germany — Frankfurt', shortName: 'Frankfurt Transit DC' },
  'US-NY':  { flag: '🇺🇸', name: 'United States — New York', shortName: 'New York Metro DC' },
  'US-CHI': { flag: '🇺🇸', name: 'United States — Chicago', shortName: 'Chicago Regional DC' },
  'SG-SIN': { flag: '🇸🇬', name: 'Singapore', shortName: 'Singapore APAC Hub' },
  'JP-TKY': { flag: '🇯🇵', name: 'Japan — Tokyo', shortName: 'Tokyo Regional Hub' },
  'IN-MUM': { flag: '🇮🇳', name: 'India — Mumbai', shortName: 'Mumbai West DC' },
  'AU-SYD': { flag: '🇦🇺', name: 'Australia — Sydney', shortName: 'Sydney Oceanic DC' },
  'INFRA-CORE': { flag: '🏢', name: 'Core Infrastructure', shortName: 'Global Core Fabric' },
  'INFRA-ACCESS': { flag: '⚡', name: 'Access Infrastructure', shortName: 'Edge Access Fabric' }
};

const TIER_METADATA = {
  core: {
    id: 'core',
    name: 'Core & WAN Backbone',
    subtitle: 'High-capacity backbone routing, DC gateways & transit',
    icon: Server,
    color: '#3b82f6',
    accentVar: 'var(--accent-blue)',
    tag: 'CORE',
    y: 130
  },
  dist_sec: {
    id: 'dist_sec',
    name: 'Distribution & Security Perimeter',
    subtitle: 'Traffic aggregation, policy enforcement & firewalls',
    icon: Shield,
    color: '#a855f7',
    accentVar: 'var(--accent-purple)',
    tag: 'DIST / SEC',
    y: 350
  },
  access: {
    id: 'access',
    name: 'Campus & Access Edge',
    subtitle: 'Campus access switches, wireless APs & client edge',
    icon: Wifi,
    color: '#06b6d4',
    accentVar: 'var(--accent-teal)',
    tag: 'ACCESS',
    y: 570
  }
};

function deriveTier(name) {
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

function getNodeHealth(device) {
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

function renderRoleIcon(tierId, color) {
  if (tierId === 'core') {
    return (
      <g className="noc-role-icon role-core" transform="translate(12, 13)">
        <rect width="20" height="20" rx="5" fill="rgba(59, 130, 246, 0.15)" stroke="rgba(59, 130, 246, 0.35)" strokeWidth="1" />
        <rect x="4" y="5" width="12" height="4" rx="1" fill="none" stroke={color} strokeWidth="1.2" />
        <rect x="4" y="11" width="12" height="4" rx="1" fill="none" stroke={color} strokeWidth="1.2" />
        <circle cx="6.5" cy="7" r="0.75" fill={color} />
        <circle cx="6.5" cy="13" r="0.75" fill={color} />
      </g>
    );
  }
  if (tierId === 'dist_sec') {
    return (
      <g className="noc-role-icon role-dist" transform="translate(12, 13)">
        <rect width="20" height="20" rx="5" fill="rgba(168, 85, 247, 0.15)" stroke="rgba(168, 85, 247, 0.35)" strokeWidth="1" />
        <path d="M 10 4.5 L 15 6.5 V 11 C 15 14 10 16.5 10 16.5 C 10 16.5 5 14 5 11 V 6.5 Z" fill="none" stroke={color} strokeWidth="1.2" strokeLinejoin="round" />
      </g>
    );
  }
  return (
    <g className="noc-role-icon role-access" transform="translate(12, 13)">
      <rect width="20" height="20" rx="5" fill="rgba(6, 182, 212, 0.15)" stroke="rgba(6, 182, 212, 0.35)" strokeWidth="1" />
      <path d="M 5 8 C 7.5 5.5 12.5 5.5 15 8 M 7 11 C 8.5 9.5 11.5 9.5 13 11 M 10 14.5 A 0.5 0.5 0 1 1 10 14" fill="none" stroke={color} strokeWidth="1.2" strokeLinecap="round" />
    </g>
  );
}

const NODE_WIDTH = 220;
const NODE_HEIGHT = 76;

const WAN_NODE_WIDTH = 240;
const WAN_NODE_HEIGHT = 110;

const WAN_SITE_COORDINATES = {
  'US-NY': { x: 230, y: 200, region: 'Americas' },
  'US-CHI': { x: 230, y: 460, region: 'Americas' },
  'UK-LON': { x: 590, y: 170, region: 'EMEA' },
  'UK-MAL': { x: 590, y: 400, region: 'EMEA' },
  'DE-FRA': { x: 590, y: 620, region: 'EMEA' },
  'SG-SIN': { x: 970, y: 240, region: 'APAC' },
  'JP-TKY': { x: 970, y: 470, region: 'APAC' },
  'IN-MUM': { x: 880, y: 680, region: 'APAC' },
  'AU-SYD': { x: 1060, y: 680, region: 'APAC' },
  'INFRA-CORE': { x: 590, y: 280, region: 'Core Infrastructure' },
  'INFRA-ACCESS': { x: 970, y: 350, region: 'Access Infrastructure' }
};

const WAN_INTERCONNECT_DEFINITIONS = [
  { source: 'US-NY', target: 'US-CHI', latency: '18ms', type: 'metro', loss: '0.00%', bandwidth: '40 Gbps', label: 'Inter-City Metro' },
  { source: 'US-NY', target: 'UK-LON', latency: '115ms', type: 'subsea', loss: '0.01%', bandwidth: '100 Gbps', label: 'Transatlantic Subsea' },
  { source: 'UK-LON', target: 'UK-MAL', latency: '6ms', type: 'metro', loss: '0.00%', bandwidth: '10 Gbps', label: 'Regional Metro' },
  { source: 'UK-LON', target: 'DE-FRA', latency: '24ms', type: 'backbone', loss: '0.00%', bandwidth: '100 Gbps', label: '100G European Core' },
  { source: 'DE-FRA', target: 'SG-SIN', latency: '128ms', type: 'terrestrial', loss: '0.02%', bandwidth: '100 Gbps', label: 'Eurasia Terrestrial Transit' },
  { source: 'SG-SIN', target: 'JP-TKY', latency: '68ms', type: 'subsea', loss: '0.00%', bandwidth: '40 Gbps', label: 'East Asia Subsea Cable' },
  { source: 'SG-SIN', target: 'IN-MUM', latency: '42ms', type: 'subsea', loss: '0.01%', bandwidth: '40 Gbps', label: 'Bay of Bengal Cable' },
  { source: 'SG-SIN', target: 'AU-SYD', latency: '92ms', type: 'subsea', loss: '0.02%', bandwidth: '40 Gbps', label: 'Indo-Pacific Subsea' }
];

export default function TopologyGraphView({
  devices = [],
  sites = [],
  selectedDevice = null,
  onSelectDevice = () => {},
  subMode = 'graph',
  onToggleSubMode = () => {},
  searchQuery = '',
  roleFilter = 'all',
  healthFilter = 'all',
  onResetFilters = null,
  // Milestone v2.0 Multi-Site Props:
  topologyLevel = 'wan',
  selectedSite = null,
  onSelectSite = () => {},
  onReturnToWan = () => {}
}) {
  const containerRef = useRef(null);
  const [containerSize, setContainerSize] = useState({ width: 1100, height: 720 });
  const [transform, setTransform] = useState({ x: 30, y: 20, k: 0.95 });
  const [zoomTransition, setZoomTransition] = useState(false);
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const [panDistance, setPanDistance] = useState(0);
  const [startTransform, setStartTransform] = useState({ x: 0, y: 0, k: 1 });
  const [hoveredNode, setHoveredNode] = useState(null);
  const [hoveredEdge, setHoveredEdge] = useState(null);
  const [hoveredWanEdge, setHoveredWanEdge] = useState(null);
  const [showWheelHint, setShowWheelHint] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const wheelHintTimerRef = useRef(null);

  // ResizeObserver to track container bounds
  useEffect(() => {
    if (!containerRef.current) return;
    const obs = new ResizeObserver(entries => {
      for (const entry of entries) {
        if (entry.contentRect.width > 0 && entry.contentRect.height > 0) {
          setContainerSize({
            width: entry.contentRect.width,
            height: Math.max(680, entry.contentRect.height)
          });
        }
      }
    });
    obs.observe(containerRef.current);
    return () => obs.disconnect();
  }, []);

  const hasActiveFilter = Boolean(searchQuery || roleFilter !== 'all' || healthFilter !== 'all');

  // ─────────────────────────────────────────────────────────────────────────────
  // Multi-Site Metadata & Resolved Sites Collection
  // ─────────────────────────────────────────────────────────────────────────────
  const resolvedSiteList = useMemo(() => {
    if (sites && sites.length > 0) return sites;
    if (devices && devices.length > 0) {
      const siteMap = {};
      devices.forEach(d => {
        const loc = d.location || 'INFRA-CORE';
        if (!siteMap[loc]) {
          siteMap[loc] = {
            code: loc,
            label: loc,
            devices: [],
            critical: 0,
            warning: 0,
            healthy: 0,
            totalAlerts: 0,
            avoidedTickets: 0
          };
        }
        siteMap[loc].devices.push(d);
        const h = getNodeHealth(d);
        if (h === 'critical') siteMap[loc].critical++;
        else if (h === 'warning') siteMap[loc].warning++;
        else siteMap[loc].healthy++;
        siteMap[loc].totalAlerts += (d.active_alerts || []).length;
        siteMap[loc].avoidedTickets += (d.auto_resolving || 0) + (d.backdated || 0);
      });
      return Object.values(siteMap).map(s => {
        let status = 'nominal';
        if (s.critical > 0) status = 'critical';
        else if (s.warning > 0) status = 'degraded';
        return { ...s, status };
      });
    }
    return [];
  }, [sites, devices]);

  const activeSiteMeta = useMemo(() => {
    const found = resolvedSiteList.find(s => s.code === selectedSite);
    const meta = SITE_METADATA[selectedSite] || {};
    return {
      code: selectedSite,
      label: found?.label || meta.name || selectedSite || 'Local Site',
      flag: meta.flag || (found?.label || '').split(' ')[0] || '🏢',
      shortName: meta.shortName || found?.label || selectedSite,
      deviceCount: found?.devices?.length || 0,
      status: found?.status || 'nominal'
    };
  }, [resolvedSiteList, selectedSite]);

  // ─────────────────────────────────────────────────────────────────────────────
  // LEVEL 1: Global Multi-Site WAN Topology Computation
  // ─────────────────────────────────────────────────────────────────────────────
  const { wanNodes, wanEdges, wanResilienceScore, wanDimensions } = useMemo(() => {
    const resolvedSites = resolvedSiteList;
    const computedWanWidth = Math.max(containerSize.width, 1280);
    const computedWanHeight = Math.max(containerSize.height, 820);

    let totalSites = resolvedSites.length;
    let nominalCount = 0;
    let criticalCount = 0;

    const computedNodes = resolvedSites.map((site, idx) => {
      const defaultCoord = WAN_SITE_COORDINATES[site.code] || {
        x: 250 + (idx % 3) * 360,
        y: 200 + Math.floor(idx / 3) * 240,
        region: 'Regional Network'
      };

      if (site.status === 'nominal') nominalCount++;
      else if (site.status === 'critical') criticalCount++;

      const flag = (site.label || '').split(' ')[0] || '🌐';
      let name = site.label || site.code;
      if (name.includes('—')) {
        name = name.split('—')[1].trim();
      }

      const totalDevs = (site.devices || []).length;
      const degradedDevs = (site.critical || 0) + (site.warning || 0);
      const blastRadius = totalDevs > 0 ? Math.round((degradedDevs / totalDevs) * 100) : 0;

      // Filter matching check
      const q = (searchQuery || '').toLowerCase().trim();
      const matchesQuery = !q ||
        site.code.toLowerCase().includes(q) ||
        (site.label && site.label.toLowerCase().includes(q));
      const matchesHealth = healthFilter === 'all' || site.status === healthFilter;
      const isDimmed = !(matchesQuery && matchesHealth);

      return {
        id: site.code,
        code: site.code,
        label: site.label,
        name,
        flag,
        region: defaultCoord.region,
        status: site.status || 'nominal',
        x: defaultCoord.x,
        y: defaultCoord.y,
        devicesCount: totalDevs,
        activeAlerts: site.totalAlerts || 0,
        avoidedTickets: site.avoidedTickets || 0,
        critical: site.critical || 0,
        warning: site.warning || 0,
        healthy: site.healthy || 0,
        blastRadius,
        hasBlastRadius: blastRadius > 0 || site.status !== 'nominal',
        isDimmed,
        rawSite: site
      };
    });

    const resilience = totalSites > 0
      ? Math.max(0, Math.min(100, Math.round(((nominalCount + (totalSites - criticalCount) * 0.5) / (totalSites * 1.5)) * 100)))
      : 100;

    // Generate WAN Interconnect Edges
    const computedWanEdges = [];
    WAN_INTERCONNECT_DEFINITIONS.forEach(def => {
      const srcNode = computedNodes.find(n => n.id === def.source);
      const tgtNode = computedNodes.find(n => n.id === def.target);
      if (srcNode && tgtNode) {
        const dx = tgtNode.x - srcNode.x;
        const dy = tgtNode.y - srcNode.y;
        const midX = (srcNode.x + tgtNode.x) / 2;
        const midY = (srcNode.y + tgtNode.y) / 2;
        const curvature = Math.abs(dx) > Math.abs(dy) ? -38 : 38;
        const path = `M ${srcNode.x} ${srcNode.y} Q ${midX} ${midY + curvature} ${tgtNode.x} ${tgtNode.y}`;

        let status = 'nominal';
        if (srcNode.status === 'critical' || tgtNode.status === 'critical') status = 'critical';
        else if (srcNode.status === 'degraded' || tgtNode.status === 'degraded') status = 'warning';

        const isDimmed = hasActiveFilter && (srcNode.isDimmed && tgtNode.isDimmed);

        computedWanEdges.push({
          id: `wan-${srcNode.id}-${tgtNode.id}`,
          source: srcNode,
          target: tgtNode,
          path,
          midX,
          midY: midY + curvature / 2,
          latency: def.latency,
          loss: def.loss,
          bandwidth: def.bandwidth,
          type: def.type,
          label: def.label,
          status,
          isDimmed
        });
      }
    });

    return {
      wanNodes: computedNodes,
      wanEdges: computedWanEdges,
      wanResilienceScore: resilience,
      wanDimensions: { width: computedWanWidth, height: computedWanHeight }
    };
  }, [resolvedSiteList, containerSize, searchQuery, healthFilter, hasActiveFilter]);

  // ─────────────────────────────────────────────────────────────────────────────
  // LEVEL 2: Site LAN Tier Topology Computation
  // ─────────────────────────────────────────────────────────────────────────────
  const { nodes, edges, tierStats, canvasDimensions } = useMemo(() => {
    const scopedDevices = (topologyLevel === 'lan' && selectedSite)
      ? devices.filter(d => (d.location === selectedSite || (d.device_name && d.device_name.startsWith(selectedSite))))
      : devices;
    const activeDeviceList = scopedDevices.length > 0 ? scopedDevices : devices;

    const buckets = { core: [], dist_sec: [], access: [] };
    activeDeviceList.forEach(d => {
      const tier = deriveTier(d.device_name);
      if (buckets[tier]) buckets[tier].push(d);
      else buckets.core.push(d);
    });

    const maxCountInTier = Math.max(
      buckets.core.length,
      buckets.dist_sec.length,
      buckets.access.length,
      1
    );

    const minGap = 50;
    const stepX = NODE_WIDTH + minGap;
    const computedWidth = Math.max(containerSize.width, (maxCountInTier + 1) * stepX + 100);
    const computedHeight = 740;

    const computedNodes = [];
    const tierStatsMap = {};

    ['core', 'dist_sec', 'access'].forEach(tierId => {
      const list = buckets[tierId];
      const tierMeta = TIER_METADATA[tierId];
      const count = list.length;
      const rowY = tierMeta.y;

      let crit = 0, warn = 0, nom = 0;
      list.forEach(d => {
        const h = getNodeHealth(d);
        if (h === 'critical') crit++;
        else if (h === 'warning') warn++;
        else nom++;
      });
      tierStatsMap[tierId] = { count, critical: crit, warning: warn, healthy: nom };

      // Center the nodes horizontally within the tier
      const tierTotalWidth = count * stepX - minGap;
      const startX = Math.max(60, (computedWidth - tierTotalWidth) / 2);

      list.forEach((device, index) => {
        const nodeX = startX + index * stepX + NODE_WIDTH / 2;
        const nodeY = rowY;
        const health = getNodeHealth(device);

        // Filter match check (role, health, search query)
        const q = (searchQuery || '').toLowerCase().trim();
        const matchesQuery = !q ||
          (device.device_name && device.device_name.toLowerCase().includes(q)) ||
          (device.location && device.location.toLowerCase().includes(q)) ||
          (device.ip_address && device.ip_address.includes(q));
        const matchesRole = roleFilter === 'all' || tierId === roleFilter || (device.role && device.role === roleFilter);
        const matchesHealth = healthFilter === 'all' || health === healthFilter;
        const isDimmed = !(matchesQuery && matchesRole && matchesHealth);

        computedNodes.push({
          id: device.device_name,
          device,
          tier: tierId,
          x: nodeX,
          y: nodeY,
          health,
          isDimmed,
          activeAlertCount: (device.active_alerts || []).length
        });
      });
    });

    // Generate topological interconnects (links)
    const computedEdges = [];
    const coreNodes = computedNodes.filter(n => n.tier === 'core');
    const distNodes = computedNodes.filter(n => n.tier === 'dist_sec');
    const accessNodes = computedNodes.filter(n => n.tier === 'access');

    // 1. Core backbone mesh links (Core <-> Core)
    for (let i = 0; i < coreNodes.length - 1; i++) {
      const src = coreNodes[i];
      const tgt = coreNodes[i + 1];
      const isCrit = src.health === 'critical' || tgt.health === 'critical';
      const isWarn = src.health === 'warning' || tgt.health === 'warning';
      const status = isCrit ? 'critical' : isWarn ? 'warning' : 'nominal';
      const path = `M ${src.x + NODE_WIDTH / 2 - 10} ${src.y} C ${(src.x + tgt.x) / 2} ${src.y - 45}, ${(src.x + tgt.x) / 2} ${src.y - 45}, ${tgt.x - NODE_WIDTH / 2 + 10} ${tgt.y}`;
      const isDimmed = hasActiveFilter && (src.isDimmed && tgt.isDimmed);

      computedEdges.push({
        id: `link-core-${src.id}-${tgt.id}`,
        source: src,
        target: tgt,
        path,
        status,
        type: 'backbone',
        label: '100G Backbone Mesh',
        isDimmed
      });
    }

    // 2. Core to Distribution uplinks (Core <-> Dist)
    distNodes.forEach((dist, idx) => {
      const primaryCore = coreNodes[idx % Math.max(1, coreNodes.length)];
      if (primaryCore) {
        const isCrit = dist.health === 'critical' || primaryCore.health === 'critical';
        const isWarn = dist.health === 'warning' || primaryCore.health === 'warning';
        const status = isCrit ? 'critical' : isWarn ? 'warning' : 'nominal';
        const yMid = (primaryCore.y + dist.y) / 2;
        const path = `M ${primaryCore.x} ${primaryCore.y + NODE_HEIGHT / 2} C ${primaryCore.x} ${yMid}, ${dist.x} ${yMid}, ${dist.x} ${dist.y - NODE_HEIGHT / 2}`;
        const isDimmed = hasActiveFilter && (primaryCore.isDimmed && dist.isDimmed);

        computedEdges.push({
          id: `link-${primaryCore.id}-${dist.id}`,
          source: primaryCore,
          target: dist,
          path,
          status,
          type: 'uplink',
          label: '40G Distribution Uplink',
          isDimmed
        });
      }

      // Redundant link to second core if multiple exist
      if (coreNodes.length > 1) {
        const secondaryCore = coreNodes[(idx + 1) % coreNodes.length];
        const isCrit = dist.health === 'critical' || secondaryCore.health === 'critical';
        const isWarn = dist.health === 'warning' || secondaryCore.health === 'warning';
        const status = isCrit ? 'critical' : isWarn ? 'warning' : 'nominal';
        const yMid = (secondaryCore.y + dist.y) / 2;
        const path = `M ${secondaryCore.x} ${secondaryCore.y + NODE_HEIGHT / 2} C ${secondaryCore.x} ${yMid}, ${dist.x} ${yMid}, ${dist.x} ${dist.y - NODE_HEIGHT / 2}`;
        const isDimmed = hasActiveFilter && (secondaryCore.isDimmed && dist.isDimmed);

        computedEdges.push({
          id: `link-red-${secondaryCore.id}-${dist.id}`,
          source: secondaryCore,
          target: dist,
          path,
          status,
          type: 'redundant',
          label: '40G Redundant Path',
          isDimmed
        });
      }
    });

    // 3. Distribution to Access downlinks (Dist <-> Access)
    accessNodes.forEach((access, idx) => {
      const parentDist = distNodes[idx % Math.max(1, distNodes.length)];
      if (parentDist) {
        const isCrit = access.health === 'critical' || parentDist.health === 'critical';
        const isWarn = access.health === 'warning' || parentDist.health === 'warning';
        const status = isCrit ? 'critical' : isWarn ? 'warning' : 'nominal';
        const yMid = (parentDist.y + access.y) / 2;
        const path = `M ${parentDist.x} ${parentDist.y + NODE_HEIGHT / 2} C ${parentDist.x} ${yMid}, ${access.x} ${yMid}, ${access.x} ${access.y - NODE_HEIGHT / 2}`;
        const isDimmed = hasActiveFilter && (parentDist.isDimmed && access.isDimmed);

        computedEdges.push({
          id: `link-${parentDist.id}-${access.id}`,
          source: parentDist,
          target: access,
          path,
          status,
          type: 'access',
          label: '10G Campus Downlink',
          isDimmed
        });
      }
    });

    return {
      nodes: computedNodes,
      edges: computedEdges,
      tierStats: tierStatsMap,
      canvasDimensions: { width: computedWidth, height: computedHeight }
    };
  }, [devices, selectedSite, topologyLevel, containerSize, searchQuery, roleFilter, healthFilter, hasActiveFilter]);

  const matchCount = useMemo(() => {
    if (topologyLevel === 'wan') {
      return wanNodes.filter(n => !n.isDimmed).length;
    }
    return nodes.filter(n => !n.isDimmed).length;
  }, [topologyLevel, wanNodes, nodes]);

  // Handle Drag / Pan Operations
  const handlePointerDown = (e) => {
    if (e.button !== 0) return;
    if (
      e.target.closest('.noc-graph-control-btn') ||
      e.target.closest('.noc-graph-node-card') ||
      e.target.closest('.noc-graph-filter-badge') ||
      e.target.closest('.noc-wan-site-group') ||
      e.target.closest('.noc-wan-back-btn') ||
      e.target.closest('.noc-topology-level-banner') ||
      e.target.closest('.noc-topology-breadcrumbs') ||
      e.target.closest('.noc-site-switcher-select')
    ) {
      return;
    }

    setIsPanning(true);
    setPanDistance(0);
    setPanStart({ x: e.clientX, y: e.clientY });
    setStartTransform({ ...transform });
    if (containerRef.current) {
      containerRef.current.setPointerCapture(e.pointerId);
    }
  };

  const handlePointerMove = (e) => {
    if (!isPanning) return;
    const dx = e.clientX - panStart.x;
    const dy = e.clientY - panStart.y;
    setPanDistance(Math.sqrt(dx * dx + dy * dy));
    const nextX = startTransform.x + dx;
    const nextY = startTransform.y + dy;
    const clampedX = Math.max(-1200, Math.min(1200, nextX));
    const clampedY = Math.max(-800, Math.min(800, nextY));
    setTransform({
      ...startTransform,
      x: clampedX,
      y: clampedY
    });
  };

  const handlePointerUp = (e) => {
    if (isPanning) {
      setIsPanning(false);
      try {
        if (containerRef.current && containerRef.current.hasPointerCapture(e.pointerId)) {
          containerRef.current.releasePointerCapture(e.pointerId);
        }
      } catch {
        // Safe release
      }
    }
  };

  // Zoom Operations
  const handleZoom = useCallback((factor, centerX, centerY) => {
    setTransform(prev => {
      const newK = Math.max(0.4, Math.min(2.2, prev.k * factor));
      const cx = centerX !== undefined ? centerX : containerSize.width / 2;
      const cy = centerY !== undefined ? centerY : containerSize.height / 2;
      const newX = cx - (cx - prev.x) * (newK / prev.k);
      const newY = cy - (cy - prev.y) * (newK / prev.k);
      return { x: newX, y: newY, k: newK };
    });
  }, [containerSize]);

  // Wheel Zoom Listener
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const handleWheel = (e) => {
      e.preventDefault();
      if (!e.ctrlKey && !e.metaKey) {
        setShowWheelHint(true);
        if (wheelHintTimerRef.current) clearTimeout(wheelHintTimerRef.current);
        wheelHintTimerRef.current = setTimeout(() => setShowWheelHint(false), 1800);
        return;
      }

      setShowWheelHint(false);
      const rect = el.getBoundingClientRect();
      const cursorX = e.clientX - rect.left;
      const cursorY = e.clientY - rect.top;
      const factor = e.deltaY < 0 ? 1.12 : 0.89;
      handleZoom(factor, cursorX, cursorY);
    };

    el.addEventListener('wheel', handleWheel, { passive: false });
    return () => {
      el.removeEventListener('wheel', handleWheel);
      if (wheelHintTimerRef.current) clearTimeout(wheelHintTimerRef.current);
    };
  }, [handleZoom]);

  // Escape key listener to exit fullscreen
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isFullscreen) {
        setIsFullscreen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isFullscreen]);

  const handleZoomIn = () => handleZoom(1.2);
  const handleZoomOut = () => handleZoom(0.83);

  const handleResetZoom = () => {
    setZoomTransition(true);
    setTransform({ x: 30, y: 20, k: 0.95 });
    setTimeout(() => setZoomTransition(false), 320);
  };

  const handleFitToScreen = () => {
    const activeWidth = topologyLevel === 'wan' ? wanDimensions.width : canvasDimensions.width;
    const activeHeight = topologyLevel === 'wan' ? wanDimensions.height : canvasDimensions.height;
    const scaleX = (containerSize.width - 80) / activeWidth;
    const scaleY = (containerSize.height - 80) / activeHeight;
    const fitK = Math.max(0.45, Math.min(1.2, Math.min(scaleX, scaleY)));
    const fitX = (containerSize.width - activeWidth * fitK) / 2;
    const fitY = (containerSize.height - activeHeight * fitK) / 2;

    setZoomTransition(true);
    setTransform({ x: fitX, y: fitY, k: fitK });
    setTimeout(() => setZoomTransition(false), 320);
  };

  const toggleFullscreen = () => {
    setIsFullscreen(prev => !prev);
  };

  const getStatusColor = (status) => {
    if (status === 'critical') return 'var(--accent-rose, #ef4444)';
    if (status === 'warning' || status === 'degraded') return 'var(--accent-amber, #f59e0b)';
    return 'var(--accent-blue, #3b82f6)';
  };

  return (
    <div
      ref={containerRef}
      className={`noc-topology-graph-container ${isPanning ? 'is-panning' : ''} ${isFullscreen ? 'fullscreen' : ''}`}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
    >
      {/* Floating Wheel Zoom Modifier Hint Toast */}
      {showWheelHint && (
        <div className="noc-wheel-zoom-hint" role="status" aria-live="polite">
          Use Ctrl + scroll to zoom
        </div>
      )}

      {/* Level Indicator Banner (Top Left) */}
      <div
        className="noc-topology-level-banner"
        style={{
          position: 'absolute',
          top: '16px',
          left: '16px',
          zIndex: 12,
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}
      >
        {topologyLevel === 'wan' ? (
          <>
            <div className="noc-topology-level-badge">
              <Globe size={13} />
              <span>GLOBAL WAN TOPOLOGY (LEVEL 1)</span>
            </div>
            <div className="noc-wan-stats-pill">
              <span>{wanNodes.length} Connected Sites • Fleet Resilience {wanResilienceScore}%</span>
            </div>
          </>
        ) : (
          <div className="noc-topology-breadcrumbs" role="navigation" aria-label="Topology Level Navigation">
            <button
              type="button"
              className="noc-wan-back-btn"
              onClick={onReturnToWan}
              title="Return to Global WAN Overview"
            >
              <ArrowLeft size={13} />
              <span>← Back to Global WAN</span>
            </button>

            <div className="noc-topology-breadcrumb-trail">
              <button
                type="button"
                className="noc-breadcrumb-item noc-breadcrumb-root clickable"
                onClick={onReturnToWan}
                title="Return to Global WAN Interconnect (Level 1)"
              >
                <Globe size={13} />
                <span>Global WAN Interconnect</span>
              </button>

              <ChevronRight size={13} className="noc-breadcrumb-separator" />

              <span className="noc-breadcrumb-item noc-breadcrumb-site active" aria-current="location">
                <span className="noc-breadcrumb-flag">{activeSiteMeta.flag}</span>
                <span className="noc-breadcrumb-code">{selectedSite || 'SITE'}</span>
                <span className="noc-breadcrumb-label">({activeSiteMeta.shortName})</span>
              </span>
            </div>

            {/* Site Switcher Dropdown (SITE-04) */}
            <div className="noc-site-switcher-wrapper">
              <label htmlFor="noc-site-switcher" className="sr-only">Switch Site Topology</label>
              <select
                id="noc-site-switcher"
                className="noc-site-switcher-select"
                value={selectedSite || ''}
                onChange={(e) => onSelectSite(e.target.value)}
                title="Switch Site Topology"
                aria-label="Switch Site Topology"
              >
                {resolvedSiteList.map(s => (
                  <option key={s.code} value={s.code}>
                    {s.status === 'critical' ? '✖ ' : s.status === 'degraded' ? '⚠ ' : '● '}
                    {s.code} — {s.label} ({s.devices?.length || 0} devs)
                  </option>
                ))}
              </select>
            </div>

            <div className="noc-topology-level-badge" style={{ borderColor: 'var(--accent-purple)', color: 'var(--accent-purple)' }}>
              <Layers size={13} />
              <span>SITE LAN: {selectedSite || 'LOCAL CLUSTER'} (LEVEL 2)</span>
            </div>
          </div>
        )}
      </div>

      {/* Floating Canvas Controls Toolbar */}
      <div className="noc-graph-controls-toolbar">
        <button
          type="button"
          className={`noc-graph-control-btn ${isFullscreen ? 'active-pill' : ''}`}
          onClick={toggleFullscreen}
          title={isFullscreen ? "Exit Fullscreen Canvas (Esc)" : "Expand Topology View"}
          aria-label={isFullscreen ? "Exit Fullscreen Canvas" : "Expand Topology View"}
        >
          {isFullscreen ? <Minimize2 size={13} /> : <Maximize2 size={13} />}
          <span>{isFullscreen ? 'Exit' : 'Expand'}</span>
        </button>

        <div className="noc-graph-btn-divider" />

        <button
          type="button"
          className="noc-graph-control-btn active-pill"
          onClick={onToggleSubMode}
          title="Switch to Card Grid View"
        >
          <LayoutGrid size={13} />
          <span>Card View</span>
        </button>

        <div className="noc-graph-btn-divider" />

        <button
          type="button"
          className="noc-graph-control-btn"
          onClick={handleZoomIn}
          title="Zoom In (+)"
        >
          <ZoomIn size={14} />
        </button>
        <button
          type="button"
          className="noc-graph-control-btn"
          onClick={handleZoomOut}
          title="Zoom Out (-)"
        >
          <ZoomOut size={14} />
        </button>
        <button
          type="button"
          className="noc-graph-control-btn"
          onClick={handleFitToScreen}
          title="Fit Network to View"
        >
          <Layers size={13} />
        </button>
        <button
          type="button"
          className="noc-graph-control-btn"
          onClick={handleResetZoom}
          title="Reset View (100%)"
        >
          <RotateCcw size={13} />
          <span style={{ fontSize: '0.7rem', fontWeight: 600 }}>1:1</span>
        </button>
      </div>

      {/* Floating Canvas Legend or Active Filter Match Banner */}
      <div style={{ position: 'absolute', top: '56px', left: '16px', zIndex: 10 }}>
        {hasActiveFilter ? (
          <div className="noc-graph-filter-badge" style={{ position: 'static' }}>
            <Activity size={13} style={{ color: 'var(--accent-blue)' }} />
            <span>
              Filtered: <strong>{matchCount}</strong> {topologyLevel === 'wan' ? 'sites' : `of ${nodes.length} devices in ${selectedSite || 'Site LAN'}`}
            </span>
            {onResetFilters && (
              <button
                type="button"
                className="noc-graph-filter-reset-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  onResetFilters();
                }}
                title="Clear all active filters"
              >
                Reset
              </button>
            )}
          </div>
        ) : (
          <div className="noc-graph-legend-badge" style={{ position: 'static' }}>
            <span className="noc-legend-icon"><Move size={12} /></span>
            <span>
              {topologyLevel === 'wan'
                ? 'Drag to pan • Scroll to zoom • Click site to drill down into LAN'
                : 'Drag to pan • Scroll to zoom • Click node to inspect triage drawer'}
            </span>
          </div>
        )}
      </div>

      {/* Main SVG Graph Surface */}
      <svg
        className="noc-topology-canvas"
        width="100%"
        height="100%"
        style={{ display: 'block' }}
      >
        <defs>
          <pattern id="noc-grid-dots" width="24" height="24" patternUnits="userSpaceOnUse">
            <circle cx="2" cy="2" r="1" fill="var(--card-border)" opacity="0.35" />
          </pattern>

          <filter id="glow-teal" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          <filter id="glow-blue" x="-30%" y="-30%" width="160%" height="160%">
            <feDropShadow dx="0" dy="0" stdDeviation="5" floodColor="rgba(59, 130, 246, 0.75)" />
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          <filter id="glow-red" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          <filter id="node-shadow" x="-10%" y="-10%" width="130%" height="130%">
            <feDropShadow dx="0" dy="6" stdDeviation="8" floodColor="rgba(0, 0, 0, 0.35)" />
          </filter>
        </defs>

        <rect id="noc-canvas-bg" width="100%" height="100%" fill="url(#noc-grid-dots)" />

        <g
          className="noc-graph-transform-group"
          transform={`translate(${transform.x}, ${transform.y}) scale(${transform.k})`}
          style={{ transition: zoomTransition ? 'transform 0.3s cubic-bezier(0.2, 0, 0, 1)' : 'none' }}
        >
          {/* ═════════════════════════════════════════════════════════════════════
              LEVEL 1: GLOBAL MULTI-SITE WAN INTERCONNECT TOPOLOGY
              ═════════════════════════════════════════════════════════════════════ */}
          {topologyLevel === 'wan' ? (
            <>
              {/* 1. Global WAN Interconnect Links */}
              <g className="noc-wan-edges-group">
                {wanEdges.map(edge => {
                  const isHovered = hoveredWanEdge === edge.id;
                  const strokeColor = getStatusColor(edge.status);

                  return (
                    <g key={edge.id} className="noc-wan-edge-item">
                      {/* Broad invisible hover trigger path */}
                      <path
                        d={edge.path}
                        fill="none"
                        stroke="transparent"
                        strokeWidth="20"
                        onMouseEnter={() => setHoveredWanEdge(edge.id)}
                        onMouseLeave={() => setHoveredWanEdge(null)}
                        style={{ cursor: 'pointer' }}
                      >
                        <title>{`${edge.label} (${edge.type.toUpperCase()}): ${edge.latency} RTT • Loss: ${edge.loss} • Bandwidth: ${edge.bandwidth}`}</title>
                      </path>

                      {/* Main WAN Cable Path */}
                      <path
                        d={edge.path}
                        fill="none"
                        className={`noc-wan-link-cable ${edge.status} ${isHovered ? 'hovered' : ''}`}
                        strokeWidth={isHovered ? '3.5' : '2.5'}
                      />

                      {/* Animated Active Telemetry Dash Flow */}
                      <path
                        d={edge.path}
                        fill="none"
                        className="noc-wan-link-flow"
                        strokeWidth="2"
                        opacity={isHovered ? 0.95 : 0.65}
                      />

                      {/* Midpoint Latency Pill Badge Marker */}
                      <g
                        className="noc-wan-link-badge-group"
                        style={{ cursor: 'pointer' }}
                        onMouseEnter={() => setHoveredWanEdge(edge.id)}
                        onMouseLeave={() => setHoveredWanEdge(null)}
                      >
                        <title>{`${edge.label}: ${edge.latency} round-trip latency (${edge.loss} loss)`}</title>
                        <rect
                          x={edge.midX - 27}
                          y={edge.midY - 11}
                          width="54"
                          height="22"
                          rx="11"
                          className="noc-wan-link-badge-bg"
                        />
                        <text
                          x={edge.midX}
                          y={edge.midY}
                          className="noc-wan-link-badge-text"
                        >
                          {edge.latency}
                        </text>
                      </g>
                    </g>
                  );
                })}
              </g>

              {/* 2. Global WAN Macro Site Nodes */}
              <g className="noc-wan-nodes-group">
                {wanNodes.map(site => {
                  const isDegraded = site.status === 'degraded' || site.status === 'critical';
                  const statusBg = site.status === 'critical'
                    ? 'rgba(239, 68, 68, 0.15)'
                    : site.status === 'degraded'
                    ? 'rgba(245, 158, 11, 0.15)'
                    : 'rgba(16, 185, 129, 0.12)';
                  const statusBorder = site.status === 'critical'
                    ? 'rgba(239, 68, 68, 0.4)'
                    : site.status === 'degraded'
                    ? 'rgba(245, 158, 11, 0.4)'
                    : 'rgba(16, 185, 129, 0.3)';
                  const statusColor = site.status === 'critical'
                    ? 'var(--accent-rose)'
                    : site.status === 'degraded'
                    ? 'var(--accent-amber)'
                    : 'var(--health-healthy)';

                  return (
                    <g
                      key={site.id}
                      className={`noc-wan-site-group ${site.isDimmed ? 'dimmed' : ''}`}
                      transform={`translate(${site.x - WAN_NODE_WIDTH / 2}, ${site.y - WAN_NODE_HEIGHT / 2})`}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectSite(site.code);
                      }}
                      style={{ cursor: 'pointer' }}
                      role="button"
                      tabIndex="0"
                      aria-label={`Site ${site.code}, Health: ${site.status}`}
                    >
                      {/* Perimeter Blast Radius Animated Halo */}
                      {site.hasBlastRadius && (
                        <rect
                          x="-6"
                          y="-6"
                          width={WAN_NODE_WIDTH + 12}
                          height={WAN_NODE_HEIGHT + 12}
                          rx="16"
                          fill="none"
                          stroke={site.status === 'critical' ? 'var(--accent-rose, #ef4444)' : 'var(--accent-amber, #f59e0b)'}
                          strokeWidth="2.5"
                          className="blast-radius-halo"
                        />
                      )}

                      {/* Main Macro Card Surface */}
                      <rect
                        width={WAN_NODE_WIDTH}
                        height={WAN_NODE_HEIGHT}
                        rx="12"
                        className={`noc-wan-site-card-bg ${site.status}`}
                      />

                      {/* Row 1: Regional Flag + Site Code + Health Badge */}
                      <text x="14" y="22" className="noc-wan-flag">
                        {site.flag}
                      </text>
                      <text x="38" y="23" className="noc-wan-code">
                        {site.code}
                      </text>

                      <g transform={`translate(${WAN_NODE_WIDTH - 86}, 12)`}>
                        <rect
                          width="72"
                          height="18"
                          rx="9"
                          fill={statusBg}
                          stroke={statusBorder}
                          strokeWidth="1"
                        />
                        <circle cx="9" cy="9" r="3" fill={statusColor} />
                        <text
                          x="20"
                          y="9.5"
                          fill={statusColor}
                          className="noc-wan-status-text"
                        >
                          {site.status.toUpperCase()}
                        </text>
                      </g>

                      {/* Row 2: Location Name & Registered Devices */}
                      <text x="14" y="44" className="noc-wan-name">
                        {site.name.length > 20 ? site.name.slice(0, 19) + '…' : site.name}
                      </text>
                      <text x="14" y="60" className="noc-wan-sub">
                        {site.devicesCount} Devices Registered • {site.region}
                      </text>

                      {/* Row 3: Active Alerts & Avoided Tickets */}
                      <text
                        x="14"
                        y="78"
                        className="noc-wan-alert-text"
                        fill={site.activeAlerts > 0 ? 'var(--accent-rose, #ef4444)' : 'var(--text-tertiary)'}
                      >
                        ● {site.activeAlerts} Active Alert{site.activeAlerts === 1 ? '' : 's'}
                      </text>
                      <text x="126" y="78" className="noc-wan-avoid-text">
                        ⚡ {site.avoidedTickets} Avoided
                      </text>

                      {/* Row 4: Blast Radius Metric Chip & Drill Down Action */}
                      <rect
                        x="14"
                        y="86"
                        width="88"
                        height="16"
                        rx="4"
                        fill={site.blastRadius > 0 ? 'rgba(239, 68, 68, 0.14)' : 'rgba(16, 185, 129, 0.1)'}
                        stroke={site.blastRadius > 0 ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.25)'}
                        strokeWidth="0.8"
                      />
                      <text
                        x="18"
                        y="94.5"
                        fill={site.blastRadius > 0 ? 'var(--accent-rose, #ef4444)' : 'var(--health-healthy, #10b981)'}
                        className="noc-wan-blast-text"
                      >
                        Blast: {site.blastRadius}%
                      </text>

                      {/* Drill Down Action Target */}
                      <g
                        className="noc-wan-drilldown-btn"
                        transform={`translate(${WAN_NODE_WIDTH - 82}, 85)`}
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectSite(site.code);
                        }}
                      >
                        <rect
                          width="68"
                          height="18"
                          rx="4"
                          className="noc-wan-drill-bg"
                        />
                        <text
                          x="7"
                          y="9.5"
                          className="noc-wan-drill-text"
                        >
                          Drill Down →
                        </text>
                      </g>
                    </g>
                  );
                })}
              </g>
            </>
          ) : (
            /* ═════════════════════════════════════════════════════════════════════
                LEVEL 2: SITE LAN TIER TOPOLOGY (CORE ↔ DIST ↔ ACCESS)
                ═════════════════════════════════════════════════════════════════════ */
            <>
              {/* 1. Horizontal Tier Lane Backgrounds */}
              {[
                { id: 'core', y: 40, height: 180, label: 'CORE & WAN BACKBONE', meta: TIER_METADATA.core },
                { id: 'dist_sec', y: 260, height: 180, label: 'DISTRIBUTION & SECURITY PERIMETER', meta: TIER_METADATA.dist_sec },
                { id: 'access', y: 480, height: 180, label: 'CAMPUS & ACCESS EDGE', meta: TIER_METADATA.access }
              ].map(lane => {
                const stats = tierStats[lane.id] || { count: 0, critical: 0, warning: 0, healthy: 0 };
                return (
                  <g key={lane.id} className={`noc-tier-lane-group lane-${lane.id}`}>
                    <rect
                      x="20"
                      y={lane.y}
                      width={canvasDimensions.width - 40}
                      height={lane.height}
                      rx="12"
                      className="noc-tier-lane-bg"
                    />
                    <rect
                      x="20"
                      y={lane.y}
                      width="4"
                      height={lane.height}
                      rx="2"
                      fill={lane.meta.color}
                    />
                    <text
                      x="36"
                      y={lane.y + 24}
                      className="noc-tier-lane-title"
                    >
                      {lane.label}
                    </text>
                    <text
                      x="36"
                      y={lane.y + 40}
                      className="noc-tier-lane-sub"
                    >
                      {stats.count} nodes • {stats.critical > 0 ? `${stats.critical} critical • ` : ''}{stats.warning > 0 ? `${stats.warning} warning • ` : ''}{stats.healthy} nominal
                    </text>
                  </g>
                );
              })}

              {/* 2. Interconnected Link Edges */}
              <g className="noc-edges-group">
                {edges.map(edge => {
                  const isHovered = hoveredEdge === edge.id;
                  const strokeColor = getStatusColor(edge.status);
                  const isBroken = edge.status === 'critical';

                  return (
                    <g key={edge.id} className="noc-edge-item">
                      <path
                        d={edge.path}
                        fill="none"
                        stroke="transparent"
                        strokeWidth="16"
                        onMouseEnter={() => setHoveredEdge(edge.id)}
                        onMouseLeave={() => setHoveredEdge(null)}
                        style={{ cursor: 'pointer' }}
                      />
                      <path
                        id={edge.id}
                        d={edge.path}
                        fill="none"
                        stroke={strokeColor}
                        strokeWidth={isHovered ? '2.5' : edge.type === 'backbone' ? '2.2' : '1.8'}
                        strokeDasharray={edge.type === 'redundant' ? '5,4' : isBroken ? '6,4' : 'none'}
                        className={`noc-link-path ${isHovered ? 'hovered' : ''} ${edge.isDimmed ? 'dimmed' : ''}`}
                        opacity={edge.isDimmed ? 0.08 : isHovered ? 1 : edge.type === 'redundant' ? 0.45 : 0.75}
                      />
                      <circle
                        r={isHovered ? '4' : '3'}
                        fill={strokeColor}
                        className="noc-traffic-pulse"
                        opacity={edge.isDimmed ? 0 : edge.status === 'critical' ? 0.3 : 0.85}
                      >
                        <animateMotion
                          path={edge.path}
                          dur={edge.type === 'backbone' ? '2.5s' : '3.8s'}
                          repeatCount="indefinite"
                        />
                      </circle>
                    </g>
                  );
                })}
              </g>

              {/* 3. Device Node Micro-Cards */}
              <g className="noc-nodes-group">
                {nodes.map(node => {
                  const isSelected = selectedDevice && selectedDevice.device_name === node.id;
                  const isHovered = hoveredNode === node.id;
                  const tierMeta = TIER_METADATA[node.tier];
                  const healthColor = getStatusColor(node.health);

                  return (
                    <g
                      key={node.id}
                      className={`noc-graph-node-card ${isSelected ? 'selected' : ''} ${node.isDimmed ? 'dimmed' : ''}`}
                      transform={`translate(${node.x - NODE_WIDTH / 2}, ${node.y - NODE_HEIGHT / 2})`}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectDevice(node.device);
                      }}
                      onMouseEnter={() => setHoveredNode(node.id)}
                      onMouseLeave={() => setHoveredNode(null)}
                      style={{ cursor: 'pointer' }}
                    >
                      {isSelected && (
                        <rect
                          x="-4"
                          y="-4"
                          width={NODE_WIDTH + 8}
                          height={NODE_HEIGHT + 8}
                          rx="14"
                          fill="none"
                          stroke="var(--accent-blue)"
                          strokeWidth="2.5"
                          filter="url(#glow-blue)"
                          className="noc-node-selected-ring"
                        />
                      )}

                      <rect
                        width={NODE_WIDTH}
                        height={NODE_HEIGHT}
                        rx="10"
                        className={`noc-node-surface ${node.health}`}
                      />

                      <rect
                        x="0"
                        y="0"
                        width="4"
                        height={NODE_HEIGHT}
                        rx="2"
                        fill={tierMeta.color}
                      />

                      {renderRoleIcon(node.tier, tierMeta.color)}

                      <text
                        x="38"
                        y="23"
                        className="noc-node-title-text"
                      >
                        <title>{node.device.device_name}</title>
                        {node.device.device_name.length > 20
                          ? node.device.device_name.slice(0, 19) + '…'
                          : node.device.device_name}
                      </text>

                      <text
                        x="38"
                        y="37"
                        className="noc-node-subtitle-text"
                      >
                        {node.device.ip_address || '10.x.x.x'} • {node.device.location || 'HQ'}
                      </text>

                      <rect
                        x="12"
                        y="48"
                        width="54"
                        height="18"
                        rx="4"
                        fill="var(--bg-tertiary)"
                        stroke="var(--card-border)"
                        strokeWidth="1"
                      />
                      <text
                        x="39"
                        y="60.5"
                        textAnchor="middle"
                        className="noc-node-tier-pill"
                        fill={tierMeta.color}
                      >
                        {tierMeta.tag}
                      </text>

                      {node.activeAlertCount > 0 ? (
                        <g>
                          <rect
                            x="72"
                            y="48"
                            width="86"
                            height="18"
                            rx="4"
                            fill="rgba(239, 68, 68, 0.14)"
                            stroke="rgba(239, 68, 68, 0.35)"
                            strokeWidth="1"
                          />
                          <text
                            x="115"
                            y="60.5"
                            textAnchor="middle"
                            className="noc-node-alert-pill-text"
                            fill="#ef4444"
                          >
                            ⚠ {node.activeAlertCount} Alert{node.activeAlertCount > 1 ? 's' : ''}
                          </text>
                        </g>
                      ) : (
                        <g>
                          <rect
                            x="72"
                            y="48"
                            width="74"
                            height="18"
                            rx="4"
                            fill="rgba(16, 185, 129, 0.1)"
                            stroke="rgba(16, 185, 129, 0.25)"
                            strokeWidth="1"
                          />
                          <text
                            x="109"
                            y="60.5"
                            textAnchor="middle"
                            className="noc-node-alert-pill-text"
                            fill="var(--health-healthy)"
                          >
                            ✓ Nominal
                          </text>
                        </g>
                      )}

                      <circle
                        cx={NODE_WIDTH - 18}
                        cy="19"
                        r="4.5"
                        fill={healthColor}
                      />
                      {node.health === 'critical' && (
                        <circle
                          cx={NODE_WIDTH - 18}
                          cy="19"
                          r="10"
                          fill="none"
                          stroke="#ef4444"
                          strokeWidth="1.5"
                          className="noc-radar-pulse-ring"
                        />
                      )}
                    </g>
                  );
                })}
              </g>
            </>
          )}
        </g>
      </svg>
    </div>
  );
}
