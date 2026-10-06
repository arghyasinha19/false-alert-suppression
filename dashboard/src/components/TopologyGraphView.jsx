import React, { useState, useRef, useMemo, useEffect, useCallback } from 'react';
import {
  forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide, forceX, forceY
} from 'd3-force';
import {
  ZoomIn, ZoomOut, Maximize2, Minimize2, Shuffle, Scan, Pin, PinOff,
  ArrowLeft, Globe, Server, Shield, Wifi, Network, AlertTriangle, ChevronRight,
  Activity, Ticket, X, Play, Pause, CornerDownRight, Search
} from 'lucide-react';
import './TopologyGraphView.css';

/* ────────────────────────────────────────────────────────────────────────────
   Static metadata
   ──────────────────────────────────────────────────────────────────────────── */

const SITE_METADATA = {
  'UK-LON': { flag: '🇬🇧', name: 'London', region: 'EMEA', shortName: 'London Core DC' },
  'UK-MAL': { flag: '🇬🇧', name: 'Malmesbury', region: 'EMEA', shortName: 'Malmesbury Campus' },
  'DE-FRA': { flag: '🇩🇪', name: 'Frankfurt', region: 'EMEA', shortName: 'Frankfurt Transit DC' },
  'US-NY': { flag: '🇺🇸', name: 'New York', region: 'Americas', shortName: 'New York Metro DC' },
  'US-CHI': { flag: '🇺🇸', name: 'Chicago', region: 'Americas', shortName: 'Chicago Regional DC' },
  'SG-SIN': { flag: '🇸🇬', name: 'Singapore', region: 'APAC', shortName: 'Singapore APAC Hub' },
  'JP-TKY': { flag: '🇯🇵', name: 'Tokyo', region: 'APAC', shortName: 'Tokyo Regional Hub' },
  'IN-MUM': { flag: '🇮🇳', name: 'Mumbai', region: 'APAC', shortName: 'Mumbai West DC' },
  'AU-SYD': { flag: '🇦🇺', name: 'Sydney', region: 'APAC', shortName: 'Sydney Oceanic DC' },
  'INFRA-CORE': { flag: '🏢', name: 'Core Fabric', region: 'Global', shortName: 'Global Core Fabric' },
  'INFRA-ACCESS': { flag: '⚡', name: 'Access Fabric', region: 'Global', shortName: 'Edge Access Fabric' },
};

const TIER_METADATA = {
  site: { id: 'site', label: 'Site', color: '#6366f1', icon: Globe },
  core: { id: 'core', label: 'Core / WAN', color: '#3b82f6', icon: Server },
  dist_sec: { id: 'dist_sec', label: 'Distribution / Security', color: '#a855f7', icon: Shield },
  access: { id: 'access', label: 'Access switch', color: '#14b8a6', icon: Network },
  wireless: { id: 'wireless', label: 'Wireless AP', color: '#06b6d4', icon: Wifi },
};

const ROLE_TO_TIER = { core: 'core', distribution: 'dist_sec', security: 'dist_sec', access: 'access', wireless: 'wireless' };

const HEALTH_COLOR = {
  critical: '#ef4444',
  warning: '#f59e0b',
  healthy: '#10b981',
  degraded: '#f59e0b',
  nominal: '#10b981',
  unknown: '#94a3b8',
};

const WAN_INTERCONNECTS = [
  { source: 'US-NY', target: 'US-CHI', latency: '18ms', type: 'metro', bandwidth: '40G', loss: '0.00%', label: 'Inter-city metro' },
  { source: 'US-NY', target: 'UK-LON', latency: '115ms', type: 'subsea', bandwidth: '100G', loss: '0.01%', label: 'Transatlantic subsea' },
  { source: 'UK-LON', target: 'UK-MAL', latency: '6ms', type: 'metro', bandwidth: '10G', loss: '0.00%', label: 'Regional metro' },
  { source: 'UK-LON', target: 'DE-FRA', latency: '24ms', type: 'backbone', bandwidth: '100G', loss: '0.00%', label: 'European core' },
  { source: 'DE-FRA', target: 'SG-SIN', latency: '128ms', type: 'terrestrial', bandwidth: '100G', loss: '0.02%', label: 'Eurasia transit' },
  { source: 'SG-SIN', target: 'JP-TKY', latency: '68ms', type: 'subsea', bandwidth: '40G', loss: '0.00%', label: 'East Asia subsea' },
  { source: 'SG-SIN', target: 'IN-MUM', latency: '42ms', type: 'subsea', bandwidth: '40G', loss: '0.01%', label: 'Bay of Bengal cable' },
  { source: 'SG-SIN', target: 'AU-SYD', latency: '92ms', type: 'subsea', bandwidth: '40G', loss: '0.02%', label: 'Indo-Pacific subsea' },
  { source: 'INFRA-CORE', target: 'UK-LON', latency: '2ms', type: 'fabric', bandwidth: '400G', loss: '0.00%', label: 'Core fabric' },
  { source: 'INFRA-CORE', target: 'US-NY', latency: '2ms', type: 'fabric', bandwidth: '400G', loss: '0.00%', label: 'Core fabric' },
  { source: 'INFRA-ACCESS', target: 'INFRA-CORE', latency: '1ms', type: 'fabric', bandwidth: '400G', loss: '0.00%', label: 'Fabric uplink' },
];

const SITE_R_MIN = 30;
const SITE_R_MAX = 44;
const DEVICE_R = 22;
const HUB_R = 38;

/* ────────────────────────────────────────────────────────────────────────────
   Helpers
   ──────────────────────────────────────────────────────────────────────────── */

