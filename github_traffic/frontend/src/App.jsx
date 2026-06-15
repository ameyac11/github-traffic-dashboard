import React, { useState } from 'react';
import { Activity, Code, LogOut, Download } from 'lucide-react';
import Landing from './components/Landing';
import Dashboard from './components/Dashboard';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userProfile, setUserProfile] = useState(null);
  
  const [appMode, setAppMode] = useState(null); // 'api' or 'csv'
  const [trafficData, setTrafficData] = useState(null);
  const [isFetching, setIsFetching] = useState(false);

  const handleLogout = () => {
    setIsAuthenticated(false);
    setUserProfile(null);
    setTrafficData(null);
    setAppMode(null);
  };

  const handleApiAuthenticated = (token, profile) => {
    setIsAuthenticated(true);
    setUserProfile(profile);
    setIsFetching(true);
    setAppMode('api');
    
    const fetchTraffic = async () => {
      try {
        const API_BASE = import.meta.env.VITE_API_BASE_URL || '';
        const axios = (await import('axios')).default;
        const res = await axios.post(`${API_BASE}/api/traffic`, { token });
        setTrafficData(res.data);
      } catch (e) {
        console.error("Failed to fetch traffic", e);
        // If it fails, maybe kick them back out
        setAppMode(null);
      } finally {
        setIsFetching(false);
      }
    };
    fetchTraffic();
  };

  const handleCsvLoaded = (data) => {
    setAppMode('csv');
    setTrafficData(data);
  };

  // 1. Loading State (Animated)
  if (isFetching) {
    return (
      <div className="app-container" style={{ alignItems: 'center', justifyContent: 'center' }}>
        <div className="loading-container fade-in">
          <Activity size={32} color="var(--accent-color)" className="mb-4" />
          <h3 style={{ marginBottom: '8px' }}>Fetching Live Data</h3>
          <p className="text-secondary" style={{ fontSize: '14px', textAlign: 'center' }}>
            Connecting to GitHub API to analyze your repositories...
          </p>
          <div className="loading-bar-bg">
            <div className="loading-bar-fill"></div>
          </div>
        </div>
      </div>
    );
  }

  // 2. Landing Screen (No Navbar)
  if (!trafficData) {
    return <Landing onApiAuthenticated={handleApiAuthenticated} onCsvLoaded={handleCsvLoaded} />;
  }

  // 3. Main Dashboard (Navbar + Data)
  return (
    <div className="app-container fade-in">
      <header className="topbar">
        <div className="flex items-center gap-4">
          <Code size={28} color="var(--accent-color)" />
          <div style={{ borderLeft: '1px solid var(--border-color)', paddingLeft: '16px' }}>
            <h2 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>Traffic Monitor</h2>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              {appMode === 'api' ? 'Live Connection' : 'Historical CSV Mode'}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-6">
          {appMode === 'api' && userProfile && (
            <div className="flex items-center gap-3" style={{ borderRight: '1px solid var(--border-color)', paddingRight: '24px' }}>
              {userProfile.avatar_url ? (
                <img src={userProfile.avatar_url} alt="Avatar" style={{ width: 36, height: 36, borderRadius: '50%', border: '1px solid var(--border-color)' }} />
              ) : (
                <div style={{ width: 36, height: 36, borderRadius: '50%', backgroundColor: 'var(--border-color)' }}></div>
              )}
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '14px', fontWeight: 600, lineHeight: '1.2' }}>{userProfile.name}</span>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.2' }}>@{userProfile.login || userProfile.username}</span>
              </div>
            </div>
          )}
          <div className="flex items-center gap-2">
            {appMode === 'api' && (
              <button 
                className="btn btn-secondary" 
                onClick={() => {
                  const API_BASE = import.meta.env.VITE_API_BASE_URL || '';
                  window.open(`${API_BASE}/api/export`, '_blank');
                }}
                style={{ padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '8px' }}
              >
                <Download size={14} /> Export CSV
              </button>
            )}
            <button className="btn btn-secondary" onClick={handleLogout} style={{ padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <LogOut size={14} /> Reset
            </button>
          </div>
        </div>
      </header>

      <main className="main-content">
        <Dashboard data={trafficData} isCsvMode={appMode === 'csv'} />
      </main>
    </div>
  );
}

export default App;
