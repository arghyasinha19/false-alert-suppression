import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Activity, BarChart3, Monitor, Database, MessageSquare, Layers,
  ChevronRight, PanelLeftClose, PanelLeftOpen, Sun, Moon,
} from 'lucide-react';
import FalseAlertMetrics from './FalseAlertMetrics';
import AlertPatterns from './AlertPatterns';
import NetworkOperations from './NetworkOperations';
import ChatPanel from './ChatPanel';
import './App.css';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8004';
const POLL_INTERVAL = 15000;

const VIEW_CONFIGS = {
  metrics: {
    title: 'False Alert Suppression Metrics',
    breadcrumb: 'Alert Metrics',
    docTitle: 'Alert Metrics — DNAC Ops Center',
  },
  noc: {
    title: 'Network Operations Center',
    breadcrumb: 'Network Operations',
    docTitle: 'Network Operations — DNAC Ops Center',
  },
  patterns: {
    title: 'Alert Pattern Analysis',
    breadcrumb: 'Alert Patterns',
    docTitle: 'Alert Patterns — DNAC Ops Center',
  },
};

function App() {
  const [activeView, setActiveView] = useState('metrics');
  const [alerts, setAlerts] = useState([]);
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [apiConnected, setApiConnected] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [chatOpen, setChatOpen] = useState(false);
  const userToggledSidebar = useRef(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    try {
      if (typeof window !== 'undefined' && window.innerWidth <= 1100) {
        return true;
      }
      return localStorage.getItem('sidebar_collapsed') === 'true';
    } catch {
      return false;
    }
  });
  const [theme, setTheme] = useState(() => {
    try {
      const saved = localStorage.getItem('app_theme');
      if (saved === 'dark' || saved === 'light') return saved;
      return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    } catch {
      return 'light';
    }
  });

  // Auto-collapse sidebar below 1100px unless user manually toggled it in this session (D-01)
  useEffect(() => {
    const handleResize = () => {
      const isNarrow = window.innerWidth <= 1100;
      if (isNarrow && !userToggledSidebar.current) {
        setSidebarCollapsed(true);
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleToggleSidebar = () => {
    userToggledSidebar.current = true;
    setSidebarCollapsed(prev => !prev);
  };

  useEffect(() => {
    try {
      localStorage.setItem('sidebar_collapsed', String(sidebarCollapsed));
    } catch (e) {
      console.warn('Failed to save sidebar state to localStorage:', e);
    }
  }, [sidebarCollapsed]);

  useEffect(() => {
    try {
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('app_theme', theme);
    } catch (e) {
      console.warn('Failed to save theme to localStorage:', e);
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  };

  // Poll alerts
  const fetchData = useCallback(async () => {
    try {
      const [alertsRes, devicesRes] = await Promise.all([
        fetch(`${API_BASE}/api/alerts`).then(r => {
          if (!r.ok) throw new Error('Alerts fetch failed');
          return r.json();
        }),
        fetch(`${API_BASE}/api/devices`).then(r => {
          if (!r.ok) throw new Error('Devices fetch failed');
          return r.json();
        }),
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
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Update browser tab title on view change
  useEffect(() => {
    document.title = VIEW_CONFIGS[activeView]?.docTitle || 'DNAC Ops Center';
  }, [activeView]);

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
    {
      id: 'patterns',
      label: 'Alert Patterns',
      icon: <Layers size={18} />,
      description: 'Pattern clustering & volume',
    },
  ];

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-brand">
          <div className="sidebar-brand-left">
            <div className="sidebar-brand-icon">
              <Activity size={20} color="#fff" />
            </div>
            <div className="sidebar-brand-text">
              <h2>DNAC Ops Center</h2>
              <span>False Alert Suppression</span>
            </div>
          </div>
          <button
            className="sidebar-collapse-toggle"
            onClick={handleToggleSidebar}
            title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {sidebarCollapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
            {sidebarCollapsed && (
              <div className="nav-floating-tooltip">Expand sidebar</div>
            )}
          </button>
        </div>

        <nav className="sidebar-nav">
          {navItems.map(item => (
            <div
              key={item.id}
              className={`sidebar-nav-item ${activeView === item.id ? 'active' : ''}`}
              onClick={() => setActiveView(item.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setActiveView(item.id); }}
              aria-label={item.label}
            >
              {item.icon}
              <span className="sidebar-nav-label">{item.label}</span>
              <div className="nav-floating-tooltip">{item.label}</div>
            </div>
          ))}

          {/* Chat toggle */}
          <div
            className={`sidebar-nav-item ${chatOpen ? 'active' : ''}`}
            onClick={() => setChatOpen(!chatOpen)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setChatOpen(!chatOpen); }}
            style={{ marginTop: '0.5rem' }}
            aria-label="Ops Assistant"
          >
            <MessageSquare size={18} />
            <span className="sidebar-nav-label">Ops Assistant</span>
            {!chatOpen && <div className="chat-fab-badge" />}
            <div className="nav-floating-tooltip">Ops Assistant</div>
          </div>
        </nav>

        <div className="sidebar-status">
          <div className="sidebar-status-row">
            <div className={`sidebar-status-dot ${apiConnected ? '' : 'error'}`} />
            <Database size={13} />
            <span>{apiConnected ? 'API Connected' : 'Offline'}</span>
          </div>
          {lastRefresh && (
            <div className="sidebar-status-row sidebar-status-timestamp" style={{ marginTop: '0.4rem', fontSize: '0.72rem' }}>
              <span>Last refresh: {lastRefresh.toLocaleTimeString()}</span>
            </div>
          )}
          <div className="nav-floating-tooltip">
            {apiConnected ? 'API Connected' : 'Offline'}
            {lastRefresh ? ` • ${lastRefresh.toLocaleTimeString()}` : ''}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className={`content-area ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
        <div className="content-header">
          <div className="content-header-title-block">
            <nav className="breadcrumbs" aria-label="Breadcrumb">
              <span className="breadcrumb-root">DNAC Ops Center</span>
              <ChevronRight size={12} className="breadcrumb-separator" />
              <span className="breadcrumb-current">
                {VIEW_CONFIGS[activeView]?.breadcrumb || 'Overview'}
              </span>
            </nav>
            <h1>
              {VIEW_CONFIGS[activeView]?.title || 'Operations Center'}
            </h1>
          </div>
          <div className="content-header-actions">
            <button
              className="theme-toggle-btn"
              onClick={toggleTheme}
              title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
              aria-label={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
            >
              <span className="theme-toggle-icon">
                {theme === 'dark' ? <Sun size={14} color="#fbbf24" /> : <Moon size={14} />}
              </span>
              <span className="theme-toggle-label">{theme === 'dark' ? 'Light' : 'Dark'}</span>
            </button>
            <div className={`live-badge ${!apiConnected ? 'stale' : ''}`}>
              <span className={`dot ${!apiConnected ? 'error' : ''}`} />
              {apiConnected ? 'Live' : 'Stale'}
            </div>
            {!loading && (
              <span style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)' }}>
                {apiConnected && alerts.length > 0 ? `${alerts.length} alerts` : 'Mock Data (Demo)'}
              </span>
            )}
          </div>
        </div>

        <div className="content-body">
          {activeView === 'metrics' && (
            <div key="metrics" className="view-transition-container">
              <FalseAlertMetrics alerts={alerts} onRefresh={fetchData} />
            </div>
          )}
          {activeView === 'noc' && (
            <div key="noc" className="view-transition-container">
              <NetworkOperations
                devices={devices}
                lastRefresh={lastRefresh}
                pollInterval={POLL_INTERVAL}
                onRefresh={fetchData}
              />
            </div>
          )}
          {activeView === 'patterns' && (
            <div key="patterns" className="view-transition-container">
              <AlertPatterns />
            </div>
          )}
        </div>
      </main>

      {/* Chat Panel */}
      <ChatPanel isOpen={chatOpen} onClose={() => setChatOpen(false)} />
    </div>
  );
}

export default App;
