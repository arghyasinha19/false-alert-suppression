import React, { useState, useEffect, useMemo } from 'react';
import {
  Layers, TrendingUp, Activity, AlertTriangle, ShieldCheck, Zap,
  ChevronDown, ChevronRight, Server, Clock, Filter, Fingerprint
} from 'lucide-react';
import {
  ComposedChart, Area, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  ResponsiveContainer, Legend, Cell
} from 'recharts';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8004';

const CATEGORY_COLORS = {
  'Backdated': '#2563eb',
  'Auto Resolving': '#059669',
  'Non-Auto Resolving': '#dc2626',
  'Uncertain': '#d97706',
};

const TOOLTIP_STYLE = {
  backgroundColor: '#ffffff',
  border: '1px solid rgba(0,0,0,0.08)',
  borderRadius: '10px',
  boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
  fontSize: '0.78rem',
  color: '#0f172a',
};

/* ── Mini Sparkline (SVG) ── */
function Sparkline({ data, width = 120, height = 32, color = '#2563eb' }) {
  if (!data || data.length < 2) return <span style={{ color: 'var(--text-tertiary)', fontSize: '0.75rem' }}>—</span>;
  const values = data.map(d => d.count || 0);
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = max - min || 1;
  const points = values.map((v, i) => {
    const x = (i / (values.length - 1)) * width;
    const y = height - ((v - min) / range) * (height - 4) - 2;
    return `${x},${y}`;
  }).join(' ');
  const areaPath = `M0,${height} L${points.split(' ').map((p, i) => {
    if (i === 0) return p;
    return ` L${p}`;
  }).join('')} L${width},${height} Z`;
  
  return (
    <svg width={width} height={height} style={{ display: 'block' }}>
      <defs>
        <linearGradient id={`spark-grad-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity={0.3} />
          <stop offset="100%" stopColor={color} stopOpacity={0.02} />
        </linearGradient>
      </defs>
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/* ── Category Mini Bar ── */
function CategoryMiniBar({ breakdown }) {
  if (!breakdown) return null;
  const total = Object.values(breakdown).reduce((s, v) => s + v, 0);
  if (total === 0) return null;
  return (
    <div className="category-mini-bar">
      {Object.entries(breakdown).map(([cat, count]) => {
        const pct = (count / total * 100);
        if (pct === 0) return null;
        return (
          <div
            key={cat}
            className="category-mini-bar-segment"
            style={{ width: `${pct}%`, background: CATEGORY_COLORS[cat] || '#94a3b8' }}
            title={`${cat}: ${count}`}
          />
        );
      })}
    </div>
  );
}

/* ── Template Text with highlighted placeholders ── */
function TemplateText({ text }) {
  if (!text) return <span>—</span>;
  const parts = text.split(/(\{[A-Z]+\})/g);
  return (
    <span className="pattern-template-text">
      {parts.map((part, i) =>
        part.match(/^\{[A-Z]+\}$/)
          ? <span key={i} className="pattern-var-badge">{part}</span>
          : <span key={i}>{part}</span>
      )}
    </span>
  );
}

/* ── Mock data generator ── */
function generateMockPatterns() {
  const templates = [
    { template: 'AP {DEVICE} has flapped', category: 'Auto Resolving', count: 14 },
    { template: 'This network device {FQDN} is unreachable from Cisco Catalyst Center. The device role is {DEVICE}.', category: 'Non-Auto Resolving', count: 11 },
    { template: 'BGP peer {IP} on {DEVICE} is down', category: 'Non-Auto Resolving', count: 8 },
    { template: 'Device {DEVICE} CPU utilization is at {PCT}', category: 'Auto Resolving', count: 7 },
    { template: 'Interface {IFACE} on {DEVICE} has gone down', category: 'Auto Resolving', count: 6 },
    { template: 'OSPF neighbor {IP} on {DEVICE} is down', category: 'Non-Auto Resolving', count: 5 },
    { template: 'Memory utilization is consistently above {PCT}', category: 'Auto Resolving', count: 4 },
    { template: 'Power Supply {NUM} on {DEVICE} has failed', category: 'Non-Auto Resolving', count: 3 },
    { template: 'AP {DEVICE} is unreachable', category: 'Non-Auto Resolving', count: 2 },
  ];

  const devices = [
    'UK-MAL-DEV-AP02', 'Core-Router-01', 'Access-Switch-05',
    'Switch-12', 'US-NY-HQ-AP05', 'SG-SIN-FW01', 'UK-LON-SW01',
    'US-CHI-RT03', 'DE-FRA-AP01', 'JP-TKY-SW02'
  ];

  const now = Date.now();
  const patterns = templates.map((t, idx) => {
    const hourly = [];
    for (let h = 0; h < 48; h++) {
      const ts = new Date(now - h * 3600000);
      const count = Math.random() < 0.4 ? 0 : Math.floor(Math.random() * (t.count / 3 + 1));
      if (count > 0) {
        hourly.push({ time: ts.toISOString().slice(0, 13) + ':00', count });
      }
    }
    hourly.reverse();

    const selectedDevices = devices.slice(idx % devices.length, idx % devices.length + Math.min(3, t.count));
    const categoryBreakdown = {};
    categoryBreakdown[t.category] = Math.ceil(t.count * 0.6);
    categoryBreakdown['Backdated'] = Math.floor(t.count * 0.2);
    categoryBreakdown['Uncertain'] = t.count - categoryBreakdown[t.category] - categoryBreakdown['Backdated'];

    const suppressed = (categoryBreakdown['Backdated'] || 0) + (categoryBreakdown['Auto Resolving'] || 0);
    
    return {
      cluster_id: idx,
      template: t.template,
      alert_count: t.count,
      devices: selectedDevices,
      category_breakdown: categoryBreakdown,
      suppression_rate: t.count > 0 ? Math.round(suppressed / t.count * 100 * 10) / 10 : 0,
      time_span: {
        first: new Date(now - 168 * 3600000).toISOString(),
        last: new Date(now - 1800000).toISOString(),
      },
      hourly_distribution: hourly,
      noise: false,
      alerts: [],
    };
  });

  // Volume series
  const volume = [];
  for (let h = 0; h < 48; h++) {
    const ts = new Date(now - h * 3600000);
    volume.push({
      time: ts.toISOString().slice(0, 13) + ':00',
      Backdated: Math.floor(Math.random() * 3),
      'Auto Resolving': Math.floor(Math.random() * 5),
      'Non-Auto Resolving': Math.floor(Math.random() * 3),
      Uncertain: Math.floor(Math.random() * 2),
      total: 0,
      cumulative: 0,
    });
  }
  volume.reverse();
  let cumulative = 0;
  volume.forEach(v => {
    v.total = v.Backdated + v['Auto Resolving'] + v['Non-Auto Resolving'] + v.Uncertain;
    cumulative += v.total;
    v.cumulative = cumulative;
  });

  return { patterns, volume_series: volume, total_alerts: 60, total_patterns: patterns.length, noise_count: 0 };
}


/* ============================================================================
   Main Component
   ============================================================================ */
export default function AlertPatterns() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [granularity, setGranularity] = useState('hourly');
  const [selectedCluster, setSelectedCluster] = useState(null);
  const [expandedRows, setExpandedRows] = useState(new Set());

  // Fetch from API
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE}/api/alerts/patterns?granularity=${granularity}`);
        const json = await res.json();
        if (json.patterns && json.patterns.length > 0) {
          setData(json);
        } else {
          setData(generateMockPatterns());
        }
      } catch {
        setData(generateMockPatterns());
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [granularity]);

  const patterns = useMemo(() => {
    if (!data) return [];
    return (data.patterns || []).filter(p => !p.noise).sort((a, b) => b.alert_count - a.alert_count);
  }, [data]);

  const noisePatterns = useMemo(() => {
    if (!data) return [];
    return (data.patterns || []).filter(p => p.noise);
  }, [data]);

  const volumeSeries = useMemo(() => {
    if (!data) return [];
    if (selectedCluster !== null) {
      const cluster = (data.patterns || []).find(p => p.cluster_id === selectedCluster);
      if (cluster && cluster.hourly_distribution) {
        return cluster.hourly_distribution.map(d => ({
          time: d.time,
          total: d.count,
          cumulative: 0,
        }));
      }
    }
    return data.volume_series || [];
  }, [data, selectedCluster]);

  const toggleExpand = (id) => {
    setExpandedRows(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const getDominantCategory = (breakdown) => {
    if (!breakdown) return 'Uncertain';
    let max = 0, cat = 'Uncertain';
    for (const [k, v] of Object.entries(breakdown)) {
      if (v > max) { max = v; cat = k; }
    }
    return cat;
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '400px', color: 'var(--text-tertiary)' }}>
        <Activity size={20} className="spin" style={{ marginRight: '0.5rem' }} />
        Loading pattern analysis…
      </div>
    );
  }

  return (
    <>
      {/* KPI Summary Cards */}
      <div className="kpi-grid" style={{ marginBottom: '1.5rem' }}>
        <div className="glass-card kpi-card highlight-blue">
          <div className="kpi-icon blue"><Layers size={20} /></div>
          <div className="kpi-content">
            <h3>Discovered Patterns</h3>
            <p className="value">{data?.total_patterns || 0}</p>
            <p className="sub-value">unique alert templates</p>
          </div>
        </div>
        <div className="glass-card kpi-card highlight-green">
          <div className="kpi-icon green"><Fingerprint size={20} /></div>
          <div className="kpi-content">
            <h3>Total Alerts Clustered</h3>
            <p className="value">{data?.total_alerts || 0}</p>
            <p className="sub-value">across all patterns</p>
          </div>
        </div>
        <div className="glass-card kpi-card highlight-cyan">
          <div className="kpi-icon cyan"><ShieldCheck size={20} /></div>
          <div className="kpi-content">
            <h3>Top Pattern</h3>
            <p className="value">{patterns[0]?.alert_count || 0}</p>
            <p className="sub-value">alerts in largest cluster</p>
          </div>
        </div>
        <div className="glass-card kpi-card highlight-red">
          <div className="kpi-icon red"><AlertTriangle size={20} /></div>
          <div className="kpi-content">
            <h3>Unclustered</h3>
            <p className="value">{data?.noise_count || 0}</p>
            <p className="sub-value">anomalous / one-off alerts</p>
          </div>
        </div>
      </div>

      {/* Alerts vs Volume Chart */}
      <div className="glass-card chart-card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <TrendingUp size={16} />
            {selectedCluster !== null ? 'Cluster Volume Over Time' : 'Alerts vs Volume Over Time'}
            {selectedCluster !== null && (
              <button
                className="filter-pill active"
                onClick={() => setSelectedCluster(null)}
                style={{ marginLeft: '0.5rem', fontSize: '0.7rem' }}
              >
                ✕ Clear filter
              </button>
            )}
          </h3>
          <div className="granularity-toggle">
            {['hourly', 'daily', 'weekly'].map(g => (
              <button
                key={g}
                className={`granularity-btn ${granularity === g ? 'active' : ''}`}
                onClick={() => setGranularity(g)}
              >
                {g.charAt(0).toUpperCase() + g.slice(1)}
              </button>
            ))}
          </div>
        </div>
        <div style={{ height: '300px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={volumeSeries} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="gradBackdatedP" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2563eb" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#2563eb" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="gradAutoP" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#059669" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#059669" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="gradNonAutoP" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#dc2626" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#dc2626" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="gradUncertainP" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#d97706" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#d97706" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
              <XAxis
                dataKey="time"
                stroke="#94a3b8"
                tick={{ fontSize: 10, fill: '#94a3b8' }}
                minTickGap={45}
                tickFormatter={v => {
                  try {
                    const d = new Date(v);
                    if (isNaN(d.getTime())) return v;
                    if (granularity === 'daily') {
                      return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
                    }
                    if (granularity === 'weekly') {
                      return v;
                    }
                    const timeStr = d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', hour12: true });
                    const dateStr = d.toLocaleDateString([], { month: 'short', day: 'numeric' });
                    return `${dateStr}, ${timeStr}`;
                  } catch {
                    return v;
                  }
                }}
              />
              <YAxis yAxisId="left" stroke="#94a3b8" tick={{ fontSize: 10, fill: '#94a3b8' }} />
              {selectedCluster === null && (
                <YAxis yAxisId="right" orientation="right" stroke="#7c3aed" tick={{ fontSize: 10, fill: '#7c3aed' }} />
              )}
              <RechartsTooltip
                contentStyle={TOOLTIP_STYLE}
                labelFormatter={label => {
                  try {
                    const d = new Date(label);
                    if (isNaN(d.getTime())) return label;
                    return d.toLocaleString([], {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                      hour: 'numeric',
                      minute: '2-digit',
                      hour12: true
                    });
                  } catch {
                    return label;
                  }
                }}
              />
              <Legend verticalAlign="top" iconType="circle" iconSize={8} wrapperStyle={{ fontSize: '0.72rem', paddingBottom: '8px' }} />

              {selectedCluster === null ? (
                <>
                  <Area yAxisId="left" type="monotone" dataKey="Backdated" stackId="1" stroke="#2563eb" fill="url(#gradBackdatedP)" strokeWidth={2} />
                  <Area yAxisId="left" type="monotone" dataKey="Auto Resolving" stackId="1" stroke="#059669" fill="url(#gradAutoP)" strokeWidth={2} />
                  <Area yAxisId="left" type="monotone" dataKey="Non-Auto Resolving" stackId="1" stroke="#dc2626" fill="url(#gradNonAutoP)" strokeWidth={2} />
                  <Area yAxisId="left" type="monotone" dataKey="Uncertain" stackId="1" stroke="#d97706" fill="url(#gradUncertainP)" strokeWidth={2} />
                  <Line yAxisId="right" type="monotone" dataKey="cumulative" stroke="#7c3aed" strokeWidth={2.5} dot={false} strokeDasharray="6 3" name="Cumulative Volume" />
                </>
              ) : (
                <Area yAxisId="left" type="monotone" dataKey="total" stroke="#2563eb" fill="url(#gradBackdatedP)" strokeWidth={2} name="Cluster Alerts" />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Pattern Cluster Cards */}
      <p className="section-title"><Fingerprint size={14} /> Discovered Alert Patterns ({patterns.length})</p>
      <div className="pattern-cluster-grid">
        {patterns.map((p, idx) => {
          const dominant = getDominantCategory(p.category_breakdown);
          const isSelected = selectedCluster === p.cluster_id;
          return (
            <div
              key={p.cluster_id}
              className={`glass-card pattern-card ${isSelected ? 'selected' : ''} ${idx < 3 ? 'top-pattern' : ''}`}
              onClick={() => setSelectedCluster(isSelected ? null : p.cluster_id)}
              style={{ '--accent-bar-color': CATEGORY_COLORS[dominant] || '#94a3b8' }}
            >
              {idx < 3 && <div className="pattern-rank-badge">#{idx + 1}</div>}
              <div className="pattern-card-header">
                <span className={`badge ${dominant.toLowerCase().replace(/[\s/]/g, '-')}`}>{dominant}</span>
                <span className="pattern-count-badge">{p.alert_count} alerts</span>
              </div>
              <div className="pattern-card-template">
                <TemplateText text={p.template} />
              </div>
              <div className="pattern-card-meta">
                <div className="pattern-meta-item">
                  <Server size={12} />
                  <span>{p.devices?.length || 0} devices</span>
                </div>
                <div className="pattern-meta-item">
                  <ShieldCheck size={12} />
                  <span>{p.suppression_rate}% suppressed</span>
                </div>
              </div>
              <div className="pattern-card-sparkline">
                <Sparkline
                  data={p.hourly_distribution}
                  width={160}
                  height={28}
                  color={CATEGORY_COLORS[dominant] || '#2563eb'}
                />
              </div>
              <CategoryMiniBar breakdown={p.category_breakdown} />
            </div>
          );
        })}
      </div>

      {/* Noise / Unclustered section */}
      {noisePatterns.length > 0 && (
        <>
          <p className="section-title" style={{ marginTop: '2rem' }}>
            <Zap size={14} /> Unclustered Alerts ({noisePatterns.reduce((s, p) => s + p.alert_count, 0)})
          </p>
          <div className="pattern-noise-section">
            <div className="glass-card" style={{ padding: '1rem 1.25rem' }}>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                These alerts did not match any discovered pattern cluster (HDBSCAN noise label).
              </p>
              {noisePatterns.map(p => (
                <div key={p.cluster_id} className="noise-alert-row">
                  <TemplateText text={p.template} />
                  <span className="badge" style={{ marginLeft: '0.5rem' }}>{p.alert_count}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* Pattern Detail Table */}
      <div className="glass-card table-card" style={{ marginTop: '1.5rem' }}>
        <h3><Layers size={16} /> Pattern Detail Table</h3>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table" style={{ minWidth: '1100px' }}>
            <thead>
              <tr>
                <th style={{ width: '40px' }}></th>
                <th style={{ width: '380px' }}>Template Pattern</th>
                <th style={{ width: '80px' }}>Count</th>
                <th style={{ width: '100px' }}>Devices</th>
                <th style={{ width: '180px' }}>Category Breakdown</th>
                <th style={{ width: '100px' }}>Suppression</th>
                <th style={{ width: '140px' }}>Time Span</th>
                <th style={{ width: '140px' }}>Distribution</th>
              </tr>
            </thead>
            <tbody>
              {patterns.map((p) => {
                const isExpanded = expandedRows.has(p.cluster_id);
                return (
                  <React.Fragment key={p.cluster_id}>
                    <tr
                      className={`pattern-detail-row ${isExpanded ? 'expanded' : ''}`}
                      onClick={() => toggleExpand(p.cluster_id)}
                      style={{ cursor: 'pointer' }}
                    >
                      <td>
                        {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      </td>
                      <td>
                        <TemplateText text={p.template} />
                      </td>
                      <td style={{ fontWeight: 700 }}>{p.alert_count}</td>
                      <td>{p.devices?.length || 0}</td>
                      <td><CategoryMiniBar breakdown={p.category_breakdown} /></td>
                      <td>
                        <span style={{ color: p.suppression_rate > 50 ? 'var(--accent-green)' : 'var(--accent-red)', fontWeight: 600 }}>
                          {p.suppression_rate}%
                        </span>
                      </td>
                      <td style={{ fontSize: '0.74rem', color: 'var(--text-tertiary)' }}>
                        {p.time_span?.first ? new Date(p.time_span.first).toLocaleDateString() : '—'}
                        {' → '}
                        {p.time_span?.last ? new Date(p.time_span.last).toLocaleDateString() : '—'}
                      </td>
                      <td>
                        <Sparkline
                          data={p.hourly_distribution}
                          width={120}
                          height={24}
                          color={CATEGORY_COLORS[getDominantCategory(p.category_breakdown)] || '#2563eb'}
                        />
                      </td>
                    </tr>
                    {isExpanded && (
                      <tr className="pattern-expanded-content">
                        <td colSpan="8">
                          <div className="pattern-expanded-inner">
                            <div className="pattern-expanded-devices">
                              <strong>Affected Devices:</strong>
                              {(p.devices || []).map(d => (
                                <span key={d} className="badge" style={{ marginLeft: '0.4rem', marginBottom: '0.25rem' }}>{d}</span>
                              ))}
                            </div>
                            {p.alerts && p.alerts.length > 0 && (
                              <div className="pattern-expanded-alerts">
                                <strong>Sample Alerts:</strong>
                                <table className="data-table" style={{ marginTop: '0.5rem', fontSize: '0.76rem' }}>
                                  <thead>
                                    <tr>
                                      <th>Event ID</th>
                                      <th>Device</th>
                                      <th>Severity</th>
                                      <th>Issue</th>
                                      <th>Timestamp</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {p.alerts.slice(0, 10).map((alert, i) => (
                                      <tr key={i}>
                                        <td>{alert.event_id || '—'}</td>
                                        <td>{alert.device_name || '—'}</td>
                                        <td><span className={`badge severity-${alert.severity || 3}`}>{alert.severity || '—'}</span></td>
                                        <td style={{ maxWidth: '250px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{alert.issue_name || alert.issue_details || '—'}</td>
                                        <td style={{ color: 'var(--text-tertiary)' }}>
                                          {alert.timestamp ? new Date(typeof alert.timestamp === 'number' ? (alert.timestamp > 1e12 ? alert.timestamp : alert.timestamp * 1000) : alert.timestamp).toLocaleString() : '—'}
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                                {p.alerts.length > 10 && (
                                  <p style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)', marginTop: '0.5rem' }}>
                                    … and {p.alerts.length - 10} more alerts
                                  </p>
                                )}
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
              {patterns.length === 0 && (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-tertiary)' }}>
                    No patterns discovered yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
