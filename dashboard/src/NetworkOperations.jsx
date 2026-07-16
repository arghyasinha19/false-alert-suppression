import React, { useState, useMemo, useEffect } from 'react';
import {
  MapPin, Server, AlertTriangle, CheckCircle, HelpCircle,
  Search, X, Clock, Wifi, WifiOff, Shield, AlertOctagon,
  Activity, Ticket, PlusCircle, RotateCcw, MessageSquarePlus
} from 'lucide-react';

const LOCATION_LABELS = {
  'UK-MAL': '🇬🇧 United Kingdom — Maldon',
  'UK-LON': '🇬🇧 United Kingdom — London',
  'US-NY':  '🇺🇸 United States — New York',
  'US-CHI': '🇺🇸 United States — Chicago',
  'SG-SIN': '🇸🇬 Singapore',
  'DE-FRA': '🇩🇪 Germany — Frankfurt',
  'JP-TKY': '🇯🇵 Japan — Tokyo',
  'IN-MUM': '🇮🇳 India — Mumbai',
  'AU-SYD': '🇦🇺 Australia — Sydney',
};

function deriveLocation(name) {
  if (!name || name === 'Unknown') return 'Unknown';
  const parts = name.split('-');
  if (parts.length >= 2) return `${parts[0]}-${parts[1]}`;
  return parts[0] || 'Unknown';
}

function getLocationLabel(loc) { return LOCATION_LABELS[loc] || `📍 ${loc}`; }

