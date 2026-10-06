import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Activity, BarChart3, Monitor, Database, MessageSquare, Layers,
  ChevronRight, PanelLeftClose, PanelLeftOpen, Sun, Moon, RefreshCw, X, AlertTriangle,
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
  const [connectionState, setConnectionState] = useState({
    status: 'offline',
    lastSuccessfulSync: null,
    lastAttempt: null,
    error: null,
    consecutiveFailures: 0,
  });
  const [bannerDismissed, setBannerDismissed] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const consecutiveFailuresRef = useRef(0);
  const hadSuccessfulConnectionRef = useRef(false);
  const pollTimerRef = useRef(null);

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

  // Adaptive Retry Backoff: 10s on failure 1, 20s on failure 2, 60s for 3+ failures (D-13)
  const getBackoffInterval = (failures) => {
    if (failures <= 0) return POLL_INTERVAL;
    if (failures === 1) return 10000;
    if (failures === 2) return 20000;
    return 60000;
  };

  // Poll alerts with strict payload validation & frozen sync timestamp (D-05, D-06, D-08, D-15)
  const fetchData = useCallback(async (isManual = false) => {
    if (isManual) {
      setIsReconnecting(true);
    }
    const attemptTime = new Date();
    try {
      const [alertsRes, devicesRes] = await Promise.all([
        fetch(`${API_BASE}/api/alerts`).then(r => {
          if (!r.ok) throw new Error(`Alerts endpoint returned ${r.status}`);
          return r.json();
        }),
        fetch(`${API_BASE}/api/devices`).then(r => {
          if (!r.ok) throw new Error(`Devices endpoint returned ${r.status}`);
          return r.json();
        }),
      ]);

      // Strict payload validation (D-08, D-15)
      if (!Array.isArray(alertsRes?.alerts) || !Array.isArray(devicesRes?.devices)) {
        throw new Error('Malformed API payload structure: alerts or devices array missing');
      }

      setAlerts(alertsRes.alerts);
      setDevices(devicesRes.devices);
      consecutiveFailuresRef.current = 0;
      hadSuccessfulConnectionRef.current = true;

      setConnectionState({
        status: 'connected',
        lastSuccessfulSync: attemptTime,
        lastAttempt: attemptTime,
        error: null,
        consecutiveFailures: 0,
      });
    } catch (error) {
      console.warn('API fetch failed, using mock data:', error);
      consecutiveFailuresRef.current += 1;
      const failures = consecutiveFailuresRef.current;

      // Tri-state transition:
      // If previously connected and 1-2 consecutive failures -> 'stale'
      // If 3+ consecutive failures or never connected -> 'offline' (D-05)
      const newStatus = (hadSuccessfulConnectionRef.current && failures <= 2) ? 'stale' : 'offline';

      setConnectionState(prev => ({
        ...prev,
        status: newStatus,
        lastAttempt: attemptTime,
        error: error.message || 'Connection failed',
        consecutiveFailures: failures,
        // lastSuccessfulSync is frozen to previous value! (D-06)
      }));
    } finally {
      setLoading(false);
      if (isManual) {
        setIsReconnecting(false);
      }
    }
  }, []);

  const handleManualReconnect = useCallback(() => {
    if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    fetchData(true);
  }, [fetchData]);

  // Window focus listener triggers immediate reconnect when not connected (D-14)
  useEffect(() => {
    const handleFocus = () => {
      if (consecutiveFailuresRef.current > 0) {
        if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
        fetchData(false);
      }
    };
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [fetchData]);

  // Scheduled polling with progressive retry backoff
  useEffect(() => {
    let active = true;

    const scheduleNext = () => {
      const delay = getBackoffInterval(consecutiveFailuresRef.current);
      pollTimerRef.current = setTimeout(async () => {
        if (!active) return;
        await fetchData(false);
        if (active) {
          scheduleNext();
        }
      }, delay);
    };

    fetchData(false).then(() => {
      if (active) scheduleNext();
    });

    return () => {
      active = false;
      if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    };
  }, [fetchData]);

  const getBadgeTooltip = () => {
    const status = connectionState.status;
    const lines = [
      `Status: ${status === 'connected' ? 'Connected (Live)' : status === 'stale' ? 'Stale (1-2 failed polls)' : 'Offline'}`,
      `Endpoint: ${API_BASE}/api/alerts`,
    ];
    if (connectionState.lastSuccessfulSync) {
      lines.push(`Last Sync: ${connectionState.lastSuccessfulSync.toLocaleTimeString()}`);
    }
    if (connectionState.lastAttempt) {
      lines.push(`Last Attempt: ${connectionState.lastAttempt.toLocaleTimeString()}`);
    }
    if (connectionState.error) {
      lines.push(`Error: ${connectionState.error}`);
    }
    const nextIntervalSec = Math.round(getBackoffInterval(consecutiveFailuresRef.current) / 1000);
    lines.push(`Retry cadence: ${nextIntervalSec}s`);
    return lines.join('\n');
  };

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

  const chatToggleRef = useRef(null);

  // Global hotkey: Ctrl+/ or Cmd+/ toggles Ops Assistant chat panel (D-03)
  useEffect(() => {
    const handleGlobalKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        setChatOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, []);

  return (
    <div className={`app-shell ${chatOpen ? 'chat-open' : ''}`}>
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
            className="sidebar-collapse-toggle touch-target-expand"
            onClick={handleToggleSidebar}
            title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {sidebarCollapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
            {sidebarCollapsed && (
              <div className="nav-floating-tooltip" role="tooltip">Expand sidebar</div>
            )}
          </button>
        </div>

        <nav className="sidebar-nav">
          {navItems.map(item => (
            <button
              type="button"
              key={item.id}
              className={`sidebar-nav-item ${activeView === item.id ? 'active' : ''}`}
              onClick={() => setActiveView(item.id)}
              aria-current={activeView === item.id ? 'page' : undefined}
              aria-label={item.label}
            >
              {item.icon}
              <span className="sidebar-nav-label">{item.label}</span>
              <div className="nav-floating-tooltip" role="tooltip">{item.label}</div>
            </button>
          ))}

          {/* Chat toggle button */}
          <button
            type="button"
            ref={chatToggleRef}
            className={`sidebar-nav-item chat-nav-item ${chatOpen ? 'active' : ''}`}
            onClick={() => setChatOpen(prev => !prev)}
            aria-expanded={chatOpen}
            aria-controls="ops-assistant-panel"
            aria-label="Ops Assistant"
            style={{ marginTop: '0.5rem' }}
          >
            <MessageSquare size={18} />
            <span className="sidebar-nav-label">Ops Assistant</span>
            {!chatOpen && <div className="chat-fab-badge" />}
            <div className="nav-floating-tooltip" role="tooltip">Ops Assistant</div>
          </button>
        </nav>

        <div className="sidebar-status">
          <div className="sidebar-status-row">
            <div className={`sidebar-status-dot ${connectionState.status}`} />
            <Database size={13} />
            <span>
              {connectionState.status === 'connected'
                ? 'API Connected'
                : connectionState.status === 'stale'
                ? 'Stale (Retrying)'
                : 'Offline'}
            </span>
          </div>
          {connectionState.lastSuccessfulSync ? (
            <div className="sidebar-status-row sidebar-status-timestamp" style={{ marginTop: '0.4rem', fontSize: '0.72rem' }}>
              <span>
                {connectionState.status === 'connected'
                  ? `Last sync: ${connectionState.lastSuccessfulSync.toLocaleTimeString()}`
                  : `Last sync: ${connectionState.lastSuccessfulSync.toLocaleTimeString()} (Failed)`}
              </span>
            </div>
          ) : (
            <div className="sidebar-status-row sidebar-status-timestamp" style={{ marginTop: '0.4rem', fontSize: '0.72rem' }}>
              <span>Sync paused (Offline)</span>
            </div>
          )}
          {connectionState.status !== 'connected' && (
            <button
              className="sidebar-reconnect-btn"
              onClick={handleManualReconnect}
              disabled={isReconnecting}
              title="Trigger immediate API reconnection check"
            >
              <RefreshCw size={11} className={isReconnecting ? 'spin' : ''} />
              <span>{isReconnecting ? 'Reconnecting...' : 'Reconnect API'}</span>
            </button>
          )}
          <div className="nav-floating-tooltip">
            {connectionState.status === 'connected' ? 'API Connected' : 'Offline'}
            {connectionState.lastSuccessfulSync ? ` • ${connectionState.lastSuccessfulSync.toLocaleTimeString()}` : ''}
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
            {connectionState.status !== 'connected' && (
              <span
                className="mock-data-chip"
                title="Displaying simulated test telemetry because backend API is disconnected."
              >
                <Database size={12} />
                <span>Mock / Seed Data</span>
              </span>
            )}
            <div
              className={`live-badge ${connectionState.status}`}
              title={getBadgeTooltip()}
            >
              <span className={`dot ${connectionState.status}`} />
              <span>{connectionState.status === 'connected' ? 'Live' : connectionState.status === 'stale' ? 'Stale' : 'Offline'}</span>
            </div>
            {connectionState.status !== 'connected' && (
              <button
                className="header-reconnect-btn"
                onClick={handleManualReconnect}
                disabled={isReconnecting}
                title="Attempt immediate reconnection to backend API"
              >
                <RefreshCw size={11} className={isReconnecting ? 'spin' : ''} />
                <span>{isReconnecting ? 'Connecting...' : 'Reconnect'}</span>
              </button>
            )}
            {!loading && (
              <span style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)' }}>
                {connectionState.status === 'connected' && alerts.length > 0
                  ? `${alerts.length} alerts`
                  : 'Mock Data (Demo)'}
              </span>
            )}
          </div>
        </div>

        <div className="content-body">
          {connectionState.status !== 'connected' && !bannerDismissed && (
            <div className="demo-mode-banner" role="alert">
              <div className="demo-mode-banner-content">
                <div className="demo-mode-banner-title">
                  <Database size={15} />
                  <strong>Operating in Demo / Offline Mode</strong>
                </div>
                <p>
                  Displaying simulated test telemetry. Real-time Cisco DNA Center updates will resume automatically once backend connection is restored.
                  {connectionState.lastSuccessfulSync && (
                    <span className="demo-mode-sync-time">
                      {' '}Last valid sync: {connectionState.lastSuccessfulSync.toLocaleTimeString()} (Failed).
                    </span>
                  )}
                </p>
              </div>
              <div className="demo-mode-banner-actions">
                <button
                  className="demo-banner-reconnect-btn"
                  onClick={handleManualReconnect}
                  disabled={isReconnecting}
                  title="Attempt immediate backend connection"
                >
                  <RefreshCw size={11} className={isReconnecting ? 'spin' : ''} />
                  <span>{isReconnecting ? 'Reconnecting...' : 'Reconnect API'}</span>
                </button>
                <button
                  className="demo-banner-dismiss-btn"
                  onClick={() => setBannerDismissed(true)}
                  title="Dismiss notice"
                  aria-label="Dismiss notice"
                >
                  <X size={13} />
                  <span>Dismiss</span>
                </button>
              </div>
            </div>
          )}
          {activeView === 'metrics' && (
            <div key="metrics" className="view-transition-container">
              <FalseAlertMetrics
                alerts={alerts}
                onRefresh={handleManualReconnect}
                connectionStatus={connectionState.status}
                lastSuccessfulSync={connectionState.lastSuccessfulSync}
              />
            </div>
          )}
          {activeView === 'noc' && (
            <div key="noc" className="view-transition-container">
              <NetworkOperations
                devices={devices}
                lastRefresh={connectionState.lastSuccessfulSync}
                pollInterval={POLL_INTERVAL}
                onRefresh={handleManualReconnect}
                connectionStatus={connectionState.status}
                lastSuccessfulSync={connectionState.lastSuccessfulSync}
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
      <ChatPanel
        isOpen={chatOpen}
        onClose={() => setChatOpen(false)}
        triggerRef={chatToggleRef}
      />
    </div>
  );
}

export default App;