// Mirrors deriveDeviceRole() in NetworkOperations so the role filter chips line up.
function deriveRole(device) {
  const name = (device.device_name || '').toLowerCase();
  const cat = (device.category || '').toLowerCase();
  if (name.includes('fw') || name.includes('firewall') || cat.includes('firewall') || cat.includes('security')) return 'security';
  if (name.includes('ap') || name.includes('wlc') || name.includes('wifi') || cat.includes('wireless') || cat.includes('access point')) return 'wireless';
  if (name.includes('core') || (name.includes('router') && !name.includes('dist')) || name.includes('rt') || name.includes('gw') || name.includes('dc') || cat.includes('router')) return 'core';
  if (name.includes('dist') || name.includes('sw01')) return 'distribution';
  return 'access';
}

function getNodeHealth(device) {
  const active = (device.active_alerts || []).filter(a => a.dnac_live_status !== 'RESOLVED');
  if (active.some(a => a.severity <= 1)) return 'critical';
  if (active.some(a => a.severity === 2) || device.non_auto_resolving > 0) return 'warning';
  return 'healthy';
}

function shortDeviceName(name = '') {
  if (name.length <= 16) return name;
  const parts = name.split('-');
  return parts.length > 2 ? parts.slice(-2).join('-') : name;
}

function siteStatusLabel(status) {
  if (status === 'critical') return 'Critical';
  if (status === 'degraded') return 'Degraded';
  return 'Nominal';
}

function healthLabel(h) {
  if (h === 'critical') return 'Critical';
  if (h === 'warning') return 'Warning';
  return 'Healthy';
}

function statusToHealth(status) {
  if (status === 'critical') return 'critical';
  if (status === 'degraded') return 'warning';
  return 'healthy';
}

/* ────────────────────────────────────────────────────────────────────────────
   Component
   ──────────────────────────────────────────────────────────────────────────── */

