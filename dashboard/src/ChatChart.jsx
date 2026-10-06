import React, { useState, useCallback, useMemo } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceArea,
} from 'recharts';
import { ZoomIn, RotateCcw, Maximize2 } from 'lucide-react';
import useChartTheme from './hooks/useChartTheme';



/* ---- Helper: format a label key into a human-readable string ---- */
function humanizeKey(key) {
  if (!key) return '';
  return key
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/* ---- Helper: truncate long tick labels ---- */
function truncateLabel(val, maxLen = 14) {
  const s = String(val ?? '');
  return s.length > maxLen ? s.slice(0, maxLen - 1) + '…' : s;
}

/* ---- Custom axis tick with rotation for long labels ---- */
function AngledTick({ x, y, payload, maxLen = 14, fill }) {
  const label = truncateLabel(payload.value, maxLen);
  return (
    <g transform={`translate(${x},${y})`}>
      <text
        x={0} y={0} dy={12}
        textAnchor="end"
        fill={fill || "var(--text-secondary, #475569)"}
        fontSize={10}
        transform="rotate(-35)"
      >
        {label}
      </text>
    </g>
  );
}

/* ====================================================================
   ZoomableChart — wraps Bar / Line / Area with drag-to-zoom
   ==================================================================== */
function ZoomableChart({ data, x_key, renderInner, chartType: ChartType, margin }) {
  const chartTheme = useChartTheme();
  const [refAreaLeft, setRefAreaLeft] = useState(null);
  const [refAreaRight, setRefAreaRight] = useState(null);
  const [zoomLeft, setZoomLeft] = useState(null);
  const [zoomRight, setZoomRight] = useState(null);

  const isZoomed = zoomLeft !== null && zoomRight !== null;

  const visibleData = isZoomed
    ? (() => {
        const leftIdx = data.findIndex((d) => d[x_key] === zoomLeft);
        const rightIdx = data.findIndex((d) => d[x_key] === zoomRight);
        if (leftIdx === -1 || rightIdx === -1) return data;
        const lo = Math.min(leftIdx, rightIdx);
        const hi = Math.max(leftIdx, rightIdx);
        return data.slice(lo, hi + 1);
      })()
    : data;

  const handleMouseDown = useCallback((e) => {
    if (e && e.activeLabel != null) {
      setRefAreaLeft(e.activeLabel);
      setRefAreaRight(null);
    }
  }, []);

  const handleMouseMove = useCallback((e) => {
    if (refAreaLeft != null && e && e.activeLabel != null) {
      setRefAreaRight(e.activeLabel);
    }
  }, [refAreaLeft]);

  const handleMouseUp = useCallback(() => {
    if (refAreaLeft != null && refAreaRight != null && refAreaLeft !== refAreaRight) {
      const leftIdx = data.findIndex((d) => d[x_key] === refAreaLeft);
      const rightIdx = data.findIndex((d) => d[x_key] === refAreaRight);
      const lo = Math.min(leftIdx, rightIdx);
      const hi = Math.max(leftIdx, rightIdx);
      if (lo >= 0 && hi >= 0 && lo !== hi) {
        setZoomLeft(data[lo][x_key]);
        setZoomRight(data[hi][x_key]);
      }
    }
    setRefAreaLeft(null);
    setRefAreaRight(null);
  }, [refAreaLeft, refAreaRight, data, x_key]);

  const resetZoom = useCallback(() => {
    setZoomLeft(null);
    setZoomRight(null);
    setRefAreaLeft(null);
    setRefAreaRight(null);
  }, []);

  const needsAngle = visibleData.some((d) => String(d[x_key] ?? '').length > 6);

  return (
    <div className="chat-chart-zoom-wrapper">
      {isZoomed && (
        <button className="chat-chart-zoom-reset" onClick={resetZoom} title="Reset zoom">
          <RotateCcw size={12} />
          Reset zoom
        </button>
      )}
      {!isZoomed && data.length > 3 && (
        <div className="chat-chart-zoom-hint">
          <ZoomIn size={11} />
          <span>Drag to zoom</span>
        </div>
      )}
      <ResponsiveContainer width="100%" height={280}>
        <ChartType
          data={visibleData}
          margin={margin || { top: 10, right: 20, left: 4, bottom: needsAngle ? 32 : 4 }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
        >
          <CartesianGrid strokeDasharray={chartTheme.grid.dashArray} stroke={chartTheme.grid.stroke} />
          <XAxis
            dataKey={x_key}
            stroke={chartTheme.axis.stroke}
            tick={needsAngle ? <AngledTick maxLen={16} fill={chartTheme.axis.tickFill} /> : { fontSize: 11, fill: chartTheme.axis.tickFill }}
            interval={visibleData.length > 20 ? Math.floor(visibleData.length / 10) : 0}
          />
          <YAxis
            stroke={chartTheme.axis.stroke}
            tick={{ fontSize: 11, fill: chartTheme.axis.tickFill }}
            allowDecimals={false}
          />
          <Tooltip contentStyle={chartTheme.tooltipStyle} />

          {renderInner(visibleData)}

          {refAreaLeft && refAreaRight && (
            <ReferenceArea
              x1={refAreaLeft}
              x2={refAreaRight}
              strokeOpacity={0.3}
              fill={chartTheme.colors.primary}
              fillOpacity={0.12}
            />
          )}

        </ChartType>
      </ResponsiveContainer>
    </div>
  );
}

/* ====================================================================
   ChatChart — main exported component
   ==================================================================== */
function ChatChart({ spec }) {
  const [expanded, setExpanded] = useState(false);
  const chartTheme = useChartTheme();
  const defaultPalette = useMemo(() => [
    chartTheme.colors.primary,
    chartTheme.colors.success,
    chartTheme.colors.danger,
    chartTheme.colors.warning,
    chartTheme.colors.purple,
    chartTheme.colors.cyan,
    chartTheme.colors.orange,
    chartTheme.colors.indigo,
  ], [chartTheme]);

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

  const palette = colors.length > 0 ? colors : defaultPalette;

  const renderChart = () => {
    switch (chart_type) {
      case 'pie':
        return renderPie();
      case 'line':
        return renderZoomableLine();
      case 'area':
        return renderZoomableArea();
      case 'bar':
      default:
        return renderZoomableBar();
    }
  };

  // --- ZOOMABLE BAR ---
  const renderZoomableBar = () => {
    if (multi_series_keys.length > 0) {
      return (
        <ZoomableChart
          data={data}
          x_key={x_key}
          chartType={BarChart}
          showBrush={false}
          renderInner={() => (
            <>
              <Legend wrapperStyle={{ fontSize: '0.78rem' }} />
              {multi_series_keys.map((key, i) => (
                <Bar key={key} dataKey={key} name={humanizeKey(key)} fill={palette[i % palette.length]} radius={[4, 4, 0, 0]} />
              ))}
            </>
          )}
        />
      );
    }
    return (
      <ZoomableChart
        data={data}
        x_key={x_key}
        chartType={BarChart}
        showBrush={data.length > 8}
        renderInner={(visData) => (
          <Bar dataKey={y_key} name={humanizeKey(y_key)} radius={[4, 4, 0, 0]}>
            {visData.map((_, i) => (
              <Cell key={i} fill={palette[i % palette.length]} />
            ))}
          </Bar>
        )}
      />
    );
  };

  // --- ZOOMABLE LINE ---
  const renderZoomableLine = () => {
    const keys = multi_series_keys.length > 0 ? multi_series_keys : [y_key];
    return (
      <ZoomableChart
        data={data}
        x_key={x_key}
        chartType={LineChart}
        showBrush={data.length > 8}
        renderInner={() => (
          <>
            {keys.length > 1 && <Legend wrapperStyle={{ fontSize: '0.78rem' }} />}
            {keys.map((key, i) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                name={humanizeKey(key)}
                stroke={palette[i % palette.length]}
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            ))}
          </>
        )}
      />
    );
  };

  // --- ZOOMABLE AREA ---
  const renderZoomableArea = () => {
    const keys = multi_series_keys.length > 0 ? multi_series_keys : [y_key];
    return (
      <ZoomableChart
        data={data}
        x_key={x_key}
        chartType={AreaChart}
        showBrush={data.length > 8}
        renderInner={() => (
          <>
            {keys.length > 1 && <Legend wrapperStyle={{ fontSize: '0.78rem' }} />}
            {keys.map((key, i) => (
              <Area
                key={key}
                type="monotone"
                dataKey={key}
                name={humanizeKey(key)}
                stroke={palette[i % palette.length]}
                fill={palette[i % palette.length]}
                fillOpacity={0.15}
                strokeWidth={2}
              />
            ))}
          </>
        )}
      />
    );
  };

  // --- PIE (no zoom needed) ---
  const renderPie = () => (
    <ResponsiveContainer width="100%" height={280}>
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
          label={({ name, percent }) => `${truncateLabel(name, 16)} ${(percent * 100).toFixed(0)}%`}
          labelLine={{ stroke: chartTheme.colors.slate, strokeWidth: 1 }}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={palette[i % palette.length]} />
          ))}
        </Pie>
        <Tooltip contentStyle={chartTheme.tooltipStyle} />
        <Legend
          wrapperStyle={chartTheme.legendStyle}
          formatter={(value) => humanizeKey(value)}
        />
      </PieChart>
    </ResponsiveContainer>
  );

  return (
    <div className={`chat-chart-container ${expanded ? 'chat-chart-expanded' : ''}`}>
      {title && (
        <div className="chat-chart-title">
          <span>{title}</span>
          <button
            className="chat-chart-expand-btn"
            onClick={() => setExpanded(!expanded)}
            title={expanded ? 'Collapse chart' : 'Expand chart'}
          >
            <Maximize2 size={13} />
          </button>
        </div>
      )}
      <div className="chat-chart-body">
        {renderChart()}
      </div>
    </div>
  );
}

export default ChatChart;
