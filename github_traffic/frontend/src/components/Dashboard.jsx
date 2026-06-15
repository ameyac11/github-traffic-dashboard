import React, { useMemo, useState } from 'react';
import { 
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend 
} from 'recharts';
import { Eye, Download, Users, Star, GitFork, BookMarked, Globe, Lock, ChevronDown, ChevronUp } from 'lucide-react';

const COLORS = ['#2563eb', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#64748b'];

function RepoDetails({ repo }) {
  // 1. Time-Series (Views + Clones)
  const chartData = useMemo(() => {
    const dailyMap = {};
    const views = repo["_daily_views"] || [];
    const clones = repo["_daily_clones"] || [];
    
    views.forEach(d => {
      const date = d.timestamp.substring(0, 10);
      if (!dailyMap[date]) dailyMap[date] = { date, views: 0, uniques: 0, clones: 0 };
      dailyMap[date].views += d.count;
      dailyMap[date].uniques += d.uniques;
    });
    
    clones.forEach(d => {
      const date = d.timestamp.substring(0, 10);
      if (!dailyMap[date]) dailyMap[date] = { date, views: 0, uniques: 0, clones: 0 };
      dailyMap[date].clones += d.count;
    });
    
    let finalChartData = Object.values(dailyMap).sort((a, b) => a.date.localeCompare(b.date));
    
    // If there's only 1 day of data (common in short CSVs), duplicate it so the AreaChart draws a line instead of a dot.
    if (finalChartData.length === 1) {
      finalChartData = [
        { ...finalChartData[0], date: finalChartData[0].date + " (Start)" },
        { ...finalChartData[0], date: finalChartData[0].date + " (End)" }
      ];
    }
    
    return finalChartData;
  }, [repo]);

  // 2. Sources (Referrers)
  const referrersData = useMemo(() => {
    if (repo["_referrers"] && repo["_referrers"].length > 0) {
      return [...repo["_referrers"]]
        .sort((a, b) => b.count - a.count)
        .slice(0, 6)
        .map(r => ({ name: r.referrer, count: r.count }));
    } else if (repo["Top Referrer"]) {
      return [{ name: repo["Top Referrer"], count: repo["Top Referrer Views"] || 1 }];
    }
    return [];
  }, [repo]);

  // 3. Paths
  const pathsData = useMemo(() => {
    if (!repo["_paths"]) return [];
    return [...repo["_paths"]]
      .sort((a, b) => b.count - a.count)
      .slice(0, 5)
      .map(p => ({
        path: p.path,
        title: p.title || p.path,
        views: p.count,
        uniques: p.uniques
      }));
  }, [repo]);

  return (
    <div className="accordion-content">
      {chartData.length > 0 && (
        <div style={{ height: '300px', marginBottom: '32px' }}>
          <h4 style={{ marginBottom: '16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Daily Trends</h4>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--accent-color)" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="var(--accent-color)" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorClones" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
              <XAxis dataKey="date" stroke="var(--text-secondary)" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis yAxisId="left" stroke="var(--text-secondary)" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip 
                contentStyle={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '6px' }}
                itemStyle={{ color: 'var(--text-primary)' }}
              />
              <Legend verticalAlign="top" height={36}/>
              <Area yAxisId="left" type="monotone" dataKey="views" name="Total Views" stroke="var(--accent-color)" strokeWidth={2} fillOpacity={1} fill="url(#colorViews)" />
              <Area yAxisId="left" type="monotone" dataKey="clones" name="Total Clones" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorClones)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="grid grid-2-col">
        <div style={{ border: '1px solid var(--border-color)', borderRadius: '8px', padding: '16px' }}>
          <h4 style={{ marginBottom: '16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Top Referrers</h4>
          {referrersData.length > 0 ? (
            <div style={{ height: '250px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={referrersData} dataKey="count" nameKey="name" cx="50%" cy="45%" innerRadius={50} outerRadius={70} paddingAngle={2}>
                    {referrersData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '6px' }} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="text-secondary text-center" style={{ marginTop: '40px', fontSize: '13px' }}>
              No referrer data available.
              <div style={{ fontSize: '11px', marginTop: '4px', opacity: 0.7 }}>Historical CSVs do not track detailed referrers.</div>
            </div>
          )}
        </div>

        <div style={{ border: '1px solid var(--border-color)', borderRadius: '8px', padding: '16px' }}>
          <h4 style={{ marginBottom: '16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Popular Paths</h4>
          {pathsData.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th style={{ padding: '8px' }}>Path</th>
                    <th style={{ padding: '8px' }}>Views</th>
                  </tr>
                </thead>
                <tbody>
                  {pathsData.map((p, idx) => (
                    <tr key={idx}>
                      <td style={{ padding: '8px', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        <div style={{ fontWeight: 500, fontSize: '13px' }}>{p.path}</div>
                      </td>
                      <td style={{ padding: '8px' }}>{p.views.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-secondary text-center" style={{ marginTop: '40px', fontSize: '13px' }}>
              No path data available.
              <div style={{ fontSize: '11px', marginTop: '4px', opacity: 0.7 }}>Historical CSVs do not track detailed paths.</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Dashboard({ data, isCsvMode = false }) {
  const [expandedRepo, setExpandedRepo] = useState(null);

  if (!data || data.length === 0) {
    return <div className="card text-center">No traffic data available.</div>;
  }

  // 1. Global KPIs
  const stats = useMemo(() => {
    let totalViews = 0, uniqueViews = 0, totalClones = 0, totalStars = 0, totalForks = 0;
    data.forEach(repo => {
      totalViews += repo["Total Views"] || 0;
      uniqueViews += repo["Unique Visitors"] || 0;
      totalClones += repo["Total Clones"] || 0;
      totalStars += repo["Stars"] || 0;
      totalForks += repo["Forks"] || 0;
    });
    return { totalViews, uniqueViews, totalClones, totalStars, totalForks, totalRepos: data.length };
  }, [data]);

  // 2. Top 10 by Views
  const topViewsData = useMemo(() => {
    return [...data]
      .filter(repo => repo && repo.Repository)
      .sort((a, b) => (b["Total Views"] || 0) - (a["Total Views"] || 0))
      .slice(0, 10)
      .map(repo => ({
        name: repo.Repository.split('/').pop(),
        views: repo["Total Views"] || 0
      }));
  }, [data]);

  // 3. Top 10 by Clones
  const topClonesData = useMemo(() => {
    return [...data]
      .filter(repo => repo && repo.Repository)
      .sort((a, b) => (b["Total Clones"] || 0) - (a["Total Clones"] || 0))
      .slice(0, 10)
      .map(repo => ({
        name: repo.Repository.split('/').pop(),
        clones: repo["Total Clones"] || 0
      }));
  }, [data]);

  // 4. Sorted Repos for Accordion (sorted by Clones descending, as requested)
  const sortedRepos = useMemo(() => {
    return [...data]
      .filter(repo => repo && repo.Repository)
      .sort((a, b) => (b["Total Clones"] || 0) - (a["Total Clones"] || 0));
  }, [data]);

  const toggleRepo = (repoName) => {
    setExpandedRepo(expandedRepo === repoName ? null : repoName);
  };

  return (
    <div>
      {/* KPI Row 1 */}
      <div className="grid grid-3 mb-4">
        <div className="card stat-card" style={{ marginBottom: 0 }}>
          <div className="flex items-center justify-between">
            <span className="label">Repositories</span>
            <BookMarked size={18} color="var(--accent-color)" />
          </div>
          <span className="value">{stats.totalRepos.toLocaleString()}</span>
        </div>
        <div className="card stat-card" style={{ marginBottom: 0 }}>
          <div className="flex items-center justify-between">
            <span className="label">Total Views</span>
            <Eye size={18} color="var(--accent-color)" />
          </div>
          <span className="value">{stats.totalViews.toLocaleString()}</span>
        </div>
        <div className="card stat-card" style={{ marginBottom: 0 }}>
          <div className="flex items-center justify-between">
            <span className="label">Total Clones</span>
            <Download size={18} color="#10b981" />
          </div>
          <span className="value">{stats.totalClones.toLocaleString()}</span>
        </div>
      </div>

      {/* Side by Side Bar Charts */}
      <div className="grid grid-2 mb-8">
        <div className="card" style={{ marginBottom: 0, height: '400px' }}>
          <h3 style={{ marginBottom: '24px' }}>Top 10 Repositories by Views</h3>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={topViewsData} margin={{ bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
              <XAxis dataKey="name" stroke="var(--text-secondary)" fontSize={10} tickLine={false} axisLine={false} angle={-45} textAnchor="end" />
              <YAxis stroke="var(--text-secondary)" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip 
                cursor={{fill: 'var(--bg-hover)'}}
                contentStyle={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '6px' }}
              />
              <Bar dataKey="views" fill="var(--accent-color)" radius={[4, 4, 0, 0]} name="Views" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card" style={{ marginBottom: 0, height: '400px' }}>
          <h3 style={{ marginBottom: '24px' }}>Top 10 Repositories by Clones</h3>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={topClonesData} margin={{ bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
              <XAxis dataKey="name" stroke="var(--text-secondary)" fontSize={10} tickLine={false} axisLine={false} angle={-45} textAnchor="end" />
              <YAxis stroke="var(--text-secondary)" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip 
                cursor={{fill: 'var(--bg-hover)'}}
                contentStyle={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '6px' }}
              />
              <Bar dataKey="clones" fill="#10b981" radius={[4, 4, 0, 0]} name="Clones" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* All Repositories Accordion Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-color)' }}>
          <h3 style={{ margin: 0 }}>All Repositories</h3>
          <p className="text-secondary" style={{ fontSize: '13px', marginTop: '4px' }}>Click a row to expand deep-dive analytics</p>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ width: '40px' }}></th>
                <th>Repository</th>
                <th>Stars</th>
                <th>Views</th>
                <th>Clones</th>
                <th>Top Referrer</th>
              </tr>
            </thead>
            <tbody>
              {sortedRepos.map((repo, idx) => {
                const isOpen = expandedRepo === repo.Repository;
                return (
                  <React.Fragment key={idx}>
                    <tr className="accordion-row" onClick={() => toggleRepo(repo.Repository)}>
                      <td style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                        {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </td>
                      <td style={{ fontWeight: 500 }}>
                        {repo.Repository ? repo.Repository.split('/').pop() : 'Unknown'}
                      </td>
                      <td>{repo["Stars"]?.toLocaleString() || 0}</td>
                      <td>{repo["Total Views"]?.toLocaleString() || 0}</td>
                      <td>{repo["Total Clones"]?.toLocaleString() || 0}</td>
                      <td>{repo["Top Referrer"] || '-'}</td>
                    </tr>
                    {isOpen && (
                      <tr>
                        <td colSpan={6} style={{ padding: 0, borderBottom: 'none' }}>
                          <RepoDetails repo={repo} />
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