export default function TopologyGraphView({
  devices = [],
  sites = [],
  selectedDevice = null,
  onSelectDevice = () => {},
  searchQuery = '',
  roleFilter = 'all',
  healthFilter = 'all',
  onResetFilters = null,
  topologyLevel = 'wan',
  selectedSite = null,
  onSelectSite = () => {},
  onReturnToWan = () => {},
}) {
  const containerRef = useRef(null);
  const svgRef = useRef(null);
  const simRef = useRef(null);
  const rafRef = useRef(null);
  const [size, setSize] = useState({ width: 1100, height: 640 });
  const [view, setView] = useState({ x: 0, y: 0, k: 1 });
  const [positions, setPositions] = useState({});
  const [hovered, setHovered] = useState(null);
  const [hoveredEdge, setHoveredEdge] = useState(null);
  const [pointer, setPointer] = useState({ x: 0, y: 0 });
  const [inspected, setInspected] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [physicsOn, setPhysicsOn] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [layoutSeed, setLayoutSeed] = useState(0);
  const dragRef = useRef(null);
  const panRef = useRef(null);
  const didFitRef = useRef(false);
  const reducedMotion = typeof window !== 'undefined'
    && window.matchMedia
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── Track container size ─────────────────────────────────────────────── */
  useEffect(() => {
    if (!containerRef.current) return;
    const obs = new ResizeObserver(entries => {
      for (const e of entries) {
        if (e.contentRect.width > 0 && e.contentRect.height > 0) {
          setSize({ width: e.contentRect.width, height: e.contentRect.height });
        }
      }
    });
    obs.observe(containerRef.current);
    return () => obs.disconnect();
  }, []);

  /* ── Resolve sites (prop or derived) ──────────────────────────────────── */
  const siteList = useMemo(() => {
    if (sites && sites.length > 0) return sites;
    const map = {};
    devices.forEach(d => {
      const loc = d.location || 'INFRA-CORE';
      if (!map[loc]) map[loc] = { code: loc, label: loc, devices: [], critical: 0, warning: 0, healthy: 0, totalAlerts: 0, avoidedTickets: 0 };
      map[loc].devices.push(d);
      const h = getNodeHealth(d);
      map[loc][h]++;
      map[loc].totalAlerts += (d.active_alerts || []).length;
      map[loc].avoidedTickets += (d.auto_resolving || 0) + (d.backdated || 0);
    });
    return Object.values(map).map(s => ({
      ...s,
      status: s.critical > 0 ? 'critical' : s.warning > 0 ? 'degraded' : 'nominal',
    }));
  }, [sites, devices]);

  const hasActiveFilter = Boolean(searchQuery || roleFilter !== 'all' || healthFilter !== 'all');
  const q = (searchQuery || '').toLowerCase().trim();

  /* ── Build graph model for current level ─────────────────────────────── */
  const graph = useMemo(() => {
    const nodes = [];
    const edges = [];

    if (topologyLevel === 'wan' || !selectedSite) {
      const maxDev = Math.max(1, ...siteList.map(s => (s.devices || []).length));
      siteList.forEach(s => {
        const meta = SITE_METADATA[s.code] || {};
        const devCount = (s.devices || []).length;
        const r = SITE_R_MIN + (SITE_R_MAX - SITE_R_MIN) * (devCount / maxDev);
        const matchesQuery = !q || s.code.toLowerCase().includes(q) || (s.label || '').toLowerCase().includes(q) || (meta.name || '').toLowerCase().includes(q);
        const matchesHealth = healthFilter === 'all' || statusToHealth(s.status) === healthFilter;
        nodes.push({
          id: s.code,
          kind: 'site',
          tier: 'site',
          r,
          caption: s.code,
          title: meta.name || s.label || s.code,
          subtitle: meta.shortName || '',
          region: meta.region || 'Regional',
          flag: meta.flag || '🌐',
          status: s.status,
          health: statusToHealth(s.status),
          devices: devCount,
          critical: s.critical || 0,
          warning: s.warning || 0,
          healthy: s.healthy || 0,
          alerts: s.totalAlerts || 0,
          avoided: s.avoidedTickets || 0,
          dimmed: !(matchesQuery && matchesHealth),
          raw: s,
        });
      });
      const ids = new Set(nodes.map(n => n.id));
      WAN_INTERCONNECTS.forEach(def => {
        if (ids.has(def.source) && ids.has(def.target)) {
          const a = nodes.find(n => n.id === def.source);
          const b = nodes.find(n => n.id === def.target);
          const status = (a.status === 'critical' || b.status === 'critical') ? 'critical'
            : (a.status === 'degraded' || b.status === 'degraded') ? 'warning' : 'nominal';
          edges.push({
            id: `${def.source}→${def.target}`,
            source: def.source,
            target: def.target,
            rel: def.type.toUpperCase(),
            caption: def.latency,
            detail: `${def.label} · ${def.bandwidth} · loss ${def.loss}`,
            status,
            dimmed: hasActiveFilter && a.dimmed && b.dimmed,
          });
        }
      });
      // Connect orphan sites to the nearest hub so nothing floats unattached
      const connected = new Set(edges.flatMap(e => [e.source, e.target]));
      const hub = ids.has('INFRA-CORE') ? 'INFRA-CORE' : nodes[0]?.id;
      nodes.forEach(n => {
        if (!connected.has(n.id) && hub && n.id !== hub) {
          edges.push({ id: `${hub}→${n.id}`, source: hub, target: n.id, rel: 'PEERS', caption: '', detail: 'Logical peering', status: 'nominal', dimmed: false });
        }
      });
    } else {
      const site = siteList.find(s => s.code === selectedSite);
      const meta = SITE_METADATA[selectedSite] || {};
      const scoped = devices.filter(d => d.location === selectedSite || (d.device_name || '').startsWith(selectedSite));
      const hubId = `site:${selectedSite}`;
      nodes.push({
        id: hubId,
        kind: 'hub',
        tier: 'site',
        r: HUB_R,
        caption: selectedSite,
        title: meta.name || site?.label || selectedSite,
        subtitle: meta.shortName || '',
        region: meta.region || '',
        flag: meta.flag || '🏢',
        status: site?.status || 'nominal',
        health: statusToHealth(site?.status),
        devices: scoped.length,
        critical: site?.critical || 0,
        warning: site?.warning || 0,
        healthy: site?.healthy || 0,
        alerts: site?.totalAlerts || 0,
        avoided: site?.avoidedTickets || 0,
        dimmed: false,
        fixed: true,
        raw: site,
      });
      const byTier = { core: [], dist_sec: [], access: [], wireless: [] };
      scoped.forEach(d => {
        const role = deriveRole(d);
        const tier = ROLE_TO_TIER[role] || 'access';
        const health = getNodeHealth(d);
        const matchesQuery = !q || (d.device_name || '').toLowerCase().includes(q) || (d.device_id || '').toLowerCase().includes(q);
        const matchesRole = roleFilter === 'all' || role === roleFilter;
        const matchesHealth = healthFilter === 'all' || health === healthFilter;
        const node = {
          id: d.device_name,
          kind: 'device',
          tier,
          role,
          r: DEVICE_R,
          caption: shortDeviceName(d.device_name),
          title: d.device_name,
          subtitle: TIER_METADATA[tier].label,
          health,
          status: health,
          alerts: (d.active_alerts || []).length,
          incidents: (d.active_alerts || []).filter(a => a.snow_incident).length,
          dimmed: !(matchesQuery && matchesRole && matchesHealth),
          device: d,
        };
        nodes.push(node);
        byTier[tier].push(node);
      });
      const link = (a, b, rel, detail) => {
        const status = (a.health === 'critical' || b.health === 'critical') ? 'critical'
          : (a.health === 'warning' || b.health === 'warning') ? 'warning' : 'nominal';
        edges.push({ id: `${a.id}→${b.id}`, source: a.id, target: b.id, rel, caption: '', detail, status, dimmed: hasActiveFilter && a.dimmed && b.dimmed });
      };
      const hub = nodes[0];
      byTier.core.forEach(n => link(hub, n, 'UPLINK', '100G backbone'));
      if (byTier.core.length === 0) byTier.dist_sec.forEach(n => link(hub, n, 'UPLINK', '40G uplink'));
      byTier.dist_sec.forEach((n, i) => {
        if (byTier.core.length > 0) link(byTier.core[i % byTier.core.length], n, 'AGGREGATES', '40G distribution uplink');
      });
      const parents = byTier.dist_sec.length ? byTier.dist_sec : byTier.core.length ? byTier.core : [hub];
      byTier.access.forEach((n, i) => link(parents[i % parents.length], n, 'SERVES', '10G access downlink'));
      const apParents = byTier.access.length ? byTier.access : parents;
      byTier.wireless.forEach((n, i) => link(apParents[i % apParents.length], n, 'POWERS', 'PoE access port'));
    }

    return { nodes, edges };
  }, [topologyLevel, selectedSite, siteList, devices, q, roleFilter, healthFilter, hasActiveFilter]);

  const nodeById = useMemo(() => Object.fromEntries(graph.nodes.map(n => [n.id, n])), [graph]);

  const adjacency = useMemo(() => {
    const adj = {};
    graph.edges.forEach(e => {
      (adj[e.source] ||= new Set()).add(e.target);
      (adj[e.target] ||= new Set()).add(e.source);
    });
    return adj;
  }, [graph]);

  /* ── Simulation ───────────────────────────────────────────────────────── */
  const graphKey = `${topologyLevel}:${selectedSite}:${graph.nodes.map(n => n.id).join('|')}:${layoutSeed}`;

  useEffect(() => {
    const W = size.width, H = size.height;
    const prev = simRef.current ? Object.fromEntries(simRef.current.nodes().map(n => [n.id, n])) : {};
    const isWan = topologyLevel === 'wan' || !selectedSite;

    // Seed positions: WAN by region columns, LAN by tier rings around hub.
    const regionX = { Americas: 0.2, EMEA: 0.5, Global: 0.5, APAC: 0.8, Regional: 0.65 };
    const tierRing = { site: 0, core: 150, dist_sec: 260, access: 370, wireless: 470 };
    const simNodes = graph.nodes.map((n, i) => {
      const p = prev[n.id];
      let x, y;
      if (p && layoutSeed === 0) { x = p.x; y = p.y; }
      else if (isWan) {
        x = W * (regionX[n.region] ?? 0.5) + (Math.random() - 0.5) * 120;
        y = H * 0.5 + (Math.random() - 0.5) * H * 0.7;
      } else {
        const ring = tierRing[n.tier] ?? 300;
        const angle = (i / Math.max(1, graph.nodes.length)) * Math.PI * 2 + Math.random();
        x = W / 2 + Math.cos(angle) * ring;
        y = H / 2 + Math.sin(angle) * ring;
      }
      const node = { ...n, x, y, vx: 0, vy: 0 };
      if (n.fixed) { node.fx = W / 2; node.fy = H / 2; }
      return node;
    });
    const simLinks = graph.edges.map(e => ({ ...e }));

    if (simRef.current) simRef.current.stop();

    const sim = forceSimulation(simNodes)
      .force('link', forceLink(simLinks).id(d => d.id)
        .distance(l => {
          const a = l.source, b = l.target;
          if (isWan) return 140 + (a.r + b.r);
          if (a.kind === 'hub' || b.kind === 'hub') return 150;
          return 110;
        })
        .strength(isWan ? 0.5 : 0.8))
      .force('charge', forceManyBody().strength(isWan ? -900 : -520).distanceMax(600))
      .force('collide', forceCollide().radius(d => d.r + (showLabels ? 26 : 10)).strength(0.9))
      .force('center', forceCenter(W / 2, H / 2).strength(0.05))
      .force('x', forceX(W / 2).strength(0.03))
      .force('y', forceY(H / 2).strength(0.05))
      .alpha(1)
      .alphaDecay(reducedMotion ? 0.2 : 0.035);

    if (!isWan) {
      // Keep LAN tiers loosely in concentric rings around the hub.
      sim.force('ring', (alpha) => {
        for (const n of simNodes) {
          if (n.kind !== 'device') continue;
          const target = tierRing[n.tier] ?? 300;
          const dx = n.x - W / 2, dy = n.y - H / 2;
          const dist = Math.hypot(dx, dy) || 1;
          const diff = (target - dist) * alpha * 0.12;
          n.vx += (dx / dist) * diff;
          n.vy += (dy / dist) * diff;
        }
      });
    }

    const publish = () => {
      const pos = {};
      for (const n of simNodes) pos[n.id] = { x: n.x, y: n.y, pinned: n.fx != null && n.kind !== 'hub' };
      setPositions(pos);
    };
    sim.on('tick', () => {
      if (rafRef.current) return;
      rafRef.current = requestAnimationFrame(() => { rafRef.current = null; publish(); });
    });
    sim.on('end', () => {
      publish();
      if (!didFitRef.current) { didFitRef.current = true; fitToView(simNodes, W, H); }
    });
    simRef.current = sim;
    didFitRef.current = false;
    if (!physicsOn) { sim.stop(); publish(); }
    return () => { sim.stop(); if (rafRef.current) cancelAnimationFrame(rafRef.current); rafRef.current = null; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [graphKey, size.width, size.height]);

  useEffect(() => {
    const sim = simRef.current;
    if (!sim) return;
    if (physicsOn) sim.alpha(0.6).restart(); else sim.stop();
  }, [physicsOn]);

  /* ── View helpers ─────────────────────────────────────────────────────── */
  const fitToView = useCallback((nodes, W, H) => {
    const list = nodes || (simRef.current ? simRef.current.nodes() : []);
    if (!list.length) return;
    const pad = 50;
    const xs = list.map(n => n.x), ys = list.map(n => n.y);
    const minX = Math.min(...xs) - pad, maxX = Math.max(...xs) + pad;
    const minY = Math.min(...ys) - pad, maxY = Math.max(...ys) + pad + 20;
    const w = W ?? size.width, h = H ?? size.height;
    // Leave room for the top bar, legend and controls so nodes never sit under the chrome.
    const topInset = 64, bottomInset = w < 860 ? 112 : 68;
    const usableH = Math.max(200, h - topInset - bottomInset);
    const k = Math.min(1.25, Math.max(0.3, Math.min(w / (maxX - minX), usableH / (maxY - minY))));
    setView({ k, x: w / 2 - ((minX + maxX) / 2) * k, y: topInset + usableH / 2 - ((minY + maxY) / 2) * k });
  }, [size.width, size.height]);

  const zoomBy = (factor) => {
    setView(v => {
      const k = Math.min(3, Math.max(0.25, v.k * factor));
      const cx = size.width / 2, cy = size.height / 2;
      return { k, x: cx - (cx - v.x) * (k / v.k), y: cy - (cy - v.y) * (k / v.k) };
    });
  };

  const toGraphCoords = (clientX, clientY) => {
    const rect = svgRef.current.getBoundingClientRect();
    return { x: (clientX - rect.left - view.x) / view.k, y: (clientY - rect.top - view.y) / view.k };
  };

  /* ── Wheel zoom (non-passive) ─────────────────────────────────────────── */
  useEffect(() => {
    const el = svgRef.current;
    if (!el) return;
    const onWheel = (e) => {
      e.preventDefault();
      const rect = el.getBoundingClientRect();
      const mx = e.clientX - rect.left, my = e.clientY - rect.top;
      setView(v => {
        const k = Math.min(3, Math.max(0.25, v.k * (e.deltaY < 0 ? 1.12 : 0.89)));
        return { k, x: mx - (mx - v.x) * (k / v.k), y: my - (my - v.y) * (k / v.k) };
      });
    };
    el.addEventListener('wheel', onWheel, { passive: false });
    return () => el.removeEventListener('wheel', onWheel);
  }, []);

  /* ── Pointer interactions ─────────────────────────────────────────────── */
  const onNodePointerDown = (e, id) => {
    e.stopPropagation();
    e.currentTarget.setPointerCapture?.(e.pointerId);
    const sim = simRef.current;
    const node = sim?.nodes().find(n => n.id === id);
    if (!node) return;
    const start = toGraphCoords(e.clientX, e.clientY);
    dragRef.current = { id, node, offX: node.x - start.x, offY: node.y - start.y, moved: false, startClient: { x: e.clientX, y: e.clientY } };
    node.fx = node.x; node.fy = node.y;
    if (physicsOn) sim.alphaTarget(0.25).restart();
  };

  const onNodePointerMove = (e) => {
    const d = dragRef.current;
    if (!d) return;
    const p = toGraphCoords(e.clientX, e.clientY);
    if (Math.hypot(e.clientX - d.startClient.x, e.clientY - d.startClient.y) > 3) d.moved = true;
    d.node.fx = p.x + d.offX; d.node.fy = p.y + d.offY;
    if (!physicsOn) {
      d.node.x = d.node.fx; d.node.y = d.node.fy;
      setPositions(prev => ({ ...prev, [d.id]: { x: d.node.x, y: d.node.y, pinned: true } }));
    }
  };

  const onNodePointerUp = (e, node) => {
    const d = dragRef.current;
    dragRef.current = null;
    const sim = simRef.current;
    if (sim && physicsOn) sim.alphaTarget(0);
    if (d && !d.moved) {
      // Treat as click
      if (node.kind === 'hub') { d.node.fx = d.node.x; d.node.fy = d.node.y; }
      else { d.node.fx = null; d.node.fy = null; }
      handleNodeClick(node);
    } else if (d && node.kind !== 'hub') {
      // Keep pinned where dropped (Neo4j behaviour)
      setPositions(prev => ({ ...prev, [d.id]: { ...(prev[d.id] || {}), x: d.node.x, y: d.node.y, pinned: true } }));
    }
  };

  const unpin = (id) => {
    const node = simRef.current?.nodes().find(n => n.id === id);
    if (!node || node.kind === 'hub') return;
    node.fx = null; node.fy = null;
    setPositions(prev => ({ ...prev, [id]: { ...prev[id], pinned: false } }));
    if (physicsOn) simRef.current.alpha(0.3).restart();
  };

  const handleNodeClick = (node) => {
    if (node.kind === 'device') {
      setInspected(node.id);
      onSelectDevice(node.device);
    } else {
      setInspected(prev => (prev === node.id ? null : node.id));
    }
  };

  const handleNodeDoubleClick = (e, node) => {
    e.stopPropagation();
    if (node.kind === 'site') onSelectSite(node.id);
    else if (node.kind === 'device') onSelectDevice(node.device);
  };

  const onBackgroundPointerDown = (e) => {
    if (e.button !== 0) return;
    panRef.current = { sx: e.clientX, sy: e.clientY, ox: view.x, oy: view.y, moved: false };
    e.currentTarget.setPointerCapture?.(e.pointerId);
  };
  const onBackgroundPointerMove = (e) => {
    const p = panRef.current;
    if (!p) { setPointer({ x: e.clientX, y: e.clientY }); return; }
    const dx = e.clientX - p.sx, dy = e.clientY - p.sy;
    if (Math.hypot(dx, dy) > 2) p.moved = true;
    setView(v => ({ ...v, x: p.ox + dx, y: p.oy + dy }));
  };
  const onBackgroundPointerUp = () => {
    const p = panRef.current;
    panRef.current = null;
    if (p && !p.moved) setInspected(null);
  };

  /* ── Keyboard ─────────────────────────────────────────────────────────── */
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape' && isFullscreen) setIsFullscreen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isFullscreen]);

  useEffect(() => { setInspected(null); }, [topologyLevel, selectedSite]);

  /* ── Derived render state ─────────────────────────────────────────────── */
  const focusId = hovered || inspected || (selectedDevice ? selectedDevice.device_name : null);
  const focusSet = useMemo(() => {
    if (!focusId || !nodeById[focusId]) return null;
    const s = new Set([focusId]);
    (adjacency[focusId] || []).forEach(n => s.add(n));
    return s;
  }, [focusId, adjacency, nodeById]);

  const counts = useMemo(() => {
    const c = {};
    graph.nodes.forEach(n => { c[n.tier] = (c[n.tier] || 0) + 1; });
    return c;
  }, [graph]);

  const healthTotals = useMemo(() => {
    const t = { critical: 0, warning: 0, healthy: 0 };
    graph.nodes.forEach(n => { if (n.kind !== 'hub') t[n.health] = (t[n.health] || 0) + 1; });
    return t;
  }, [graph]);

  const matchCount = graph.nodes.filter(n => !n.dimmed && n.kind !== 'hub').length;
  const inspectedNode = inspected ? nodeById[inspected] : null;
  const hoveredNode = hovered ? nodeById[hovered] : null;
  const hoveredEdgeObj = hoveredEdge ? graph.edges.find(e => e.id === hoveredEdge) : null;
  const isWan = topologyLevel === 'wan' || !selectedSite;
  const siteMeta = SITE_METADATA[selectedSite] || {};
  const labelsVisible = showLabels && view.k > 0.55;

  const edgeStroke = (e) => e.status === 'critical' ? HEALTH_COLOR.critical : e.status === 'warning' ? HEALTH_COLOR.warning : 'var(--graph-edge)';

  /* ── Render ───────────────────────────────────────────────────────────── */
  return (
    <div
      ref={containerRef}
      className={`tg-container ${isFullscreen ? 'is-fullscreen' : ''}`}
      role="application"
      aria-label={isWan ? 'Global WAN topology graph' : `${selectedSite} site topology graph`}
    >
      {/* Top bar */}
      <div className="tg-topbar">
        <div className="tg-crumbs">
          {!isWan && (
            <button type="button" className="tg-back" onClick={onReturnToWan} title="Back to global WAN">
              <ArrowLeft size={14} />
              <span>Global WAN</span>
            </button>
          )}
          {isWan ? (
            <span className="tg-crumb-current"><Globe size={14} /> Global WAN topology</span>
          ) : (
            <>
              <ChevronRight size={13} className="tg-crumb-sep" />
              <span className="tg-crumb-current">
                <span className="tg-flag">{siteMeta.flag || '🏢'}</span>
                {siteMeta.name || selectedSite}
                <span className="tg-crumb-code">{selectedSite}</span>
              </span>
            </>
          )}
        </div>

        <div className="tg-stats">
          {isWan
            ? <span>{counts.site || 0} sites · {graph.edges.length} links</span>
            : <span>{(graph.nodes.length - 1)} devices · {graph.edges.length} links</span>}
          <span className="tg-stat-dot critical" title="Critical">{healthTotals.critical}</span>
          <span className="tg-stat-dot warning" title="Warning">{healthTotals.warning}</span>
          <span className="tg-stat-dot healthy" title="Healthy">{healthTotals.healthy}</span>
        </div>

        {!isWan && (
          <label className="tg-site-select">
            <span className="sr-only">Jump to site</span>
            <select value={selectedSite} onChange={e => onSelectSite(e.target.value)}>
              {siteList.map(s => (
                <option key={s.code} value={s.code}>{SITE_METADATA[s.code]?.flag || '🏢'} {s.code} — {SITE_METADATA[s.code]?.name || s.label}</option>
              ))}
            </select>
          </label>
        )}
      </div>

      {/* Filter notice */}
      {hasActiveFilter && (
        <div className="tg-filter-notice">
          <Search size={12} />
          <span>{matchCount} of {graph.nodes.filter(n => n.kind !== 'hub').length} match your filters</span>
          {onResetFilters && <button type="button" onClick={onResetFilters}>Clear</button>}
        </div>
      )}

      {/* Canvas */}
      <svg
        ref={svgRef}
        className={`tg-svg ${panRef.current ? 'is-panning' : ''}`}
        width="100%"
        height="100%"
        onPointerDown={onBackgroundPointerDown}
        onPointerMove={onBackgroundPointerMove}
        onPointerUp={onBackgroundPointerUp}
        onPointerLeave={() => { panRef.current = null; }}
      >
        <defs>
          <pattern id="tg-dots" width="26" height="26" patternUnits="userSpaceOnUse" patternTransform={`translate(${view.x} ${view.y}) scale(${view.k})`}>
            <circle cx="1" cy="1" r="1" fill="var(--graph-dot)" />
          </pattern>
          <filter id="tg-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="4" result="b" />
            <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>
        <rect width="100%" height="100%" fill="url(#tg-dots)" />

        <g transform={`translate(${view.x} ${view.y}) scale(${view.k})`}>
          {/* Edges */}
          <g className="tg-edges">
            {graph.edges.map(e => {
              const a = positions[e.source], b = positions[e.target];
              if (!a || !b) return null;
              const na = nodeById[e.source], nb = nodeById[e.target];
              const dx = b.x - a.x, dy = b.y - a.y;
              const len = Math.hypot(dx, dy) || 1;
              const ux = dx / len, uy = dy / len;
              const x1 = a.x + ux * (na.r + 2), y1 = a.y + uy * (na.r + 2);
              const x2 = b.x - ux * (nb.r + 2), y2 = b.y - uy * (nb.r + 2);
              const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
              const inFocus = focusSet ? (focusSet.has(e.source) && focusSet.has(e.target) && (e.source === focusId || e.target === focusId)) : true;
              const faded = (focusSet && !inFocus) || e.dimmed;
              const isHot = hoveredEdge === e.id;
              const angle = Math.atan2(dy, dx) * 180 / Math.PI;
              const flip = angle > 90 || angle < -90;
              const label = e.caption || e.rel;
              return (
                <g
                  key={e.id}
                  className={`tg-edge status-${e.status} ${faded ? 'is-faded' : ''} ${isHot ? 'is-hot' : ''}`}
                  onPointerEnter={() => setHoveredEdge(e.id)}
                  onPointerLeave={() => setHoveredEdge(null)}
                >
                  <line x1={x1} y1={y1} x2={x2} y2={y2} className="tg-edge-hit" />
                  <line x1={x1} y1={y1} x2={x2} y2={y2} className="tg-edge-line" stroke={edgeStroke(e)} />
                  {e.status === 'critical' && !reducedMotion && (
                    <line x1={x1} y1={y1} x2={x2} y2={y2} className="tg-edge-flow" stroke={edgeStroke(e)} />
                  )}
                  {labelsVisible && label && (
                    <g transform={`translate(${mx} ${my}) rotate(${flip ? angle + 180 : angle})`}>
                      <rect x={-(label.length * 3.4 + 7)} y={-8} width={label.length * 6.8 + 14} height={16} rx={8} className="tg-edge-label-bg" />
                      <text y={3.5} textAnchor="middle" className="tg-edge-label">{label}</text>
                    </g>
                  )}
                </g>
              );
            })}
          </g>

          {/* Nodes */}
          <g className="tg-nodes">
            {graph.nodes.map(n => {
              const p = positions[n.id];
              if (!p) return null;
              const tier = TIER_METADATA[n.tier];
              const isSelected = inspected === n.id || (selectedDevice && selectedDevice.device_name === n.id);
              const isHover = hovered === n.id;
              const faded = (focusSet && !focusSet.has(n.id)) || n.dimmed;
              const Icon = tier.icon;
              const iconSize = n.kind === 'device' ? 16 : 20;
              return (
                <g
                  key={n.id}
                  className={`tg-node kind-${n.kind} health-${n.health} ${isSelected ? 'is-selected' : ''} ${isHover ? 'is-hover' : ''} ${faded ? 'is-faded' : ''} ${p.pinned ? 'is-pinned' : ''}`}
                  transform={`translate(${p.x} ${p.y})`}
                  onPointerDown={e => onNodePointerDown(e, n.id)}
                  onPointerMove={onNodePointerMove}
                  onPointerUp={e => onNodePointerUp(e, n)}
                  onPointerEnter={() => setHovered(n.id)}
                  onPointerLeave={() => setHovered(null)}
                  onDoubleClick={e => handleNodeDoubleClick(e, n)}
                  tabIndex={0}
                  role="button"
                  aria-label={`${n.title}, ${healthLabel(n.health)}${n.alerts ? `, ${n.alerts} active alerts` : ''}`}
                  onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleNodeClick(n); } }}
                >
                  {(isSelected || isHover) && (
                    <circle r={n.r + 9} className="tg-node-halo" fill={tier.color} />
                  )}
                  {n.health === 'critical' && !reducedMotion && (
                    <circle r={n.r + 4} className="tg-node-pulse" stroke={HEALTH_COLOR.critical} />
                  )}
                  <circle r={n.r} className="tg-node-body" fill={tier.color} />
                  <circle r={n.r - 2.5} className="tg-node-ring" stroke={HEALTH_COLOR[n.health] || HEALTH_COLOR.unknown} />
                  <circle r={n.r - 2.5} className="tg-node-sheen" />
                  {n.kind === 'device' ? (
                    <g transform={`translate(${-iconSize / 2} ${-iconSize / 2 - 1})`}>
                      <Icon size={iconSize} color="#fff" strokeWidth={2} />
                    </g>
                  ) : (
                    <text y={n.r > 36 ? 9 : 7} textAnchor="middle" className="tg-node-flag" style={{ fontSize: n.r * 0.72 }}>{n.flag}</text>
                  )}
                  {n.alerts > 0 && (
                    <g transform={`translate(${n.r * 0.72} ${-n.r * 0.72})`} className="tg-badge">
                      <circle r={9} fill={n.health === 'critical' ? HEALTH_COLOR.critical : HEALTH_COLOR.warning} />
                      <text y={3.5} textAnchor="middle">{n.alerts > 9 ? '9+' : n.alerts}</text>
                    </g>
                  )}
                  {p.pinned && (
                    <g transform={`translate(${-n.r * 0.78} ${-n.r * 0.78})`} className="tg-pin" onClick={e => { e.stopPropagation(); unpin(n.id); }}>
                      <circle r={7} />
                      <Pin size={8} x={-4} y={-4} color="#fff" />
                    </g>
                  )}
                  {labelsVisible && (
                    <text y={n.r + 15} textAnchor="middle" className={`tg-node-label ${n.kind === 'device' ? 'is-device' : ''}`}>
                      {n.caption}
                    </text>
                  )}
                </g>
              );
            })}
          </g>
        </g>
      </svg>

      {/* Hover tooltip */}
      {hoveredNode && !dragRef.current && (
        <div
          className="tg-tooltip"
          style={{
            left: Math.min(size.width - 240, Math.max(8, pointer.x - (containerRef.current?.getBoundingClientRect().left || 0) + 16)),
            top: Math.max(8, pointer.y - (containerRef.current?.getBoundingClientRect().top || 0) + 16),
          }}
        >
          <div className="tg-tip-head">
            <span className="tg-chip" style={{ background: TIER_METADATA[hoveredNode.tier].color }}>{TIER_METADATA[hoveredNode.tier].label}</span>
            <span className={`tg-health health-${hoveredNode.health}`}>{hoveredNode.kind === 'device' ? healthLabel(hoveredNode.health) : siteStatusLabel(hoveredNode.status)}</span>
          </div>
          <div className="tg-tip-title">{hoveredNode.title}</div>
          {hoveredNode.kind === 'device'
            ? <div className="tg-tip-sub">{hoveredNode.alerts} active alert{hoveredNode.alerts === 1 ? '' : 's'} · {hoveredNode.incidents} ServiceNow</div>
            : <div className="tg-tip-sub">{hoveredNode.devices} device{hoveredNode.devices === 1 ? '' : 's'} · {hoveredNode.alerts} active alert{hoveredNode.alerts === 1 ? '' : 's'}</div>}
          <div className="tg-tip-hint">
            {hoveredNode.kind === 'site' ? 'Click for details · double-click to open site' : hoveredNode.kind === 'device' ? 'Click to open triage drawer · drag to pin' : 'Drag devices to pin them'}
          </div>
        </div>
      )}
      {hoveredEdgeObj && !hoveredNode && (
        <div
          className="tg-tooltip is-edge"
          style={{
            left: Math.min(size.width - 240, Math.max(8, pointer.x - (containerRef.current?.getBoundingClientRect().left || 0) + 16)),
            top: Math.max(8, pointer.y - (containerRef.current?.getBoundingClientRect().top || 0) + 16),
          }}
        >
          <div className="tg-tip-head">
            <span className="tg-chip is-rel">{hoveredEdgeObj.rel}</span>
            <span className={`tg-health health-${hoveredEdgeObj.status === 'nominal' ? 'healthy' : hoveredEdgeObj.status}`}>{hoveredEdgeObj.status === 'nominal' ? 'Nominal' : hoveredEdgeObj.status === 'warning' ? 'Degraded' : 'Critical'}</span>
          </div>
          <div className="tg-tip-title">{nodeById[hoveredEdgeObj.source]?.caption} → {nodeById[hoveredEdgeObj.target]?.caption}</div>
          <div className="tg-tip-sub">{hoveredEdgeObj.caption ? `${hoveredEdgeObj.caption} · ` : ''}{hoveredEdgeObj.detail}</div>
        </div>
      )}

      {/* Inspector */}
      {inspectedNode && (
        <aside className="tg-inspector" aria-label="Node properties">
          <div className="tg-insp-head">
            <span className="tg-chip" style={{ background: TIER_METADATA[inspectedNode.tier].color }}>{TIER_METADATA[inspectedNode.tier].label}</span>
            <button type="button" className="tg-icon-btn" onClick={() => setInspected(null)} aria-label="Close properties"><X size={14} /></button>
          </div>
          <h3 className="tg-insp-title">
            {inspectedNode.flag && <span className="tg-flag">{inspectedNode.flag}</span>}
            {inspectedNode.title}
          </h3>
          {inspectedNode.subtitle && <p className="tg-insp-sub">{inspectedNode.subtitle}</p>}
          <dl className="tg-props">
            {inspectedNode.kind !== 'device' ? (
              <>
                <dt>code</dt><dd className="mono">{inspectedNode.caption}</dd>
                <dt>region</dt><dd>{inspectedNode.region}</dd>
                <dt>status</dt><dd><span className={`tg-health health-${inspectedNode.health}`}>{siteStatusLabel(inspectedNode.status)}</span></dd>
                <dt>devices</dt><dd>{inspectedNode.devices}</dd>
                <dt>critical</dt><dd>{inspectedNode.critical}</dd>
                <dt>warning</dt><dd>{inspectedNode.warning}</dd>
                <dt>healthy</dt><dd>{inspectedNode.healthy}</dd>
                <dt>active alerts</dt><dd>{inspectedNode.alerts}</dd>
                <dt>tickets avoided</dt><dd>{inspectedNode.avoided}</dd>
                <dt>links</dt><dd>{adjacency[inspectedNode.id]?.size || 0}</dd>
              </>
            ) : (
              <>
                <dt>device_id</dt><dd className="mono">{inspectedNode.device.device_id || '—'}</dd>
                <dt>site</dt><dd>{inspectedNode.device.location || '—'}</dd>
                <dt>tier</dt><dd>{TIER_METADATA[inspectedNode.tier].label}</dd>
                <dt>health</dt><dd><span className={`tg-health health-${inspectedNode.health}`}>{healthLabel(inspectedNode.health)}</span></dd>
                <dt>active alerts</dt><dd>{inspectedNode.alerts}</dd>
                <dt>servicenow</dt><dd>{inspectedNode.incidents}</dd>
                <dt>total alerts</dt><dd>{inspectedNode.device.total_alerts ?? '—'}</dd>
                <dt>auto-resolving</dt><dd>{inspectedNode.device.auto_resolving ?? 0}</dd>
              </>
            )}
          </dl>
          {inspectedNode.kind === 'site' && (
            <button type="button" className="tg-primary-btn" onClick={() => onSelectSite(inspectedNode.id)}>
              <CornerDownRight size={14} /> Open site topology
            </button>
          )}
          {inspectedNode.kind === 'device' && (
            <button type="button" className="tg-primary-btn" onClick={() => onSelectDevice(inspectedNode.device)}>
              <Activity size={14} /> Open triage drawer
            </button>
          )}
          {inspectedNode.kind !== 'hub' && positions[inspectedNode.id]?.pinned && (
            <button type="button" className="tg-ghost-btn" onClick={() => unpin(inspectedNode.id)}>
              <PinOff size={13} /> Release pin
            </button>
          )}
        </aside>
      )}

      {/* Legend */}
      <div className="tg-legend" aria-label="Legend">
        {Object.values(TIER_METADATA).filter(t => counts[t.id]).map(t => (
          <span key={t.id} className="tg-legend-item">
            <span className="tg-legend-swatch" style={{ background: t.color }} />
            {t.label}
            <span className="tg-legend-count">{counts[t.id]}</span>
          </span>
        ))}
        <span className="tg-legend-sep" />
        <span className="tg-legend-item"><span className="tg-legend-ring" style={{ borderColor: HEALTH_COLOR.healthy }} />Healthy</span>
        <span className="tg-legend-item"><span className="tg-legend-ring" style={{ borderColor: HEALTH_COLOR.warning }} />Warning</span>
        <span className="tg-legend-item"><span className="tg-legend-ring" style={{ borderColor: HEALTH_COLOR.critical }} />Critical</span>
      </div>

      {/* Controls */}
      <div className="tg-controls" role="toolbar" aria-label="Graph controls">
        <button type="button" className="tg-icon-btn" onClick={() => zoomBy(1.25)} title="Zoom in"><ZoomIn size={15} /></button>
        <button type="button" className="tg-icon-btn" onClick={() => zoomBy(0.8)} title="Zoom out"><ZoomOut size={15} /></button>
        <button type="button" className="tg-icon-btn" onClick={() => fitToView()} title="Fit to view"><Scan size={15} /></button>
        <span className="tg-ctrl-sep" />
        <button type="button" className={`tg-icon-btn ${physicsOn ? 'is-on' : ''}`} onClick={() => setPhysicsOn(p => !p)} title={physicsOn ? 'Pause physics' : 'Resume physics'}>
          {physicsOn ? <Pause size={15} /> : <Play size={15} />}
        </button>
        <button type="button" className="tg-icon-btn" onClick={() => { didFitRef.current = false; setLayoutSeed(s => s + 1); }} title="Shuffle layout"><Shuffle size={15} /></button>
        <button type="button" className={`tg-icon-btn ${showLabels ? 'is-on' : ''}`} onClick={() => setShowLabels(s => !s)} title={showLabels ? 'Hide labels' : 'Show labels'}>
          <span className="tg-ctrl-text">Aa</span>
        </button>
        <span className="tg-ctrl-sep" />
        <button type="button" className="tg-icon-btn" onClick={() => setIsFullscreen(f => !f)} title={isFullscreen ? 'Exit full screen' : 'Full screen'}>
          {isFullscreen ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
        </button>
      </div>

      {/* Empty state */}
      {graph.nodes.length === 0 && (
        <div className="tg-empty">
          <AlertTriangle size={18} />
          <p>No devices to map yet. Topology appears once device telemetry arrives.</p>
        </div>
      )}
      {graph.nodes.length <= 1 && !isWan && (
        <div className="tg-empty">
          <Ticket size={18} />
          <p>No devices registered at {selectedSite}.</p>
          <button type="button" className="tg-ghost-btn" onClick={onReturnToWan}><ArrowLeft size={13} /> Back to global WAN</button>
        </div>
      )}
    </div>
  );
}
