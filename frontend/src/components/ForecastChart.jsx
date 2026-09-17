import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

function formatIST(timestampStr) {
  if (!timestampStr) return '';
  const isoStr = timestampStr.endsWith('Z') ? timestampStr : `${timestampStr}Z`;
  const date = new Date(isoStr);
  return new Intl.DateTimeFormat('en-IN', {
    timeZone: 'Asia/Kolkata',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date);
}

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div
        style={{
          backgroundColor: '#101114',
          border: '1px solid #292B2F',
          padding: '0.5rem 0.75rem',
          borderRadius: '4px',
          fontSize: '0.8rem',
        }}
      >
        <div style={{ color: '#85827C', marginBottom: '0.2rem' }}>
          Time (IST): {label}
        </div>
        <div style={{ color: '#D6B46A', fontWeight: 600 }}>
          Predicted generation: {payload[0].value} kWh
        </div>
      </div>
    );
  }
  return null;
};

export default function ForecastChart({ forecastData }) {
  // Ensure ALL 24 points are rendered without sampling
  const chartData = (forecastData || []).map((item) => ({
    timeIST: formatIST(item.timestamp),
    predictedEnergyKWh: item.predictedEnergyKWh,
    rawTimestamp: item.timestamp,
  }));

  return (
    <div className="chart-container-box">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
          <defs>
            <linearGradient id="colorYield" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#D6B46A" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#D6B46A" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#202226" vertical={false} />
          <XAxis
            dataKey="timeIST"
            stroke="#5D5B56"
            fontSize={10}
            tickLine={false}
            axisLine={{ stroke: '#202226' }}
            interval={0}
            angle={-45}
            textAnchor="end"
            height={35}
          />
          <YAxis
            stroke="#5D5B56"
            fontSize={10}
            tickLine={false}
            axisLine={{ stroke: '#202226' }}
            unit=" kWh"
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="predictedEnergyKWh"
            stroke="#D6B46A"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorYield)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
