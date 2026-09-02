import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import CoverPage from './components/CoverPage';
import WarRoom from './components/WarRoom';
import TransactionDeepDive from './components/TransactionDeepDive';
import PatternDeepDive from './components/PatternDeepDive';
import './index.css';

function HeaderNav() {
  const location = useLocation();
  
  // Hide navbar completely on the full-screen Cover Page
  if (location.pathname === '/' || location.pathname === '/cover' || location.pathname === '/overview') {
    return null;
  }

  return (
    <header className="app-header">
      <div className="header-left">
        <Link to="/war-room" style={{ textDecoration: 'none', color: 'inherit' }}>
          <h1 className="logo">🧠 Recover<span className="logo-accent">AI</span></h1>
        </Link>
        <span className="header-badge">AUTONOMOUS RECOVERY</span>
        
        <nav className="header-nav-links">
          <Link to="/war-room" className={`nav-link ${location.pathname === '/war-room' || location.pathname === '/dashboard' ? 'active' : ''}`}>
            📊 War Room Dashboard
          </Link>
          <Link to="/patterns" className={`nav-link ${location.pathname === '/patterns' ? 'active' : ''}`}>
            🔍 Failure Patterns & Root Causes
          </Link>
        </nav>
      </div>
      <div className="header-right">
        <span className="header-tag">6 Agents</span>
        <span className="header-tag">2 MCP Servers</span>
        <span className="header-tag">12 Tools</span>
        <div className="live-indicator">
          <span className="live-dot"></span>
          LIVE
        </div>
      </div>
    </header>
  );
}

function App() {
  return (
    <Router>
      <div className="app">
        <HeaderNav />
        <Routes>
          {/* Cover Page loads as the first default page */}
          <Route path="/" element={<CoverPage />} />
          <Route path="/cover" element={<CoverPage />} />
          <Route path="/overview" element={<CoverPage />} />
          
          {/* Main Website / War Room Dashboard */}
          <Route path="/war-room" element={<WarRoom />} />
          <Route path="/dashboard" element={<WarRoom />} />
          
          {/* Deep Dive Pages */}
          <Route path="/patterns" element={<PatternDeepDive />} />
          <Route path="/transaction/:id" element={<TransactionDeepDive />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
