import React, { useState, useEffect } from 'react';
import ForecastChart from '../components/ForecastChart';

function formatISTWindow(timestampStr) {
  if (!timestampStr) return '';
  const isoStr = timestampStr.endsWith('Z') ? timestampStr : `${timestampStr}Z`;
  const date = new Date(isoStr);
  return new Intl.DateTimeFormat('en-IN', {
    timeZone: 'Asia/Kolkata',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date);
}

export default function Dashboard() {
  const [forecastData, setForecastData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/forecast')
      .then((res) => {
        if (!res.ok) throw new Error('API response failed');
        return res.json();
      })
      .then((data) => {
        setForecastData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load forecast:', err);
        setError(true);
        setLoading(false);
      });
  }, []);

  const forecastList = forecastData?.forecast || [];
  
  const totalExpected = forecastList.reduce(
    (sum, item) => sum + (item.predictedEnergyKWh || 0),
    0
  );
  
  const peakOutput = forecastList.length
    ? Math.max(...forecastList.map((item) => item.predictedEnergyKWh || 0))
    : 0;

  const windowStart = forecastList.length ? formatISTWindow(forecastList[0].timestamp) : '';
  const windowEnd = forecastList.length ? formatISTWindow(forecastList[forecastList.length - 1].timestamp) : '';

  return (
    <div className="dashboard-page">
      {/* HERO SECTION */}
      <div className="hero-section">
        <div className="hero-content">
          <div className="eyebrow">
            <span className="eyebrow-dot">•</span> NODE PREDICTIVE INTELLIGENCE
          </div>
          <h1 className="hero-title">
            Building 01 <span className="accent">Solar Node.</span>
          </h1>
          <p className="hero-description">
            Independent solar generation forecasting powered by historical NASA POWER data and an XGBoost regression model.
          </p>
        </div>

        <div className="node-identity-block">
          <div className="identity-item">
            <span className="identity-label">NODE ID</span>
            <span className="identity-value">B01</span>
          </div>
          <div style={{ width: 1, backgroundColor: '#202226' }} />
          <div className="identity-item">
            <span className="identity-label">LOCATION</span>
            <span className="identity-value">Chennai, India</span>
          </div>
        </div>
      </div>

      {/* FORECAST STATUS STRIP */}
      <div className="status-strip">
        <div className="strip-item">
          <span className="status-dot"></span>
          <span className="strip-value" style={{ color: '#55B795' }}>ML Forecast Active</span>
        </div>
        <div className="strip-divider" />
        <div className="strip-item">
          <span className="strip-label">MODEL</span>
          <span className="strip-value">XGBoost</span>
        </div>
        <div className="strip-divider" />
        <div className="strip-item">
          <span className="strip-label">SOURCE</span>
          <span className="strip-value">NASA POWER</span>
        </div>
        <div className="strip-divider" />
        <div className="strip-item">
          <span className="strip-label">FORECAST</span>
          <span className="strip-value prominent">NEXT 24 HOURS</span>
        </div>
      </div>

      {/* MAIN FORECAST PANEL */}
      {error ? (
        <div className="error-box">
          Prediction unavailable
        </div>
      ) : loading ? (
        <div className="main-forecast-panel" style={{ textAlign: 'center', padding: '3rem', color: '#85827C' }}>
          Loading 24-hour ML forecast...
        </div>
      ) : (
        <div className="main-forecast-panel">
          <div className="forecast-header">
            <div>
              <div className="eyebrow" style={{ fontSize: '0.68rem', marginBottom: '0.2rem' }}>
                PREDICTIVE OUTPUT
              </div>
              <h2 className="forecast-title">Next 24-hour solar forecast</h2>
            </div>
            <span className="model-badge">XGBoost Regression</span>
          </div>

          <div className="metrics-row">
            <div className="primary-metric">
              <span className="metric-label-small">EXPECTED GENERATION</span>
              <div className="main-metric-value">
                {totalExpected.toFixed(2)}
                <span className="metric-unit-large">kWh</span>
              </div>
              <div className="metric-subtext">
                Predicted solar yield over the next 24 hours.
              </div>
            </div>

            <div className="secondary-metrics-group">
              <div className="secondary-metric-item">
                <span className="metric-label-small">PEAK HOURLY OUTPUT</span>
                <div className="secondary-metric-val">
                  {peakOutput.toFixed(2)}
                  <span className="secondary-metric-unit">kWh</span>
                </div>
              </div>

              <div className="secondary-metric-item">
                <span className="metric-label-small">PV CAPACITY</span>
                <div className="secondary-metric-val">
                  5<span className="secondary-metric-unit">kWp</span>
                </div>
              </div>

              <div className="secondary-metric-item">
                <span className="metric-label-small">FORECAST POINTS</span>
                <div className="secondary-metric-val">
                  {forecastList.length}
                  <span className="secondary-metric-unit">hours</span>
                </div>
              </div>
            </div>
          </div>

          <ForecastChart forecastData={forecastList} />

          <div className="chart-caption-strip">
            <span>Hourly prediction for the upcoming 24-hour forecast window.</span>
            {windowStart && windowEnd && (
              <div>
                FORECAST WINDOW: <span className="window-val">{windowStart} → {windowEnd} (IST)</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* SECONDARY PANELS GRID */}
      <div className="secondary-grid">
        <div className="secondary-panel">
          <div className="panel-eyebrow">MODEL PERFORMANCE</div>
          <div className="kv-list">
            <div className="kv-row">
              <span className="kv-key">MAE</span>
              <span className="kv-value">0.1161 kWh</span>
            </div>
            <div className="kv-row">
              <span className="kv-key">RMSE</span>
              <span className="kv-value">0.2673 kWh</span>
            </div>
            <div className="kv-row">
              <span className="kv-key">Validation Method</span>
              <span className="kv-value">20% chronological holdout</span>
            </div>
          </div>
          <div className="panel-note">
            Validation performed using a chronological test period.
          </div>
        </div>

        <div className="secondary-panel">
          <div className="panel-eyebrow">PV INSTALLATION</div>
          <div className="kv-list">
            <div className="kv-row">
              <span className="kv-key">Capacity</span>
              <span className="kv-value">5 kWp</span>
            </div>
            <div className="kv-row">
              <span className="kv-key">Panel Efficiency</span>
              <span className="kv-value">19%</span>
            </div>
            <div className="kv-row">
              <span className="kv-key">Fixed Tilt</span>
              <span className="kv-value">13°</span>
            </div>
            <div className="kv-row">
              <span className="kv-key">System Derate</span>
              <span className="kv-value">15%</span>
            </div>
          </div>
        </div>
      </div>

      {/* INDEPENDENCE NOTICE */}
      <div className="independence-strip">
        <span className="notice-check">✓</span>
        <div>
          <div className="notice-title">Independent node intelligence</div>
          <div className="notice-text">
            Prediction generated independently from the central GridShare simulation using historical NASA POWER data and the B01 XGBoost model.
          </div>
        </div>
      </div>
    </div>
  );
}
