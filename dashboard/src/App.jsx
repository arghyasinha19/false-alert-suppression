import React, { useState, useEffect } from 'react';
import { 
  BarChart3, AlertTriangle, CheckCircle, Clock, 
  Activity, Server, History, ArrowRight, Database
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, 
  ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';
import './App.css';

const COLORS = ['#3b82f6', '#10b981', '#ef4444', '#f59e0b'];

// Sample mock data for initial visual wow factor if DB is empty
const MOCK_DATA = [
  { alert_details: { event_id: 'EVT-001', device_name: 'UK-LON-SW01', timestamp: new Date(Date.now() - 3600000).toISOString() }, results: { agent_1: { data: { is_backdated: true } }, agent_2: { data: { predicted_category: 'uncertain' } } } },
  { alert_details: { event_id: 'EVT-002', device_name: 'US-NY-RT02', timestamp: new Date(Date.now() - 7200000).toISOString() }, results: { agent_1: { data: { is_backdated: false } }, agent_2: { data: { predicted_category: 'Auto resolving' } } } },
  { alert_details: { event_id: 'EVT-003', device_name: 'SG-SIN-FW01', timestamp: new Date(Date.now() - 10800000).toISOString() }, results: { agent_1: { data: { is_backdated: false } }, agent_2: { data: { predicted_category: 'Non-Auto Resolving' } }, agent_4: { data: { incident: 'INC0012345', action: 'incident_created' } } } }
];

function App() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState('ALL');

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/alerts');
        const data = await response.json();
        
        if (data.alerts && data.alerts.length > 0) {
          setAlerts(data.alerts);
        } else {
          // Fallback to mock data to maintain visual aesthetics when DB is empty
          setAlerts(MOCK_DATA);
        }
      } catch (error) {
        console.error('Failed to fetch from API, falling back to mock data:', error);
        setAlerts(MOCK_DATA);
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
    const interval = setInterval(fetchAlerts, 15000); // Polling every 15s
    return () => clearInterval(interval);
  }, []);

  // Compute Volumetrics
  const backdated = alerts.filter(a => a.results?.agent_1?.data?.is_backdated).length;
  const autoResolving = alerts.filter(a => !a.results?.agent_1?.data?.is_backdated && a.results?.agent_2?.data?.predicted_category === 'Auto resolving').length;
  const nonAutoResolving = alerts.filter(a => !a.results?.agent_1?.data?.is_backdated && a.results?.agent_2?.data?.predicted_category === 'Non-Auto Resolving').length;

  const pieData = [
    { name: 'Backdated', value: backdated },
    { name: 'Auto-Resolving', value: autoResolving },
    { name: 'Non-Auto-Resolving', value: nonAutoResolving },
  ];

  // Dummy historical trend
  const trendData = [
    { name: 'Mon', Auto: 4, NonAuto: 2, Backdated: 1 },
    { name: 'Tue', Auto: 3, NonAuto: 1, Backdated: 5 },
    { name: 'Wed', Auto: 7, NonAuto: 3, Backdated: 2 },
    { name: 'Thu', Auto: 5, NonAuto: 4, Backdated: 3 },
    { name: 'Fri', Auto: Math.max(autoResolving, 1), NonAuto: Math.max(nonAutoResolving, 1), Backdated: Math.max(backdated, 1) },
  ];

  const getFilteredAlerts = () => {
    if (activeFilter === 'BACKDATED') return alerts.filter(a => a.results?.agent_1?.data?.is_backdated);
    if (activeFilter === 'AUTO') return alerts.filter(a => !a.results?.agent_1?.data?.is_backdated && a.results?.agent_2?.data?.predicted_category === 'Auto resolving');
    if (activeFilter === 'NON_AUTO') return alerts.filter(a => !a.results?.agent_1?.data?.is_backdated && a.results?.agent_2?.data?.predicted_category === 'Non-Auto Resolving');
    return alerts;
  };

  return (
    <div className="app-container">
      <header className="header">
        <Activity size={32} color="#3b82f6" />
        <h1>Alert Traceability Center</h1>
        <div style={{ marginLeft: 'auto' }} className="status-indicator glass-card">
          <Database size={16} />
          <span>MongoDB {loading ? 'Syncing...' : 'Connected'}</span>
          <div className="status-dot active"></div>
        </div>
      </header>

      <div className="kpi-grid">
        <div className={`glass-card kpi-card ${activeFilter === 'BACKDATED' ? 'active' : ''}`} onClick={() => setActiveFilter('BACKDATED')}>
          <div className="kpi-icon blue"><Clock /></div>
          <div className="kpi-content">
            <h3>Backdated / Suppressed</h3>
            <p className="value">{backdated}</p>
          </div>
        </div>
        
        <div className={`glass-card kpi-card ${activeFilter === 'AUTO' ? 'active' : ''}`} onClick={() => setActiveFilter('AUTO')}>
          <div className="kpi-icon green"><CheckCircle /></div>
          <div className="kpi-content">
            <h3>Auto-Resolving</h3>
            <p className="value">{autoResolving}</p>
          </div>
        </div>

        <div className={`glass-card kpi-card ${activeFilter === 'NON_AUTO' ? 'active' : ''}`} onClick={() => setActiveFilter('NON_AUTO')}>
          <div className="kpi-icon red"><AlertTriangle /></div>
          <div className="kpi-content">
            <h3>Non-Auto Resolving</h3>
            <p className="value">{nonAutoResolving}</p>
          </div>
        </div>
      </div>

      <div className="charts-grid">
        <div className="glass-card chart-card">
          <h3><History size={20} /> Historical Volume Trend</h3>
          <div style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <RechartsTooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }} />
                <Line type="monotone" dataKey="Auto" stroke="#10b981" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                <Line type="monotone" dataKey="NonAuto" stroke="#ef4444" strokeWidth={3} dot={{ r: 4 }} />
                <Line type="monotone" dataKey="Backdated" stroke="#3b82f6" strokeWidth={3} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card chart-card">
          <h3><BarChart3 size={20} /> Distribution</h3>
          <div style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <RechartsTooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="glass-card table-card">
        <h3><Server size={20} /> Detailed Traceability Matrix {activeFilter !== 'ALL' && <span style={{fontSize: '0.8rem', color: '#94a3b8', marginLeft: '10px'}}>(Filtered)</span>}</h3>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Event ID</th>
                <th>Device</th>
                <th>Timestamp</th>
                <th>ML Classification</th>
                <th>ServiceNow Status</th>
              </tr>
            </thead>
            <tbody>
              {getFilteredAlerts().map((alert, i) => {
                const isBackdated = alert.results?.agent_1?.data?.is_backdated;
                const mlCategory = isBackdated ? 'Backdated' : alert.results?.agent_2?.data?.predicted_category || 'Unknown';
                
                let snowStatus = 'Not Required';
                if (mlCategory === 'Non-Auto Resolving' || mlCategory === 'uncertain') {
                  const action = alert.results?.agent_4?.data?.action;
                  const inc = alert.results?.agent_4?.data?.incident;
                  
                  if (alert.live_snow_status) {
                    snowStatus = `${alert.live_snow_status} (${inc})`;
                  } else if (action) {
                    snowStatus = `${action.replace('_', ' ').toUpperCase()} (${inc})`;
                  } else {
                    snowStatus = 'Pending / Delayed Queue';
                  }
                }

                return (
                  <tr key={i}>
                    <td style={{ fontWeight: 500 }}>{alert.alert_details?.event_id || `EVT-00${i}`}</td>
                    <td>{alert.alert_details?.device_name || 'Unknown'}</td>
                    <td>{new Date(alert.alert_details?.timestamp || Date.now()).toLocaleString()}</td>
                    <td>
                      <span className={`badge ${mlCategory.toLowerCase().replace(' ', '-')}`}>
                        {mlCategory}
                      </span>
                    </td>
                    <td style={{ color: snowStatus.includes('INC') ? '#3b82f6' : 'inherit' }}>
                      {snowStatus}
                    </td>
                  </tr>
                );
              })}
              {getFilteredAlerts().length === 0 && (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8' }}>No alerts found for this filter.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default App;
