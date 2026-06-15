import React, { useState } from 'react';
import { KeyRound, ArrowRight, Code } from 'lucide-react';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export default function Auth({ onAuthenticated }) {
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!token.trim()) return;
    
    setLoading(true);
    setError(null);
    try {
      const res = await axios.post(`${API_BASE}/api/auth`, { token });
      onAuthenticated(token, res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed. Please check your token.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ maxWidth: '400px', margin: '80px auto' }}>
      <div className="flex items-center gap-4 mb-8" style={{ justifyContent: 'center' }}>
        <Code size={32} />
        <h2 style={{ marginBottom: 0 }}>Gitlytics</h2>
      </div>
      
      <p className="text-center mb-8">
        Enter your GitHub Personal Access Token to analyze your repository traffic.
      </p>

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '16px', position: 'relative' }}>
          <KeyRound size={18} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-secondary)' }} />
          <input
            type="password"
            placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            style={{ paddingLeft: '40px' }}
            disabled={loading}
          />
        </div>
        
        {error && <p className="text-secondary" style={{ color: 'var(--danger-color)', fontSize: '14px' }}>{error}</p>}
        
        <button 
          type="submit" 
          className="btn btn-primary" 
          style={{ width: '100%' }}
          disabled={!token || loading}
        >
          {loading ? 'Authenticating...' : 'Connect to GitHub'}
          {!loading && <ArrowRight size={16} />}
        </button>
      </form>
    </div>
  );
}
