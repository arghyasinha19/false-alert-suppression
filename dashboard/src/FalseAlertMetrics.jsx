import React, { useState, useMemo } from 'react';
import {
  BarChart3, AlertTriangle, CheckCircle, Clock, ShieldCheck,
  Activity, Server, TrendingDown, Ticket, Ban, Filter,
  Zap, Award, FileText, RotateCcw, MessageSquarePlus, PlusCircle
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

export default function FalseAlertMetrics({ alerts: rawAlerts }) {
  const [deviceFilter, setDeviceFilter] = useState('ALL');
  const [timeRange, setTimeRange] = useState('ALL');
  const [categoryFilter, setCategoryFilter] = useState('ALL');

  const alerts = rawAlerts;

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
        const ts = a.alert_details?.timestamp;
        if (!ts) return true;
        const t = typeof ts === 'number' ? (ts > 1e12 ? ts : ts * 1000) : new Date(ts).getTime();
        return t >= cutoff;
      });
    }
    if (categoryFilter !== 'ALL') {
      result = result.filter(a => {
        const isBackdated = a.results?.agent_1?.data?.is_backdated;
        if (categoryFilter === 'BACKDATED') return isBackdated;
        if (isBackdated) return false;
        const predicted = a.results?.agent_2?.data?.predicted_category || '';
        if (categoryFilter === 'AUTO') return predicted === 'Auto resolving';
        if (categoryFilter === 'NON_AUTO') return predicted === 'Non-Auto Resolving';
        if (categoryFilter === 'UNCERTAIN') return predicted !== 'Auto resolving' && predicted !== 'Non-Auto Resolving';
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
      const predicted = a.results?.agent_2?.data?.predicted_category || '';
      const snowAction = a.results?.agent_4?.data?.action || '';
      const snowInc = a.results?.agent_4?.data?.incident || '';
      const device = a.alert_details?.device_name || 'Unknown';

      if (isBackdated) backdated++;
      else if (predicted === 'Auto resolving') autoResolving++;
      else if (predicted === 'Non-Auto Resolving') nonAutoResolving++;
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
        deviceStats[device] = { device, genuine: 0, false: 0, autoResolving: 0, total: 0, snowCreated: 0, snowReopened: 0 };
      }
      deviceStats[device].total++;
      if (isBackdated) deviceStats[device].false++;
      else if (predicted === 'Auto resolving') deviceStats[device].autoResolving++;
      else if (predicted === 'Non-Auto Resolving') deviceStats[device].genuine++;
      if (snowAction === 'incident_created') deviceStats[device].snowCreated++;
      if (snowAction === 'incident_reopened') deviceStats[device].snowReopened++;

      const ts = a.alert_details?.timestamp;
      if (ts) {
        try {
          const dt = new Date(typeof ts === 'number' ? (ts > 1e12 ? ts : ts * 1000) : ts);
          const hourKey = dt.toISOString().slice(0, 13) + ':00';
          if (!hourlyBuckets[hourKey]) hourlyBuckets[hourKey] = { time: hourKey, Backdated: 0, 'Auto Resolving': 0, 'Non-Auto Resolving': 0, Uncertain: 0 };
          if (isBackdated) hourlyBuckets[hourKey].Backdated++;
          else if (predicted === 'Auto resolving') hourlyBuckets[hourKey]['Auto Resolving']++;
          else if (predicted === 'Non-Auto Resolving') hourlyBuckets[hourKey]['Non-Auto Resolving']++;
          else hourlyBuckets[hourKey].Uncertain++;
        } catch (e) {}
      }
    });

    const suppressionRate = total > 0 ? ((backdated + autoResolving) / total * 100).toFixed(1) : 0;
    const ticketsAvoided = backdated + autoResolving;
    const hourlySeries = Object.values(hourlyBuckets).sort((a, b) => a.time.localeCompare(b.time));

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
              <AreaChart data={kpi.hourlySeries}>
                <defs>
                  <linearGradient id="gradBackdated" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2563eb" stopOpacity={0.2} />
                    <stop offset="100%" stopColor="#2563eb" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gradAuto" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#059669" stopOpacity={0.2} />
                    <stop offset="100%" stopColor="#059669" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gradNonAuto" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#dc2626" stopOpacity={0.2} />
                    <stop offset="100%" stopColor="#dc2626" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
                <XAxis dataKey="time" stroke="#94a3b8" tick={{ fontSize: 10, fill: '#94a3b8' }} tickFormatter={v => { try { return new Date(v).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); } catch { return v; } }} />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <RechartsTooltip contentStyle={TOOLTIP_STYLE} />
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
          <table className="rank-table">
            <thead>
              <tr>
                <th style={{ width: '50px' }}>Rank</th>
                <th>Device</th>
                <th>Total</th>
                <th>Genuine Alerts</th>
                <th>False / Suppressed</th>
                <th>Auto-Resolving</th>
                <th>SNOW Created</th>
                <th>SNOW Reopened</th>
                <th style={{ minWidth: '100px' }}>Volume</th>
              </tr>
            </thead>
            <tbody>
              {deviceRanking.slice(0, 15).map(d => (
                <tr key={d.device}>
                  <td><span className={`rank-number ${getRankClass(d.rank)}`}>{d.rank}</span></td>
                  <td style={{ fontWeight: 700, fontSize: '0.82rem' }}>{d.device}</td>
                  <td style={{ fontWeight: 700 }}>{d.total}</td>
                  <td><span className="badge non-auto">{d.genuine}</span></td>
                  <td><span className="badge backdated">{d.false}</span></td>
                  <td><span className="badge auto">{d.autoResolving}</span></td>
                  <td>{d.snowCreated > 0 ? <span className="badge snow-new">{d.snowCreated}</span> : <span style={{ color: 'var(--text-tertiary)' }}>—</span>}</td>
                  <td>{d.snowReopened > 0 ? <span className="badge snow-reopen">{d.snowReopened}</span> : <span style={{ color: 'var(--text-tertiary)' }}>—</span>}</td>
                  <td>
                    <div className="mini-bar">
                      <div className="mini-bar-fill" style={{ width: `${d.pct}%`, background: d.genuine > d.false ? 'var(--accent-red)' : 'var(--accent-blue)' }} />
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
          <table className="data-table">
            <thead>
              <tr>
                <th>Event ID</th>
                <th>Device</th>
                <th>Severity</th>
                <th>Issue</th>
                <th>Timestamp</th>
                <th>Agent 1</th>
                <th>ML Classification</th>
                <th>Agent 3</th>
                <th>ServiceNow</th>
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
                    <td style={{ fontWeight: 700, fontSize: '0.8rem' }}>{details.event_id || `EVT-${i}`}</td>
                    <td>{details.device_name || 'Unknown'}</td>
                    <td><span className={`badge severity-${details.severity || 3}`}>{details.severity || '—'}</span></td>
                    <td style={{ maxWidth: '170px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{details.issue_name || '—'}</td>
                    <td style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>{details.timestamp ? new Date(details.timestamp).toLocaleString() : '—'}</td>
                    <td><span className={`badge ${isBackdated ? 'backdated' : 'auto-resolving'}`}>{isBackdated ? 'Suppressed' : 'Fresh'}</span></td>
                    <td>
                      <span className={`badge ${mlCategory.toLowerCase().replace(/[\s/]/g, '-')}`}>{mlCategory}</span>
                      {confidence && <span style={{ fontSize: '0.65rem', color: 'var(--text-tertiary)', marginLeft: '3px' }}>({confidence})</span>}
                    </td>
                    <td>{queueStatus ? <span className="badge delayed">Queued</span> : '—'}</td>
                    <td style={{ fontSize: '0.78rem', color: snowInc ? 'var(--accent-blue)' : 'var(--text-tertiary)', fontWeight: snowInc ? 600 : 400 }}>{snowDisplay}</td>
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
    </>
  );
}
