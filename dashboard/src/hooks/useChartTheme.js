import { useState, useEffect } from 'react';

/**
 * Custom React hook that resolves theme-aware colors and styles for Recharts and SVG charts.
 * Reacts automatically to mutations on `document.documentElement[data-theme]`.
 */
export function useChartTheme() {
  const getTheme = () => {
    if (typeof document !== 'undefined') {
      return document.documentElement.getAttribute('data-theme') || 'dark';
    }
    return 'dark';
  };

  const [theme, setTheme] = useState(getTheme);

  useEffect(() => {
    if (typeof document === 'undefined') return;

    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
          const newTheme = document.documentElement.getAttribute('data-theme') || 'dark';
          setTheme(newTheme);
        }
      }
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    });

    const handleStorage = (e) => {
      if (e.key === 'app_theme' && e.newValue) {
        setTheme(e.newValue);
      }
    };
    window.addEventListener('storage', handleStorage);

    return () => {
      observer.disconnect();
      window.removeEventListener('storage', handleStorage);
    };
  }, []);

  const isDark = theme === 'dark';

  return {
    theme,
    isDark,
    colors: {
      primary: isDark ? '#3b82f6' : '#2563eb',
      primaryBright: isDark ? '#60a5fa' : '#3b82f6',
      primaryLight: isDark ? 'rgba(59, 130, 246, 0.16)' : '#eff6ff',
      success: isDark ? '#10b981' : '#059669',
      successBright: isDark ? '#34d399' : '#10b981',
      danger: isDark ? '#ef4444' : '#dc2626',
      dangerBright: isDark ? '#f87171' : '#ef4444',
      warning: isDark ? '#f59e0b' : '#d97706',
      warningBright: isDark ? '#fbbf24' : '#f59e0b',
      purple: isDark ? '#8b5cf6' : '#7c3aed',
      purpleLight: isDark ? 'rgba(139, 92, 246, 0.16)' : '#f5f3ff',
      cyan: isDark ? '#06b6d4' : '#0891b2',
      orange: isDark ? '#f97316' : '#ea580c',
      indigo: isDark ? '#6366f1' : '#4f46e5',
      slate: isDark ? '#94a3b8' : '#64748b',
    },
    axis: {
      stroke: isDark ? '#cbd5e1' : '#475569',
      tickFill: isDark ? '#cbd5e1' : '#475569',
      fontSize: 10,
    },
    grid: {
      stroke: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)',
      dashArray: '3 3',
    },
    tooltipStyle: {
      backgroundColor: isDark ? '#111827' : '#ffffff',
      border: `1px solid ${isDark ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.08)'}`,
      borderRadius: '10px',
      boxShadow: isDark ? '0 10px 15px -3px rgba(0, 0, 0, 0.5)' : '0 10px 15px -3px rgba(0, 0, 0, 0.08)',
      color: isDark ? '#f8fafc' : '#0f172a',
      fontSize: '0.82rem',
      padding: '10px 14px',
    },
    legendStyle: {
      fontSize: '0.72rem',
      color: isDark ? '#cbd5e1' : '#475569',
    },
  };
}

export default useChartTheme;
