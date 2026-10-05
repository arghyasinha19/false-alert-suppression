import React, { useState, useRef, useMemo, useEffect, useCallback } from 'react';
import {
  ZoomIn, ZoomOut, Maximize2, RotateCcw,
  LayoutGrid, Server, Shield, Wifi,
  Activity, Move
} from 'lucide-react';

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

export default function TopologyGraphView({
  devices = [],
  selectedDevice = null,
  onSelectDevice = () => {},
  subMode = 'graph',
  onToggleSubMode = () => {},
  searchQuery = '',
  roleFilter = 'all',
  healthFilter = 'all',
  onResetFilters = null
}) {
  const containerRef = useRef(null);
  const [containerSize, setContainerSize] = useState({ width: 1100, height: 720 });
  const [transform, setTransform] = useState({ x: 30, y: 20, k: 0.95 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const [panDistance, setPanDistance] = useState(0);
  const [startTransform, setStartTransform] = useState({ x: 0, y: 0, k: 1 });
  const [hoveredNode, setHoveredNode] = useState(null);
  const [hoveredEdge, setHoveredEdge] = useState(null);

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

  // Compute node coordinates grouped by tier
  const { nodes, edges, tierStats, canvasDimensions } = useMemo(() => {
    const buckets = { core: [], dist_sec: [], access: [] };
    devices.forEach(d => {
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
  }, [devices, containerSize, searchQuery, roleFilter, healthFilter, hasActiveFilter]);

  const matchCount = useMemo(() => {
    return nodes.filter(n => !n.isDimmed).length;
  }, [nodes]);

  // Handle Drag / Pan Operations
  const handlePointerDown = (e) => {
    if (e.button !== 0) return; // Only primary mouse button
    // Don't pan if clicking directly on a button, node, or badge
    if (
      e.target.closest('.noc-graph-control-btn') ||
      e.target.closest('.noc-graph-node-card') ||
      e.target.closest('.noc-graph-filter-badge')
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
    setPanDistance(d => d + Math.abs(dx) + Math.abs(dy));
    setTransform({
      ...startTransform,
      x: startTransform.x + dx,
      y: startTransform.y + dy
    });
  };

  const handlePointerUp = (e) => {
    if (isPanning) {
      setIsPanning(false);
      try {
        if (containerRef.current) {
          containerRef.current.releasePointerCapture(e.pointerId);
        }
      } catch {
        // Safe ignore
      }
      // If user tapped empty canvas without panning, deselect device
      if (panDistance < 6) {
        if (e.target.tagName === 'svg' || e.target.id === 'noc-canvas-bg' || e.target.classList?.contains('noc-tier-lane-bg')) {
          onSelectDevice(null);
        }
      }
    }
  };

  // Handle Mouse Wheel Zooming (clamped 0.4x to 2.2x)
  const handleWheel = useCallback((e) => {
    e.preventDefault();
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.909;
    setTransform(curr => {
      const nextK = Math.min(2.2, Math.max(0.4, curr.k * zoomFactor));
      if (nextK === curr.k) return curr;

      // Zoom towards mouse coordinate
      const nextX = mouseX - (mouseX - curr.x) * (nextK / curr.k);
      const nextY = mouseY - (mouseY - curr.y) * (nextK / curr.k);

      return { x: nextX, y: nextY, k: nextK };
    });
  }, []);

  // Attach non-passive wheel listener for clean e.preventDefault()
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    el.addEventListener('wheel', handleWheel, { passive: false });
    return () => el.removeEventListener('wheel', handleWheel);
  }, [handleWheel]);

  // Toolbar Actions
  const handleZoomIn = () => {
    setTransform(curr => ({
      ...curr,
      k: Math.min(2.2, curr.k * 1.2)
    }));
  };

  const handleZoomOut = () => {
    setTransform(curr => ({
      ...curr,
      k: Math.max(0.4, curr.k * 0.83)
    }));
  };

  const handleResetZoom = () => {
    setTransform({ x: 30, y: 20, k: 0.95 });
  };

  const handleFitToScreen = () => {
    if (nodes.length === 0) return;
    const padding = 60;
    const scaleX = (containerSize.width - padding * 2) / canvasDimensions.width;
    const scaleY = (containerSize.height - padding * 2) / canvasDimensions.height;
    const newK = Math.min(1.2, Math.max(0.45, Math.min(scaleX, scaleY)));
    const newX = (containerSize.width - canvasDimensions.width * newK) / 2;
    const newY = Math.max(20, (containerSize.height - canvasDimensions.height * newK) / 2);
    setTransform({ x: newX, y: newY, k: newK });
  };

  // Color mapper helper
  const getStatusColor = (status) => {
    if (status === 'critical') return '#ef4444';
    if (status === 'warning') return '#f59e0b';
    return '#06b6d4'; // teal
  };

  return (
    <div
      ref={containerRef}
      className={`noc-topology-graph-container ${isPanning ? 'is-panning' : ''}`}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
    >
      {/* Floating Canvas Controls Toolbar */}
      <div className="noc-graph-controls-toolbar">
        {/* Sub-mode switch button: Graph vs Cards */}
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
          <Maximize2 size={13} />
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

      {/* Floating Canvas Legend or Active Filter Match Banner (Top Left) */}
      {hasActiveFilter ? (
        <div className="noc-graph-filter-badge">
          <Activity size={13} style={{ color: 'var(--accent-blue)' }} />
          <span>
            Filtered: <strong>{matchCount}</strong> of {nodes.length} devices
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
        <div className="noc-graph-legend-badge">
          <span className="noc-legend-icon"><Move size={12} /></span>
          <span>Drag canvas to pan • Scroll to zoom • Click node to triage</span>
        </div>
      )}

      {/* Main SVG Graph Surface */}
      <svg
        className="noc-topology-canvas"
        width="100%"
        height="100%"
        style={{ display: 'block' }}
      >
        <defs>
          {/* Subtle Grid Dot Pattern */}
          <pattern id="noc-grid-dots" width="24" height="24" patternUnits="userSpaceOnUse">
            <circle cx="2" cy="2" r="1" fill="var(--card-border)" opacity="0.35" />
          </pattern>

          {/* Node Glow Filters */}
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

        {/* Dot Grid Background */}
        <rect id="noc-canvas-bg" width="100%" height="100%" fill="url(#noc-grid-dots)" />

        {/* Pan & Zoom Transform Group */}
        <g transform={`translate(${transform.x}, ${transform.y}) scale(${transform.k})`}>
          {/* 1. Horizontal Tier Lane Backgrounds */}
          {[
            { id: 'core', y: 40, height: 180, label: 'CORE & WAN BACKBONE', meta: TIER_METADATA.core },
            { id: 'dist_sec', y: 260, height: 180, label: 'DISTRIBUTION & SECURITY PERIMETER', meta: TIER_METADATA.dist_sec },
            { id: 'access', y: 480, height: 180, label: 'CAMPUS & ACCESS EDGE', meta: TIER_METADATA.access }
          ].map(lane => {
            const stats = tierStats[lane.id] || { count: 0, critical: 0, warning: 0, healthy: 0 };
            return (
              <g key={lane.id} className={`noc-tier-lane-group lane-${lane.id}`}>
                {/* Lane Background Band */}
                <rect
                  x="20"
                  y={lane.y}
                  width={canvasDimensions.width - 40}
                  height={lane.height}
                  rx="12"
                  className="noc-tier-lane-bg"
                />
                {/* Lane Header Banner */}
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
                  {/* Invisible broad stroke for easier hovering */}
                  <path
                    d={edge.path}
                    fill="none"
                    stroke="transparent"
                    strokeWidth="16"
                    onMouseEnter={() => setHoveredEdge(edge.id)}
                    onMouseLeave={() => setHoveredEdge(null)}
                    style={{ cursor: 'pointer' }}
                  />

                  {/* Main Link Cable Path */}
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

                  {/* Animated Traveling Traffic Pulse (SVG native animateMotion) */}
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
                  <circle
                    r="1.5"
                    fill="#ffffff"
                    opacity={edge.isDimmed ? 0 : 0.9}
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
                  {/* Selection Glowing Highlight Ring */}
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

                  {/* Node Card Container */}
                  <rect
                    x="0"
                    y="0"
                    width={NODE_WIDTH}
                    height={NODE_HEIGHT}
                    rx="10"
                    className="noc-node-card-body"
                    stroke={isSelected ? 'var(--accent-blue)' : isHovered ? 'var(--card-border-hover)' : 'var(--card-border)'}
                    strokeWidth={isSelected ? '2' : '1'}
                    filter="url(#node-shadow)"
                  />

                  {/* Tier Accent Left Edge */}
                  <rect
                    x="0"
                    y="0"
                    width="4"
                    height={NODE_HEIGHT}
                    rx="2"
                    fill={tierMeta.color}
                  />

                  {/* Vector Role Icon */}
                  {renderRoleIcon(node.tier, tierMeta.color)}

                  {/* Device Hostname with Tooltip */}
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

                  {/* Device IP & Location Subtitle */}
                  <text
                    x="38"
                    y="37"
                    className="noc-node-subtitle-text"
                  >
                    {node.device.ip_address || '10.x.x.x'} • {node.device.location || 'HQ'}
                  </text>

                  {/* Tier Pill Badge */}
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

                  {/* Active Alert Count Pill (if any) */}
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

                  {/* Health Status Dot & Radar Pulse */}
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
        </g>
      </svg>
    </div>
  );
}
