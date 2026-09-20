import React, { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';
import type { ODCorridorsData, Corridor, StateProfile } from '../types';
import {
  ArrowRight,
  Filter,
  ShieldCheck,
  Compass,
  Activity,
  AlertTriangle,
  Search,
  X,
  Sparkles,
  Hotel,
  Users,
  Wallet,
  ExternalLink
} from 'lucide-react';

interface CorridorNetworkProps {
  corridorData: ODCorridorsData;
  geoJson: any;
  stateProfiles?: Record<string, StateProfile>;
  selectedYear?: number;
  onSelectCorridorForScenario?: (destination: string) => void;
}

export const CorridorNetwork: React.FC<CorridorNetworkProps> = ({
  corridorData,
  geoJson,
  stateProfiles,
  selectedYear = 2025,
  onSelectCorridorForScenario
}) => {
  const [selectedTier, setSelectedTier] = useState<string>('All');
  const [selectedOrigin, setSelectedOrigin] = useState<string>('All');
  const [selectedDestination, setSelectedDestination] = useState<string>('All');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedCorridor, setSelectedCorridor] = useState<Corridor | null>(null);

  useEffect(() => {
    if (geoJson) {
      echarts.registerMap('malaysia', geoJson);
    }
  }, [geoJson]);

  // Support Longitudinal Year filter (Recommendation 4)
  const allCorridors = (selectedYear && corridorData.corridors_by_year && corridorData.corridors_by_year[selectedYear])
    ? corridorData.corridors_by_year[selectedYear]
    : (corridorData.corridors_2025 || []);

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
    'Priority Conversion Corridor': '#b9782f', // Amber/Orange
    'Protect & Deepen': '#6d4bc1',             // Emerald
    'Growth Opportunity': '#8b8798',           // Cyan
    'Lower Strategic Priority': '#a29aaa',     // Slate
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
        color: tierColorMap[c.corridor_category] || '#8b8798',
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
      backgroundColor: '#ffffff',
      borderColor: 'rgba(70, 50, 100, 0.16)',
      textStyle: { color: '#241d32', fontSize: 12 },
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
        areaColor: '#eee9f4',
        borderColor: 'rgba(70, 50, 100, 0.16)',
        borderWidth: 0.8,
      },
      emphasis: {
        itemStyle: { areaColor: '#e3deea' },
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

  const onArcClick = (params: any) => {
    if (params.data && params.data.corridorMeta) {
      setSelectedCorridor(params.data.corridorMeta);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner: Tinbergen Gravity Model & RQ6 Target */}
      <div className="glass-panel p-6 border-l-4 border-l-cyan-500">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-indigo-400/20 text-indigo-600">
                Spatial Econometrics & RQ6
              </span>
              <span className="text-xs text-stone-600">Tinbergen Gravity Model (R² = 0.7092)</span>
            </div>
            <h2 className="text-2xl font-bold text-stone-900 tracking-tight">
              Domestic Tourism Value Corridors & Mobility Gravity
            </h2>
            <p className="text-sm text-stone-700 mt-1 max-w-3xl">
              Targeting high-flow corridors with weak accommodation capture enables Malaysia to generate additional overnight tourism value without needing new visitor headcount. Structural gravity modeling reveals that <strong>Origin Working-Age Population (+0.890)</strong> and <strong>Origin Median Income (+0.725)</strong> are powerful outbound mobility engines.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="p-3.5 rounded-xl bg-white/90 border border-indigo-300/30 text-center min-w-[130px]">
              <span className="text-xs text-stone-600 uppercase font-semibold">Origin Income</span>
              <div className="text-2xl font-extrabold text-indigo-600 font-mono">+0.725</div>
              <span className="text-[10px] text-indigo-600">Elasticity (p &lt; 0.001)</span>
            </div>
            <div className="p-3.5 rounded-xl bg-white/90 border border-rose-500/30 text-center min-w-[130px]">
              <span className="text-xs text-stone-600 uppercase font-semibold">Borneo Barrier</span>
              <div className="text-2xl font-extrabold text-rose-700 font-mono">-73.6%</div>
              <span className="text-[10px] text-rose-700">Flight Volume Penalty</span>
            </div>
          </div>
        </div>
      </div>

      {/* Filter Controls Bar */}
      <div className="glass-panel p-4 flex flex-wrap items-center justify-between gap-3 text-xs">
        {/* Tier Filter Buttons */}
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-stone-600 font-semibold mr-1 flex items-center gap-1">
            <Filter className="w-3.5 h-3.5 text-indigo-600" /> Tier:
          </span>
          {['All', 'Priority Conversion Corridor', 'Protect & Deepen', 'Growth Opportunity'].map((tier) => (
            <button
              key={tier}
              onClick={() => setSelectedTier(tier)}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                selectedTier === tier
                  ? 'bg-indigo-400/20 text-indigo-600 border border-indigo-300/40 shadow-sm'
                  : 'bg-white/60 text-stone-600 border border-violet-100 hover:text-stone-900'
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
            className="bg-white border border-violet-100 text-stone-800 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-300"
          >
            <option value="All">All Origins</option>
            {origins.map((o) => (
              <option key={o} value={o}>{o}</option>
            ))}
          </select>

          <select
            value={selectedDestination}
            onChange={(e) => setSelectedDestination(e.target.value)}
            className="bg-white border border-violet-100 text-stone-800 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-300"
          >
            <option value="All">All Destinations</option>
            {destinations.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>

          <div className="relative">
            <Search className="w-3.5 h-3.5 text-stone-600 absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Search corridor..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-white border border-violet-100 text-stone-800 rounded-lg pl-8 pr-3 py-1.5 text-xs focus:outline-none focus:border-indigo-300 w-36"
            />
          </div>
        </div>
      </div>

      {/* Main Grid: Flow Map & Priority Corridor Table */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Animated Geodesic Arcs Map (7 cols) */}
        <div className="glass-panel p-5 lg:col-span-7 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-stone-700 uppercase tracking-wider flex items-center gap-1.5">
              <Compass className="w-4 h-4 text-indigo-600" />
              Inter-State Flow Network (Top 50 Geodesic Arcs)
            </span>
            <div className="flex items-center gap-2 text-[11px]">
              <span className="flex items-center gap-1 text-amber-700"><span className="w-2 h-2 rounded-full bg-amber-500"></span> Conversion</span>
              <span className="flex items-center gap-1 text-violet-700"><span className="w-2 h-2 rounded-full bg-violet-600"></span> Protect</span>
              <span className="flex items-center gap-1 text-indigo-600"><span className="w-2 h-2 rounded-full bg-indigo-400"></span> Growth</span>
            </div>
          </div>

          <div className="h-[460px] w-full">
            <ReactECharts
              option={mapArcsOption}
              style={{ height: '100%', width: '100%' }}
              onEvents={{ click: onArcClick }}
            />
          </div>

          <div className="pt-3 border-t border-violet-100/60 flex items-center justify-between text-xs text-stone-600">
            <span>Click any arc to inspect bilateral corridor profile</span>
            <span className="text-indigo-600 font-mono font-medium">
              Showing {filteredCorridors.length} of {allCorridors.length} inter-state corridors ({selectedYear})
            </span>
          </div>
        </div>

        {/* Priority Corridors Ranked List (5 cols) */}
        <div className="glass-panel p-5 lg:col-span-5 flex flex-col space-y-3">
          <div className="flex items-center justify-between border-b border-violet-100/60 pb-2">
            <div>
              <h3 className="text-sm font-bold text-stone-900">Corridor Strategic Ranking</h3>
              <p className="text-[11px] text-stone-600">Sorted by {selectedYear} tourist flow volume</p>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-800 font-semibold uppercase">
              Action Priority
            </span>
          </div>

          {/* Scrollable list of corridors */}
          <div className="space-y-2 max-h-[430px] overflow-y-auto pr-1">
            {filteredCorridors.slice(0, 15).map((c, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-white/70 border border-violet-100 hover:border-violet-200 transition-all space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 font-bold text-stone-900 text-xs">
                    <span>{c.origin}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-indigo-600" />
                    <span className="text-violet-700">{c.destination}</span>
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
                  <div className="p-1 rounded bg-stone-50/60">
                    <span className="text-[9px] text-stone-600 block uppercase">Tourist Flow</span>
                    <strong className="text-stone-900 font-mono">{c.tourist_flow_thousands.toFixed(0)}k</strong>
                  </div>
                  <div className="p-1 rounded bg-stone-50/60">
                    <span className="text-[9px] text-stone-600 block uppercase">Dest ALOS</span>
                    <strong className="text-indigo-600 font-mono">{c.dest_alos?.toFixed(2) || 'N/A'}d</strong>
                  </div>
                  <div className="p-1 rounded bg-stone-50/60">
                    <span className="text-[9px] text-stone-600 block uppercase">Spend/Night</span>
                    <strong className="text-violet-700 font-mono">RM {c.dest_spend_per_night?.toFixed(0) || 'N/A'}</strong>
                  </div>
                </div>

                {c.corridor_category === 'Priority Conversion Corridor' && (
                  <div className="text-[10px] text-amber-800/90 flex items-center gap-1 bg-amber-500/10 px-2 py-1 rounded">
                    <AlertTriangle className="w-3 h-3 text-amber-700 shrink-0" />
                    <span>High volume, short stay: Prime target to convert day-trips into hotel stays.</span>
                  </div>
                )}

                <button
                  onClick={() => setSelectedCorridor(c)}
                  className="w-full flex items-center justify-center gap-1.5 py-1 px-2 rounded bg-violet-50/80 hover:bg-violet-100 text-indigo-600 text-[11px] font-semibold transition-all mt-1 cursor-pointer border border-violet-200"
                >
                  <Compass className="w-3 h-3" />
                  <span>Inspect Bilateral Profile</span>
                </button>
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
            <h3 className="text-sm font-bold text-stone-900 flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-600" />
              Structural Tinbergen Gravity Equation Parameters
            </h3>
            <span className="text-xs text-stone-600 font-mono">N = 1,890 observations</span>
          </div>

          <p className="text-xs text-stone-700 leading-relaxed font-mono bg-white/80 p-2.5 rounded border border-violet-100">
            ln(Flow) = β₀ + 0.890 ln(Origin WA Pop) + 0.725 ln(Origin Income) + 0.704 ln(Dest Pull) - 0.603 ln(Dist) - 1.332 CrossRegion
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
            <div className="p-2 rounded bg-white/60 border border-violet-100">
              <span className="text-[10px] text-stone-600 block">Origin Working Age</span>
              <strong className="text-violet-700 font-mono text-sm">+0.890</strong>
              <span className="text-[9px] text-stone-600 block">p &lt; 0.001</span>
            </div>
            <div className="p-2 rounded bg-white/60 border border-violet-100">
              <span className="text-[10px] text-stone-600 block">Origin Income</span>
              <strong className="text-violet-700 font-mono text-sm">+0.725</strong>
              <span className="text-[9px] text-stone-600 block">p &lt; 0.001</span>
            </div>
            <div className="p-2 rounded bg-white/60 border border-violet-100">
              <span className="text-[10px] text-stone-600 block">Distance Friction</span>
              <strong className="text-rose-700 font-mono text-sm">-0.603</strong>
              <span className="text-[9px] text-stone-600 block">p &lt; 0.001</span>
            </div>
            <div className="p-2 rounded bg-white/60 border border-violet-100">
              <span className="text-[10px] text-stone-600 block">Out-of-Sample R²</span>
              <strong className="text-indigo-600 font-mono text-sm">0.5900</strong>
              <span className="text-[9px] text-stone-600 block">Tested on 2025</span>
            </div>
          </div>
        </div>

        {/* Market Fragility & Feeder Concentration (HHI) */}
        <div className="glass-panel p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-stone-900 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-violet-700" />
              Destination Feeder Concentration (HHI Index)
            </h3>
            <span className="text-xs text-stone-600">SDG Market Resilience</span>
          </div>

          <p className="text-xs text-stone-700 leading-relaxed">
            Market concentration distinguishes <strong>Interstate Origin HHI</strong> (evaluating vulnerability to external feeder shocks) from <strong>All-Origin HHI</strong> (which reflects local resident travel).
          </p>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2.5 rounded bg-white/60 border border-amber-500/20 space-y-1">
              <span className="font-bold text-amber-700 text-xs">Interstate Concentrated Feeders</span>
              <div className="text-stone-700 text-[11px] space-y-1">
                <div>• <strong>Pulau Pinang</strong> (HHI: 2,462 — 44.5% from Selangor)</div>
                <div>• <strong>Melaka</strong> (HHI: 2,156 — 38.8% from Selangor)</div>
              </div>
            </div>

            <div className="p-2.5 rounded bg-white/60 border border-violet-400/20 space-y-1">
              <span className="font-bold text-violet-700 text-xs">Borneo & Diversified Feeders</span>
              <div className="text-stone-700 text-[11px] space-y-1">
                <div>• <strong>Sabah</strong>: Interstate HHI = 1,450 (Diversified); All-Origin HHI = 5,747 (75.2% Intrastate travel)</div>
                <div>• <strong>Negeri Sembilan</strong>: Interstate HHI = 2,127 (32.5% from Selangor)</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bilateral Comparative Inspector Modal (Recommendation 2) */}
      {selectedCorridor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white border border-violet-200 rounded-2xl w-full max-w-4xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Header */}
            <div className="p-4 px-6 border-b border-violet-100 flex items-center justify-between bg-stone-50/70">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-indigo-400/10 border border-indigo-300/30 text-indigo-600">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-bold text-stone-900">
                      Bilateral Corridor Inspector: {selectedCorridor.origin} → {selectedCorridor.destination}
                    </h3>
                    <span
                      className="text-[10px] font-bold px-2.5 py-0.5 rounded-full"
                      style={{
                        backgroundColor: `${tierColorMap[selectedCorridor.corridor_category]}20`,
                        color: tierColorMap[selectedCorridor.corridor_category],
                        border: `1px solid ${tierColorMap[selectedCorridor.corridor_category]}50`
                      }}
                    >
                      {selectedCorridor.corridor_category}
                    </span>
                  </div>
                  <p className="text-xs text-stone-600">
                    Cross-State Gravity & Bilateral Value Conversion Diagnostic • Year {selectedYear}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {onSelectCorridorForScenario && (
                  <button
                    onClick={() => {
                      const dest = selectedCorridor.destination;
                      setSelectedCorridor(null);
                      onSelectCorridorForScenario(dest);
                    }}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-violet-700 hover:bg-violet-600 text-stone-900 text-xs font-semibold transition-all cursor-pointer shadow-sm"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    Simulate Destination
                  </button>
                )}
                <button
                  onClick={() => setSelectedCorridor(null)}
                  className="p-1.5 rounded-lg bg-violet-50 hover:bg-violet-100 text-stone-600 hover:text-stone-900 transition-all cursor-pointer ml-1"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6 text-xs text-stone-700">
              {/* Top Bilateral Quick Facts Strip */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <div className="p-2.5 rounded-lg bg-stone-50/70 border border-violet-100">
                  <span className="text-[10px] uppercase text-stone-600 block font-semibold">Tourist Volume</span>
                  <strong className="text-stone-900 text-base font-mono">{selectedCorridor.tourist_flow_thousands.toFixed(1)}k</strong>
                  <span className="text-[10px] text-stone-600 block">tourists / year</span>
                </div>
                <div className="p-2.5 rounded-lg bg-stone-50/70 border border-violet-100">
                  <span className="text-[10px] uppercase text-stone-600 block font-semibold">Spatial Distance</span>
                  <strong className="text-indigo-600 text-base font-mono">{selectedCorridor.distance_km?.toFixed(0) || '250'} km</strong>
                  <span className="text-[10px] text-stone-600 block">{selectedCorridor.is_cross_region ? '✈️ Cross-Region Air' : '🚗 Overland Highway'}</span>
                </div>
                <div className="p-2.5 rounded-lg bg-stone-50/70 border border-violet-100">
                  <span className="text-[10px] uppercase text-stone-600 block font-semibold">Dest Stay Duration</span>
                  <strong className="text-violet-700 text-base font-mono">{selectedCorridor.dest_alos?.toFixed(2) || 'N/A'} days</strong>
                  <span className="text-[10px] text-stone-600 block">Average Length of Stay</span>
                </div>
                <div className="p-2.5 rounded-lg bg-stone-50/70 border border-violet-100">
                  <span className="text-[10px] uppercase text-stone-600 block font-semibold">Nightly Spend Yield</span>
                  <strong className="text-amber-800 text-base font-mono">RM {selectedCorridor.dest_spend_per_night?.toFixed(0) || 'N/A'}</strong>
                  <span className="text-[10px] text-stone-600 block">per tourist / night</span>
                </div>
              </div>

              {/* Side-by-Side: Origin Demographics vs Destination Lodging */}
              {(() => {
                const orig = stateProfiles ? stateProfiles[selectedCorridor.origin] : null;
                const dest = stateProfiles ? stateProfiles[selectedCorridor.destination] : null;
                return (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Origin Demographics & Spending Engine */}
                    <div className="p-4 rounded-xl bg-stone-50/80 border border-violet-100 space-y-3">
                      <div className="flex items-center justify-between border-b border-violet-100/80 pb-2">
                        <div className="flex items-center gap-2">
                          <Users className="w-4 h-4 text-indigo-600" />
                          <h4 className="font-bold text-stone-900 text-sm">
                            Origin Feeder: {selectedCorridor.origin}
                          </h4>
                        </div>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-400/20 text-indigo-600 font-mono">
                          Outbound Engine
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        <div className="p-2 rounded bg-white/80 border border-violet-100">
                          <span className="text-stone-600 block text-[10px]">Total Population</span>
                          <strong className="text-stone-900 font-mono text-xs">
                            {orig?.demographics?.total_population_millions?.toFixed(2) || 'N/A'} Million
                          </strong>
                        </div>
                        <div className="p-2 rounded bg-white/80 border border-violet-100">
                          <span className="text-stone-600 block text-[10px]">Adults (15+ years)</span>
                          <strong className="text-stone-900 font-mono text-xs">
                            {orig?.demographics?.adult_15plus_thousands ? (orig.demographics.adult_15plus_thousands / 1000).toFixed(2) : 'N/A'} M
                          </strong>
                        </div>
                      </div>

                      {/* DTS Non-overlapping Adult Cohorts */}
                      <div className="space-y-1.5 bg-white/50 p-2.5 rounded-lg border border-violet-100/60">
                        <span className="text-[10px] font-semibold text-stone-700 block uppercase tracking-wide">
                          DTS Visitor Adult Cohort Distribution
                        </span>
                        <div className="grid grid-cols-4 gap-1 text-center text-[10px]">
                          <div className="p-1 rounded bg-stone-50/80">
                            <span className="text-indigo-600 block font-medium">15–24</span>
                            <strong className="text-stone-900 font-mono">{orig?.demographics?.dts_age_classes?.age_15_24_pct || 22}%</strong>
                          </div>
                          <div className="p-1 rounded bg-violet-50/30 border border-violet-400/30">
                            <span className="text-violet-700 block font-medium">25–39 (Prime)</span>
                            <strong className="text-violet-700 font-mono">{orig?.demographics?.dts_age_classes?.age_25_39_pct || 35}%</strong>
                          </div>
                          <div className="p-1 rounded bg-stone-50/80">
                            <span className="text-amber-700 block font-medium">40–54</span>
                            <strong className="text-stone-900 font-mono">{orig?.demographics?.dts_age_classes?.age_40_54_pct || 24}%</strong>
                          </div>
                          <div className="p-1 rounded bg-stone-50/80">
                            <span className="text-violet-700 block font-medium">≥ 55</span>
                            <strong className="text-stone-900 font-mono">{orig?.demographics?.dts_age_classes?.age_55plus_pct || 19}%</strong>
                          </div>
                        </div>
                      </div>

                      <div className="p-2.5 rounded-lg bg-white/80 border border-violet-100 flex items-center justify-between text-[11px]">
                        <span className="text-stone-600 flex items-center gap-1.5">
                          <Wallet className="w-3.5 h-3.5 text-violet-700" />
                          Resident Median Income:
                        </span>
                        <strong className="text-violet-700 font-mono text-xs">
                          RM {orig?.baseline_2025?.resident_median_income_rm?.toLocaleString() || 'N/A'}
                        </strong>
                      </div>
                    </div>

                    {/* Destination Absorption & Lodging Capacity */}
                    <div className="p-4 rounded-xl bg-stone-50/80 border border-violet-100 space-y-3">
                      <div className="flex items-center justify-between border-b border-violet-100/80 pb-2">
                        <div className="flex items-center gap-2">
                          <Hotel className="w-4 h-4 text-violet-700" />
                          <h4 className="font-bold text-stone-900 text-sm">
                            Destination Host: {selectedCorridor.destination}
                          </h4>
                        </div>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-violet-600/20 text-violet-700 font-mono">
                          Absorption Capacity
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        <div className="p-2 rounded bg-white/80 border border-violet-100">
                          <span className="text-stone-600 block text-[10px]">Hotel Capacity</span>
                          <strong className="text-stone-900 font-mono text-xs">
                            {dest?.hotel_stars?.total_rooms?.toLocaleString() || dest?.baseline_2025?.hotel_rooms?.toLocaleString() || 'N/A'} rooms
                          </strong>
                        </div>
                        <div className="p-2 rounded bg-white/80 border border-violet-100">
                          <span className="text-stone-600 block text-[10px]">4/5-Star Luxury Share</span>
                          <strong className="text-amber-700 font-mono text-xs">
                            {dest?.hotel_stars?.luxury_room_share_pct?.toFixed(1) || '25.0'}%
                          </strong>
                        </div>
                      </div>

                      <div className="space-y-1.5 bg-white/50 p-2.5 rounded-lg border border-violet-100/60">
                        <div className="flex justify-between text-[10px] text-stone-700">
                          <span>Lodging Mix (Commercial vs Unpaid VFR)</span>
                          <span className="font-mono text-amber-700 font-semibold">{dest?.lodging_shares?.unpaid_vfr_pct ?? 50}% VFR</span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-violet-50 overflow-hidden flex">
                          <div
                            className="bg-violet-600 h-full"
                            style={{ width: `${dest?.lodging_shares?.paid_commercial_pct ?? 50}%` }}
                            title={`Paid Commercial: ${dest?.lodging_shares?.paid_commercial_pct ?? 50}%`}
                          ></div>
                          <div
                            className="bg-amber-500 h-full"
                            style={{ width: `${dest?.lodging_shares?.unpaid_vfr_pct ?? 50}%` }}
                            title={`Unpaid VFR: ${dest?.lodging_shares?.unpaid_vfr_pct ?? 50}%`}
                          ></div>
                        </div>
                        <div className="flex justify-between text-[9px] text-stone-600 pt-0.5">
                          <span>Paid Hotel / Commercial: <strong className="text-violet-700 font-mono">{dest?.lodging_shares?.paid_commercial_pct ?? 50}%</strong></span>
                          <span>Unpaid VFR / Relatives: <strong className="text-amber-700 font-mono">{dest?.lodging_shares?.unpaid_vfr_pct ?? 50}%</strong></span>
                        </div>
                      </div>

                      <div className="p-2.5 rounded-lg bg-white/80 border border-violet-100 flex items-center justify-between text-[11px]">
                        <span className="text-stone-600">Average Room Occupancy (AOR):</span>
                        <strong className="text-indigo-600 font-mono text-xs">
                          {dest?.baseline_2025?.aor_pct?.toFixed(1) || '55.0'}%
                        </strong>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* Gravity Diagnostic & Tailored Strategic Playbook */}
              <div className="p-4 rounded-xl bg-stone-50/90 border border-violet-100 space-y-3">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-indigo-600" />
                  <h4 className="font-bold text-stone-900 text-sm">
                    Structural Gravity Diagnostic & Conversion Action Playbook
                  </h4>
                </div>

                <p className="text-xs text-stone-700 leading-relaxed">
                  Under the Tinbergen Gravity Model (R² = 0.7092), outbound flow from <strong>{selectedCorridor.origin}</strong> is heavily propelled by its working-age demographic mass (β = +0.890) and median household income (β = +0.725).
                </p>

                {/* Specific Policy Playbook Box */}
                <div
                  className="p-3 rounded-lg border text-xs space-y-1.5"
                  style={{
                    backgroundColor: `${tierColorMap[selectedCorridor.corridor_category]}15`,
                    borderColor: `${tierColorMap[selectedCorridor.corridor_category]}40`
                  }}
                >
                  <div className="font-bold flex items-center gap-1.5" style={{ color: tierColorMap[selectedCorridor.corridor_category] }}>
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Recommended Policy Playbook ({selectedCorridor.corridor_category}):
                  </div>
                  {selectedCorridor.corridor_category === 'Priority Conversion Corridor' && (
                    <ul className="text-stone-800 text-[11px] space-y-1 list-disc list-inside">
                      <li><strong>Stay Extension Levers:</strong> Introduce corporate mid-week retreats and weekend staycation incentive vouchers to turn quick transit into overnight stays (+0.5 nights target).</li>
                      <li><strong>Night-Time Economy:</strong> Curate evening cultural experiences, heritage food trails, and waterfront light festivals to discourage same-day return travel.</li>
                      <li><strong>Homestay Integration (SDG 8.9):</strong> Transition unpaid VFR stays into licensed community homestays and heritage boutique inns to capture local accommodation GVA.</li>
                    </ul>
                  )}
                  {selectedCorridor.corridor_category === 'Protect & Deepen' && (
                    <ul className="text-stone-800 text-[11px] space-y-1 list-disc list-inside">
                      <li><strong>Premium Loyalty Partnerships:</strong> Partner with high-income employers and flight/rail operators to offer VIP repeat-visitor privileges.</li>
                      <li><strong>High-Yield Add-Ons:</strong> Expand luxury nature retreats, wellness packages, and certified eco-tourism experiential activities.</li>
                      <li><strong>Service Quality Assurance:</strong> Maintain strict hotel standards and green certification (SDG 12.b) to sustain top-quartile spend per night.</li>
                    </ul>
                  )}
                  {selectedCorridor.corridor_category === 'Growth Opportunity' && (
                    <ul className="text-stone-800 text-[11px] space-y-1 list-disc list-inside">
                      <li><strong>Transport Friction Relief:</strong> Subsidize direct inter-state flight or express coach frequencies to overcome distance friction (β = -0.603).</li>
                      <li><strong>Targeted Feeder Marketing:</strong> Launch focused digital marketing campaigns targeting the 25–39 prime mobile demographic in {selectedCorridor.origin}.</li>
                      <li><strong>Bundled Thematic Circuits:</strong> Partner with neighboring states to offer multi-destination regional passes.</li>
                    </ul>
                  )}
                  {selectedCorridor.corridor_category === 'Lower Strategic Priority' && (
                    <p className="text-stone-800 text-[11px]">
                      Maintain baseline organic presence in regional tourism campaigns. Focus state investment on higher-yield conversion corridors.
                    </p>
                  )}
                </div>

                <div className="text-[10px] text-stone-600 italic">
                  * Structural gravity equation: ln(Flow) = β₀ + 0.890 ln(Origin WA Pop) + 0.725 ln(Origin Income) - 0.603 ln(Distance) - 1.332 CrossRegionBarrier.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
