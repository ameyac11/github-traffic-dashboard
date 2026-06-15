import React, { useState } from 'react';
import { Activity, Upload, Key, Code } from 'lucide-react';
import CsvUpload from './CsvUpload';

export default function Landing({ onApiAuthenticated, onCsvLoaded }) {
  const [tab, setTab] = useState('api');
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleApiSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const API_BASE = import.meta.env.VITE_API_BASE_URL || '';
      const axios = (await import('axios')).default;
      
      const res = await axios.post(`${API_BASE}/api/auth`, { token });
      onApiAuthenticated(token, res.data);
    } catch (err) {
      console.error(err);
      setError('Authentication failed. Please check your token and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', padding: '20px' }}>
      
      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
        <div style={{ display: 'inline-flex', padding: '12px', backgroundColor: 'var(--bg-hover)', borderRadius: '16px', marginBottom: '16px' }}>
          <Code size={32} color="var(--accent-color)" />
        </div>
        <h1 style={{ fontSize: '28px', marginBottom: '12px' }}>GitHub Traffic Monitor</h1>
        <p className="text-secondary">Track views, clones and visitors across all your repositories.</p>
      </div>

      <div className="card" style={{ width: '100%', maxWidth: '480px', padding: '32px' }}>
        <div className="landing-tabs">
          <div 
            className={`landing-tab ${tab === 'api' ? 'active' : ''}`}
            onClick={() => setTab('api')}
          >
            <Activity size={16} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'text-bottom' }} />
            Live API
          </div>
          <div 
            className={`landing-tab ${tab === 'csv' ? 'active' : ''}`}
            onClick={() => setTab('csv')}
          >
            <Upload size={16} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'text-bottom' }} />
            CSV Upload
          </div>
        </div>

        {tab === 'api' && (
          <form onSubmit={handleApiSubmit}>
            <div className="form-group" style={{ marginBottom: '24px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', fontSize: '14px', color: 'var(--text-secondary)' }}>
                <Key size={14} /> Personal Access Token
              </label>
              <input
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="ghp_......................................."
                required
              />
            </div>
            
            {error && (
              <div style={{ color: 'var(--danger-color)', fontSize: '14px', marginBottom: '16px', textAlign: 'center' }}>
                {error}
              </div>
            )}

            <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '12px' }} disabled={loading}>
              {loading ? 'Connecting...' : 'Connect Account'}
            </button>
            
            <p style={{ textAlign: 'center', fontSize: '12px', color: 'var(--text-secondary)', marginTop: '16px' }}>
              Your token is sent only to your local backend and never stored remotely.
            </p>
          </form>
        )}

        {tab === 'csv' && (
          <CsvUpload onDataLoaded={onCsvLoaded} />
        )}
      </div>
      
      <div style={{ marginTop: '40px', display: 'flex', gap: '24px', fontSize: '14px', color: 'var(--text-secondary)' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><Code size={14}/> github-traffic-monitor</span>
      </div>
    </div>
  );
}
