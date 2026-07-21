import React from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from 'recharts';

const DEFAULT_COLORS = [
  '#2563eb', '#059669', '#dc2626', '#d97706',
  '#7c3aed', '#0891b2', '#ea580c', '#4f46e5',
  '#0d9488', '#be185d',
];

const CHART_TOOLTIP_STYLE = {
  backgroundColor: 'var(--card-bg, #fff)',
  border: '1px solid var(--card-border, #e2e8f0)',
  borderRadius: '8px',
  boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
  fontSize: '0.82rem',
  padding: '8px 12px',
};

function ChatChart({ spec }) {
  if (!spec || !spec.data || spec.data.length === 0) {
    return (
      <div className="chat-chart-empty">
        No data available for visualization.
      </div>
    );
  }

  const {
    chart_type = 'bar',
    title = '',
    data,
    x_key = 'label',
    y_key = 'value',
    colors = [],
    multi_series_keys = [],
  } = spec;

  const palette = colors.length > 0 ? colors : DEFAULT_COLORS;

  const renderChart = () => {
    switch (chart_type) {
      case 'pie':
        return renderPie();
      case 'line':
        return renderLine();
      case 'area':
        return renderArea();
      case 'bar':
      default:
        return renderBar();
    }
  };

  // --- BAR ---
  const renderBar = () => {
    if (multi_series_keys.length > 0) {
      return (
        <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--card-border, #e2e8f0)" />
          <XAxis dataKey={x_key} tick={{ fontSize: 11, fill: 'var(--text-secondary, #475569)' }} />
          <YAxis tick={{ fontSize: 11, fill: 'var(--text-secondary, #475569)' }} />
          <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
          <Legend wrapperStyle={{ fontSize: '0.78rem' }} />
          {multi_series_keys.map((key, i) => (
            <Bar key={key} dataKey={key} fill={palette[i % palette.length]} radius={[4, 4, 0, 0]} />
          ))}
        </BarChart>
      );
    }
    return (
      <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--card-border, #e2e8f0)" />
        <XAxis dataKey={x_key} tick={{ fontSize: 11, fill: 'var(--text-secondary, #475569)' }} />
        <YAxis tick={{ fontSize: 11, fill: 'var(--text-secondary, #475569)' }} />
        <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
        <Bar dataKey={y_key} radius={[4, 4, 0, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={palette[i % palette.length]} />
          ))}
        </Bar>
      </BarChart>
    );
  };

  // --- LINE ---
  const renderLine = () => {
    const keys = multi_series_keys.length > 0 ? multi_series_keys : [y_key];
    return (
      <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--card-border, #e2e8f0)" />
        <XAxis dataKey={x_key} tick={{ fontSize: 11, fill: 'var(--text-secondary, #475569)' }} />
        <YAxis tick={{ fontSize: 11, fill: 'var(--text-secondary, #475569)' }} />
        <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
        {keys.length > 1 && <Legend wrapperStyle={{ fontSize: '0.78rem' }} />}
        {keys.map((key, i) => (
          <Line
            key={key}
            type="monotone"
            dataKey={key}
            stroke={palette[i % palette.length]}
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        ))}
      </LineChart>
    );
  };

  // --- AREA ---
  const renderArea = () => {
    const keys = multi_series_keys.length > 0 ? multi_series_keys : [y_key];
    return (
      <AreaChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--card-border, #e2e8f0)" />
        <XAxis dataKey={x_key} tick={{ fontSize: 11, fill: 'var(--text-secondary, #475569)' }} />
        <YAxis tick={{ fontSize: 11, fill: 'var(--text-secondary, #475569)' }} />
        <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
        {keys.length > 1 && <Legend wrapperStyle={{ fontSize: '0.78rem' }} />}
        {keys.map((key, i) => (
          <Area
            key={key}
            type="monotone"
            dataKey={key}
            stroke={palette[i % palette.length]}
            fill={palette[i % palette.length]}
            fillOpacity={0.15}
            strokeWidth={2}
          />
        ))}
      </AreaChart>
    );
  };

  // --- PIE ---
  const renderPie = () => (
    <PieChart>
      <Pie
        data={data}
        dataKey={y_key}
        nameKey={x_key}
        cx="50%"
        cy="50%"
        outerRadius="75%"
        innerRadius="40%"
        paddingAngle={2}
        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
        labelLine={{ stroke: 'var(--text-tertiary, #94a3b8)', strokeWidth: 1 }}
      >
        {data.map((_, i) => (
          <Cell key={i} fill={palette[i % palette.length]} />
        ))}
      </Pie>
      <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
      <Legend wrapperStyle={{ fontSize: '0.78rem' }} />
    </PieChart>
  );

  return (
    <div className="chat-chart-container">
      {title && <div className="chat-chart-title">{title}</div>}
      <div className="chat-chart-body">
        <ResponsiveContainer width="100%" height={260}>
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default ChatChart;