function getDeviceHealth(device) {
  const activeAlerts = device.active_alerts || [];
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

export default function NetworkOperations({ devices: rawDevices }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [panelOpen, setPanelOpen] = useState(false);

  const devices = rawDevices;

  // Freeze body scroll when detail panel is open
  useEffect(() => {
    if (panelOpen) {
      document.body.classList.add('panel-open');
    } else {
      document.body.classList.remove('panel-open');
    }
    return () => document.body.classList.remove('panel-open');
  }, [panelOpen]);

  const filteredDevices = useMemo(() => {
    if (!searchQuery) return devices;
    const q = searchQuery.toLowerCase();
    return devices.filter(d => d.device_name.toLowerCase().includes(q) || d.location?.toLowerCase().includes(q));
  }, [devices, searchQuery]);

  const locationGroups = useMemo(() => {
    const groups = {};
    filteredDevices.forEach(d => {
      const loc = d.location || deriveLocation(d.device_name);
      if (!groups[loc]) groups[loc] = [];
      groups[loc].push(d);
    });
    return Object.entries(groups).sort(([a], [b]) => {
      if (a === 'Unknown') return 1;
      if (b === 'Unknown') return -1;
      return a.localeCompare(b);
    });
  }, [filteredDevices]);

  const healthKPI = useMemo(() => {
    let healthy = 0, warning = 0, critical = 0, unknown = 0;
    devices.forEach(d => {
      const h = getDeviceHealth(d);
      if (h === 'healthy') healthy++;
      else if (h === 'warning') warning++;
      else if (h === 'critical') critical++;
      else unknown++;
    });
    return { total: devices.length, healthy, warning, critical, unknown };
  }, [devices]);

  const openDevicePanel = (device) => { setSelectedDevice(device); setPanelOpen(true); };
  const closePanel = () => { setPanelOpen(false); setTimeout(() => setSelectedDevice(null), 300); };

  return (
    <>
      {/* Health Summary KPIs */}
      <div className="noc-summary-grid">
        <div className="glass-card kpi-card highlight-blue">
          <div className="kpi-icon blue"><Server size={20} /></div>
          <div className="kpi-content">
            <h3>Total Devices</h3>
            <p className="value">{healthKPI.total}</p>
          </div>
        </div>
        <div className="glass-card kpi-card highlight-green">
          <div className="kpi-icon green"><CheckCircle size={20} /></div>
          <div className="kpi-content">
            <h3>Healthy</h3>
            <p className="value" style={{ color: 'var(--accent-green)' }}>{healthKPI.healthy}</p>
          </div>
        </div>
        <div className="glass-card kpi-card highlight-yellow">
          <div className="kpi-icon yellow"><AlertTriangle size={20} /></div>
          <div className="kpi-content">
            <h3>Warning</h3>
            <p className="value" style={{ color: 'var(--accent-yellow)' }}>{healthKPI.warning}</p>
          </div>
        </div>
        <div className="glass-card kpi-card highlight-red">
          <div className="kpi-icon red"><AlertOctagon size={20} /></div>
          <div className="kpi-content">
            <h3>Critical</h3>
            <p className="value" style={{ color: 'var(--accent-red)' }}>{healthKPI.critical}</p>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="filter-bar">
        <Search size={15} style={{ color: 'var(--text-tertiary)' }} />
        <input className="filter-search" type="text" placeholder="Search devices by name or location..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
        {searchQuery && (
          <button className="filter-pill" onClick={() => setSearchQuery('')} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <X size={12} /> Clear
          </button>
        )}
        <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginLeft: 'auto' }}>
          {filteredDevices.length} device{filteredDevices.length !== 1 ? 's' : ''} shown
        </span>
      </div>

      {/* Location Groups */}
      {locationGroups.map(([location, locDevices]) => (
        <div key={location} className="location-group">
          <div className="location-header">
            <MapPin size={15} style={{ color: 'var(--accent-blue)' }} />
            <h3>{getLocationLabel(location)}</h3>
            <span className="device-count">{locDevices.length} device{locDevices.length !== 1 ? 's' : ''}</span>
          </div>

          <div className="device-grid">
            {locDevices.map(device => {
              const health = getDeviceHealth(device);
              const isAlerting = health === 'critical' || health === 'warning';
              const activeCount = (device.active_alerts || []).length;
              const snow = getSnowSummary(device);

              return (
                <div key={device.device_name} className={`device-tile ${isAlerting ? 'alerting' : 'healthy'}`} onClick={() => openDevicePanel(device)}>
                  <div className="device-tile-header">
                    <span className="device-tile-name">{device.device_name}</span>
                    <span className={`device-tile-status-dot ${health}`} />
                  </div>
                  <div className="device-tile-meta">
                    <span>
                      {health === 'critical' ? <WifiOff size={12} /> : <Wifi size={12} />}
                      {health === 'critical' ? 'Critical' : health === 'warning' ? 'Warning' : 'Healthy'}
                    </span>
                    {device.last_alert_time && (
                      <span><Clock size={12} /> Last: {new Date(device.last_alert_time).toLocaleTimeString()}</span>
                    )}
                    <span><Activity size={12} /> {device.total_alerts} total alerts</span>
                  </div>
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
            })}
          </div>
        </div>
      ))}

      {filteredDevices.length === 0 && (
        <div className="empty-state"><Server size={48} /><p>No devices match your search.</p></div>
      )}

      {/* Detail Panel Overlay */}
      <div className={`detail-overlay ${panelOpen ? 'open' : ''}`} onClick={closePanel} />

      {/* Detail Slide-Out Panel */}
      <div className={`detail-panel ${panelOpen ? 'open' : ''}`}>
        {selectedDevice && (() => {
          const snow = getSnowSummary(selectedDevice);
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

                {/* Active Alerts */}
                <h3 style={{ fontSize: '0.88rem', marginBottom: '0.6rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <AlertTriangle size={15} /> Active Alerts ({(selectedDevice.active_alerts || []).length})
                </h3>

                {(selectedDevice.active_alerts || []).length === 0 ? (
                  <div className="empty-state" style={{ padding: '1.5rem' }}><Shield size={28} /><p>No active alerts for this device.</p></div>
                ) : (
                  (selectedDevice.active_alerts || []).map((alert, i) => (
                    <div key={i} className="detail-alert-item">
                      <h4 style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span className={`badge severity-${alert.severity || 3}`}>SEV {alert.severity || '?'}</span>
                        {alert.issue_name || 'Unknown Alert'}
                      </h4>
                      <p>{alert.issue_details || 'No details available.'}</p>
                      <div className="detail-meta-grid">
                        <div className="detail-meta-item"><div className="label">Event ID</div><div className="value">{alert.event_id || '—'}</div></div>
                        <div className="detail-meta-item"><div className="label">Category</div><div className="value">{alert.category || '—'}</div></div>
                        <div className="detail-meta-item">
                          <div className="label">Classification</div>
                          <div className="value"><span className={`badge ${(alert.predicted_category || '').toLowerCase().replace(/[\s/]/g, '-')}`}>{alert.predicted_category || '—'}</span></div>
                        </div>
                        <div className="detail-meta-item"><div className="label">Time</div><div className="value">{alert.timestamp ? new Date(alert.timestamp).toLocaleString() : '—'}</div></div>
                        {alert.snow_incident && (<div className="detail-meta-item"><div className="label">SNOW Incident</div><div className="value" style={{ color: 'var(--accent-blue)', fontWeight: 700 }}>{alert.snow_incident}</div></div>)}
                        {alert.snow_action && (<div className="detail-meta-item"><div className="label">SNOW Action</div><div className="value">{alert.snow_action.replace(/_/g, ' ')}</div></div>)}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </>
          );
        })()}
      </div>
    </>
  );
}
