import React, { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';
import type { ODCorridorsData, Corridor } from '../types';
import { 
  ArrowRight, 
  Filter, 
  ShieldCheck, 
  Compass, 
  Activity, 
  AlertTriangle, 
  Search
} from 'lucide-react';

interface CorridorNetworkProps {
  corridorData: ODCorridorsData;
  geoJson: any;
}

export const CorridorNetwork: React.FC<CorridorNetworkProps> = ({ corridorData, geoJson }) => {
  const [selectedTier, setSelectedTier] = useState<string>('All');
  const [selectedOrigin, setSelectedOrigin] = useState<string>('All');
  const [selectedDestination, setSelectedDestination] = useState<string>('All');
  const [searchQuery, setSearchQuery] = useState<string>('');

  useEffect(() => {
    if (geoJson) {
      echarts.registerMap('malaysia', geoJson);
    }
  }, [geoJson]);

  const allCorridors = corridorData.corridors_2025 || [];

  // Filter corridors
  const filteredCorridors = allCorridors.filter((c) => {
    if (selectedTier !== 'All' && c.corridor_category !== selectedTier) return false;
    if (selectedOrigin !== 'All' && c.origin !== selectedOrigin) return false;
    if (selectedDestination !== 'All' && c.destination !== selectedDestination) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return c.origin.toLowerCase().includes(q) || c.destination.toLowerCase().includes(q);
    }
    return true;
  });

  // Extract unique origins and destinations
  const origins = Array.from(new Set(allCorridors.map((c) => c.origin))).sort();
  const destinations = Array.from(new Set(allCorridors.map((c) => c.destination))).sort();

  // Color mapping by tier
  const tierColorMap: Record<string, string> = {
    'Priority Conversion Corridor': '#f59e0b', // Amber/Orange
    'Protect & Deepen': '#10b981',             // Emerald
    'Growth Opportunity': '#06b6d4',           // Cyan
    'Lower Strategic Priority': '#64748b',     // Slate
  };

  // Build ECharts Lines (Geo Arcs) Option
  const linesData = filteredCorridors.slice(0, 50).map((c) => {
    const origLon = c.origin_lon ?? c.orig_lon ?? 101.5;
    const origLat = c.origin_lat ?? c.orig_lat ?? 3.1;
    const destLon = c.destination_lon ?? c.dest_lon ?? 101.5;
    const destLat = c.destination_lat ?? c.dest_lat ?? 3.1;
    const isCross = c.is_cross_region ?? (c.origin_region !== c.destination_region);

    return {
      coords: [
        [origLon, origLat],
        [destLon, destLat],
      ],
      lineStyle: {
        color: tierColorMap[c.corridor_category] || '#06b6d4',
        width: Math.min(6, Math.max(1.5, Math.log(c.tourist_flow_thousands + 1) * 1.2)),
        opacity: 0.75,
        curveness: isCross ? 0.35 : 0.2,
      },
      corridorMeta: c,
    };
  });

  const mapArcsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: '#0e1526',
      borderColor: 'rgba(255, 255, 255, 0.15)',
      textStyle: { color: '#f8fafc', fontSize: 12 },
      formatter: (params: any) => {
        if (params.data && params.data.corridorMeta) {
          const c: Corridor = params.data.corridorMeta;
          const isCross = c.is_cross_region ?? (c.origin_region !== c.destination_region);
          const distKm = c.distance_km ?? 250;
          return `<div style="font-weight: bold; margin-bottom: 4px;">
              ${c.origin} → ${c.destination}
            </div>
            <div>Category: <strong style="color: ${tierColorMap[c.corridor_category]};">${c.corridor_category}</strong></div>
            <div>Tourist Flow: <strong>${c.tourist_flow_thousands.toFixed(1)}k tourists</strong></div>
            <div>Distance: <strong>${distKm.toFixed(0)} km</strong> (${isCross ? 'Flight' : 'Overland'})</div>
            <div>Dest ALOS: <strong>${c.dest_alos?.toFixed(2) || 'N/A'} days</strong></div>
            <div>Dest Spend/Night: <strong>RM ${c.dest_spend_per_night?.toFixed(1) || 'N/A'}</strong></div>`;
        }
        return params.name;
      },
    },
    geo: {
      map: 'malaysia',
      roam: true,
      scaleLimit: { min: 1.0, max: 4.5 },
      zoom: 1.25,
      center: [108.5, 4.0],
      itemStyle: {
        areaColor: '#0f172a',
        borderColor: 'rgba(255, 255, 255, 0.15)',
        borderWidth: 0.8,
      },
      emphasis: {
        itemStyle: { areaColor: '#1e293b' },
        label: { show: false },
      },
    },
    series: [
      {
        type: 'lines',
        coordinateSystem: 'geo',
        data: linesData,
        large: false,
        effect: {
          show: true,
          period: 5,
          trailLength: 0.2,
          symbol: 'arrow',
          symbolSize: 6,
        },
      },
    ],
  };

  return (
    <div className="space-y-6">
      {/* Top Banner: Tinbergen Gravity Model & RQ6 Target */}
      <div className="glass-panel p-6 border-l-4 border-l-cyan-500">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300">
                Spatial Econometrics & RQ6
              </span>
              <span className="text-xs text-slate-400">Tinbergen Gravity Model (R² = 0.7092)</span>
            </div>
            <h2 className="text-2xl font-bold text-white tracking-tight">
              Domestic Tourism Value Corridors & Mobility Gravity
            </h2>
            <p className="text-sm text-slate-300 mt-1 max-w-3xl">
              Targeting high-flow corridors with weak accommodation capture enables Malaysia to generate additional overnight tourism value without needing new visitor headcount. Structural gravity modeling reveals that <strong>Origin Working-Age Population (+0.890)</strong> and <strong>Origin Median Income (+0.725)</strong> are powerful outbound mobility engines.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-cyan-500/30 text-center min-w-[130px]">
              <span className="text-xs text-slate-400 uppercase font-semibold">Origin Income</span>
              <div className="text-2xl font-extrabold text-cyan-400 font-mono">+0.725</div>
              <span className="text-[10px] text-cyan-300">Elasticity (p &lt; 0.001)</span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-rose-500/30 text-center min-w-[130px]">
              <span className="text-xs text-slate-400 uppercase font-semibold">Borneo Barrier</span>
              <div className="text-2xl font-extrabold text-rose-400 font-mono">-73.6%</div>
              <span className="text-[10px] text-rose-300">Flight Volume Penalty</span>
            </div>
          </div>
        </div>
      </div>

      {/* Filter Controls Bar */}
      <div className="glass-panel p-4 flex flex-wrap items-center justify-between gap-3 text-xs">
        {/* Tier Filter Buttons */}
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-slate-400 font-semibold mr-1 flex items-center gap-1">
            <Filter className="w-3.5 h-3.5 text-cyan-400" /> Tier:
          </span>
          {['All', 'Priority Conversion Corridor', 'Protect & Deepen', 'Growth Opportunity'].map((tier) => (
            <button
              key={tier}
              onClick={() => setSelectedTier(tier)}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                selectedTier === tier
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                  : 'bg-slate-900/60 text-slate-400 border border-slate-800 hover:text-white'
              }`}
            >
              {tier === 'All' ? 'All Corridors' : tier}
            </button>
          ))}
        </div>

        {/* Origin / Destination Dropdowns & Search */}
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={selectedOrigin}
            onChange={(e) => setSelectedOrigin(e.target.value)}
            className="bg-slate-900 border border-slate-800 text-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-cyan-500"
          >
            <option value="All">All Origins</option>
            {origins.map((o) => (
              <option key={o} value={o}>{o}</option>
            ))}
          </select>

          <select
            value={selectedDestination}
            onChange={(e) => setSelectedDestination(e.target.value)}
            className="bg-slate-900 border border-slate-800 text-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-cyan-500"
          >
            <option value="All">All Destinations</option>
            {destinations.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>

          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Search corridor..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-slate-900 border border-slate-800 text-slate-200 rounded-lg pl-8 pr-3 py-1.5 text-xs focus:outline-none focus:border-cyan-500 w-36"
            />
          </div>
        </div>
      </div>

      {/* Main Grid: Flow Map & Priority Corridor Table */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Animated Geodesic Arcs Map (7 cols) */}
        <div className="glass-panel p-5 lg:col-span-7 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Compass className="w-4 h-4 text-cyan-400" />
              Inter-State Flow Network (Top 50 Geodesic Arcs)
            </span>
            <div className="flex items-center gap-2 text-[11px]">
              <span className="flex items-center gap-1 text-amber-400"><span className="w-2 h-2 rounded-full bg-amber-500"></span> Conversion</span>
              <span className="flex items-center gap-1 text-emerald-400"><span className="w-2 h-2 rounded-full bg-emerald-500"></span> Protect</span>
              <span className="flex items-center gap-1 text-cyan-400"><span className="w-2 h-2 rounded-full bg-cyan-500"></span> Growth</span>
            </div>
          </div>

          <div className="h-[460px] w-full">
            <ReactECharts option={mapArcsOption} style={{ height: '100%', width: '100%' }} />
          </div>

          <div className="pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
            <span>Thickness denotes tourist flow scale</span>
            <span className="text-cyan-400 font-mono font-medium">
              Showing {filteredCorridors.length} of {allCorridors.length} inter-state corridors
            </span>
          </div>
        </div>

        {/* Priority Corridors Ranked List (5 cols) */}
        <div className="glass-panel p-5 lg:col-span-5 flex flex-col space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
            <div>
              <h3 className="text-sm font-bold text-white">Corridor Strategic Ranking</h3>
              <p className="text-[11px] text-slate-400">Sorted by 2025 tourist flow volume</p>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-semibold uppercase">
              Action Priority
            </span>
          </div>

          {/* Scrollable list of corridors */}
          <div className="space-y-2 max-h-[430px] overflow-y-auto pr-1">
            {filteredCorridors.slice(0, 15).map((c, idx) => (
              <div 
                key={idx}
                className="p-3 rounded-lg bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition-all space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 font-bold text-white text-xs">
                    <span>{c.origin}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-cyan-400" />
                    <span className="text-emerald-300">{c.destination}</span>
                  </div>

                  <span 
                    className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                    style={{ 
                      backgroundColor: `${tierColorMap[c.corridor_category]}20`,
                      color: tierColorMap[c.corridor_category],
                      border: `1px solid ${tierColorMap[c.corridor_category]}40`
                    }}
                  >
                    {c.corridor_category}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center text-[11px] pt-1">
                  <div className="p-1 rounded bg-slate-950/60">
                    <span className="text-[9px] text-slate-400 block uppercase">Tourist Flow</span>
                    <strong className="text-white font-mono">{c.tourist_flow_thousands.toFixed(0)}k</strong>
                  </div>
                  <div className="p-1 rounded bg-slate-950/60">
                    <span className="text-[9px] text-slate-400 block uppercase">Dest ALOS</span>
                    <strong className="text-cyan-300 font-mono">{c.dest_alos?.toFixed(2) || 'N/A'}d</strong>
                  </div>
                  <div className="p-1 rounded bg-slate-950/60">
                    <span className="text-[9px] text-slate-400 block uppercase">Spend/Night</span>
                    <strong className="text-emerald-300 font-mono">RM {c.dest_spend_per_night?.toFixed(0) || 'N/A'}</strong>
                  </div>
                </div>

                {c.corridor_category === 'Priority Conversion Corridor' && (
                  <div className="text-[10px] text-amber-300/90 flex items-center gap-1 bg-amber-500/10 px-2 py-1 rounded">
                    <AlertTriangle className="w-3 h-3 text-amber-400 shrink-0" />
                    <span>High volume, short stay: Prime target to convert day-trips into hotel stays.</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Gravity Model Specifications & Inbound Market Concentration (HHI) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Gravity Model Specification Card */}
        <div className="glass-panel p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              Structural Tinbergen Gravity Equation Parameters
            </h3>
            <span className="text-xs text-slate-400 font-mono">N = 1,890 observations</span>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed font-mono bg-slate-900/80 p-2.5 rounded border border-slate-800">
            ln(Flow) = β₀ + 0.890 ln(Origin WA Pop) + 0.725 ln(Origin Income) + 0.704 ln(Dest Pull) - 0.603 ln(Dist) - 1.332 CrossRegion
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
            <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Origin Working Age</span>
              <strong className="text-emerald-400 font-mono text-sm">+0.890</strong>
              <span className="text-[9px] text-slate-400 block">p &lt; 0.001</span>
            </div>
            <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Origin Income</span>
              <strong className="text-emerald-400 font-mono text-sm">+0.725</strong>
              <span className="text-[9px] text-slate-400 block">p &lt; 0.001</span>
            </div>
            <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Distance Friction</span>
              <strong className="text-rose-400 font-mono text-sm">-0.603</strong>
              <span className="text-[9px] text-slate-400 block">p &lt; 0.001</span>
            </div>
            <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Out-of-Sample R²</span>
              <strong className="text-cyan-400 font-mono text-sm">0.5900</strong>
              <span className="text-[9px] text-slate-400 block">Tested on 2025</span>
            </div>
          </div>
        </div>

        {/* Market Fragility & Feeder Concentration (HHI) */}
        <div className="glass-panel p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Destination Feeder Concentration (HHI Index)
            </h3>
            <span className="text-xs text-slate-400">SDG Market Resilience</span>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            High Herfindahl-Hirschman Index (HHI &gt; 2,500) indicates acute vulnerability to economic shocks or transport disruptions in a single source market (e.g. over-reliance on Klang Valley outbound visitors).
          </p>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2.5 rounded bg-slate-900/60 border border-rose-500/20 space-y-1">
              <span className="font-bold text-rose-400 text-xs">High Vulnerability Destinations</span>
              <div className="text-slate-300 text-[11px]">
                • <strong>Negeri Sembilan</strong> (HHI: 3,420 — 55% from Selangor/KL)<br />
                • <strong>Melaka</strong> (HHI: 2,890 — 48% from Selangor/Johor)
              </div>
            </div>

            <div className="p-2.5 rounded bg-slate-900/60 border border-emerald-500/20 space-y-1">
              <span className="font-bold text-emerald-400 text-xs">Balanced Feeder Destinations</span>
              <div className="text-slate-300 text-[11px]">
                • <strong>Pulau Pinang</strong> (HHI: 1,480 — Diversified North/Central)<br />
                • <strong>Sabah</strong> (HHI: 1,620 — Multi-state feeder pool)
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
