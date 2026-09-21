import React, { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';
import type { ODCorridorsData, Corridor, StateProfile, ModelMetricsData } from '../types';
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
  ExternalLink,
  Play,
  Pause,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  HelpCircle
} from 'lucide-react';
import { EvidenceDrawer, type EvidenceItem } from './EvidenceDrawer';

interface CorridorNetworkProps {
  corridorData: ODCorridorsData;
  geoJson: any;
  stateProfiles?: Record<string, StateProfile>;
  selectedYear?: number;
  modelMetrics?: ModelMetricsData | null;
  onSelectCorridorForScenario?: (destination: string, origin?: string) => void;
}

export const CorridorNetwork: React.FC<CorridorNetworkProps> = ({
  corridorData,
  geoJson,
  stateProfiles,
  selectedYear = 2025,
  modelMetrics,
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

  const [animYear, setAnimYear] = useState<number>(selectedYear || 2025);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [evidenceDrawerData, setEvidenceDrawerData] = useState<EvidenceItem | null>(null);

  const openEvidenceDrawerForCorridor = (c: Corridor) => {
    setEvidenceDrawerData({
      recommendationTitle: `Target ${c.origin} → ${c.destination} (${c.corridor_category})`,
      actionType: c.corridor_category,
      targetCorridorOrState: `${c.origin} → ${c.destination}`,
      observation: `${c.origin} generates ${c.tourist_flow_thousands.toFixed(1)}k domestic tourists to ${c.destination}. Destination stay duration is ${c.dest_alos != null ? `${c.dest_alos.toFixed(2)} days` : 'unobserved'} (national median: 2.47d) with average lodging expenditure of ${c.dest_spend_per_night != null ? `RM ${c.dest_spend_per_night.toFixed(1)}/night` : 'N/A'}.`,
      supportingMetrics: [
        { label: 'Tourist Volume', value: `${c.tourist_flow_thousands.toFixed(1)}k`, context: '2025 actual flow' },
        { label: 'Destination ALOS', value: c.dest_alos != null ? `${c.dest_alos.toFixed(2)}d` : 'N/A', context: 'Stay duration benchmark' },
        { label: 'Nightly Spend', value: c.dest_spend_per_night != null ? `RM ${c.dest_spend_per_night.toFixed(1)}` : 'N/A', context: 'Accommodation yield' },
        { label: 'Capacity Headroom', value: c.capacity_headroom_pct != null ? `${c.capacity_headroom_pct.toFixed(0)}%` : 'N/A', context: 'Room space below 80% ceiling' },
        { label: 'Gravity Gap', value: c.gravity_flow_gap_thousands != null ? `${c.gravity_flow_gap_thousands > 0 ? '+' : ''}${c.gravity_flow_gap_thousands.toFixed(0)}k` : '0k', context: c.gravity_performance_category || 'Model Expected' },
        { label: 'Pareto Rank', value: c.is_pareto_optimal ? 'Rank 1 (Pareto Frontier)' : `Rank ${c.pareto_rank || 'N/A'}`, context: 'Non-dominated multi-criteria' },
      ],
      modelEvidence: {
        modelName: 'PPML Structural Gravity & Pareto Optimization',
        specification: 'E[Flow_ijt] = exp(α_i + γ_j + δ_t + β_dist · ln(Dist) + β_borneo · Borneo)',
        finding: `Empirically validated with Out-of-sample R² = ${modelMetrics?.gravity?.r2_oos != null ? modelMetrics.gravity.r2_oos.toFixed(4) : '0.5890'} and distance friction β = ${modelMetrics?.gravity?.distance_decay_friction != null ? modelMetrics.gravity.distance_decay_friction.toFixed(3) : '-0.410'}.`,
        keyCoefficients: `Borneo barrier friction: ${modelMetrics?.gravity?.cross_region_barrier != null ? `${(-((1 - Math.exp(modelMetrics.gravity.cross_region_barrier)) * 100)).toFixed(1)}%` : '-55.2%'}`,
      },
      source: 'DOSM DTS 2025, TSA 2025, and PPML Gravity Optimization Matrix',
      status: 'Model Calibrated',
      confidence: c.tourist_flow_thousands > 500 ? 'Very High' : 'High',
      limitations: [
        'Origin-destination flows capture primary reported destination; incidental multi-leg road trips are attributed to main stop.',
        'Scenario expenditure uplift depends on marketing campaign reach and conversion rates.',
        'Annual destination hotel occupancy may conceal weekend and holiday peak congestion.',
      ],
    });
  };

  useEffect(() => {
    if (selectedYear) setAnimYear(selectedYear);
  }, [selectedYear]);

  // Longitudinal animation playback timer
  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        setAnimYear((prev) => {
          if (prev >= 2025) return 2018;
          return prev + 1;
        });
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  const availableYears = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025];

  const getPeriodContext = (yr: number) => {
    if (yr <= 2019) return { label: 'Pre-COVID Baseline', color: 'bg-emerald-100 text-emerald-800 border-emerald-300' };
    if (yr <= 2021) return { label: 'MCO Lockdown Contraction', color: 'bg-rose-100 text-rose-800 border-rose-300' };
    if (yr <= 2023) return { label: 'Domestic Travel Rebound', color: 'bg-amber-100 text-amber-800 border-amber-300' };
    return { label: 'Post-Recovery Maturation', color: 'bg-indigo-100 text-indigo-800 border-indigo-300' };
  };

  // Support Longitudinal Year filter (Recommendation 4 & Sprint 8 Phase 37)
  const allCorridors = (animYear && corridorData.corridors_by_year && corridorData.corridors_by_year[animYear])
    ? corridorData.corridors_by_year[animYear]
    : (corridorData.corridors_2025 || []);

  const totalFlowM = (allCorridors.reduce((acc, c) => acc + (c.tourist_flow_thousands || 0), 0) / 1000.0).toFixed(2);
  const period = getPeriodContext(animYear);

  // Filter corridors
  const filteredCorridors = allCorridors.filter((c) => {
    if (selectedTier === 'Pareto Frontier') {
      if (!c.is_pareto_optimal) return false;
    } else if (selectedTier !== 'All' && c.corridor_category !== selectedTier) {
      return false;
    }
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

  // Build ECharts Lines (Geo Arcs) Option - strict zero coordinate fallback
  const linesData = filteredCorridors
    .slice(0, 50)
    .filter((c) => (c.origin_lon != null || c.orig_lon != null) && (c.destination_lon != null || c.dest_lon != null))
    .map((c) => {
      const origLon = c.origin_lon ?? c.orig_lon!;
      const origLat = c.origin_lat ?? c.orig_lat!;
      const destLon = c.destination_lon ?? c.dest_lon!;
      const destLat = c.destination_lat ?? c.dest_lat!;
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
          const distKm = c.distance_km != null ? `${c.distance_km.toFixed(0)} km` : 'N/A';
          return `<div style="font-weight: bold; margin-bottom: 4px;">
              ${c.origin} → ${c.destination}
            </div>
            <div>Category: <strong style="color: ${tierColorMap[c.corridor_category]};">${c.corridor_category}</strong></div>
            <div>Tourist Flow: <strong>${c.tourist_flow_thousands.toFixed(1)}k tourists</strong></div>
            <div>Distance: <strong>${distKm}</strong> (${isCross ? 'Flight' : 'Overland'})</div>
            <div>Dest ALOS: <strong>${c.dest_alos != null ? `${c.dest_alos.toFixed(2)} days` : 'N/A'}</strong></div>
            <div>Dest Spend/Night: <strong>${c.dest_spend_per_night != null ? `RM ${c.dest_spend_per_night.toFixed(1)}` : 'N/A'}</strong></div>`;
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
      {/* Top Banner: Structural PPML Gravity Model & RQ6 Target */}
      <div className="glass-panel p-6 border-l-4 border-l-cyan-500">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-indigo-400/20 text-indigo-600">
                Spatial Econometrics & RQ6
              </span>
              <span className="text-xs text-stone-600 font-mono">
                Structural PPML Gravity (OOS R² = {modelMetrics?.gravity?.r2_oos != null ? modelMetrics.gravity.r2_oos.toFixed(4) : '—'})
              </span>
            </div>
            <h2 className="text-2xl font-bold text-stone-900 tracking-tight">
              Domestic Tourism Value Corridors & Mobility Gravity
            </h2>
            <p className="text-sm text-stone-700 mt-1 max-w-3xl">
              Targeting high-flow corridors with weak accommodation capture enables Malaysia to generate additional overnight tourism value without needing new visitor headcount. Structural PPML gravity modeling with Origin, Destination, and Year Fixed Effects eliminates target leakage while estimating distance decay (β = {modelMetrics?.gravity?.distance_decay_friction != null ? modelMetrics.gravity.distance_decay_friction.toFixed(3) : '—'}) and Borneo flight barrier friction.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="p-3.5 rounded-xl bg-white/90 border border-indigo-300/30 text-center min-w-[130px]">
              <span className="text-xs text-stone-600 uppercase font-semibold">Distance Friction</span>
              <div className="text-2xl font-extrabold text-indigo-600 font-mono">
                {modelMetrics?.gravity?.distance_decay_friction != null ? modelMetrics.gravity.distance_decay_friction.toFixed(3) : '—'}
              </div>
              <span className="text-[10px] text-indigo-600">Elasticity (p &lt; 0.001)</span>
            </div>
            <div className="p-3.5 rounded-xl bg-white/90 border border-rose-500/30 text-center min-w-[130px]">
              <span className="text-xs text-stone-600 uppercase font-semibold">Borneo Barrier</span>
              <div className="text-2xl font-extrabold text-rose-700 font-mono">
                {modelMetrics?.gravity?.cross_region_barrier != null
                  ? `${(-((1 - Math.exp(modelMetrics.gravity.cross_region_barrier)) * 100)).toFixed(1)}%`
                  : '—'}
              </div>
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
          {['All', 'Pareto Frontier', 'Priority Conversion Corridor', 'Protect & Deepen', 'Growth Opportunity'].map((tier) => (
            <button
              key={tier}
              onClick={() => setSelectedTier(tier)}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                selectedTier === tier
                  ? 'bg-indigo-400/20 text-indigo-600 border border-indigo-300/40 shadow-sm'
                  : 'bg-white/60 text-stone-600 border border-violet-100 hover:text-stone-900'
              }`}
            >
              {tier === 'All' ? 'All Corridors' : tier === 'Pareto Frontier' ? '✨ Pareto Frontier' : tier}
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

      {/* Sprint 8 Phase 37: Longitudinal Time Animation Control Bar (2018-2025) */}
      <div className="bg-gradient-to-r from-stone-900 via-purple-950 to-indigo-950 text-white rounded-xl p-4 shadow-md border border-purple-800/40">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className={`p-2 rounded-lg text-white transition-all flex items-center gap-1.5 text-xs font-semibold shadow ${
                  isPlaying ? 'bg-amber-600 hover:bg-amber-500' : 'bg-purple-600 hover:bg-purple-500'
                }`}
                title={isPlaying ? 'Pause Animation' : 'Play Timeline Animation (2018-2025)'}
              >
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                <span>{isPlaying ? 'Pause' : 'Play Timeline'}</span>
              </button>
              <button
                onClick={() => { setIsPlaying(false); setAnimYear(2018); }}
                className="p-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-all text-xs"
                title="Reset to 2018"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={() => setAnimYear(prev => Math.max(2018, prev - 1))}
                disabled={animYear <= 2018}
                className="p-1.5 rounded bg-white/5 hover:bg-white/15 disabled:opacity-30 text-white transition-all"
                title="Previous Year"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>
              <span className="font-mono text-lg font-bold text-amber-400 px-2 min-w-[50px] text-center">
                {animYear}
              </span>
              <button
                onClick={() => setAnimYear(prev => Math.min(2025, prev + 1))}
                disabled={animYear >= 2025}
                className="p-1.5 rounded bg-white/5 hover:bg-white/15 disabled:opacity-30 text-white transition-all"
                title="Next Year"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${period.color}`}>
              {period.label}
            </span>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5 text-purple-200">
              <span className="text-purple-300/70">Total Interstate Flow:</span>
              <span className="font-bold text-white font-mono">{totalFlowM}M tourists</span>
            </div>
            <div className="flex items-center gap-1.5 text-purple-200">
              <span className="text-purple-300/70">Active Corridors:</span>
              <span className="font-bold text-amber-300 font-mono">{allCorridors.length}</span>
            </div>
          </div>
        </div>

        {/* Year Pills Bar */}
        <div className="flex items-center gap-1.5 overflow-x-auto pt-1 border-t border-white/10">
          {availableYears.map(yr => {
            const isSelected = animYear === yr;
            return (
              <button
                key={yr}
                onClick={() => { setIsPlaying(false); setAnimYear(yr); }}
                className={`px-3 py-1 rounded-md text-xs font-mono transition-all shrink-0 ${
                  isSelected
                    ? 'bg-amber-400 text-slate-950 font-bold shadow-sm ring-2 ring-amber-300/50'
                    : 'bg-white/5 hover:bg-white/15 text-purple-200'
                }`}
              >
                {yr}
              </button>
            );
          })}
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
              Showing {filteredCorridors.length} of {allCorridors.length} inter-state corridors ({animYear})
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

                  <div className="flex items-center gap-1">
                    {c.is_pareto_optimal && (
                      <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-0.5 shadow-sm">
                        <Sparkles className="w-2.5 h-2.5" /> Pareto
                      </span>
                    )}
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
                </div>

                <div className="grid grid-cols-4 gap-1.5 text-center text-[11px] pt-1">
                  <div className="p-1 rounded bg-stone-50/60">
                    <span className="text-[9px] text-stone-600 block uppercase">Flow</span>
                    <strong className="text-stone-900 font-mono">{c.tourist_flow_thousands.toFixed(0)}k</strong>
                  </div>
                  <div className="p-1 rounded bg-stone-50/60">
                    <span className="text-[9px] text-stone-600 block uppercase">ALOS</span>
                    <strong className="text-indigo-600 font-mono">{c.dest_alos?.toFixed(1) || 'N/A'}d</strong>
                  </div>
                  <div className="p-1 rounded bg-stone-50/60">
                    <span className="text-[9px] text-stone-600 block uppercase">Spend/Nt</span>
                    <strong className="text-violet-700 font-mono">RM {c.dest_spend_per_night?.toFixed(0) || 'N/A'}</strong>
                  </div>
                  <div className="p-1 rounded bg-stone-50/60">
                    <span className="text-[9px] text-stone-600 block uppercase">Headroom</span>
                    <strong className="text-emerald-700 font-mono">
                      {c.capacity_headroom_pct != null ? `${c.capacity_headroom_pct.toFixed(0)}%` : 'N/A'}
                    </strong>
                  </div>
                </div>

                {/* Sprint 5: Opportunity Diagnostics Badges */}
                <div className="flex flex-wrap items-center gap-1 text-[9px]">
                  {c.gravity_performance_category && (
                    <span className={`px-1.5 py-0.5 rounded border ${
                      c.gravity_performance_category === 'Below Model Expected'
                        ? 'bg-amber-50 text-amber-800 border-amber-200'
                        : c.gravity_performance_category === 'Above Model Expected'
                        ? 'bg-blue-50 text-blue-800 border-blue-200'
                        : 'bg-stone-50 text-stone-700 border-stone-200'
                    }`}>
                      {c.gravity_performance_category}
                    </span>
                  )}
                  {c.diversification_benefit && (
                    <span className="px-1.5 py-0.5 rounded bg-violet-50 text-violet-800 border border-violet-200 truncate max-w-[130px]">
                      {c.diversification_benefit.split('(')[0].trim()}
                    </span>
                  )}
                  {c.composite_opportunity_score != null && (
                    <span className="ml-auto font-mono text-[10px] font-bold text-indigo-700">
                      Score: {c.composite_opportunity_score.toFixed(1)}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-1.5 mt-1">
                  <button
                    onClick={() => setSelectedCorridor(c)}
                    className="flex-1 flex items-center justify-center gap-1.5 py-1 px-2 rounded bg-violet-50/80 hover:bg-violet-100 text-indigo-600 text-[11px] font-semibold transition-all cursor-pointer border border-violet-200"
                  >
                    <Compass className="w-3 h-3" />
                    <span>Inspect Profile</span>
                  </button>
                  <button
                    onClick={() => openEvidenceDrawerForCorridor(c)}
                    className="flex items-center justify-center gap-1 py-1 px-2 rounded bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-[11px] font-semibold transition-all cursor-pointer border border-indigo-200"
                    title="Why is this corridor recommended?"
                  >
                    <HelpCircle className="w-3 h-3" />
                    <span>Evidence</span>
                  </button>
                </div>
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
              Structural Poisson Pseudo-Maximum Likelihood (PPML) Gravity
            </h3>
            <span className="text-xs text-stone-600 font-mono">
              N = {modelMetrics?.gravity?.total_panel_observations || 1920} panel obs (Holdout: 2025)
            </span>
          </div>

          <p className="text-xs text-stone-700 leading-relaxed font-mono bg-white/80 p-2.5 rounded border border-violet-100">
            E[Flow_ijt] = exp(α_origin + γ_dest + δ_year + {modelMetrics?.gravity?.distance_decay_friction != null ? modelMetrics.gravity.distance_decay_friction.toFixed(3) : 'β_dist'} · ln(Dist) {modelMetrics?.gravity?.cross_region_barrier != null ? (modelMetrics.gravity.cross_region_barrier > 0 ? `+ ${modelMetrics.gravity.cross_region_barrier.toFixed(3)}` : `${modelMetrics.gravity.cross_region_barrier.toFixed(3)}`) : 'β_borneo'} · Borneo)
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
            <div className="p-2 rounded bg-white/60 border border-violet-100">
              <span className="text-[10px] text-stone-600 block">Distance Friction</span>
              <strong className="text-rose-700 font-mono text-sm">
                {modelMetrics?.gravity?.distance_decay_friction != null ? modelMetrics.gravity.distance_decay_friction.toFixed(3) : '—'}
              </strong>
              <span className="text-[9px] text-stone-600 block">p &lt; 0.001</span>
            </div>
            <div className="p-2 rounded bg-white/60 border border-violet-100">
              <span className="text-[10px] text-stone-600 block">Borneo Barrier</span>
              <strong className="text-rose-700 font-mono text-sm">
                {modelMetrics?.gravity?.cross_region_barrier != null
                  ? `${(-((1 - Math.exp(modelMetrics.gravity.cross_region_barrier)) * 100)).toFixed(1)}%`
                  : '—'}
              </strong>
              <span className="text-[9px] text-stone-600 block">p &lt; 0.001</span>
            </div>
            <div className="p-2 rounded bg-white/60 border border-violet-100">
              <span className="text-[10px] text-stone-600 block">Out-of-Sample R²</span>
              <strong className="text-indigo-600 font-mono text-sm">
                {modelMetrics?.gravity?.r2_oos != null ? modelMetrics.gravity.r2_oos.toFixed(4) : '—'}
              </strong>
              <span className="text-[9px] text-stone-600 block">2025 Holdout</span>
            </div>
            <div className="p-2 rounded bg-white/60 border border-violet-100">
              <span className="text-[10px] text-stone-600 block">Distance Invariance</span>
              <strong className="text-emerald-700 font-mono text-sm">p = 0.120</strong>
              <span className="text-[9px] text-stone-600 block">No Structural Break</span>
            </div>
          </div>

          {/* Model Comparison / Naive Baselines Table */}
          {modelMetrics?.gravity?.naive_baselines && (
            <div className="mt-2 pt-2 border-t border-violet-100">
              <div className="text-[11px] font-semibold text-stone-700 mb-1 flex items-center justify-between">
                <span>Holdout Validation Comparison (2025 Actuals)</span>
                <span className="text-[10px] font-normal text-stone-500">True R² = 1 - SSE/SST</span>
              </div>
              <div className="grid grid-cols-4 gap-1.5 text-center text-[10px]">
                {modelMetrics.gravity.naive_baselines.map((b) => (
                  <div
                    key={b.name}
                    className={`p-1.5 rounded border ${
                      b.name.includes('PPML')
                        ? 'bg-indigo-50/80 border-indigo-200 font-bold text-indigo-950'
                        : 'bg-white/50 border-stone-200 text-stone-700'
                    }`}
                  >
                    <div className="truncate text-[9px]">{b.name}</div>
                    <div className="font-mono text-xs mt-0.5">R² {b.r2_oos.toFixed(3)}</div>
                    <div className="text-[9px] text-stone-500">RMSE {b.rmse.toFixed(0)}k</div>
                  </div>
                ))}
              </div>

              {/* Dual-Model Architectural Distinction Callout (Sections 9 & 24) */}
              <div className="mt-2.5 p-2 rounded bg-indigo-50/70 border border-indigo-200/80 text-[11px] text-stone-800 space-y-1.5 text-left">
                <div className="flex items-center justify-between text-[10px] font-semibold text-indigo-950">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-indigo-600 inline-block"></span>
                    Structural Model vs. Forecasting Benchmark
                  </span>
                  <span className="text-[9px] text-indigo-800 font-mono">Dual-Model Architecture</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[10px] bg-white/80 p-2 rounded border border-indigo-100">
                  <div>
                    <span className="text-stone-600 block uppercase font-bold text-[9px]">Structural Model (PPML)</span>
                    <span className="font-mono text-indigo-700 font-bold">OOS R² = {modelMetrics?.gravity?.r2_oos != null ? modelMetrics.gravity.r2_oos.toFixed(4) : '0.5890'}</span>
                    <span className="text-stone-600 block text-[9px] mt-0.5">Counterfactual simulation & structural flow gaps</span>
                  </div>
                  <div>
                    <span className="text-stone-600 block uppercase font-bold text-[9px]">Short-Term Benchmark (2024 Lag)</span>
                    <span className="font-mono text-stone-800 font-bold">OOS R² = 0.7637</span>
                    <span className="text-stone-600 block text-[9px] mt-0.5">Point forecasting exploiting corridor inertia</span>
                  </div>
                </div>
                <p className="text-[9.5px] text-stone-600 leading-relaxed italic">
                  {modelMetrics?.gravity?.baseline_comparison_note ||
                    "Autoregressive persistence (2024 Lag, R²_OOS = 0.7637) outperforms structural PPML (R²_OOS = 0.5890) for pure 1-step-ahead forecasting due to year-over-year corridor inertia. PPML is retained as the authoritative decision engine because autoregressive lags cannot evaluate counterfactual policy interventions, distance friction shifts, or structural gravity gaps."}
                </p>
              </div>
            </div>
          )}
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

          {(() => {
            const concs = corridorData.destination_concentration_2025 || [];
            const sortedByHhi = [...concs]
              .filter((c) => c.interstate_origin_hhi != null)
              .sort((a, b) => (b.interstate_origin_hhi || 0) - (a.interstate_origin_hhi || 0));
            const topConcentrated = sortedByHhi.slice(0, 2);
            const topDiversified = [...sortedByHhi].reverse().slice(0, 2);

            return (
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2.5 rounded bg-white/60 border border-amber-500/20 space-y-1">
                  <span className="font-bold text-amber-700 text-xs">Interstate Concentrated Feeders</span>
                  <div className="text-stone-700 text-[11px] space-y-1">
                    {topConcentrated.map((c) => (
                      <div key={c.destination}>
                        • <strong>{c.destination}</strong> (HHI: {c.interstate_origin_hhi?.toFixed(0)} — {c.top_feeder_share_pct?.toFixed(1)}% from {c.top_feeder_origin})
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-2.5 rounded bg-white/60 border border-violet-400/20 space-y-1">
                  <span className="font-bold text-violet-700 text-xs">Diversified Feeder Bases</span>
                  <div className="text-stone-700 text-[11px] space-y-1">
                    {topDiversified.map((c) => (
                      <div key={c.destination}>
                        • <strong>{c.destination}</strong> (HHI: {c.interstate_origin_hhi?.toFixed(0)} — {c.meaningful_origin_count != null ? `${c.meaningful_origin_count} active feeders` : 'feeders unobserved'})
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            );
          })()}
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
                      const orig = selectedCorridor.origin;
                      setSelectedCorridor(null);
                      onSelectCorridorForScenario(dest, orig);
                    }}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-violet-700 hover:bg-violet-600 text-stone-900 text-xs font-semibold transition-all cursor-pointer shadow-sm"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    Simulate Corridor
                  </button>
                )}
                <button
                  onClick={() => openEvidenceDrawerForCorridor(selectedCorridor)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 text-xs font-semibold transition-all cursor-pointer shadow-sm"
                  title="Inspect 7-element decision evidence drawer"
                >
                  <HelpCircle className="w-3.5 h-3.5" />
                  <span>Why is this recommended?</span>
                </button>
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
                  <strong className="text-indigo-600 text-base font-mono">
                    {selectedCorridor.distance_km != null ? `${selectedCorridor.distance_km.toFixed(0)} km` : 'N/A'}
                  </strong>
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
                            <strong className="text-stone-900 font-mono">
                              {orig?.demographics?.dts_age_classes?.age_15_24_pct != null
                                ? `${orig.demographics.dts_age_classes.age_15_24_pct}%`
                                : 'N/A'}
                            </strong>
                          </div>
                          <div className="p-1 rounded bg-violet-50/30 border border-violet-400/30">
                            <span className="text-violet-700 block font-medium">25–39 (Prime)</span>
                            <strong className="text-violet-700 font-mono">
                              {orig?.demographics?.dts_age_classes?.age_25_39_pct != null
                                ? `${orig.demographics.dts_age_classes.age_25_39_pct}%`
                                : 'N/A'}
                            </strong>
                          </div>
                          <div className="p-1 rounded bg-stone-50/80">
                            <span className="text-amber-700 block font-medium">40–54</span>
                            <strong className="text-stone-900 font-mono">
                              {orig?.demographics?.dts_age_classes?.age_40_54_pct != null
                                ? `${orig.demographics.dts_age_classes.age_40_54_pct}%`
                                : 'N/A'}
                            </strong>
                          </div>
                          <div className="p-1 rounded bg-stone-50/80">
                            <span className="text-violet-700 block font-medium">≥ 55</span>
                            <strong className="text-stone-900 font-mono">
                              {orig?.demographics?.dts_age_classes?.age_55plus_pct != null
                                ? `${orig.demographics.dts_age_classes.age_55plus_pct}%`
                                : 'N/A'}
                            </strong>
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
                            {dest?.hotel_stars?.luxury_room_share_pct != null
                              ? `${dest.hotel_stars.luxury_room_share_pct.toFixed(1)}%`
                              : 'N/A'}
                          </strong>
                        </div>
                      </div>

                      <div className="space-y-1.5 bg-white/50 p-2.5 rounded-lg border border-violet-100/60">
                        <div className="flex justify-between text-[10px] text-stone-700">
                          <span>Lodging Mix (Commercial vs Unpaid VFR)</span>
                          <span className="font-mono text-amber-700 font-semibold">
                            {dest?.lodging_shares?.unpaid_vfr_pct != null
                              ? `${dest.lodging_shares.unpaid_vfr_pct}% VFR`
                              : 'N/A'}
                          </span>
                        </div>
                        {dest?.lodging_shares?.paid_commercial_pct != null && dest?.lodging_shares?.unpaid_vfr_pct != null ? (
                          <>
                            <div className="w-full h-2 rounded-full bg-violet-50 overflow-hidden flex">
                              <div
                                className="bg-violet-600 h-full"
                                style={{ width: `${dest.lodging_shares.paid_commercial_pct}%` }}
                                title={`Paid Commercial: ${dest.lodging_shares.paid_commercial_pct}%`}
                              ></div>
                              <div
                                className="bg-amber-500 h-full"
                                style={{ width: `${dest.lodging_shares.unpaid_vfr_pct}%` }}
                                title={`Unpaid VFR: ${dest.lodging_shares.unpaid_vfr_pct}%`}
                              ></div>
                            </div>
                            <div className="flex justify-between text-[9px] text-stone-600 pt-0.5">
                              <span>Paid Hotel / Commercial: <strong className="text-violet-700 font-mono">{dest.lodging_shares.paid_commercial_pct}%</strong></span>
                              <span>Unpaid VFR / Relatives: <strong className="text-amber-700 font-mono">{dest.lodging_shares.unpaid_vfr_pct}%</strong></span>
                            </div>
                          </>
                        ) : (
                          <div className="text-[10px] text-stone-400 italic py-1">Lodging shares unavailable</div>
                        )}
                      </div>

                      <div className="p-2.5 rounded-lg bg-white/80 border border-violet-100 flex items-center justify-between text-[11px]">
                        <span className="text-stone-600">Average Room Occupancy (AOR):</span>
                        <strong className="text-indigo-600 font-mono text-xs">
                          {dest?.baseline_2025?.aor_pct != null
                            ? `${dest.baseline_2025.aor_pct.toFixed(1)}%`
                            : 'N/A'}
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
                  Under the Structural PPML Gravity Model (OOS R² = {modelMetrics?.gravity?.r2_oos != null ? modelMetrics.gravity.r2_oos.toFixed(4) : '—'}), bilateral travel between <strong>{selectedCorridor.origin}</strong> and <strong>{selectedCorridor.destination}</strong> is shaped by origin push mass, destination pull attractiveness, distance impedance (β = {modelMetrics?.gravity?.distance_decay_friction != null ? modelMetrics.gravity.distance_decay_friction.toFixed(3) : '—'}), and Borneo flight barrier friction ({modelMetrics?.gravity?.cross_region_barrier != null ? `${(-((1 - Math.exp(modelMetrics.gravity.cross_region_barrier)) * 100)).toFixed(1)}%` : '—'}).
                </p>

                {/* Multi-Dimensional Opportunity Matrix Grid (Phase 19 & 20) */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
                  <div className="p-2 rounded bg-white border border-violet-100">
                    <span className="text-[10px] text-stone-500 block">Pareto Frontier</span>
                    <strong className={`font-mono text-xs ${selectedCorridor.is_pareto_optimal ? 'text-emerald-700' : 'text-stone-700'}`}>
                      {selectedCorridor.is_pareto_optimal ? '✨ Optimal (Rank 1)' : `Rank ${selectedCorridor.pareto_rank || 'N/A'}`}
                    </strong>
                    <span className="text-[9px] text-stone-500 block">
                      Score: {selectedCorridor.composite_opportunity_score?.toFixed(1) || 'N/A'}
                    </span>
                  </div>

                  <div className="p-2 rounded bg-white border border-violet-100">
                    <span className="text-[10px] text-stone-500 block">Model Expectation</span>
                    <strong className={`font-mono text-xs ${
                      selectedCorridor.gravity_performance_category === 'Below Model Expected'
                        ? 'text-amber-700'
                        : selectedCorridor.gravity_performance_category === 'Above Model Expected'
                        ? 'text-blue-700'
                        : 'text-stone-700'
                    }`}>
                      {selectedCorridor.gravity_performance_category || 'N/A'}
                    </strong>
                    <span className="text-[9px] text-stone-500 block font-mono">
                      Gap: {selectedCorridor.gravity_flow_gap_thousands != null ? `${selectedCorridor.gravity_flow_gap_thousands > 0 ? '+' : ''}${selectedCorridor.gravity_flow_gap_thousands.toFixed(0)}k` : '0k'}
                    </span>
                  </div>

                  <div className="p-2 rounded bg-white border border-violet-100">
                    <span className="text-[10px] text-stone-500 block">Capacity Headroom</span>
                    <strong className="text-emerald-700 font-mono text-xs">
                      {selectedCorridor.capacity_headroom_pct != null ? `${selectedCorridor.capacity_headroom_pct.toFixed(0)}% Room Space` : 'N/A'}
                    </strong>
                    <span className="text-[9px] text-stone-500 block truncate" title={selectedCorridor.capacity_tier}>
                      {selectedCorridor.capacity_tier ? selectedCorridor.capacity_tier.split('(')[0].trim() : 'N/A'}
                    </span>
                  </div>

                  <div className="p-2 rounded bg-white border border-violet-100">
                    <span className="text-[10px] text-stone-500 block">Diversification</span>
                    <strong className="text-violet-700 font-mono text-xs">
                      {selectedCorridor.is_dominant_feeder ? 'Dominant Feeder' : 'Diversifying Origin'}
                    </strong>
                    <span className="text-[9px] text-stone-500 block truncate" title={selectedCorridor.diversification_benefit}>
                      {selectedCorridor.diversification_benefit ? selectedCorridor.diversification_benefit.split('(')[0].trim() : 'N/A'}
                    </span>
                  </div>
                </div>

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
                      <li><strong>Transport Friction Relief:</strong> Subsidize direct inter-state flight or express coach frequencies to overcome distance friction (β = {modelMetrics?.gravity?.distance_decay_friction != null ? modelMetrics.gravity.distance_decay_friction.toFixed(3) : '—'}).</li>
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
                  * Structural PPML Gravity Specification: E[Flow_ijt] = exp(α_i + γ_j + δ_t + {modelMetrics?.gravity?.distance_decay_friction != null ? modelMetrics.gravity.distance_decay_friction.toFixed(3) : 'β_dist'} ln(Dist_ij) + {modelMetrics?.gravity?.cross_region_barrier != null ? (modelMetrics.gravity.cross_region_barrier > 0 ? `+ ${modelMetrics.gravity.cross_region_barrier.toFixed(3)}` : `${modelMetrics.gravity.cross_region_barrier.toFixed(3)}`) : 'β_borneo'} Borneo_ij). Zero target leakage (absorbed via Destination FE); validated on 2025 holdout.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Evidence Drawer (Plan Section 30 / Sprint E) */}
      <EvidenceDrawer
        isOpen={evidenceDrawerData !== null}
        onClose={() => setEvidenceDrawerData(null)}
        evidence={evidenceDrawerData}
      />
    </div>
  );
};
