import React from 'react';
import { 
  TrendingUp, 
  MapPin, 
  GitFork, 
  Sliders, 
  Layers
} from 'lucide-react';

interface HeaderProps {
  activeTab: 'monitor' | 'map' | 'corridors' | 'simulator';
  onSelectTab: (tab: 'monitor' | 'map' | 'corridors' | 'simulator') => void;
  selectedYear?: number;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, onSelectTab }) => {
  return (
    <header className="w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl sticky top-0 z-50">
      {/* Top Banner: SDGs & Official Citations */}
      <div className="max-w-7xl mx-auto px-4 py-2 flex flex-wrap items-center justify-between gap-3 text-xs border-b border-slate-800/40">
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-medium">
            <span className="pulse-emerald"></span>
            UN SDG 8.9: Sustainable Tourism Value Capture
          </span>
          <span className="hidden sm:inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-medium">
            <Layers className="w-3 h-3" />
            UN SDG 12.b: Impact Monitoring
          </span>
        </div>

        <div className="flex items-center gap-3 text-slate-400">
          <span>Sources: <strong>DOSM TSA (2015–2025)</strong> • <strong>DTS (2018–2025)</strong> • <strong>HIES Table 6</strong></span>
          <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[11px]">v2.4 Live</span>
        </div>
      </div>

      {/* Main Header & Navigation */}
      <div className="max-w-7xl mx-auto px-4 py-3 flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 via-teal-500 to-cyan-400 p-[1px] shadow-lg shadow-emerald-500/20">
            <div className="w-full h-full bg-slate-950 rounded-[11px] flex items-center justify-center text-lg">
              🇲🇾
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-extrabold tracking-tight text-white flex items-center gap-2">
                Malaysia Tourism Value Optimizer
              </h1>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-gradient-to-r from-emerald-500 to-teal-600 text-slate-950">
                Decision System
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Shift from <span className="text-slate-200 font-medium">Volume Expansion</span> to <span className="text-emerald-400 font-semibold">Economic Value Capture</span> from Existing Visitors
            </p>
          </div>
        </div>

        {/* View Navigation Tabs */}
        <nav className="flex items-center gap-1.5 p-1 rounded-full bg-slate-900/90 border border-slate-800 shadow-inner overflow-x-auto">
          <button
            onClick={() => onSelectTab('monitor')}
            className={`nav-tab-btn ${activeTab === 'monitor' ? 'active' : ''}`}
          >
            <TrendingUp className="w-4 h-4" />
            <span>Value Monitor</span>
          </button>

          <button
            onClick={() => onSelectTab('map')}
            className={`nav-tab-btn ${activeTab === 'map' ? 'active' : ''}`}
          >
            <MapPin className="w-4 h-4" />
            <span>Accommodation & States</span>
          </button>

          <button
            onClick={() => onSelectTab('corridors')}
            className={`nav-tab-btn ${activeTab === 'corridors' ? 'active' : ''}`}
          >
            <GitFork className="w-4 h-4" />
            <span>Value Corridors</span>
          </button>

          <button
            onClick={() => onSelectTab('simulator')}
            className={`nav-tab-btn ${activeTab === 'simulator' ? 'active' : ''}`}
          >
            <Sliders className="w-4 h-4" />
            <span>Scenario Simulator</span>
          </button>
        </nav>
      </div>

      {/* Macro Ticker Strip */}
      <div className="bg-slate-900/40 border-t border-slate-800/40 py-2 px-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-6 overflow-x-auto text-xs whitespace-nowrap">
          <div className="flex items-center gap-2">
            <span className="text-slate-400">2025 Internal Consumption (ITC):</span>
            <span className="font-mono font-bold text-white text-sm">RM 112.5 Billion</span>
          </div>

          <div className="h-3 w-[1px] bg-slate-800"></div>

          <div className="flex items-center gap-2">
            <span className="text-slate-400">Tourism Direct GVA (TDGVA):</span>
            <span className="font-mono font-bold text-emerald-400 text-sm">RM 59.4 Billion</span>
            <span className="text-[11px] text-slate-400">(52.8% Economic Yield)</span>
          </div>

          <div className="h-3 w-[1px] bg-slate-800"></div>

          <div className="flex items-center gap-2">
            <span className="text-slate-400">Top Value Activity:</span>
            <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-medium">Accommodation Services</span>
            <span className="font-mono font-bold text-emerald-400">85.8% VAI</span>
          </div>

          <div className="h-3 w-[1px] bg-slate-800"></div>

          <div className="flex items-center gap-2">
            <span className="text-slate-400">Inter-State Corridors:</span>
            <span className="font-mono font-bold text-cyan-400 text-sm">240 Modeled Corridors</span>
          </div>
        </div>
      </div>
    </header>
  );
};
