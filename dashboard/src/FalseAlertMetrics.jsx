import React, { useState, useMemo, useCallback, useRef } from 'react';
import {
  BarChart3, AlertTriangle, CheckCircle, Clock, ShieldCheck,
  Activity, Server, TrendingDown, Ticket, Ban, Filter,
  Zap, Award, FileText, RotateCcw, MessageSquarePlus, PlusCircle, X,
  Search, ArrowUpDown, ArrowUp, ArrowDown, Calendar, FilterX, ServerOff,
  ChevronDown, ChevronUp
} from 'lucide-react';
import {
  AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend
} from 'recharts';
import AnimatedCounter from './AnimatedCounter';
import TableScrollWrapper from './components/TableScrollWrapper';

const COLORS = ['#2563eb', '#059669', '#dc2626', '#d97706', '#7c3aed', '#0891b2'];
const CATEGORY_COLORS = {
  'Backdated': '#2563eb',
  'Auto Resolving': '#059669',
  'Non-Auto Resolving': '#dc2626',
  'Uncertain': '#d97706',
};

const TOOLTIP_STYLE = {
  backgroundColor: 'var(--bg-secondary)',
  border: '1px solid var(--card-border)',
  borderRadius: '10px',
  boxShadow: 'var(--shadow-md)',
  fontSize: '0.78rem',
  color: 'var(--text-primary)',
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
  const [customStartTime, setCustomStartTime] = useState('');
  const [customEndTime, setCustomEndTime] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [simulating, setSimulating] = useState(false);

  // Table-specific filters & sorting
  const [matrixSearch, setMatrixSearch] = useState('');
  const [searchScope, setSearchScope] = useState('all');
  const [matrixDevice, setMatrixDevice] = useState('ALL');
  const [matrixSeverity, setMatrixSeverity] = useState('ALL');
  const [matrixOutcome, setMatrixOutcome] = useState('ALL');
  const [matrixSnow, setMatrixSnow] = useState('ALL');
  const [sortColumn, setSortColumn] = useState('timestamp');
  const [sortDirection, setSortDirection] = useState('desc');
  const [rankingExpanded, setRankingExpanded] = useState(false);
  const [traceExpanded, setTraceExpanded] = useState(false);

  const { tableRef: traceTableRef, onMouseDown: onTraceColResize } = useResizableColumns();

  const alerts = useMemo(() => {
    if (rawAlerts && rawAlerts.length > 0) return rawAlerts;
    return generateMockData();
  }, [rawAlerts]);

  const handleSort = (columnKey) => {
    if (sortColumn === columnKey) {
      if (sortDirection === 'asc') {
        setSortDirection('desc');
      } else {
        setSortColumn(null);
        setSortDirection('asc');
      }
    } else {
      setSortColumn(columnKey);
      setSortDirection('asc');
    }
  };

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

  const customRangeWarning = useMemo(() => {
    if (timeRange !== 'CUSTOM' || !customStartTime || !customEndTime) return null;
    const s = new Date(customStartTime).getTime();
    const e = new Date(customEndTime).getTime();
    if (!isNaN(s) && !isNaN(e) && s > e) {
      return 'Start time is after End time';
    }
    return null;
  }, [timeRange, customStartTime, customEndTime]);

  // 1. Alerts filtered by global Device & Time Range (scope for system KPI totals)
  const scopeAlerts = useMemo(() => {
    let result = alerts;
    if (deviceFilter !== 'ALL') result = result.filter(a => a.alert_details?.device_name === deviceFilter);
    if (timeRange === 'CUSTOM') {
      const startMs = customStartTime ? new Date(customStartTime).getTime() : null;
      const endMs = customEndTime ? new Date(customEndTime).getTime() : null;
      const hasStart = startMs !== null && !isNaN(startMs);
      const hasEnd = endMs !== null && !isNaN(endMs);

      if (hasStart || hasEnd) {
        result = result.filter(a => {
          const ts = a.alert_details?.timestamp || a.alert_details?.raw_timestamp;
          const d = parseTimestamp(ts);
          if (!d) return true;
          const time = d.getTime();
          if (hasStart && time < startMs) return false;
          if (hasEnd && time > endMs) return false;
          return true;
        });
      }
    } else if (timeRange !== 'ALL') {
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
    return result;
  }, [alerts, deviceFilter, timeRange, customStartTime, customEndTime]);

  // 2. Alerts filtered by Category (drives table matrix, detail cards, and scoped views)
  const filteredAlerts = useMemo(() => {
    if (categoryFilter === 'ALL') return scopeAlerts;
    return scopeAlerts.filter(a => {
      const isBackdated = a.results?.agent_1?.data?.is_backdated;
      if (categoryFilter === 'BACKDATED') return isBackdated;
      if (isBackdated) return false;
      const predicted = (a.results?.agent_2?.data?.predicted_category || '').toLowerCase();
      if (categoryFilter === 'AUTO') return predicted === 'auto resolving';
      if (categoryFilter === 'NON_AUTO') return predicted === 'non-auto resolving';
      if (categoryFilter === 'UNCERTAIN') return predicted !== 'auto resolving' && predicted !== 'non-auto resolving';
      return true;
    });
  }, [scopeAlerts, categoryFilter]);

  // KPIs & SNOW details & Device Ranking computed from scopeAlerts
  // Total Processed = Suppressed (Backdated) + Auto-Resolving + Non-Auto-Resolving + Uncertain
  // Tickets Avoided is derived = Suppressed + Auto-Resolving (no double-counting)
  const { kpi, snowDetails, deviceRanking } = useMemo(() => {
    let backdated = 0, autoResolving = 0, nonAutoResolving = 0, uncertain = 0;
    let snowCreated = 0, snowAppended = 0, snowReopened = 0;
    const deviceStats = {};
    const hourlyBuckets = {};
    const snowNewDevices = [];
    const snowAppendedDevices = [];
    const snowReopenDevices = [];

    scopeAlerts.forEach(a => {
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
      if (snowAction === 'comment_appended') {
        snowAppended++;
        snowAppendedDevices.push({ device, incident: snowInc, timestamp: a.alert_details?.timestamp });
      }
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

    // Total Processed is strictly the sum of all 4 mutually exclusive classification categories
    const total = backdated + autoResolving + nonAutoResolving + uncertain;
    // Tickets avoided is derived from backdated (suppressed by Agent 1) + autoResolving (delayed wait-queue by Agent 3)
    const ticketsAvoided = backdated + autoResolving;
    const suppressionRate = total > 0 ? ((ticketsAvoided) / total * 100).toFixed(1) : 0;
    const hourlySeries = Object.values(hourlyBuckets).sort((a, b) => a.time - b.time);

    // Device ranking — sort by genuine alerts (non-auto-resolving) descending
    const ranking = Object.values(deviceStats).sort((a, b) => b.genuine - a.genuine || b.total - a.total);
    const maxTotal = Math.max(...ranking.map(d => d.total), 1);

    return {
      kpi: {
        total,
        backdated,
        autoResolving,
        nonAutoResolving,
        uncertain,
        suppressionRate,
        ticketsAvoided,
        snowCreated,
        snowAppended,
        snowReopened,
        totalSnowTickets: snowCreated + snowAppended + snowReopened,
        hourlySeries,
      },
      snowDetails: { newDevices: snowNewDevices, appendDevices: snowAppendedDevices, reopenDevices: snowReopenDevices },
      deviceRanking: ranking.map((d, i) => ({ ...d, rank: i + 1, pct: Math.round(d.total / maxTotal * 100) })),
    };
  }, [scopeAlerts]);

  // Matrix Filtered & Sorted Alerts
  const matrixAlerts = useMemo(() => {
    let list = filteredAlerts;

    // 0. Dedicated Device Filter (Exact match)
    if (matrixDevice !== 'ALL') {
      list = list.filter(a => {
        const d = a.alert_details?.device_name || a.alert_details?.device || 'Unknown';
        return d === matrixDevice;
      });
    }

    // 1. Text Search Filter with Scoped Matching
    if (matrixSearch.trim()) {
      const q = matrixSearch.trim().toLowerCase();
      list = list.filter(a => {
        const det = a.alert_details || {};
        const res = a.results || {};
        const eventId = String(det.event_id || '').toLowerCase();
        const device = String(det.device_name || det.device || '').toLowerCase();
        // Only search visible issue_name (not verbose issue_details) to prevent cross-device boilerplate matches
        const issue = String(det.issue_name || '').toLowerCase();
        const incident = String(res.agent_4?.data?.incident || '').toLowerCase();

        if (searchScope === 'device') return device.includes(q);
        if (searchScope === 'event_id') return eventId.includes(q);
        if (searchScope === 'issue') return issue.includes(q);
        if (searchScope === 'snow') return incident.includes(q);
        // 'all' matches across all visible table columns:
        return device.includes(q) || eventId.includes(q) || issue.includes(q) || incident.includes(q);
      });
    }

    // 2. Severity Filter
    if (matrixSeverity !== 'ALL') {
      const targetSev = Number(matrixSeverity);
      list = list.filter(a => Number(a.alert_details?.severity) === targetSev);
    }

    // 3. Decision / Classification Filter
    if (matrixOutcome !== 'ALL') {
      list = list.filter(a => {
        const isBd = a.results?.agent_1?.data?.is_backdated;
        const pred = (a.results?.agent_2?.data?.predicted_category || '').toLowerCase();
        if (matrixOutcome === 'BACKDATED') return isBd;
        if (isBd) return false;
        if (matrixOutcome === 'AUTO') return pred === 'auto resolving';
        if (matrixOutcome === 'NON_AUTO') return pred === 'non-auto resolving';
        if (matrixOutcome === 'UNCERTAIN') return pred !== 'auto resolving' && pred !== 'non-auto resolving';
        return true;
      });
    }

    // 4. ServiceNow Filter
    if (matrixSnow !== 'ALL') {
      list = list.filter(a => {
        const action = a.results?.agent_4?.data?.action || '';
        if (matrixSnow === 'CREATED') return action === 'incident_created';
        if (matrixSnow === 'APPENDED') return action === 'comment_appended';
        if (matrixSnow === 'REOPENED') return action === 'incident_reopened';
        if (matrixSnow === 'NONE') return !action;
        return true;
      });
    }

    // 5. Column Sorting
    if (sortColumn) {
      list = [...list].sort((a, b) => {
        let valA, valB;
        const detA = a.alert_details || {};
        const detB = b.alert_details || {};
        const resA = a.results || {};
        const resB = b.results || {};

        switch (sortColumn) {
          case 'event_id':
            valA = String(detA.event_id || '');
            valB = String(detB.event_id || '');
            return sortDirection === 'asc'
              ? valA.localeCompare(valB, undefined, { numeric: true })
              : valB.localeCompare(valA, undefined, { numeric: true });

          case 'device':
            valA = String(detA.device_name || '');
            valB = String(detB.device_name || '');
            return sortDirection === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);

          case 'severity':
            valA = Number(detA.severity || 99);
            valB = Number(detB.severity || 99);
            return sortDirection === 'asc' ? valA - valB : valB - valA;

          case 'issue':
            valA = String(detA.issue_name || detA.issue_details || '');
            valB = String(detB.issue_name || detB.issue_details || '');
            return sortDirection === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);

          case 'timestamp': {
            const dA = parseTimestamp(detA.timestamp || detA.raw_timestamp);
            const dB = parseTimestamp(detB.timestamp || detB.raw_timestamp);
            valA = dA ? dA.getTime() : 0;
            valB = dB ? dB.getTime() : 0;
            return sortDirection === 'asc' ? valA - valB : valB - valA;
          }

          case 'agent1': {
            const isBdA = resA.agent_1?.data?.is_backdated ? 1 : 0;
            const isBdB = resB.agent_1?.data?.is_backdated ? 1 : 0;
            return sortDirection === 'asc' ? isBdA - isBdB : isBdB - isBdA;
          }

          case 'ml': {
            const catA = String(resA.agent_2?.data?.predicted_category || (resA.agent_1?.data?.is_backdated ? 'Backdated' : 'Unknown'));
            const catB = String(resB.agent_2?.data?.predicted_category || (resB.agent_1?.data?.is_backdated ? 'Backdated' : 'Unknown'));
            return sortDirection === 'asc' ? catA.localeCompare(catB) : catB.localeCompare(catA);
          }

          case 'agent3': {
            const qA = String(resA.agent_3?.data?.queue_status || '');
            const qB = String(resB.agent_3?.data?.queue_status || '');
            return sortDirection === 'asc' ? qA.localeCompare(qB) : qB.localeCompare(qA);
          }

          case 'snow': {
            const actA = String(resA.agent_4?.data?.action || '');
            const actB = String(resB.agent_4?.data?.action || '');
            return sortDirection === 'asc' ? actA.localeCompare(actB) : actB.localeCompare(actA);
          }

          default:
            return 0;
        }
      });
    }

    return list;
  }, [filteredAlerts, matrixDevice, matrixSearch, searchScope, matrixSeverity, matrixOutcome, matrixSnow, sortColumn, sortDirection]);

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
    { key: 'event_id', label: 'Event ID', width: '220px', minWidth: '160px', tooltip: 'Unique DNAC event identifier — click ID to view alert trace' },
    { key: 'device', label: 'Device', width: '180px', minWidth: '130px', tooltip: 'Network device hostname — click to filter matrix by device' },
    { key: 'severity', label: 'Severity', width: '85px', minWidth: '70px', tooltip: 'Alert severity level (1=Critical, 2=Major, 3=Minor)' },
    { key: 'issue', label: 'Issue', width: '200px', minWidth: '140px', tooltip: 'Reported network failure description or issue category' },
    { key: 'timestamp', label: 'Timestamp', width: '160px', minWidth: '130px', tooltip: 'Alert timestamp in local time' },
    { key: 'agent1', label: 'Agent 1', width: '100px', minWidth: '85px', tooltip: 'Backdated / freshness check (Suppressed vs Fresh)' },
    { key: 'ml', label: 'ML Classification', width: '180px', minWidth: '140px', tooltip: 'Machine learning classifier category and confidence score' },
    { key: 'agent3', label: 'Agent 3', width: '95px', minWidth: '80px', tooltip: 'Correlation and suppression queue status' },
    { key: 'snow', label: 'ServiceNow', width: '190px', minWidth: '140px', tooltip: 'ITSM ticket action and incident reference' },
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
          <option value="CUSTOM">📅 Custom Range...</option>
        </select>
        {timeRange !== 'CUSTOM' ? (
          <button
            type="button"
            className="filter-pill custom-range-btn"
            onClick={() => setTimeRange('CUSTOM')}
            title="Set custom start and end date/time range"
          >
            <Calendar size={13} style={{ marginRight: '4px' }} />
            Custom Range
          </button>
        ) : null}
        {timeRange === 'CUSTOM' && (
          <div className="custom-datetime-container">
            <div className="datetime-input-group">
              <span className="datetime-label">From</span>
              <input
                type="datetime-local"
                className="filter-input-datetime"
                value={customStartTime}
                onChange={e => setCustomStartTime(e.target.value)}
                title="Start date and time"
              />
            </div>
            <div className="datetime-input-group">
              <span className="datetime-label">To</span>
              <input
                type="datetime-local"
                className="filter-input-datetime"
                value={customEndTime}
                onChange={e => setCustomEndTime(e.target.value)}
                title="End date and time"
              />
            </div>
            {(customStartTime || customEndTime) && (
              <button
                type="button"
                className="datetime-action-btn clear"
                onClick={() => {
                  setCustomStartTime('');
                  setCustomEndTime('');
                }}
                title="Clear date inputs"
              >
                <X size={12} />
                <span>Clear</span>
              </button>
            )}
            <button
              type="button"
              className="datetime-action-btn reset"
              onClick={() => {
                setCustomStartTime('');
                setCustomEndTime('');
                setTimeRange('ALL');
              }}
              title="Return to preset ranges"
            >
              <RotateCcw size={12} />
              <span>Presets</span>
            </button>
            {customRangeWarning ? (
              <span className="custom-datetime-warning">
                <AlertTriangle size={12} />
                {customRangeWarning}
              </span>
            ) : (customStartTime || customEndTime) ? (
              <span className="custom-datetime-chip">
                {scopeAlerts.length} in range
              </span>
            ) : (
              <span className="custom-datetime-hint">
                Select start & end time
              </span>
            )}
          </div>
        )}
        {['ALL', 'BACKDATED', 'AUTO', 'NON_AUTO', 'UNCERTAIN'].map(f => (
          <button key={f} className={`filter-pill ${categoryFilter === f ? 'active' : ''}`} onClick={() => setCategoryFilter(f)}>
            {f === 'ALL' ? 'All' : f === 'BACKDATED' ? 'Backdated' : f === 'AUTO' ? 'Auto-Resolving' : f === 'NON_AUTO' ? 'Non-Auto' : 'Uncertain'}
          </button>
        ))}
      </div>

      {/* Simulate Action */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '0.75rem' }}>
        <button
          className="filter-pill simulate-btn"
          style={{
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
            <p className="value"><AnimatedCounter value={kpi.total} /></p>
            <p className="sub-value">
              {categoryFilter !== 'ALL'
                ? `${filteredAlerts.length} ${categoryFilter === 'BACKDATED' ? 'Backdated' : categoryFilter === 'AUTO' ? 'Auto-Resolving' : categoryFilter === 'NON_AUTO' ? 'Non-Auto' : 'Uncertain'} filtered · ${kpi.total} total`
                : `alerts ingested (${kpi.total} total)`}
            </p>
          </div>
        </div>
        <div className="glass-card kpi-card highlight-green">
          <div className="kpi-icon green"><ShieldCheck size={20} /></div>
          <div className="kpi-content">
            <h3>Suppression Rate</h3>
            <p className="value" style={{ color: 'var(--accent-green)' }}>
              <AnimatedCounter value={kpi.suppressionRate} decimals={1} suffix="%" />
            </p>
            <p className="sub-value">noise eliminated</p>
          </div>
        </div>
        <div className="glass-card kpi-card highlight-cyan">
          <div className="kpi-icon cyan"><Ban size={20} /></div>
          <div className="kpi-content">
            <h3>Tickets Avoided</h3>
            <p className="value"><AnimatedCounter value={kpi.ticketsAvoided} /></p>
            <p className="sub-value" title={`${kpi.backdated} backdated alerts suppressed + ${kpi.autoResolving} predicted auto-resolved`}>
              {kpi.backdated} suppressed · {kpi.autoResolving} resolved
            </p>
          </div>
        </div>
        <div className="glass-card kpi-card highlight-red">
          <div className="kpi-icon red"><Ticket size={20} /></div>
          <div className="kpi-content">
            <h3>SNOW Tickets</h3>
            <p className="value"><AnimatedCounter value={kpi.totalSnowTickets} /></p>
            <p className="sub-value" title={`${kpi.snowCreated} new incidents, ${kpi.snowAppended} work notes appended, ${kpi.snowReopened} incidents reopened`}>
              {kpi.snowCreated} new · {kpi.snowReopened} reopen · {kpi.snowAppended} notes
            </p>
          </div>
        </div>
      </div>

      {/* KPI Cards Row 2 */}
      <div className="kpi-grid">
        <div
          className={`glass-card kpi-card ${categoryFilter === 'BACKDATED' ? 'active highlight-blue' : ''}`}
          onClick={() => setCategoryFilter(f => f === 'BACKDATED' ? 'ALL' : 'BACKDATED')}
          title="Click to toggle filter for Backdated / Suppressed alerts"
        >
          <div className="kpi-icon blue"><Clock size={20} /></div>
          <div className="kpi-content">
            <h3>Backdated / Suppressed</h3>
            <p className="value"><AnimatedCounter value={kpi.backdated} /></p>
            <p className="sub-value">{categoryFilter === 'BACKDATED' ? '✓ Filter active (click to clear)' : 'suppressed by Agent 1'}</p>
          </div>
        </div>
        <div
          className={`glass-card kpi-card ${categoryFilter === 'AUTO' ? 'active highlight-green' : ''}`}
          onClick={() => setCategoryFilter(f => f === 'AUTO' ? 'ALL' : 'AUTO')}
          title="Click to toggle filter for Auto-Resolving alerts"
        >
          <div className="kpi-icon green"><CheckCircle size={20} /></div>
          <div className="kpi-content">
            <h3>Auto-Resolving</h3>
            <p className="value"><AnimatedCounter value={kpi.autoResolving} /></p>
            <p className="sub-value">{categoryFilter === 'AUTO' ? '✓ Filter active (click to clear)' : 'queued for delayed re-check'}</p>
          </div>
        </div>
        <div
          className={`glass-card kpi-card ${categoryFilter === 'NON_AUTO' ? 'active highlight-red' : ''}`}
          onClick={() => setCategoryFilter(f => f === 'NON_AUTO' ? 'ALL' : 'NON_AUTO')}
          title="Click to toggle filter for Non-Auto Resolving alerts"
        >
          <div className="kpi-icon red"><AlertTriangle size={20} /></div>
          <div className="kpi-content">
            <h3>Non-Auto Resolving</h3>
            <p className="value"><AnimatedCounter value={kpi.nonAutoResolving} /></p>
            <p className="sub-value">{categoryFilter === 'NON_AUTO' ? '✓ Filter active (click to clear)' : 'escalated to ServiceNow'}</p>
          </div>
        </div>
        <div
          className={`glass-card kpi-card ${categoryFilter === 'UNCERTAIN' ? 'active highlight-yellow' : ''}`}
          onClick={() => setCategoryFilter(f => f === 'UNCERTAIN' ? 'ALL' : 'UNCERTAIN')}
          title="Click to toggle filter for Uncertain alerts"
        >
          <div className="kpi-icon yellow"><Zap size={20} /></div>
          <div className="kpi-content">
            <h3>Uncertain</h3>
            <p className="value"><AnimatedCounter value={kpi.uncertain} /></p>
            <p className="sub-value">{categoryFilter === 'UNCERTAIN' ? '✓ Filter active (click to clear)' : 'low ML confidence'}</p>
          </div>
        </div>
      </div>

      {/* ===== SERVICENOW INCIDENT ACTIVITY ===== */}
      <div className="snow-section-header">
        <div className="snow-section-title-wrap">
          <div className="snow-section-icon-badge">
            <FileText size={15} />
          </div>
          <h3 className="snow-section-title">ServiceNow Incident Activity</h3>
        </div>
        <span className="snow-total-badge">
          {snowDetails.newDevices.length + (snowDetails.appendDevices?.length || 0) + snowDetails.reopenDevices.length} Total Impact
        </span>
      </div>

      <div className="snow-detail-grid">
        <div className="snow-detail-card card-blue">
          <div className="snow-detail-card-header">
            <h4><PlusCircle size={16} style={{ color: 'var(--accent-blue)' }} /> New Incidents Created</h4>
            <span className="snow-card-count-badge">{snowDetails.newDevices.length}</span>
          </div>
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
        <div className="snow-detail-card card-purple">
          <div className="snow-detail-card-header">
            <h4><MessageSquarePlus size={16} style={{ color: 'var(--accent-purple)' }} /> Comments Appended</h4>
            <span className="snow-card-count-badge">{snowDetails.appendDevices?.length || 0}</span>
          </div>
          {!snowDetails.appendDevices || snowDetails.appendDevices.length === 0 ? (
            <p style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>No comments appended in this period.</p>
          ) : (
            <ul className="snow-device-list">
              {snowDetails.appendDevices.map((item, i) => (
                <li key={i}>
                  <span className="snow-device-name">{item.device}</span>
                  <span className="snow-device-inc">{item.incident}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="snow-detail-card card-orange">
          <div className="snow-detail-card-header">
            <h4><RotateCcw size={16} style={{ color: 'var(--accent-orange)' }} /> Incidents Re-opened</h4>
            <span className="snow-card-count-badge">{snowDetails.reopenDevices.length}</span>
          </div>
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
                <CartesianGrid strokeDasharray="3 3" stroke="var(--card-border)" />
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
                <Legend verticalAlign="bottom" iconType="circle" iconSize={8} wrapperStyle={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ===== DEVICE RANKING TABLE ===== */}
      <div className="glass-card table-card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
          <h3 style={{ margin: 0 }}><Award size={16} /> Device Ranking — by Alert Profile</h3>
          <span className="table-counter-chip">
            Showing {Math.min(deviceRanking.length, rankingExpanded ? deviceRanking.length : 10)} of {deviceRanking.length} devices
          </span>
        </div>
        <TableScrollWrapper maxHeight={rankingExpanded ? null : '480px'}>
          <table className="rank-table" style={{ minWidth: '950px' }}>
            <thead>
              <tr>
                <th style={{ width: '50px' }} title="Device rank based on alert volume">Rank</th>
                <th style={{ width: '180px', minWidth: '130px' }} title="Device hostname — click to filter Detailed Traceability Matrix">Device</th>
                <th style={{ width: '70px' }} title="Total alert count recorded for this device">Total</th>
                <th style={{ width: '120px' }} title="Alerts verified as actionable and genuine">Genuine Alerts</th>
                <th style={{ width: '130px' }} title="Alerts identified as backdated, redundant, or false positives">False / Suppressed</th>
                <th style={{ width: '120px' }} title="Alerts expected to clear without human intervention">Auto-Resolving</th>
                <th style={{ width: '90px' }} title="Alerts with low machine learning confidence requiring investigation">Uncertain</th>
                <th style={{ width: '110px' }} title="New ServiceNow incident tickets dispatched">SNOW Created</th>
                <th style={{ width: '110px' }} title="ServiceNow incident tickets reopened due to recurring issues">SNOW Reopened</th>
                <th style={{ width: '120px', minWidth: '100px' }} title="Relative alert volume distribution across ranked devices">Volume</th>
              </tr>
            </thead>
            <tbody>
              {deviceRanking.slice(0, rankingExpanded ? deviceRanking.length : 10).map(d => (
                <tr key={d.device}>
                  <td><span className={`rank-number ${getRankClass(d.rank)}`}>{d.rank}</span></td>
                  <td
                    onClick={() => {
                      setMatrixDevice(d.device);
                      traceTableRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }}
                    style={{ fontWeight: 700, fontSize: '0.82rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', cursor: 'pointer' }}
                    title={`Click to filter Detailed Traceability Matrix for ${d.device}`}
                  >
                    <span style={{ borderBottom: '1px dashed var(--accent-blue)', color: matrixDevice === d.device ? 'var(--accent-blue)' : 'inherit' }}>
                      {d.device}
                    </span>
                  </td>
                  <td style={{ fontWeight: 700 }}>{d.total}</td>
                  <td><span className="badge non-auto">{d.genuine}</span></td>
                  <td><span className="badge backdated">{d.false}</span></td>
                  <td><span className="badge auto">{d.autoResolving}</span></td>
                  <td>{d.uncertain > 0 ? <span className="badge uncertain">{d.uncertain}</span> : <span style={{ color: 'var(--text-tertiary)' }}>—</span>}</td>
                  <td>{d.snowCreated > 0 ? <span className="badge snow-new">{d.snowCreated}</span> : <span style={{ color: 'var(--text-tertiary)' }}>—</span>}</td>
                  <td>{d.snowReopened > 0 ? <span className="badge snow-reopen">{d.snowReopened}</span> : <span style={{ color: 'var(--text-tertiary)' }}>—</span>}</td>
                  <td>
                    <div className="mini-bar">
                      <div className="mini-bar-fill" style={{ width: `${d.pct}%`, background: getBarColor(d) }} />
                    </div>
                  </td>
                </tr>
              ))}
              {deviceRanking.length === 0 && (
                <tr>
                  <td colSpan="10" style={{ padding: 0 }}>
                    <div className="table-empty-state">
                      <div className="empty-state-badge">
                        <ServerOff size={22} />
                      </div>
                      <div className="empty-state-title">No devices found in selected scope</div>
                      <div className="empty-state-desc">
                        No alert telemetry was found for the current device filter or time range. Try resetting your filters to view device rankings.
                      </div>
                      <button
                        onClick={() => {
                          setDeviceFilter('ALL');
                          setTimeRange('ALL');
                        }}
                        className="empty-state-action"
                      >
                        <RotateCcw size={13} /> Reset Device & Time Scope
                      </button>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </TableScrollWrapper>
        {deviceRanking.length > 10 && (
          <button
            type="button"
            className="table-expand-toggle-btn"
            onClick={() => setRankingExpanded(prev => !prev)}
          >
            {rankingExpanded ? (
              <>
                <ChevronUp size={14} />
                <span>Show 10 rows</span>
              </>
            ) : (
              <>
                <ChevronDown size={14} />
                <span>Show all {deviceRanking.length} rows</span>
              </>
            )}
          </button>
        )}
      </div>

      {/* Detailed Traceability Table */}
      <div className="glass-card table-card">
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '0.85rem', marginBottom: '1rem' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.6rem' }}>
            <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Server size={16} /> Detailed Traceability Matrix
            </h3>
            <span className={`table-counter-chip ${matrixAlerts.length !== filteredAlerts.length ? 'has-filter' : ''}`}>
              {matrixAlerts.length !== filteredAlerts.length && <span className="filter-active-dot" title="Filtered results" />}
              Showing {Math.min(matrixAlerts.length, traceExpanded ? matrixAlerts.length : 10)} of {matrixAlerts.length} alerts
            </span>
            {matrixDevice !== 'ALL' && (
              <span
                className="badge"
                style={{
                  background: 'rgba(37, 99, 235, 0.12)',
                  color: 'var(--accent-blue)',
                  border: '1px solid rgba(37, 99, 235, 0.3)',
                  fontWeight: 600,
                  fontSize: '0.72rem',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                Device: {matrixDevice}
                <button
                  onClick={() => setMatrixDevice('ALL')}
                  style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'inherit', padding: 0, display: 'flex' }}
                  title="Clear device filter"
                >
                  <X size={11} />
                </button>
              </span>
            )}
            {matrixAlerts.length !== filteredAlerts.length && (
              <span style={{ fontSize: '0.74rem', color: 'var(--text-tertiary)' }}>
                (of {filteredAlerts.length} total)
              </span>
            )}
          </div>

          {/* Table-specific Search & Filter Bar */}
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.5rem' }}>
            {/* Search Scope Selector */}
            <select
              className="filter-select"
              value={searchScope}
              onChange={(e) => setSearchScope(e.target.value)}
              style={{ fontSize: '0.76rem', padding: '0.35rem 0.55rem' }}
              title="Select which column to search"
            >
              <option value="all">Search: All</option>
              <option value="device">Search: Device Only</option>
              <option value="event_id">Search: Event ID Only</option>
              <option value="issue">Search: Issue Only</option>
              <option value="snow">Search: SNOW Only</option>
            </select>

            {/* Search Input */}
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <Search size={13} style={{ position: 'absolute', left: '10px', color: 'var(--text-tertiary)', pointerEvents: 'none' }} />
              <input
                type="text"
                placeholder={searchScope === 'device' ? 'Filter by device...' : searchScope === 'event_id' ? 'Search event ID...' : searchScope === 'issue' ? 'Search issue...' : searchScope === 'snow' ? 'Search incident...' : 'Search matrix...'}
                value={matrixSearch}
                onChange={(e) => setMatrixSearch(e.target.value)}
                style={{
                  padding: '0.38rem 1.8rem 0.38rem 2rem',
                  fontSize: '0.78rem',
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--card-border)',
                  borderRadius: '6px',
                  color: 'var(--text-primary)',
                  width: '180px',
                  outline: 'none',
                }}
              />
              {matrixSearch && (
                <button
                  onClick={() => setMatrixSearch('')}
                  style={{
                    position: 'absolute',
                    right: '6px',
                    background: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    color: 'var(--text-tertiary)',
                    padding: 0,
                    display: 'flex',
                  }}
                  title="Clear search"
                >
                  <X size={13} />
                </button>
              )}
            </div>

            {/* Dedicated Device Dropdown */}
            <select
              className="filter-select"
              value={matrixDevice}
              onChange={(e) => setMatrixDevice(e.target.value)}
              style={{ fontSize: '0.76rem', padding: '0.35rem 0.55rem', maxWidth: '160px' }}
              title="Filter matrix to a specific device"
            >
              <option value="ALL">Device: All</option>
              {deviceNames.filter(d => d !== 'ALL').map(d => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>

            {/* Severity Filter */}
            <select
              className="filter-select"
              value={matrixSeverity}
              onChange={(e) => setMatrixSeverity(e.target.value)}
              style={{ fontSize: '0.76rem', padding: '0.35rem 0.55rem' }}
            >
              <option value="ALL">Severity: All</option>
              <option value="1">P1 — Critical</option>
              <option value="2">P2 — Major</option>
              <option value="3">P3 — Warning</option>
            </select>

            {/* Classification Filter */}
            <select
              className="filter-select"
              value={matrixOutcome}
              onChange={(e) => setMatrixOutcome(e.target.value)}
              style={{ fontSize: '0.76rem', padding: '0.35rem 0.55rem' }}
            >
              <option value="ALL">Classification: All</option>
              <option value="BACKDATED">Backdated</option>
              <option value="AUTO">Auto-Resolving</option>
              <option value="NON_AUTO">Non-Auto Resolving</option>
              <option value="UNCERTAIN">Uncertain</option>
            </select>

            {/* ServiceNow Filter */}
            <select
              className="filter-select"
              value={matrixSnow}
              onChange={(e) => setMatrixSnow(e.target.value)}
              style={{ fontSize: '0.76rem', padding: '0.35rem 0.55rem' }}
            >
              <option value="ALL">SNOW: All</option>
              <option value="CREATED">Created</option>
              <option value="APPENDED">Appended</option>
              <option value="REOPENED">Reopened</option>
              <option value="NONE">None (Suppressed)</option>
            </select>

            {/* Reset Filters / Sorting */}
            {(matrixSearch || searchScope !== 'all' || matrixDevice !== 'ALL' || matrixSeverity !== 'ALL' || matrixOutcome !== 'ALL' || matrixSnow !== 'ALL' || sortColumn !== 'timestamp' || sortDirection !== 'desc') && (
              <button
                onClick={() => {
                  setMatrixSearch('');
                  setSearchScope('all');
                  setMatrixDevice('ALL');
                  setMatrixSeverity('ALL');
                  setMatrixOutcome('ALL');
                  setMatrixSnow('ALL');
                  setSortColumn('timestamp');
                  setSortDirection('desc');
                }}
                className="filter-pill"
                style={{ fontSize: '0.74rem', padding: '0.32rem 0.6rem', display: 'flex', alignItems: 'center', gap: '4px' }}
                title="Reset table filters and sort"
              >
                <RotateCcw size={12} /> Reset
              </button>
            )}
          </div>
        </div>

        <TableScrollWrapper maxHeight={traceExpanded ? null : '480px'}>
          <table className="data-table resizable-table" ref={traceTableRef} style={{ minWidth: '1410px' }}>
            <thead>
              <tr>
                {TRACE_COLUMNS.map((col, idx) => {
                  const isSorted = sortColumn === col.key;
                  return (
                    <th
                      key={col.key}
                      onClick={(e) => {
                        if (e.target.classList.contains('col-resize-handle')) return;
                        handleSort(col.key);
                      }}
                      className={`sortable ${isSorted ? 'sort-active' : ''}`}
                      style={{
                        width: col.width,
                        minWidth: col.minWidth,
                        position: 'relative',
                        userSelect: 'none',
                      }}
                      title={`${col.tooltip} (Click to sort)`}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '6px' }}>
                        <span>{col.label}</span>
                        <span style={{ display: 'inline-flex', alignItems: 'center', opacity: isSorted ? 1 : 0.4 }}>
                          {isSorted ? (
                            sortDirection === 'asc' ? <ArrowUp size={12} color="var(--accent-blue)" /> : <ArrowDown size={12} color="var(--accent-blue)" />
                          ) : (
                            <ArrowUpDown size={11} />
                          )}
                        </span>
                      </div>
                      <span
                        className="col-resize-handle"
                        onMouseDown={(e) => onTraceColResize(e, idx)}
                      />
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {(traceExpanded ? matrixAlerts : matrixAlerts.slice(0, 10)).map((alert, i) => {
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
                  <tr key={details.event_id || i}>
                    <td style={{ width: TRACE_COLUMNS[0].width, minWidth: TRACE_COLUMNS[0].minWidth, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      <button
                        className="event-id-link"
                        onClick={() => setSelectedEvent(alert)}
                        title={`Click to view full trace for ${details.event_id || `EVT-${i}`}`}
                      >
                        {details.event_id || `EVT-${i}`}
                      </button>
                    </td>
                    <td style={{ width: TRACE_COLUMNS[1].width, minWidth: TRACE_COLUMNS[1].minWidth, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={`Filter matrix for ${details.device_name || 'Unknown'}`}>
                      <button
                        className="device-filter-btn"
                        onClick={() => setMatrixDevice(details.device_name || 'Unknown')}
                        style={{
                          background: matrixDevice === details.device_name ? 'rgba(37, 99, 235, 0.15)' : 'transparent',
                          border: matrixDevice === details.device_name ? '1px solid rgba(37, 99, 235, 0.4)' : '1px solid transparent',
                          color: matrixDevice === details.device_name ? 'var(--accent-blue)' : 'var(--text-primary)',
                          fontWeight: 600,
                          cursor: 'pointer',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          textAlign: 'left',
                          maxWidth: '100%',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          fontSize: '0.8rem',
                          display: 'inline-block',
                          transition: 'all 0.15s ease',
                        }}
                      >
                        {details.device_name || 'Unknown'}
                      </button>
                    </td>
                    <td style={{ width: TRACE_COLUMNS[2].width, minWidth: TRACE_COLUMNS[2].minWidth }} title={`Severity ${details.severity || 3}`}>
                      <span className={`badge severity-${details.severity || 3}`}>{details.severity || '—'}</span>
                    </td>
                    <td style={{ width: TRACE_COLUMNS[3].width, minWidth: TRACE_COLUMNS[3].minWidth, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={details.issue_name || '—'}>
                      {details.issue_name || '—'}
                    </td>
                    <td style={{ width: TRACE_COLUMNS[4].width, minWidth: TRACE_COLUMNS[4].minWidth, fontSize: '0.76rem', color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={formatTimestamp(details.timestamp || details.raw_timestamp)}>
                      {formatTimestamp(details.timestamp || details.raw_timestamp)}
                    </td>
                    <td style={{ width: TRACE_COLUMNS[5].width, minWidth: TRACE_COLUMNS[5].minWidth }} title={isBackdated ? 'Backdated alert — suppressed from ServiceNow' : 'Fresh incoming alert'}>
                      <span className={`badge ${isBackdated ? 'backdated' : 'auto-resolving'}`}>{isBackdated ? 'Suppressed' : 'Fresh'}</span>
                    </td>
                    <td style={{ width: TRACE_COLUMNS[6].width, minWidth: TRACE_COLUMNS[6].minWidth, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={`Predicted: ${mlCategory}${confidence ? ` (confidence: ${confidence})` : ''}`}>
                      <span className={`badge ${mlCategory.toLowerCase().replace(/[\s/]/g, '-')}`}>{mlCategory}</span>
                      {confidence && <span style={{ fontSize: '0.65rem', color: 'var(--text-tertiary)', marginLeft: '3px' }}>({confidence})</span>}
                    </td>
                    <td style={{ width: TRACE_COLUMNS[7].width, minWidth: TRACE_COLUMNS[7].minWidth }} title={queueStatus ? 'Queued for correlation and suppression' : 'Processed directly'}>
                      {queueStatus ? <span className="badge delayed">Queued</span> : '—'}
                    </td>
                    <td style={{ width: TRACE_COLUMNS[8].width, minWidth: TRACE_COLUMNS[8].minWidth, fontSize: '0.78rem', color: snowInc ? 'var(--accent-blue)' : 'var(--text-tertiary)', fontWeight: snowInc ? 600 : 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={snowDisplay}>
                      {snowDisplay}
                    </td>
                  </tr>
                );
              })}
              {matrixAlerts.length === 0 && (
                <tr>
                  <td colSpan="9" style={{ padding: 0 }}>
                    <div className="table-empty-state">
                      <div className="empty-state-badge">
                        <FilterX size={22} />
                      </div>
                      <div className="empty-state-title">No alerts match the current matrix filters</div>
                      <div className="empty-state-desc">
                        Try broadening your search term or resetting the severity, ML category, or ServiceNow filter pills.
                      </div>
                      <button
                        onClick={() => {
                          setMatrixSearch('');
                          setMatrixDevice('ALL');
                          setMatrixSeverity('ALL');
                          setMatrixOutcome('ALL');
                          setMatrixSnow('ALL');
                        }}
                        className="empty-state-action"
                      >
                        <RotateCcw size={13} /> Clear matrix filters
                      </button>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </TableScrollWrapper>
        {matrixAlerts.length > 10 && (
          <button
            type="button"
            className="table-expand-toggle-btn"
            onClick={() => setTraceExpanded(prev => !prev)}
          >
            {traceExpanded ? (
              <>
                <ChevronUp size={14} />
                <span>Show 10 rows</span>
              </>
            ) : (
              <>
                <ChevronDown size={14} />
                <span>Show all {matrixAlerts.length} rows</span>
              </>
            )}
          </button>
        )}
      </div>

      {/* Event Detail Modal */}
      <EventDetailModal alert={selectedEvent} onClose={() => setSelectedEvent(null)} />
    </>
  );
}
