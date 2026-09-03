import React, { useState, useMemo, useCallback, useRef } from 'react';
import {
  BarChart3, AlertTriangle, CheckCircle, CheckCircle2, Clock, ShieldCheck, ShieldAlert,
  Activity, Server, TrendingDown, TrendingUp, Ticket, Ban, Filter,
  Zap, Award, FileText, RotateCcw, MessageSquarePlus, PlusCircle, X
} from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend
} from 'recharts';

const COLORS = ['#2563eb', '#059669', '#dc2626', '#d97706', '#7c3aed', '#0891b2'];
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

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8004';

function parseTimestamp(ts) {
  if (ts === null || ts === undefined || ts === '') return null;
  if (typeof ts === 'number') {
    if (isNaN(ts)) return null;
    const ms = ts > 1e12 ? ts : ts * 1000;
    const d = new Date(ms);
    return isNaN(d.getTime()) ? null : d;
  }
  if (typeof ts === 'string') {
    const trimmed = ts.trim();
    const asNum = Number(trimmed);
    if (trimmed.length > 0 && !isNaN(asNum) && isFinite(asNum)) {
      const ms = asNum > 1e12 ? asNum : asNum * 1000;
      const d = new Date(ms);
      if (!isNaN(d.getTime())) return d;
    }
    const d = new Date(trimmed);
    return isNaN(d.getTime()) ? null : d;
  }
  return null;
}

function formatTimestamp(ts, fallback = '—') {
  const d = parseTimestamp(ts);
  return d ? d.toLocaleString() : fallback;
}

function generateMockData() {
  const devices = [
    'UK-MAL-DEV-AP02', 'Core-Router-01', 'Access-Switch-05',
    'Switch-12', 'Dist-Router', 'Core-Switch-02', 'US-NY-HQ-AP05',
    'SG-SIN-FW01', 'UK-LON-SW01', 'US-CHI-RT03', 'DE-FRA-AP01', 'JP-TKY-SW02'
  ];
  const categories = ['Auto resolving', 'Non-Auto Resolving', 'Auto resolving', 'Auto resolving', 'Non-Auto Resolving'];
  const issueNames = [
    'AP has flapped', 'BGP Peer is Down', 'High CPU Utilization',
    'Interface State Down', 'OSPF Neighbor Down', 'High Memory Utilization',
    'Power Supply Failure', 'AP is Offline'
  ];
  const severities = [1, 2, 3, 3, 1, 2, 1, 1];
  const alerts = [];
  const now = Date.now();

  for (let i = 0; i < 48; i++) {
    const deviceIdx = i % devices.length;
    const catIdx = i % categories.length;
    const issueIdx = i % issueNames.length;
    const isBackdated = i % 7 === 0;
    const predicted = isBackdated ? null : categories[catIdx];
    const ts = new Date(now - (i * 1800000 + Math.random() * 600000)).toISOString();
    const snowAction = predicted === 'Non-Auto Resolving'
      ? (i % 3 === 0 ? 'incident_created' : i % 3 === 1 ? 'comment_appended' : 'incident_reopened')
      : null;
    const snowInc = snowAction ? `INC00${12345 + i}` : null;

    alerts.push({
      alert_details: {
        event_id: `EVT-${String(i + 1).padStart(3, '0')}`,
        device_name: devices[deviceIdx],
        device_id: `dev-${String(deviceIdx + 1).padStart(3, '0')}`,
        timestamp: ts,
        severity: severities[issueIdx],
        category: severities[issueIdx] <= 1 ? 'ERROR' : 'WARN',
        status: i % 5 === 0 ? 'resolved' : 'active',
        issue_name: issueNames[issueIdx],
        issue_details: `${issueNames[issueIdx]} detected on ${devices[deviceIdx]}`,
      },
      results: {
        agent_1: { data: { is_backdated: isBackdated }, status: 'success' },
        ...(isBackdated ? {} : {
          agent_2: { data: { predicted_category: predicted, confidence: (0.65 + Math.random() * 0.3).toFixed(2) }, status: 'success' },
        }),
        ...(predicted === 'Auto resolving' ? { agent_3: { data: { queue_status: 'delayed' }, status: 'success' } } : {}),
        ...(snowAction ? { agent_4: { data: { action: snowAction, incident: snowInc }, status: 'success' } } : {}),
      },
      live_snow_status: snowAction === 'incident_created' ? 'New' : snowAction === 'comment_appended' ? 'In Progress' : snowAction === 'incident_reopened' ? 'Re-opened' : null,
    });
  }
  return alerts;
}

