import React, { useState, useEffect } from 'react';
import {
  Activity, BarChart3, Monitor, Database, Radio
} from 'lucide-react';
import FalseAlertMetrics from './FalseAlertMetrics';
import NetworkOperations from './NetworkOperations';
import './App.css';

const API_BASE = 'http://127.0.0.1:8000';
const POLL_INTERVAL = 10000;

function App() {
  const [activeView, setActiveView] = useState('metrics');
  const [alerts, setAlerts] = useState([]);
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [apiConnected, setApiConnected] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);

  // Poll alerts
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [alertsRes, devicesRes] = await Promise.all([
          fetch(`${API_BASE}/api/alerts`).then(r => r.json()).catch(() => ({ alerts: [] })),
          fetch(`${API_BASE}/api/devices`).then(r => r.json()).catch(() => ({ devices: [] })),
        ]);

        if (alertsRes.alerts) setAlerts(alertsRes.alerts);
        if (devicesRes.devices) setDevices(devicesRes.devices);
        setApiConnected(true);
      } catch (error) {
        console.warn('API fetch failed, using mock data:', error);
        setApiConnected(false);
      } finally {
        setLoading(false);
        setLastRefresh(new Date());
      }
    };

    fetchData();
    const interval = setInterval(fetchData, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    {
      id: 'metrics',
      label: 'Alert Metrics',
      icon: <BarChart3 size={18} />,
      description: 'False alert suppression KPIs',
    },
    {
      id: 'noc',
      label: 'Network Operations',
      icon: <Monitor size={18} />,
      description: 'Live device health overview',
    },
  ];

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">
            <Activity size={20} color="#fff" />
          </div>
          <div>
            <h2>DNAC Ops Center</h2>
            <span>False Alert Suppression</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map(item => (
            <div
              key={item.id}
              className={`sidebar-nav-item ${activeView === item.id ? 'active' : ''}`}
              onClick={() => setActiveView(item.id)}
            >
              {item.icon}
              <span>{item.label}</span>
            </div>
          ))}
        </nav>

        <div className="sidebar-status">
          <div className="sidebar-status-row">
            <div className={`sidebar-status-dot ${apiConnected ? '' : 'error'}`} />
            <Database size={13} />
            <span>{apiConnected ? 'API Connected' : 'Offline'}</span>
          </div>
          {lastRefresh && (
            <div className="sidebar-status-row" style={{ marginTop: '0.4rem', fontSize: '0.72rem' }}>
              <span>Last refresh: {lastRefresh.toLocaleTimeString()}</span>
            </div>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="content-area">
        <div className="content-header">
          <h1>
            {activeView === 'metrics' ? 'False Alert Suppression Metrics' : 'Network Operations Center'}
          </h1>
          <div className="content-header-actions">
            <div className="live-badge">
              <span className="dot" />
              Live
            </div>
            {!loading && (
              <span style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)' }}>
                {alerts.length > 0 ? `${alerts.length} alerts` : '0 alerts'}
              </span>
            )}
          </div>
        </div>

        <div className="content-body">
          {activeView === 'metrics' && (
            <FalseAlertMetrics alerts={alerts} />
          )}
          {activeView === 'noc' && (
            <NetworkOperations devices={devices} />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
