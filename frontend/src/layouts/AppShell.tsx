import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  ShieldCheck, LayoutDashboard, Building2, Car, ShieldAlert, 
  CloudSun, Zap, Bot, Settings, LogOut, Menu, X 
} from 'lucide-react';

export const AppShell: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isConnected] = useState(true);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/app/overview', label: 'Overview', icon: LayoutDashboard },
    { path: '/app/cities', label: 'Cities', icon: Building2 },
    { path: '/app/traffic', label: 'Traffic', icon: Car },
    { path: '/app/risk', label: 'Risk', icon: ShieldAlert },
    { path: '/app/environment', label: 'Environment', icon: CloudSun },
    { path: '/app/events', label: 'Events', icon: Zap },
    { path: '/app/copilot', label: 'AI Copilot', icon: Bot },
    { path: '/app/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-[#070B14] text-slate-100 flex flex-col font-sans">
      {/* Top Header Bar */}
      <header className="sticky top-0 z-40 glass-nav h-16 px-4 md:px-8 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <span className="font-bold text-base tracking-tight text-white block">SOUTH INDIA</span>
            <span className="text-[10px] font-bold tracking-widest text-blue-400 uppercase block -mt-1">Urban Intelligence</span>
          </div>
        </div>

        {/* Desktop Status & User Menu */}
        <div className="hidden md:flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900/80 border border-slate-800 text-xs font-medium">
            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
            <span>{isConnected ? 'LIVE PIPELINE' : 'BACKEND OFFLINE'}</span>
          </div>

          <div className="flex items-center gap-3 pl-4 border-l border-slate-800">
            <div className="text-right">
              <p className="text-xs font-semibold text-white">{user?.full_name || 'Operator'}</p>
              <p className="text-[11px] text-slate-400">{user?.email || ''}</p>
            </div>
            <button
              onClick={handleLogout}
              className="p-2 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Mobile Hamburger Toggle */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden p-2 text-slate-400 hover:text-white"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </header>

      {/* Main Content Area with Desktop Sidebar */}
      <div className="flex-1 flex overflow-hidden">
        {/* Desktop Floating Sidebar */}
        <aside className="hidden md:flex w-64 p-4 flex-col justify-between border-r border-slate-800/80 bg-slate-950/40">
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname.startsWith(item.path);
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>

          <div className="p-3 rounded-2xl glass-surface text-xs text-slate-400 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-white">20 Nodes Active</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 font-mono">HYBRID</span>
            </div>
            <p className="text-[11px] leading-relaxed text-slate-400">
              Tamil Nadu (8) • Kerala (6) • Andhra Pradesh (6)
            </p>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 p-4 md:p-8 overflow-y-auto">
          <Outlet />
        </main>
      </div>

      {/* Mobile Bottom Floating Navigation Bar */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 glass-nav px-4 py-2 flex items-center justify-around border-t border-slate-800">
        {navItems.slice(0, 5).map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname.startsWith(item.path);
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`flex flex-col items-center gap-1 p-1 text-[11px] font-medium transition-colors ${
                isActive ? 'text-blue-400' : 'text-slate-400'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </div>
  );
};