/* ── Resizable column hook ── */
function useResizableColumns() {
  const tableRef = useRef(null);
  const startX = useRef(0);
  const startWidth = useRef(0);
  const activeCol = useRef(null);

  const onMouseDown = useCallback((e, colIndex) => {
    e.preventDefault();
    const table = tableRef.current;
    if (!table) return;
    const th = table.querySelectorAll('thead th')[colIndex];
    if (!th) return;
    startX.current = e.clientX;
    startWidth.current = th.offsetWidth;
    activeCol.current = th;

    const onMouseMove = (ev) => {
      const diff = ev.clientX - startX.current;
      const newWidth = Math.max(60, startWidth.current + diff);
      activeCol.current.style.width = newWidth + 'px';
      activeCol.current.style.minWidth = newWidth + 'px';
    };
    const onMouseUp = () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      activeCol.current = null;
    };
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  }, []);

  return { tableRef, onMouseDown };
}

/* ── Event Detail Modal ── */
function EventDetailModal({ alert, onClose }) {
  if (!alert) return null;
  const details = alert.alert_details || {};
  const results = alert.results || {};
  const isBackdated = results.agent_1?.data?.is_backdated;
  const mlCategory = isBackdated ? 'Backdated' : (results.agent_2?.data?.predicted_category || 'Unknown');
  const confidence = results.agent_2?.data?.confidence;
  const queueStatus = results.agent_3?.data?.queue_status;
  const snowAction = results.agent_4?.data?.action;
  const snowInc = results.agent_4?.data?.incident;
  const liveStatus = alert.live_snow_status;

  const formatTs = (ts) => formatTimestamp(ts);

  return (
    <div className="event-modal-overlay" onClick={onClose}>
      <div className="event-modal" onClick={e => e.stopPropagation()}>
        <div className="event-modal-header">
          <h2><Zap size={18} style={{ color: 'var(--accent-blue)' }} /> {details.event_id || 'Event Details'}</h2>
          <button className="event-modal-close" onClick={onClose}><X size={18} /></button>
        </div>
        <div className="event-modal-body">
          {/* Alert Information */}
          <div className="event-modal-section">
            <h3>Alert Information</h3>
            <div className="event-modal-grid">
              <div className="event-modal-field">
                <span className="label">Event ID</span>
                <span className="value">{details.event_id || '—'}</span>
              </div>
              <div className="event-modal-field">
                <span className="label">Device Name</span>
                <span className="value">{details.device_name || '—'}</span>
              </div>
              <div className="event-modal-field">
                <span className="label">Device ID</span>
                <span className="value">{details.device_id || '—'}</span>
              </div>
              <div className="event-modal-field">
                <span className="label">Severity</span>
                <span className="value"><span className={`badge severity-${details.severity || 3}`}>{details.severity || '—'}</span></span>
              </div>
              <div className="event-modal-field">
                <span className="label">Category</span>
                <span className="value">{details.category || '—'}</span>
              </div>
              <div className="event-modal-field">
                <span className="label">Status</span>
                <span className="value"><span className={`badge ${details.status === 'resolved' ? 'auto-resolving' : 'non-auto-resolving'}`}>{details.status || '—'}</span></span>
              </div>
              <div className="event-modal-field">
                <span className="label">Timestamp</span>
                <span className="value">{formatTs(details.timestamp || details.raw_timestamp)}</span>
              </div>
              <div className="event-modal-field">
                <span className="label">Issue Name</span>
                <span className="value">{details.issue_name || '—'}</span>
              </div>
            </div>
            {details.issue_details && (
              <div className="event-modal-field full-width">
                <span className="label">Issue Details</span>
                <span className="value">{details.issue_details}</span>
              </div>
            )}
          </div>

          {/* Pipeline Results */}
          <div className="event-modal-section">
            <h3>Pipeline Results</h3>
            <div className="event-modal-pipeline">
              {/* Agent 1 */}
              <div className={`pipeline-step ${isBackdated ? 'backdated' : 'fresh'}`}>
                <div className="pipeline-step-header">
                  <span className="pipeline-step-num">1</span>
                  <span className="pipeline-step-title">Backdated Check</span>
                  <span className={`badge ${isBackdated ? 'backdated' : 'auto-resolving'}`}>{isBackdated ? 'Suppressed' : 'Fresh'}</span>
                </div>
                <p>Alert was {isBackdated ? 'identified as backdated and suppressed from further processing.' : 'identified as a fresh alert and passed to classification.'}</p>
              </div>

              {/* Agent 2 */}
              {!isBackdated && (
                <div className={`pipeline-step ${mlCategory.toLowerCase().replace(/[\s/]/g, '-')}`}>
                  <div className="pipeline-step-header">
                    <span className="pipeline-step-num">2</span>
                    <span className="pipeline-step-title">ML Classification</span>
                    <span className={`badge ${mlCategory.toLowerCase().replace(/[\s/]/g, '-')}`}>{mlCategory}</span>
                  </div>
                  <p>Predicted category: <strong>{mlCategory}</strong>{confidence && <> with confidence <strong>{confidence}</strong></>}.</p>
                </div>
              )}

              {/* Agent 3 */}
              {queueStatus && (
                <div className="pipeline-step queued">
                  <div className="pipeline-step-header">
                    <span className="pipeline-step-num">3</span>
                    <span className="pipeline-step-title">Queue / Re-check</span>
                    <span className="badge delayed">Queued</span>
                  </div>
                  <p>Alert queued for delayed re-check. Queue status: <strong>{queueStatus}</strong>.</p>
                </div>
              )}

              {/* Agent 4 */}
              {snowAction && (
                <div className="pipeline-step snow">
                  <div className="pipeline-step-header">
                    <span className="pipeline-step-num">4</span>
                    <span className="pipeline-step-title">ServiceNow</span>
                    <span className={`badge ${snowAction === 'incident_created' ? 'snow-new' : snowAction === 'incident_reopened' ? 'snow-reopen' : 'snow-comment'}`}>{snowAction.replace(/_/g, ' ')}</span>
                  </div>
                  <div className="event-modal-grid">
                    <div className="event-modal-field">
                      <span className="label">Action</span>
                      <span className="value">{snowAction.replace(/_/g, ' ')}</span>
                    </div>
                    {snowInc && (
                      <div className="event-modal-field">
                        <span className="label">Incident #</span>
                        <span className="value" style={{ color: 'var(--accent-blue)', fontWeight: 700 }}>{snowInc}</span>
                      </div>
                    )}
                    {liveStatus && (
                      <div className="event-modal-field">
                        <span className="label">Live Status</span>
                        <span className="value">{liveStatus}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Raw JSON */}
          <div className="event-modal-section">
            <h3>Raw Event Data</h3>
            <pre className="event-modal-raw">{JSON.stringify(alert, null, 2)}</pre>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function FalseAlertMetrics({ alerts: rawAlerts, onRefresh }) {
  const [deviceFilter, setDeviceFilter] = useState('ALL');
  const [timeRange, setTimeRange] = useState('ALL');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [simulating, setSimulating] = useState(false);

  const { tableRef: traceTableRef, onMouseDown: onTraceColResize } = useResizableColumns();

  const alerts = useMemo(() => {
    if (rawAlerts && rawAlerts.length > 0) return rawAlerts;
    return generateMockData();
  }, [rawAlerts]);

  const handleSimulate = async (count = 5) => {
    setSimulating(true);
    try {
      await fetch(`${API_BASE}/api/alerts/simulate?count=${count}`, { method: 'POST' });
      if (onRefresh) {
        await onRefresh();
      }
    } catch (e) {
      console.error('Failed to simulate alerts:', e);
    } finally {
      setSimulating(false);
    }
  };

  const deviceNames = useMemo(() => {
    const names = new Set();
    alerts.forEach(a => { const n = a.alert_details?.device_name; if (n) names.add(n); });
    return ['ALL', ...Array.from(names).sort()];
  }, [alerts]);

  const filteredAlerts = useMemo(() => {
    let result = alerts;
    if (deviceFilter !== 'ALL') result = result.filter(a => a.alert_details?.device_name === deviceFilter);
    if (timeRange !== 'ALL') {
      const now = Date.now();
      const ranges = { '24H': 86400000, '7D': 604800000, '30D': 2592000000 };
      const cutoff = now - (ranges[timeRange] || 0);
      result = result.filter(a => {
        const ts = a.alert_details?.timestamp || a.alert_details?.raw_timestamp;
        const d = parseTimestamp(ts);
        if (!d) return true;
        return d.getTime() >= cutoff;
      });
    }
    if (categoryFilter !== 'ALL') {
      result = result.filter(a => {
        const isBackdated = a.results?.agent_1?.data?.is_backdated;
        if (categoryFilter === 'BACKDATED') return isBackdated;
        if (isBackdated) return false;
        const predicted = (a.results?.agent_2?.data?.predicted_category || '').toLowerCase();
        if (categoryFilter === 'AUTO') return predicted === 'auto resolving';
        if (categoryFilter === 'NON_AUTO') return predicted === 'non-auto resolving';
        if (categoryFilter === 'UNCERTAIN') return predicted !== 'auto resolving' && predicted !== 'non-auto resolving';
        return true;
      });
    }
    return result;
  }, [alerts, deviceFilter, timeRange, categoryFilter]);

  // KPIs & SNOW details & Device Ranking
  const { kpi, snowDetails, deviceRanking } = useMemo(() => {
    const total = filteredAlerts.length;
    let backdated = 0, autoResolving = 0, nonAutoResolving = 0, uncertain = 0;
    let snowCreated = 0, snowAppended = 0, snowReopened = 0;
    const deviceStats = {};
    const hourlyBuckets = {};
    const snowNewDevices = [];
    const snowReopenDevices = [];

    filteredAlerts.forEach(a => {
      const isBackdated = a.results?.agent_1?.data?.is_backdated;
      const predicted = (a.results?.agent_2?.data?.predicted_category || '').toLowerCase();
      const snowAction = a.results?.agent_4?.data?.action || '';
      const snowInc = a.results?.agent_4?.data?.incident || '';
      const device = a.alert_details?.device_name || a.alert_details?.device || 'Unknown';

      if (isBackdated) backdated++;
      else if (predicted === 'auto resolving') autoResolving++;
      else if (predicted === 'non-auto resolving') nonAutoResolving++;
      else uncertain++;

      if (snowAction === 'incident_created') {
        snowCreated++;
        snowNewDevices.push({ device, incident: snowInc, timestamp: a.alert_details?.timestamp });
      }
      if (snowAction === 'comment_appended') snowAppended++;
      if (snowAction === 'incident_reopened') {
        snowReopened++;
        snowReopenDevices.push({ device, incident: snowInc, timestamp: a.alert_details?.timestamp });
      }

      // Device stats
      if (!deviceStats[device]) {
        deviceStats[device] = { device, genuine: 0, false: 0, autoResolving: 0, uncertain: 0, total: 0, snowCreated: 0, snowReopened: 0 };
      }
      deviceStats[device].total++;
      if (isBackdated) deviceStats[device].false++;
      else if (predicted === 'auto resolving') deviceStats[device].autoResolving++;
      else if (predicted === 'non-auto resolving') deviceStats[device].genuine++;
      else deviceStats[device].uncertain++;
      if (snowAction === 'incident_created') deviceStats[device].snowCreated++;
      if (snowAction === 'incident_reopened') deviceStats[device].snowReopened++;

      const ts = a.alert_details?.timestamp || a.alert_details?.raw_timestamp;
      const d = parseTimestamp(ts);
      if (d) {
        // Round down to the local hour boundary
        const bucketDate = new Date(d.getFullYear(), d.getMonth(), d.getDate(), d.getHours(), 0, 0, 0);
        const hourKey = bucketDate.getTime();
        if (!hourlyBuckets[hourKey]) {
          hourlyBuckets[hourKey] = {
            time: hourKey,
            Backdated: 0,
            'Auto Resolving': 0,
            'Non-Auto Resolving': 0,
            Uncertain: 0,
          };
        }
        if (isBackdated) hourlyBuckets[hourKey].Backdated++;
        else if (predicted === 'auto resolving') hourlyBuckets[hourKey]['Auto Resolving']++;
        else if (predicted === 'non-auto resolving') hourlyBuckets[hourKey]['Non-Auto Resolving']++;
        else hourlyBuckets[hourKey].Uncertain++;
      }
    });

    const suppressionRate = total > 0 ? ((backdated + autoResolving) / total * 100).toFixed(1) : 0;
    const ticketsAvoided = backdated + autoResolving;
    const hourlySeries = Object.values(hourlyBuckets).sort((a, b) => a.time - b.time);

    // Device ranking — sort by genuine alerts (non-auto-resolving) descending
    const ranking = Object.values(deviceStats).sort((a, b) => b.genuine - a.genuine || b.total - a.total);
    const maxTotal = Math.max(...ranking.map(d => d.total), 1);

    return {
      kpi: { total, backdated, autoResolving, nonAutoResolving, uncertain, suppressionRate, ticketsAvoided, snowCreated, snowAppended, snowReopened, totalSnowTickets: snowCreated + snowAppended + snowReopened, hourlySeries },
      snowDetails: { newDevices: snowNewDevices, reopenDevices: snowReopenDevices },
      deviceRanking: ranking.map((d, i) => ({ ...d, rank: i + 1, pct: Math.round(d.total / maxTotal * 100) })),
    };
  }, [filteredAlerts]);

  const pieData = [
    { name: 'Backdated', value: kpi.backdated },
    { name: 'Auto Resolving', value: kpi.autoResolving },
    { name: 'Non-Auto Resolving', value: kpi.nonAutoResolving },
    { name: 'Uncertain', value: kpi.uncertain },
  ].filter(d => d.value > 0);

  const getRankClass = (rank) => rank === 1 ? 'gold' : rank === 2 ? 'silver' : rank === 3 ? 'bronze' : 'default';

  const getBarColor = (d) => {
    const auto = d.autoResolving || 0;
    const unc = d.uncertain || 0;
    const gen = d.genuine || 0;
    const f = d.false || 0;

    if (auto >= gen && auto >= unc && auto > 0) return 'var(--accent-green)';
    if (unc >= gen && unc >= auto && unc > 0) return 'var(--accent-blue)';
    if (gen > 0 && gen >= auto && gen >= unc) return 'var(--accent-red)';
    if (f > 0) return 'var(--accent-blue)';
    return 'var(--accent-blue)';
  };

  const TRACE_COLUMNS = [
    { key: 'event_id', label: 'Event ID', width: '220px', minWidth: '160px' },
    { key: 'device', label: 'Device', width: '180px', minWidth: '130px' },
    { key: 'severity', label: 'Severity', width: '85px', minWidth: '70px' },
    { key: 'issue', label: 'Issue', width: '200px', minWidth: '140px' },
    { key: 'timestamp', label: 'Timestamp', width: '160px', minWidth: '130px' },
    { key: 'agent1', label: 'Agent 1', width: '100px', minWidth: '85px' },
    { key: 'ml', label: 'ML Classification', width: '180px', minWidth: '140px' },
    { key: 'agent3', label: 'Agent 3', width: '95px', minWidth: '80px' },
    { key: 'snow', label: 'ServiceNow', width: '190px', minWidth: '140px' },
  ];

  return (
    <>
      {/* Filter Bar */}
      <div className="filter-bar">
        <Filter size={15} style={{ color: 'var(--text-tertiary)' }} />
        <select className="filter-select" value={deviceFilter} onChange={e => setDeviceFilter(e.target.value)}>
          {deviceNames.map(d => (<option key={d} value={d}>{d === 'ALL' ? '🖥 All Devices' : d}</option>))}
        </select>
        <select className="filter-select" value={timeRange} onChange={e => setTimeRange(e.target.value)}>
          <option value="ALL">⏰ All Time</option>
          <option value="24H">Last 24 Hours</option>
          <option value="7D">Last 7 Days</option>
          <option value="30D">Last 30 Days</option>
        </select>
        {['ALL', 'BACKDATED', 'AUTO', 'NON_AUTO', 'UNCERTAIN'].map(f => (
          <button key={f} className={`filter-pill ${categoryFilter === f ? 'active' : ''}`} onClick={() => setCategoryFilter(f)}>
            {f === 'ALL' ? 'All' : f === 'BACKDATED' ? 'Backdated' : f === 'AUTO' ? 'Auto-Resolving' : f === 'NON_AUTO' ? 'Non-Auto' : 'Uncertain'}
          </button>
        ))}

        <button
          className="filter-pill simulate-btn"
          style={{
            marginLeft: 'auto',
            background: 'linear-gradient(135deg, #2563eb, #0891b2)',
            color: '#ffffff',
            border: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontWeight: 600,
            cursor: simulating ? 'wait' : 'pointer',
            boxShadow: '0 2px 8px rgba(37, 99, 235, 0.3)',
            padding: '0.45rem 0.9rem',
          }}
          disabled={simulating}
          onClick={() => handleSimulate(5)}
          title="Simulate 5 incoming alerts and run through ML pipeline"
        >
          <Zap size={14} className={simulating ? 'spin-once' : ''} />
          {simulating ? 'Simulating...' : '⚡ Simulate +5 Alerts'}
        </button>
      </div>

      {/* KPI Cards Row 1 */}
      <div className="kpi-grid">
        <div className="glass-card kpi-card highlight-blue">
          <div className="kpi-icon blue"><Activity size={20} /></div>
          <div className="kpi-content">
            <h3>Total Processed</h3>
            <p className="value">{kpi.total}</p>
            <p className="sub-value">alerts ingested</p>
          </div>
        </div>
        <div className="glass-card kpi-card highlight-green">
          <div className="kpi-icon green"><ShieldCheck size={20} /></div>
          <div className="kpi-content">
            <h3>Suppression Rate</h3>
            <p className="value" style={{ color: 'var(--accent-green)' }}>{kpi.suppressionRate}%</p>
            <p className="sub-value">noise eliminated</p>
          </div>
        </div>
        <div className="glass-card kpi-card highlight-cyan">
          <div className="kpi-icon cyan"><Ban size={20} /></div>
          <div className="kpi-content">
            <h3>Tickets Avoided</h3>
            <p className="value">{kpi.ticketsAvoided}</p>
            <p className="sub-value">SNOW tickets prevented</p>
          </div>
        </div>
        <div className="glass-card kpi-card highlight-red">
          <div className="kpi-icon red"><Ticket size={20} /></div>
          <div className="kpi-content">
            <h3>SNOW Tickets</h3>
            <p className="value">{kpi.totalSnowTickets}</p>
            <p className="sub-value">{kpi.snowCreated} new · {kpi.snowAppended} comments · {kpi.snowReopened} reopened</p>
          </div>
        </div>
      </div>

      {/* KPI Cards Row 2 */}
      <div className="kpi-grid">
        <div className="glass-card kpi-card" onClick={() => setCategoryFilter('BACKDATED')}>
          <div className="kpi-icon blue"><Clock size={20} /></div>
          <div className="kpi-content">
            <h3>Backdated / Suppressed</h3>
            <p className="value">{kpi.backdated}</p>
          </div>
        </div>
        <div className="glass-card kpi-card" onClick={() => setCategoryFilter('AUTO')}>
          <div className="kpi-icon green"><CheckCircle size={20} /></div>
          <div className="kpi-content">
            <h3>Auto-Resolving</h3>
            <p className="value">{kpi.autoResolving}</p>
            <p className="sub-value">queued for delayed re-check</p>
          </div>
        </div>
        <div className="glass-card kpi-card" onClick={() => setCategoryFilter('NON_AUTO')}>
          <div className="kpi-icon red"><AlertTriangle size={20} /></div>
          <div className="kpi-content">
            <h3>Non-Auto Resolving</h3>
            <p className="value">{kpi.nonAutoResolving}</p>
            <p className="sub-value">escalated to ServiceNow</p>
          </div>
        </div>
        <div className="glass-card kpi-card" onClick={() => setCategoryFilter('UNCERTAIN')}>
          <div className="kpi-icon yellow"><Zap size={20} /></div>
          <div className="kpi-content">
            <h3>Uncertain</h3>
            <p className="value">{kpi.uncertain}</p>
            <p className="sub-value">low ML confidence</p>
          </div>
        </div>
      </div>

      {/* ===== SNOW TICKET DETAIL CARDS ===== */}
      <p className="section-title"><FileText size={14} /> ServiceNow Ticket Details</p>
      <div className="snow-detail-grid">
        <div className="snow-detail-card">
          <h4><PlusCircle size={16} style={{ color: 'var(--accent-blue)' }} /> New Incidents Created ({snowDetails.newDevices.length})</h4>
          {snowDetails.newDevices.length === 0 ? (
            <p style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>No new incidents in this period.</p>
          ) : (
            <ul className="snow-device-list">
              {snowDetails.newDevices.map((item, i) => (
                <li key={i}>
                  <span className="snow-device-name">{item.device}</span>
                  <span className="snow-device-inc">{item.incident}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="snow-detail-card">
          <h4><RotateCcw size={16} style={{ color: 'var(--accent-orange)' }} /> Incidents Re-opened ({snowDetails.reopenDevices.length})</h4>
          {snowDetails.reopenDevices.length === 0 ? (
            <p style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>No re-opened incidents in this period.</p>
          ) : (
            <ul className="snow-device-list">
              {snowDetails.reopenDevices.map((item, i) => (
                <li key={i}>
                  <span className="snow-device-name">{item.device}</span>
                  <span className="snow-device-inc">{item.incident}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>


      {/* Charts Row */}
      <div className="charts-grid">
        <div className="glass-card chart-card">
          <h3><TrendingDown size={16} /> Alert Volume Trend</h3>
          <div style={{ height: '280px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={kpi.hourlySeries} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="gradBackdated" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="gradAuto" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#059669" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#059669" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="gradNonAuto" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#dc2626" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#dc2626" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
                <XAxis
                  dataKey="time"
                  stroke="#94a3b8"
                  tick={{ fontSize: 10, fill: '#94a3b8' }}
                  minTickGap={35}
                  tickFormatter={v => {
                    try {
                      const d = new Date(v);
                      const timeStr = d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', hour12: true });
                      const dateStr = d.toLocaleDateString([], { month: 'short', day: 'numeric' });
                      return `${dateStr}, ${timeStr}`;
                    } catch {
                      return v;
                    }
                  }}
                />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <RechartsTooltip
                  contentStyle={TOOLTIP_STYLE}
                  labelFormatter={v => {
                    try {
                      return new Date(v).toLocaleString([], {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                        hour: 'numeric',
                        minute: '2-digit',
                        hour12: true,
                      });
                    } catch {
                      return v;
                    }
                  }}
                />
                <Area type="monotone" dataKey="Backdated" stroke="#2563eb" fill="url(#gradBackdated)" strokeWidth={2} />
                <Area type="monotone" dataKey="Auto Resolving" stroke="#059669" fill="url(#gradAuto)" strokeWidth={2} />
                <Area type="monotone" dataKey="Non-Auto Resolving" stroke="#dc2626" fill="url(#gradNonAuto)" strokeWidth={2} />
                <Area type="monotone" dataKey="Uncertain" stroke="#d97706" fill="transparent" strokeWidth={2} strokeDasharray="5 5" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="glass-card chart-card">
          <h3><BarChart3 size={16} /> Category Distribution</h3>
          <div style={{ height: '280px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} cx="50%" cy="45%" innerRadius={52} outerRadius={82} paddingAngle={4} dataKey="value" stroke="none">
                  {pieData.map((entry, index) => (<Cell key={`cell-${index}`} fill={CATEGORY_COLORS[entry.name] || COLORS[index]} />))}
                </Pie>
                <RechartsTooltip contentStyle={TOOLTIP_STYLE} />
                <Legend verticalAlign="bottom" iconType="circle" iconSize={8} wrapperStyle={{ fontSize: '0.72rem', color: '#475569' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ===== DEVICE RANKING TABLE ===== */}
      <div className="glass-card table-card">
        <h3><Award size={16} /> Device Ranking — by Alert Profile</h3>
        <div style={{ overflowX: 'auto' }}>
          <table className="rank-table" style={{ minWidth: '950px' }}>
            <thead>
              <tr>
                <th style={{ width: '50px' }}>Rank</th>
                <th style={{ width: '180px', minWidth: '130px' }}>Device</th>
                <th style={{ width: '70px' }}>Total</th>
                <th style={{ width: '120px' }}>Genuine Alerts</th>
                <th style={{ width: '130px' }}>False / Suppressed</th>
                <th style={{ width: '120px' }}>Auto-Resolving</th>
                <th style={{ width: '120px' }}>SNOW Created</th>
                <th style={{ width: '120px' }}>SNOW Reopened</th>
                <th style={{ width: '120px', minWidth: '100px' }}>Volume</th>
              </tr>
            </thead>
            <tbody>
              {deviceRanking.slice(0, 15).map(d => (
                <tr key={d.device}>
                  <td><span className={`rank-number ${getRankClass(d.rank)}`}>{d.rank}</span></td>
                  <td style={{ fontWeight: 700, fontSize: '0.82rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={d.device}>{d.device}</td>
                  <td style={{ fontWeight: 700 }}>{d.total}</td>
                  <td><span className="badge non-auto">{d.genuine}</span></td>
                  <td><span className="badge backdated">{d.false}</span></td>
                  <td><span className="badge auto">{d.autoResolving}</span></td>
                  <td>{d.snowCreated > 0 ? <span className="badge snow-new">{d.snowCreated}</span> : <span style={{ color: 'var(--text-tertiary)' }}>—</span>}</td>
                  <td>{d.snowReopened > 0 ? <span className="badge snow-reopen">{d.snowReopened}</span> : <span style={{ color: 'var(--text-tertiary)' }}>—</span>}</td>
                  <td>
                    <div className="mini-bar">
                      <div className="mini-bar-fill" style={{ width: `${d.pct}%`, background: getBarColor(d) }} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detailed Traceability Table */}
      <div className="glass-card table-card">
        <h3>
          <Server size={16} /> Detailed Traceability Matrix
          {(deviceFilter !== 'ALL' || categoryFilter !== 'ALL' || timeRange !== 'ALL') && (
            <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginLeft: '8px', fontWeight: 400 }}>({filteredAlerts.length} results)</span>
          )}
        </h3>
        <div style={{ overflowX: 'auto', maxHeight: '460px', overflowY: 'auto' }}>
          <table className="data-table resizable-table" ref={traceTableRef} style={{ minWidth: '1410px' }}>
            <thead>
              <tr>
                {TRACE_COLUMNS.map((col, idx) => (
                  <th key={col.key} style={{ width: col.width, minWidth: col.minWidth, position: 'relative' }}>
                    {col.label}
                    <span
                      className="col-resize-handle"
                      onMouseDown={(e) => onTraceColResize(e, idx)}
                    />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredAlerts.map((alert, i) => {
                const details = alert.alert_details || {};
                const results = alert.results || {};
                const isBackdated = results.agent_1?.data?.is_backdated;
                const mlCategory = isBackdated ? 'Backdated' : (results.agent_2?.data?.predicted_category || 'Unknown');
                const confidence = results.agent_2?.data?.confidence;
                const queueStatus = results.agent_3?.data?.queue_status;
                const snowAction = results.agent_4?.data?.action;
                const snowInc = results.agent_4?.data?.incident;
                const liveStatus = alert.live_snow_status;
                let snowDisplay = '—';
                if (snowAction) {
                  const actionLabel = snowAction.replace(/_/g, ' ');
                  snowDisplay = snowInc ? `${actionLabel} (${snowInc})` : actionLabel;
                  if (liveStatus) snowDisplay += ` · ${liveStatus}`;
                }
                return (
                  <tr key={i}>
                    <td style={{ width: TRACE_COLUMNS[0].width, minWidth: TRACE_COLUMNS[0].minWidth, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      <button
                        className="event-id-link"
                        onClick={() => setSelectedEvent(alert)}
                        title={details.event_id || `EVT-${i}`}
                      >
                        {details.event_id || `EVT-${i}`}
                      </button>
                    </td>
                    <td style={{ width: TRACE_COLUMNS[1].width, minWidth: TRACE_COLUMNS[1].minWidth, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={details.device_name || 'Unknown'}>
                      {details.device_name || 'Unknown'}
                    </td>
                    <td style={{ width: TRACE_COLUMNS[2].width, minWidth: TRACE_COLUMNS[2].minWidth }}>
                      <span className={`badge severity-${details.severity || 3}`}>{details.severity || '—'}</span>
                    </td>
                    <td style={{ width: TRACE_COLUMNS[3].width, minWidth: TRACE_COLUMNS[3].minWidth, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={details.issue_name || '—'}>
                      {details.issue_name || '—'}
                    </td>
                    <td style={{ width: TRACE_COLUMNS[4].width, minWidth: TRACE_COLUMNS[4].minWidth, fontSize: '0.76rem', color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {formatTimestamp(details.timestamp || details.raw_timestamp)}
                    </td>
                    <td style={{ width: TRACE_COLUMNS[5].width, minWidth: TRACE_COLUMNS[5].minWidth }}>
                      <span className={`badge ${isBackdated ? 'backdated' : 'auto-resolving'}`}>{isBackdated ? 'Suppressed' : 'Fresh'}</span>
                    </td>
                    <td style={{ width: TRACE_COLUMNS[6].width, minWidth: TRACE_COLUMNS[6].minWidth, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      <span className={`badge ${mlCategory.toLowerCase().replace(/[\s/]/g, '-')}`}>{mlCategory}</span>
                      {confidence && <span style={{ fontSize: '0.65rem', color: 'var(--text-tertiary)', marginLeft: '3px' }}>({confidence})</span>}
                    </td>
                    <td style={{ width: TRACE_COLUMNS[7].width, minWidth: TRACE_COLUMNS[7].minWidth }}>
                      {queueStatus ? <span className="badge delayed">Queued</span> : '—'}
                    </td>
                    <td style={{ width: TRACE_COLUMNS[8].width, minWidth: TRACE_COLUMNS[8].minWidth, fontSize: '0.78rem', color: snowInc ? 'var(--accent-blue)' : 'var(--text-tertiary)', fontWeight: snowInc ? 600 : 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={snowDisplay}>
                      {snowDisplay}
                    </td>
                  </tr>
                );
              })}
              {filteredAlerts.length === 0 && (
                <tr><td colSpan="9" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-tertiary)' }}>No alerts match the current filters.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Event Detail Modal */}
      <EventDetailModal alert={selectedEvent} onClose={() => setSelectedEvent(null)} />
    </>
  );
}
