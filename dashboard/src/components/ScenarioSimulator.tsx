import React, { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';
import type { ScenarioEngineConfig, StateProfile } from '../types';
import { 
  Sliders, 
  Sparkles, 
  Hotel, 
  ShieldAlert, 
  RotateCcw,
  Home,
  Shield,
  Zap,
  Rocket,
  ArrowUpRight,
  Info,
  ChevronDown,
  ChevronUp,
  SlidersHorizontal,
  Route,
  BarChart3
} from 'lucide-react';

// Custom smooth interpolation hook using requestAnimationFrame & cubic ease-out (~400ms)
function useAnimatedCounter(targetValue: number, duration: number = 400, decimals: number = 1): string {
  const [displayValue, setDisplayValue] = useState<number>(targetValue);
  const startValueRef = useRef<number>(targetValue);
  const startTimeRef = useRef<number | null>(null);
  const targetRef = useRef<number>(targetValue);

  useEffect(() => {
    startValueRef.current = displayValue;
    targetRef.current = targetValue;
    startTimeRef.current = null;

    let animFrameId: number;

    const step = (timestamp: number) => {
      if (!startTimeRef.current) startTimeRef.current = timestamp;
      const elapsed = timestamp - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out cubic: 1 - (1 - t)^3
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const current = startValueRef.current + (targetRef.current - startValueRef.current) * easeOut;

      setDisplayValue(current);

      if (progress < 1) {
        animFrameId = requestAnimationFrame(step);
      } else {
        setDisplayValue(targetRef.current);
      }
    };

    animFrameId = requestAnimationFrame(step);
    return () => cancelAnimationFrame(animFrameId);
  }, [targetValue, duration]);

  return displayValue.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

const AnimatedCounter: React.FC<{
  value: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  className?: string;
}> = ({ value, decimals = 1, prefix = '', suffix = '', className = '' }) => {
  const formatted = useAnimatedCounter(value, 400, decimals);
  return (
    <span className={`tabular-nums transition-colors duration-150 ${className}`}>
      {prefix}{formatted}{suffix}
    </span>
  );
};

type PresetKey = 'conservative' | 'moderate' | 'ambitious' | 'custom';

interface PolicyPreset {
  key: PresetKey;
  label: string;
  sublabel: string;
  badge: string;
  deltaAlos: number;
  affectedShare: number;
  conversionRate: number;
  yieldUplift: number;
  vfrConversionRate: number;
  icon: React.ComponentType<{ className?: string }>;
}

const PRESETS: PolicyPreset[] = [
  {
    key: 'conservative',
    label: 'Conservative',
    sublabel: '+0.2d / 10% reach / 5% conv',
    badge: 'Baseline',
    deltaAlos: 0.2,
    affectedShare: 10,
    conversionRate: 5,
    yieldUplift: 5,
    vfrConversionRate: 3,
    icon: Shield,
  },
  {
    key: 'moderate',
    label: 'Moderate',
    sublabel: '+0.4d / 15% reach / 10% conv',
    badge: 'Targeted',
    deltaAlos: 0.4,
    affectedShare: 15,
    conversionRate: 10,
    yieldUplift: 10,
    vfrConversionRate: 5,
    icon: Zap,
  },
  {
    key: 'ambitious',
    label: 'Ambitious',
    sublabel: '+0.6d / 25% reach / 20% conv',
    badge: 'Transform',
    deltaAlos: 0.6,
    affectedShare: 25,
    conversionRate: 20,
    yieldUplift: 15,
    vfrConversionRate: 10,
    icon: Rocket,
  },
];

interface ScenarioSimulatorProps {
  scenarioConfig: ScenarioEngineConfig;
  stateProfiles: Record<string, StateProfile>;
  initialDestination?: string;
  initialOrigin?: string;
}

export const ScenarioSimulator: React.FC<ScenarioSimulatorProps> = ({ 
  scenarioConfig, 
  stateProfiles,
  initialDestination,
  initialOrigin
}) => {
  const [selectedState, setSelectedState] = useState<string>(
    initialDestination && stateProfiles[initialDestination] ? initialDestination : 'Melaka'
  );
  const [activeCorridorOrigin, setActiveCorridorOrigin] = useState<string | null>(initialOrigin || null);
  const [activePreset, setActivePreset] = useState<PresetKey>('moderate');
  const [deltaAlos, setDeltaAlos] = useState<number>(0.4); // Moderate default
  const [affectedShare, setAffectedShare] = useState<number>(15); // 15% campaign reach default (Phase 22)
  const [conversionRate, setConversionRate] = useState<number>(10); // 10% day-trippers converted
  const [yieldUplift, setYieldUplift] = useState<number>(10); // +10% spend/night uplift
  const [vfrConversionRate, setVfrConversionRate] = useState<number>(5); // 5% VFR to paid lodging
  const [planningThreshold, setPlanningThreshold] = useState<number>(80); // 80% planning ceiling (Phase 27)
  const [showProvenanceDrawer, setShowProvenanceDrawer] = useState<boolean>(false); // Phase 25
  const [simulationMode, setSimulationMode] = useState<'policy' | 'monte_carlo' | 'portfolio'>('policy'); // Sprint 8
  const [selectedBudget, setSelectedBudget] = useState<number>(5.0);
  const [selectedOptimizerThreshold, setSelectedOptimizerThreshold] = useState<number>(80);

  useEffect(() => {
    if (initialDestination && stateProfiles[initialDestination]) {
      setSelectedState(initialDestination);
    }
    if (initialOrigin) {
      setActiveCorridorOrigin(initialOrigin);
    }
  }, [initialDestination, initialOrigin, stateProfiles]);

  const handleSelectPreset = (preset: PolicyPreset) => {
    setActivePreset(preset.key);
    setDeltaAlos(preset.deltaAlos);
    setAffectedShare(preset.affectedShare);
    setConversionRate(preset.conversionRate);
    setYieldUplift(preset.yieldUplift);
    setVfrConversionRate(preset.vfrConversionRate);
  };

  const handleReset = () => {
    handleSelectPreset(PRESETS[1]); // Reset to moderate preset
    setPlanningThreshold(80);
  };

  const stateList = Object.values(stateProfiles);
  const activeProfile = stateProfiles[selectedState] || stateList[0];
  const b = activeProfile.baseline_2025;

  const baselineTouristsK = b.tourists_thousands;
  const baselineExcursionistsK = activeProfile.baseline_2025.visitors_thousands - b.tourists_thousands;
  const baselineAlos = b.alos_days;
  const baselineSpendPerNight = b.spend_per_night_rm;
  const accomVAI = scenarioConfig.constants?.accommodation_vai || 0.8579;
  const guestsPerRoom = scenarioConfig.constants?.average_guests_per_room || 1.8;
  const seasonalCaveat = scenarioConfig.constants?.seasonal_caveat || "Annual occupancy may hide seasonal/weekend capacity pressure.";
  const residentHouseholds = activeProfile.demographics?.households_thousands || null;
  const hasCapacityData = b.hotel_rooms != null && b.aor_pct != null;
  const totalRooms = b.hotel_rooms;
  const baselineAor = b.aor_pct;

  // Real-Time Scenario Calculations (AGENTS.md Stage F & Sprint 6 Formulas)
  // 1. Stay extension with campaign affected share (Phase 22)
  const addNightsFromAlosK = baselineTouristsK * (affectedShare / 100.0) * deltaAlos;

  // 2. Converted excursionists into overnight tourists
  const convertedTouristsK = baselineExcursionistsK * (conversionRate / 100.0);
  const addNightsFromConvertedK = convertedTouristsK * (baselineAlos + deltaAlos);

  // 3. Converted unpaid VFR stays into commercial/registered paid lodging (Phase 24)
  const hasVfrData = activeProfile.lodging_shares?.unpaid_vfr_pct != null;
  const unpaidVfrPct = hasVfrData ? activeProfile.lodging_shares!.unpaid_vfr_pct : 0.0;
  const vfrTouristsK = baselineTouristsK * (unpaidVfrPct / 100.0);
  const convertedVfrTouristsK = vfrTouristsK * (vfrConversionRate / 100.0);
  const vfrNightsK = convertedVfrTouristsK * (baselineAlos + deltaAlos);
  const homestayNightlyRate = Math.max(75, baselineSpendPerNight * 0.85);
  const vfrAccomSpendRM = hasVfrData ? (vfrNightsK * 1e3 * homestayNightlyRate) / 1e6 : 0.0;

  // Total additional guest nights (thousands) — Phase 24 includes VFR nights
  const totalAdditionalGuestNightsK = addNightsFromAlosK + addNightsFromConvertedK + vfrNightsK;

  // New spend per night (RM)
  const newSpendPerNight = baselineSpendPerNight * (1 + yieldUplift / 100.0);

  // Additional accommodation expenditure (RM Million)
  const existingNightsK = baselineTouristsK * baselineAlos;
  const newNightsSpendRM = ((addNightsFromAlosK + addNightsFromConvertedK) * 1e3 * newSpendPerNight) / 1e6;
  const existingNightsUpliftRM = (existingNightsK * 1e3 * (newSpendPerNight - baselineSpendPerNight)) / 1e6;
  const totalAdditionalAccomSpendMil = newNightsSpendRM + existingNightsUpliftRM + vfrAccomSpendRM;

  // Potential Additional Tourism Value Added Proxy (RM Million at official VAI)
  const potentialAdditionalTdgvaMil = totalAdditionalAccomSpendMil * accomVAI;

  // Incremental Yield per Resident Household (RM / Household)
  const yieldPerHouseholdRM = (residentHouseholds && residentHouseholds > 0)
    ? (totalAdditionalAccomSpendMil * 1e6) / (residentHouseholds * 1e3)
    : 0;

  // Capacity Feasibility: Convert Guest Nights to Room Nights (Phase 23 & 24)
  const availableRoomNightsYearK = (hasCapacityData && totalRooms && totalRooms > 0) ? (totalRooms * 365) / 1e3 : null;
  const additionalRoomNightsYearK = totalAdditionalGuestNightsK / guestsPerRoom;
  const additionalAorPct = (hasCapacityData && availableRoomNightsYearK && availableRoomNightsYearK > 0)
    ? (additionalRoomNightsYearK / availableRoomNightsYearK) * 100
    : null;
  const simulatedAor = (hasCapacityData && baselineAor != null && additionalAorPct != null)
    ? baselineAor + additionalAorPct
    : null;

  // Saturation Tier based on Configurable Planning Threshold (Phase 27)
  const getCapacityStatus = (aor: number | null) => {
    if (aor == null) return { tier: 'Unknown', color: 'text-stone-500', bg: 'bg-stone-500', isConstrained: false, msg: 'Capacity Unobserved' };
    if (aor > 100.0) {
      return {
        tier: 'Physical Breach',
        color: 'text-rose-700',
        bg: 'bg-rose-600',
        isConstrained: true,
        msg: `Physical Capacity Breach (${aor.toFixed(1)}% AOR > 100% Ceiling) — Exceeds total available hotel room inventory`,
      };
    }
    if (aor > planningThreshold) {
      return {
        tier: 'Severe Saturation',
        color: 'text-amber-700',
        bg: 'bg-amber-500',
        isConstrained: true,
        msg: `Severe Capacity Saturation (${aor.toFixed(1)}% AOR > ${planningThreshold}% Threshold) — Requires room supply expansion or off-peak redistribution`,
      };
    }
    if (aor >= (planningThreshold - 10)) {
      return {
        tier: 'Planning Watch',
        color: 'text-indigo-600',
        bg: 'bg-indigo-500',
        isConstrained: false,
        msg: `Planning Watch (${aor.toFixed(1)}% AOR in ${planningThreshold - 10}-${planningThreshold}% range) — Tightening headroom during peak periods`,
      };
    }
    return {
      tier: 'Normal',
      color: 'text-violet-700',
      bg: 'bg-violet-600',
      isConstrained: false,
      msg: `Feasible (${aor.toFixed(1)}% AOR within sustainable hotel capacity)`,
    };
  };

  const capacityStatus = getCapacityStatus(simulatedAor);

  // ECharts Comparison Waterfall / Bar
  const impactChartOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#ffffff',
      borderColor: 'rgba(70, 50, 100, 0.16)',
      textStyle: { color: '#241d32', fontSize: 12 },
    },
    grid: { left: '3%', right: '4%', bottom: '8%', top: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      data: ['Accom Revenue (Baseline)', 'Simulated Accom Revenue', 'Baseline TDGVA Proxy', 'Simulated TDGVA Proxy'],
      axisLine: { lineStyle: { color: '#d6d0df' } },
      axisLabel: { color: '#746d80', fontSize: 10, interval: 0 },
    },
    yAxis: {
      type: 'value',
      name: 'RM Million',
      axisLabel: { color: '#746d80' },
      splitLine: { lineStyle: { color: 'rgba(70, 50, 100, 0.09)' } },
    },
    series: [
      {
        name: 'Economic Value',
        type: 'bar',
        barWidth: '40%',
        data: [
          { value: b.accommodation_expenditure_rm_million, itemStyle: { color: '#d6d0df' } },
          { value: b.accommodation_expenditure_rm_million + totalAdditionalAccomSpendMil, itemStyle: { color: '#6d4bc1' } },
          { value: b.accommodation_expenditure_rm_million * accomVAI, itemStyle: { color: '#e3deea' } },
          { value: (b.accommodation_expenditure_rm_million + totalAdditionalAccomSpendMil) * accomVAI, itemStyle: { color: '#6d4bc1' } },
        ],
        label: {
          show: true,
          position: 'top',
          color: '#241d32',
          formatter: (p: any) => `RM ${p.value.toFixed(0)}M`,
          fontWeight: 'bold',
          fontSize: 11,
        },
      },
    ],
  };

  return (
    <div className="space-y-6">
      {/* Top Header Banner & Mandatory Disclaimer */}
      <div className="glass-panel p-6 border-l-4 border-l-violet-500">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-violet-600/20 text-violet-700">
                Transparent What-If Policy Lab
              </span>
              <span className="text-xs text-stone-600">Research Question 7 & Policy Simulator</span>
            </div>
            <h2 className="text-2xl font-bold text-stone-900 tracking-tight">
              Tourism Economic Value Scenario Simulator
            </h2>
            <p className="text-sm text-stone-700 mt-1 max-w-3xl">
              Simulate the macroeconomic impact of targeted interventions: extending length of stay, converting excursionist day-trippers into overnight guests, and optimizing accommodation yield per night under room capacity constraints.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowProvenanceDrawer(!showProvenanceDrawer)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-violet-50 border border-violet-200 text-violet-800 hover:bg-violet-100 text-xs font-semibold transition-all"
            >
              <Info className="w-3.5 h-3.5" />
              <span>Audit Provenance</span>
              {showProvenanceDrawer ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-violet-200 text-stone-700 hover:text-stone-900 text-xs font-semibold transition-all"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Reset
            </button>
          </div>
        </div>

        {/* Mandatory Causal Disclaimer Badge (AGENTS.md Section 7 & 9) */}
        <div className="mt-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center gap-2.5 text-xs text-amber-800">
          <ShieldAlert className="w-4 h-4 text-amber-700 shrink-0" />
          <span>
            <strong>Mandatory Methodological Guardrail:</strong> <em>"Scenario estimate, not a causal forecast."</em> Calculations rely on official TSA 2015–2025 accommodation value-added intensity ({((accomVAI * 100)).toFixed(1)}%) and Domestic Tourism Survey parameters under transparent proportional assumptions.
          </span>
        </div>

        {/* Collapsible Assumption & Provenance Drawer (Phase 25) */}
        {showProvenanceDrawer && (
          <div className="mt-4 p-4 rounded-xl bg-violet-50/50 border border-violet-200 text-xs space-y-3 animate-in fade-in duration-200">
            <div className="flex items-center justify-between border-b border-violet-200/60 pb-2">
              <span className="font-bold text-stone-900 flex items-center gap-1.5">
                <SlidersHorizontal className="w-3.5 h-3.5 text-violet-700" />
                Scenario Parameter Provenance & Status Classification
              </span>
              <div className="flex items-center gap-2 text-[10px]">
                <span className="px-1.5 py-0.5 rounded bg-blue-100 text-blue-800 font-semibold">[Official]</span>
                <span className="px-1.5 py-0.5 rounded bg-purple-100 text-purple-800 font-semibold">[Derived]</span>
                <span className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 font-semibold">[Scenario Assumption]</span>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5 text-[11px]">
              <div className="p-2 rounded bg-white border border-violet-100 space-y-0.5">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-stone-800">Baseline Tourists</span>
                  <span className="px-1.5 py-0.2 rounded bg-blue-100 text-blue-800 text-[9px] font-bold">Official</span>
                </div>
                <p className="text-stone-500 text-[10px]">DTS 2025 table of overnight tourist volume</p>
              </div>
              <div className="p-2 rounded bg-white border border-violet-100 space-y-0.5">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-stone-800">Baseline ALOS</span>
                  <span className="px-1.5 py-0.2 rounded bg-blue-100 text-blue-800 text-[9px] font-bold">Official</span>
                </div>
                <p className="text-stone-500 text-[10px]">DTS 2025 Average Length of Stay by destination</p>
              </div>
              <div className="p-2 rounded bg-white border border-violet-100 space-y-0.5">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-stone-800">Spend per Night</span>
                  <span className="px-1.5 py-0.2 rounded bg-purple-100 text-purple-800 text-[9px] font-bold">Derived</span>
                </div>
                <p className="text-stone-500 text-[10px]">Accommodation spend / (Tourists × ALOS)</p>
              </div>
              <div className="p-2 rounded bg-white border border-violet-100 space-y-0.5">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-stone-800">Campaign Affected Share</span>
                  <span className="px-1.5 py-0.2 rounded bg-amber-100 text-amber-800 text-[9px] font-bold">Scenario Assumption</span>
                </div>
                <p className="text-stone-500 text-[10px]">Target reach of promotion campaign (default 15%)</p>
              </div>
              <div className="p-2 rounded bg-white border border-violet-100 space-y-0.5">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-stone-800">Guests per Occupied Room</span>
                  <span className="px-1.5 py-0.2 rounded bg-amber-100 text-amber-800 text-[9px] font-bold">Scenario Assumption</span>
                </div>
                <p className="text-stone-500 text-[10px]">Standard domestic tourist density (1.8 guests/room)</p>
              </div>
              <div className="p-2 rounded bg-white border border-violet-100 space-y-0.5">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-stone-800">Planning Threshold</span>
                  <span className="px-1.5 py-0.2 rounded bg-amber-100 text-amber-800 text-[9px] font-bold">Scenario Assumption</span>
                </div>
                <p className="text-stone-500 text-[10px]">Sustainable annual AOR ceiling ({planningThreshold}%)</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Sprint 8 Mode Selector: Deterministic Policy | Monte Carlo Uncertainty | Portfolio Optimizer */}
      <div className="flex flex-wrap items-center gap-2 p-1.5 bg-violet-100/60 rounded-xl border border-violet-200/80 w-fit">
        <button
          onClick={() => setSimulationMode('policy')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            simulationMode === 'policy'
              ? 'bg-white text-violet-950 shadow-sm'
              : 'text-stone-600 hover:text-stone-900'
          }`}
        >
          Deterministic Policy Levers
        </button>
        <button
          onClick={() => setSimulationMode('monte_carlo')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
            simulationMode === 'monte_carlo'
              ? 'bg-white text-violet-950 shadow-sm'
              : 'text-stone-600 hover:text-stone-900'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5 text-amber-500" />
          <span>Monte Carlo Uncertainty (Phase 26)</span>
        </button>
        <button
          onClick={() => setSimulationMode('portfolio')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
            simulationMode === 'portfolio'
              ? 'bg-white text-violet-950 shadow-sm'
              : 'text-stone-600 hover:text-stone-900'
          }`}
        >
          <SlidersHorizontal className="w-3.5 h-3.5 text-indigo-600" />
          <span>Portfolio Optimizer (Phase 36)</span>
        </button>
      </div>

      {/* MODE 1: Deterministic Policy Levers */}
      {simulationMode === 'policy' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Policy Lever Controls (5 cols) */}
        <div className="glass-panel p-5 lg:col-span-5 space-y-5">
          <div className="flex items-center justify-between border-b border-violet-100/60 pb-3">
            <h3 className="text-base font-bold text-stone-900 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-violet-700" />
              Policy Levers & Target Selection
            </h3>
            <span className="text-xs text-stone-600">Simulate by Destination</span>
          </div>

          {/* One-Click Strategic Policy Presets */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="block text-xs text-stone-600 uppercase font-bold tracking-wider">
                One-Click Policy Presets
              </label>
              <span className="text-[11px] font-semibold text-violet-700 capitalize">
                {activePreset === 'custom' ? 'Custom Tuning' : `${activePreset} Plan`}
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {PRESETS.map((p) => {
                const Icon = p.icon;
                const isActive = activePreset === p.key;
                return (
                  <button
                    key={p.key}
                    type="button"
                    onClick={() => handleSelectPreset(p)}
                    className={`p-2.5 rounded-xl text-left border transition-all flex flex-col justify-between gap-1.5 ${
                      isActive
                        ? 'bg-violet-600 text-white border-violet-600 shadow-sm shadow-violet-500/20'
                        : 'bg-white hover:bg-violet-50/60 border-violet-200/80 text-stone-800'
                    }`}
                  >
                    <div className="flex items-center justify-between w-full">
                      <span className={`p-1 rounded-md ${isActive ? 'bg-white/20 text-white' : 'bg-violet-100 text-violet-700'}`}>
                        <Icon className="w-3.5 h-3.5" />
                      </span>
                      <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${
                        isActive ? 'bg-white/25 text-white' : 'bg-stone-100 text-stone-600'
                      }`}>
                        {p.badge}
                      </span>
                    </div>
                    <div>
                      <div className="font-bold text-xs leading-tight">{p.label}</div>
                      <div className={`text-[10px] leading-tight mt-0.5 ${isActive ? 'text-violet-100' : 'text-stone-500'}`}>
                        {p.sublabel}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Active Corridor Focus Banner (Phase 28) */}
          {activeCorridorOrigin && (
            <div className="p-3 bg-violet-600/10 border border-violet-400/40 rounded-xl flex items-center justify-between gap-3 animate-fadeIn">
              <div className="flex items-center gap-2">
                <Route className="w-4 h-4 text-violet-700 shrink-0" />
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-violet-600/20 text-violet-700">
                      Active Corridor Focus
                    </span>
                    <span className="text-xs font-mono font-bold text-stone-900">
                      {activeCorridorOrigin} ➔ {selectedState}
                    </span>
                  </div>
                  <p className="text-[11px] text-stone-600 mt-0.5">
                    Pre-populated from OD Value Network. Simulating stay extension and accommodation capture for arrivals into {selectedState}.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setActiveCorridorOrigin(null)}
                className="text-[11px] text-stone-600 hover:text-stone-900 px-2 py-1 rounded bg-white border border-violet-100 transition-all cursor-pointer whitespace-nowrap"
              >
                Clear
              </button>
            </div>
          )}

          {/* Destination Selector */}
          <div>
            <label className="block text-xs text-stone-600 uppercase font-semibold mb-1.5">
              Target Destination State
            </label>
            <select
              value={selectedState}
              onChange={(e) => setSelectedState(e.target.value)}
              className="w-full bg-white border border-violet-200 text-stone-900 rounded-lg p-2.5 text-sm font-semibold focus:outline-none focus:border-violet-400"
            >
              {stateList.map((s) => (
                <option key={s.state} value={s.state}>
                  {s.state} ({s.archetype_name})
                </option>
              ))}
            </select>
          </div>

          {/* Baseline Summary Card for Target State */}
          <div className="p-3 rounded-lg bg-white/60 border border-violet-100 text-xs space-y-1">
            <div className="flex justify-between text-stone-600">
              <span>Overnight Tourists:</span>
              <strong className="text-stone-900 font-mono">{b.tourists_thousands.toFixed(0)}k</strong>
            </div>
            <div className="flex justify-between text-stone-600">
              <span>Excursionists (Day-Trips):</span>
              <strong className="text-amber-700 font-mono">{baselineExcursionistsK.toFixed(0)}k</strong>
            </div>
            <div className="flex justify-between text-stone-600">
              <span>Baseline ALOS:</span>
              <strong className="text-indigo-600 font-mono">{baselineAlos.toFixed(2)} days</strong>
            </div>
            <div className="flex justify-between text-stone-600">
              <span>Baseline Spend / Night:</span>
              <strong className="text-violet-700 font-mono">RM {baselineSpendPerNight.toFixed(1)}</strong>
            </div>
          </div>

          {/* Slider 1: Length of Stay (+Delta ALOS) */}
          <div className="space-y-2 pt-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-stone-800">
                1. Length-of-Stay Expansion (+ΔALOS)
              </span>
              <span className="font-mono font-bold text-violet-700 text-sm">
                +{deltaAlos.toFixed(1)} days (→ {(baselineAlos + deltaAlos).toFixed(2)}d)
              </span>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.5"
              step="0.1"
              value={deltaAlos}
              onChange={(e) => {
                setDeltaAlos(parseFloat(e.target.value));
                setActivePreset('custom');
              }}
            />
            <span className="text-[10px] text-stone-600 block">
              Policy lever: Sunset cultural programming, weekend retreat packages, multi-day attraction passes.
            </span>
          </div>

          {/* Slider 2: Campaign Affected Share (%) — Phase 22 */}
          <div className="space-y-2 pt-2 border-t border-violet-100/60">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-stone-800 flex items-center gap-1.5">
                <span className="px-1.5 py-0.2 rounded bg-amber-100 text-amber-800 text-[9px] font-bold">Assumption</span>
                2. Campaign Affected Share (% of tourists)
              </span>
              <span className="font-mono font-bold text-violet-700 text-sm">
                {affectedShare}% (→ +{addNightsFromAlosK.toFixed(0)}k nights)
              </span>
            </div>
            <input
              type="range"
              min="5"
              max="100"
              step="5"
              value={affectedShare}
              onChange={(e) => {
                setAffectedShare(parseInt(e.target.value));
                setActivePreset('custom');
              }}
            />
            <div className="flex justify-between text-[9px] text-stone-500">
              <span>5% (Niche pilot)</span>
              <span>15% (Targeted campaign)</span>
              <span>50% (Broad initiative)</span>
              <span>100% (Unconstrained)</span>
            </div>
          </div>

          {/* Slider 3: Excursionist Conversion (%) */}
          <div className="space-y-2 pt-2 border-t border-violet-100/60">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-stone-800">
                3. Excursionist Day-Trip Conversion
              </span>
              <span className="font-mono font-bold text-indigo-600 text-sm">
                {conversionRate}% (→ +{convertedTouristsK.toFixed(0)}k tourists)
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="25"
              step="1"
              value={conversionRate}
              onChange={(e) => {
                setConversionRate(parseInt(e.target.value));
                setActivePreset('custom');
              }}
            />
            <span className="text-[10px] text-stone-600 block">
              Policy lever: Evening night markets, weekend hotel discounts for day-trippers from neighboring states.
            </span>
          </div>

          {/* Slider 4: Spend-per-Night Yield Uplift (%) */}
          <div className="space-y-2 pt-2 border-t border-violet-100/60">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-stone-800">
                4. Nightly Spend Yield Optimization
              </span>
              <span className="font-mono font-bold text-amber-700 text-sm">
                +{yieldUplift}% (→ RM {newSpendPerNight.toFixed(0)}/night)
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="30"
              step="5"
              value={yieldUplift}
              onChange={(e) => {
                setYieldUplift(parseInt(e.target.value));
                setActivePreset('custom');
              }}
            />
            <span className="text-[10px] text-stone-600 block">
              Policy lever: Hotel quality upgrades, premium boutique packages, eco-tourism experiential add-ons.
            </span>
          </div>

          {/* Slider 5: VFR Unpaid to Paid Homestay / Commercial Lodging Conversion (Phase 24) */}
          <div className="space-y-2 pt-2 border-t border-violet-100/60">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-stone-800 flex items-center gap-1.5">
                <Home className="w-3.5 h-3.5 text-violet-700" />
                5. VFR to Paid Lodging / Homestay Conversion
              </span>
              <span className="font-mono font-bold text-violet-700 text-sm">
                {vfrConversionRate}% (→ +{convertedVfrTouristsK.toFixed(0)}k stays)
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="20"
              step="1"
              value={vfrConversionRate}
              onChange={(e) => {
                setVfrConversionRate(parseInt(e.target.value));
                setActivePreset('custom');
              }}
            />
            <div className="flex items-center justify-between text-[10px] text-stone-600">
              <span>Unpaid VFR Base: <strong className="text-stone-700 font-mono">{hasVfrData ? `${unpaidVfrPct.toFixed(1)}%` : 'N/A'}</strong> {hasVfrData ? `(${vfrTouristsK.toFixed(0)}k tourists)` : ''}</span>
              <span>Rate: <strong className="text-violet-800 font-mono">RM {homestayNightlyRate.toFixed(0)}/night</strong></span>
            </div>
            {!hasVfrData && (
              <span className="text-[10px] text-amber-700 block bg-amber-50 border border-amber-200/60 p-1.5 rounded">
                Note: DTS lodging share data unavailable for {selectedState}. VFR conversion impact set to 0 to prevent synthetic imputation.
              </span>
            )}
            <span className="text-[10px] text-violet-800/90 block bg-violet-50/30 border border-violet-200/20 p-1.5 rounded">
              UN SDG 8.9 Policy lever: Transition visiting-friends-and-relatives (VFR) into licensed village Kampungstay, certified community homestays, and boutique heritage inns.
            </span>
          </div>

          {/* Capacity Planning Sensitivity Selector (Phase 27) */}
          <div className="space-y-2 pt-2 border-t border-violet-100/60">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-stone-800 flex items-center gap-1.5">
                <Hotel className="w-3.5 h-3.5 text-amber-700" />
                Capacity Planning Ceiling Threshold
              </span>
              <span className="font-mono font-bold text-violet-800 text-sm">
                {planningThreshold}% AOR
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {[75, 80, 85].map((thresh) => (
                <button
                  key={thresh}
                  type="button"
                  onClick={() => setPlanningThreshold(thresh)}
                  className={`py-1.5 px-2 rounded-lg text-xs font-semibold border transition-all ${
                    planningThreshold === thresh
                      ? 'bg-violet-600 text-white border-violet-600'
                      : 'bg-white text-stone-700 border-violet-200 hover:bg-violet-50'
                  }`}
                >
                  {thresh}% {thresh === 75 ? '(Strict)' : thresh === 80 ? '(Standard)' : '(Peak Pressure)'}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Real-Time Impact Dashboard (7 cols) */}
        <div className="glass-panel p-5 lg:col-span-7 flex flex-col justify-between space-y-4">
          <div className="flex items-center justify-between border-b border-violet-100/60 pb-3">
            <div>
              <h3 className="text-base font-bold text-stone-900 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-violet-700" />
                Simulated Economic Outcomes ({selectedState})
              </h3>
              <p className="text-xs text-stone-600">Projected incremental domestic economic capture under {planningThreshold}% capacity ceiling</p>
            </div>
            <span className="text-xs px-2.5 py-0.5 rounded bg-violet-600/20 text-violet-700 font-mono">
              VAI = {((accomVAI * 100)).toFixed(1)}%
            </span>
          </div>

          {/* Key Impact Outcome Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {/* Additional Tourist Nights */}
            <div className="metric-card p-3 border-l-2 border-l-violet-400">
              <span className="metric-label">Extra Guest Nights</span>
              <div className="metric-value text-stone-900 text-xl">
                +<AnimatedCounter value={totalAdditionalGuestNightsK / 1e3} decimals={2} />M
              </div>
              <div className="mt-1 flex flex-col gap-0.5">
                <span className="text-[10px] text-violet-700 font-medium">
                  +<AnimatedCounter value={totalAdditionalGuestNightsK} decimals={0} />k nights
                </span>
                <div className="inline-flex items-center gap-0.5 text-[10px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded-full border border-emerald-200/60 w-fit">
                  <ArrowUpRight className="w-3 h-3" />
                  <span>+<AnimatedCounter value={totalAdditionalGuestNightsK} decimals={0} />k</span>
                </div>
              </div>
            </div>

            {/* Additional Accommodation Revenue */}
            <div className="metric-card p-3 border-l-2 border-l-violet-400">
              <span className="metric-label">Accom Spend</span>
              <div className="metric-value text-indigo-600 text-xl">
                +RM <AnimatedCounter value={totalAdditionalAccomSpendMil} decimals={1} />M
              </div>
              <div className="mt-1 flex flex-col gap-0.5">
                <span className="text-[10px] text-indigo-600 font-medium">
                  +<AnimatedCounter value={(totalAdditionalAccomSpendMil / Math.max(1, b.accommodation_expenditure_rm_million)) * 100} decimals={1} />% uplift
                </span>
                <div className="inline-flex items-center gap-0.5 text-[10px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded-full border border-emerald-200/60 w-fit">
                  <ArrowUpRight className="w-3 h-3" />
                  <span>+RM <AnimatedCounter value={totalAdditionalAccomSpendMil} decimals={1} />M</span>
                </div>
              </div>
            </div>

            {/* Potential TDGVA Added */}
            <div className="metric-card p-3 border-l-2 border-l-violet-500">
              <span className="metric-label">Potential GVA</span>
              <div className="metric-value text-violet-700 text-xl">
                +RM <AnimatedCounter value={potentialAdditionalTdgvaMil} decimals={1} />M
              </div>
              <div className="mt-1 flex flex-col gap-0.5">
                <span className="text-[10px] text-violet-700 font-medium">
                  {((accomVAI * 100)).toFixed(1)}% retained value
                </span>
                <div className="inline-flex items-center gap-0.5 text-[10px] font-bold text-violet-700 bg-violet-50 px-1.5 py-0.5 rounded-full border border-violet-200/60 w-fit">
                  <ArrowUpRight className="w-3 h-3" />
                  <span>+RM <AnimatedCounter value={potentialAdditionalTdgvaMil} decimals={1} />M proxy</span>
                </div>
              </div>
            </div>

            {/* Return per Resident Household */}
            <div className="metric-card p-3 border-l-2 border-l-purple-400">
              <span className="metric-label">Household Yield</span>
              <div className="metric-value text-violet-700 text-xl">
                +RM <AnimatedCounter value={yieldPerHouseholdRM} decimals={0} />
              </div>
              <div className="mt-1 flex flex-col gap-0.5">
                <span className="text-[10px] text-violet-700 font-medium">
                  per resident HH
                </span>
                <div className="inline-flex items-center gap-0.5 text-[10px] font-bold text-purple-700 bg-purple-50 px-1.5 py-0.5 rounded-full border border-purple-200/60 w-fit">
                  <ArrowUpRight className="w-3 h-3" />
                  <span>+RM <AnimatedCounter value={yieldPerHouseholdRM} decimals={0} /> / HH</span>
                </div>
              </div>
            </div>
          </div>

          {/* Direct Community & Homestay Value Retention Strip (SDG 8.9) */}
          {vfrAccomSpendRM > 0 && (
            <div className="p-3 rounded-lg bg-violet-50/20 border border-violet-200/30 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <Home className="w-4 h-4 text-violet-700 shrink-0" />
                <span className="text-stone-700">
                  <strong className="text-violet-800">UN SDG Target 8.9 Community Retained Lodging:</strong>{' '}
                  Converting {vfrConversionRate}% of unpaid VFR stays injects{' '}
                  <strong className="text-stone-900 font-mono">+RM <AnimatedCounter value={vfrAccomSpendRM} decimals={1} />M</strong> directly into registered homestay operators and local host households.
                </span>
              </div>
              <span className="px-2 py-0.5 rounded bg-violet-200/20 text-violet-800 font-mono font-bold text-[11px] shrink-0 ml-2">
                +<AnimatedCounter value={vfrNightsK} decimals={0} />k Paid Nights
              </span>
            </div>
          )}

          {/* Comparison Bar Chart */}
          <div className="glass-panel p-3 border-violet-100">
            <span className="text-xs font-bold text-stone-700 block mb-1">
              Economic Revenue & Value-Added Expansion (RM Million)
            </span>
            <div className="h-[200px] w-full">
              <ReactECharts option={impactChartOption} style={{ height: '100%', width: '100%' }} />
            </div>
          </div>

          {/* Hotel Capacity Feasibility Bar with Configurable Threshold (Phase 23, 24, 27) */}
          <div className="p-3 rounded-lg bg-white/80 border border-violet-100 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-stone-700 flex items-center gap-1.5">
                <Hotel className="w-3.5 h-3.5 text-amber-700" />
                Hotel Capacity Feasibility Check ({guestsPerRoom} guests/occupied room)
              </span>
              {hasCapacityData && simulatedAor != null && baselineAor != null ? (
                <span className="font-mono text-stone-700 text-xs">
                  Simulated AOR: <strong className={capacityStatus.color}>{simulatedAor.toFixed(1)}%</strong>{' '}
                  (Baseline: {baselineAor.toFixed(1)}%, Headroom: {(100 - simulatedAor).toFixed(1)}%)
                </span>
              ) : (
                <span className="text-[10px] px-2 py-0.5 rounded bg-stone-100 text-stone-600 font-mono">
                  Capacity Unobserved
                </span>
              )}
            </div>

            {hasCapacityData && simulatedAor != null ? (
              <>
                <div className="w-full h-2.5 rounded-full bg-stone-100 overflow-hidden relative">
                  {/* Planning Threshold indicator bar */}
                  <div 
                    className="absolute top-0 bottom-0 w-0.5 bg-stone-400 z-10" 
                    style={{ left: `${Math.min(100, planningThreshold)}%` }}
                    title={`Planning Threshold: ${planningThreshold}%`}
                  ></div>
                  <div 
                    className={`h-full rounded-full transition-all duration-300 ${capacityStatus.bg}`}
                    style={{ width: `${Math.min(100, simulatedAor)}%` }}
                  ></div>
                </div>

                <div className="flex items-center justify-between text-[10px] text-stone-600">
                  <span>Available Rooms: {totalRooms ? totalRooms.toLocaleString() : 'N/A'}</span>
                  <span className={`font-semibold ${capacityStatus.color}`}>
                    {capacityStatus.msg}
                  </span>
                </div>

                {/* Seasonal pressure caveat (Phase 27) */}
                <div className="p-2 rounded bg-amber-500/10 border border-amber-500/20 text-[10px] text-amber-900 flex items-center gap-1.5">
                  <Info className="w-3.5 h-3.5 text-amber-700 shrink-0" />
                  <span>
                    <strong>Sensitivity Notice:</strong> {seasonalCaveat} Selected planning threshold: {planningThreshold}% AOR.
                  </span>
                </div>
              </>
            ) : (
              <div className="text-[10px] text-stone-500 italic py-1">
                Hotel room inventory or occupancy rate unobserved in official survey tables for {selectedState}. Capacity check skipped.
              </div>
            )}
          </div>
        </div>
      </div>
      )}

      {/* MODE 2: Monte Carlo Stochastic Uncertainty Engine (Phase 26) */}
      {simulationMode === 'monte_carlo' && (() => {
        const activeMcKey = activeCorridorOrigin 
          ? `${activeCorridorOrigin} -> ${selectedState}`
          : (scenarioConfig.monte_carlo_benchmarks && scenarioConfig.monte_carlo_benchmarks[`Selangor -> ${selectedState}`]
              ? `Selangor -> ${selectedState}`
              : Object.keys(scenarioConfig.monte_carlo_benchmarks || {})[0] || 'Selangor -> Melaka');
        
        const mc = scenarioConfig.monte_carlo_benchmarks?.[activeMcKey] || scenarioConfig.monte_carlo_benchmarks?.['Selangor -> Melaka'];
        const histData = mc?.distribution?.gva_density || [];

        const mcChartOption = {
          backgroundColor: 'transparent',
          tooltip: {
            trigger: 'axis',
            formatter: (params: any) => {
              const p = params[0];
              return `<strong>${p.name}</strong><br/>Simulation Frequency: <strong>${p.value} draws</strong>`;
            }
          },
          grid: { left: '8%', right: '5%', bottom: '15%', top: '15%' },
          xAxis: {
            type: 'category',
            name: 'Incremental GVA (RM M)',
            nameLocation: 'middle',
            nameGap: 24,
            data: histData.map((d: any) => `RM ${d.bin_mid}M`),
            axisLabel: { fontSize: 10, color: '#4b5563' }
          },
          yAxis: {
            type: 'value',
            name: 'Draw Frequency',
            axisLabel: { fontSize: 10, color: '#4b5563' }
          },
          series: [
            {
              type: 'bar',
              data: histData.map((d: any) => d.frequency),
              itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: '#7c3aed' },
                  { offset: 1, color: '#a78bfa' }
                ]),
                borderRadius: [4, 4, 0, 0]
              }
            }
          ]
        };

        return (
          <div className="space-y-6 animate-fadeIn">
            <div className="glass-panel p-5 border border-purple-200">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="px-2 py-0.5 rounded bg-purple-100 text-purple-800 text-[10px] font-bold uppercase tracking-wider">
                      Phase 26 Stochastic Simulation
                    </span>
                    <span className="text-xs text-stone-500">1,000 Iterations across Policy Levers</span>
                  </div>
                  <h3 className="text-xl font-bold text-stone-900">
                    Corridor Uncertainty: {mc ? `${mc.origin} ➔ ${mc.destination}` : `${selectedState} Feeder Corridor`}
                  </h3>
                  <p className="text-xs text-stone-600 mt-0.5">
                    Stochastic variation in campaign reach (5–40%), stay duration (+0.05d to +2.0d), spending velocity (CV 15%), and guest density.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded-lg bg-stone-100 text-stone-700 text-xs font-mono font-medium">
                    Seed: 42 (100% Reproducible)
                  </span>
                </div>
              </div>

              {/* 3 Metric Cards with P10 - P50 - P90 */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-5">
                <div className="p-4 rounded-xl bg-white border border-purple-100 shadow-sm">
                  <div className="text-[11px] font-semibold text-stone-500 uppercase tracking-wider">Additional Tourist Nights</div>
                  <div className="text-2xl font-bold text-purple-900 mt-1 font-mono">
                    +{mc ? (mc.percentiles.additional_nights.p50).toLocaleString() : '—'}
                  </div>
                  <div className="text-xs text-stone-500 mt-1 flex justify-between font-mono">
                    <span>P10: +{mc ? (mc.percentiles.additional_nights.p10).toLocaleString() : '—'}</span>
                    <span>P90: +{mc ? (mc.percentiles.additional_nights.p90).toLocaleString() : '—'}</span>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-white border border-purple-100 shadow-sm">
                  <div className="text-[11px] font-semibold text-stone-500 uppercase tracking-wider">Additional Spend (RM M)</div>
                  <div className="text-2xl font-bold text-emerald-700 mt-1 font-mono">
                    +RM {mc ? mc.percentiles.additional_spend_rm_m.p50.toFixed(2) : '—'}M
                  </div>
                  <div className="text-xs text-stone-500 mt-1 flex justify-between font-mono">
                    <span>P10: RM {mc ? mc.percentiles.additional_spend_rm_m.p10.toFixed(2) : '—'}M</span>
                    <span>P90: RM {mc ? mc.percentiles.additional_spend_rm_m.p90.toFixed(2) : '—'}M</span>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-white border border-purple-100 shadow-sm">
                  <div className="text-[11px] font-semibold text-stone-500 uppercase tracking-wider">Potential Tourism GVA (RM M)</div>
                  <div className="text-2xl font-bold text-indigo-700 mt-1 font-mono">
                    +RM {mc ? mc.percentiles.potential_gva_rm_m.p50.toFixed(2) : '—'}M
                  </div>
                  <div className="text-xs text-stone-500 mt-1 flex justify-between font-mono">
                    <span>P10: RM {mc ? mc.percentiles.potential_gva_rm_m.p10.toFixed(2) : '—'}M</span>
                    <span>P90: RM {mc ? mc.percentiles.potential_gva_rm_m.p90.toFixed(2) : '—'}M</span>
                  </div>
                </div>
              </div>

              {/* Capacity Risk Gauge */}
              <div className="mt-5 p-4 rounded-xl bg-amber-50/70 border border-amber-200/80 flex items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <ShieldAlert className="w-5 h-5 text-amber-700 shrink-0" />
                  <div>
                    <div className="text-xs font-bold text-amber-900">Capacity Saturation Breach Risk</div>
                    <div className="text-xs text-amber-800 mt-0.5">
                      Probability that destination hotel occupancy exceeds {planningThreshold}% planning threshold under stochastic arrivals.
                    </div>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <span className="text-xl font-bold text-amber-900 font-mono">
                    {mc ? (mc.prob_capacity_breach * 100).toFixed(1) : 0}%
                  </span>
                  <span className="block text-[10px] text-amber-700 font-semibold">Risk of Saturation</span>
                </div>
              </div>
            </div>

            {/* Chart: Probability Density Distribution */}
            <div className="glass-panel p-5 border border-purple-100">
              <h4 className="text-sm font-bold text-stone-800 mb-2 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-purple-600" />
                Stochastic Incremental GVA Frequency Distribution (20 Bins)
              </h4>
              <div className="h-64 w-full">
                <ReactECharts option={mcChartOption} style={{ height: '100%', width: '100%' }} />
              </div>
            </div>
          </div>
        );
      })()}

      {/* MODE 3: Tourism Investment Portfolio Optimizer (Phase 36) */}
      {simulationMode === 'portfolio' && (() => {
        const tiers = scenarioConfig.portfolio_optimization?.solved_tiers || {};
        const currentTier = tiers[String(selectedBudget)]?.[String(selectedOptimizerThreshold)] || tiers['5.0']?.['80'];
        const summary = currentTier?.summary;
        const corridors = currentTier?.selected_corridors || [];

        return (
          <div className="space-y-6 animate-fadeIn">
            {/* Portfolio Optimizer Header & Controls */}
            <div className="glass-panel p-5 border border-indigo-200">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="px-2 py-0.5 rounded bg-indigo-100 text-indigo-800 text-[10px] font-bold uppercase tracking-wider">
                      Phase 36 Mixed-Integer Linear Programming (MILP)
                    </span>
                    <span className="text-xs text-stone-500">Global Optimal Resource Allocation</span>
                  </div>
                  <h3 className="text-xl font-bold text-stone-900">Tourism Investment Portfolio Optimizer</h3>
                  <p className="text-xs text-stone-600 mt-0.5">
                    Maximizes national Gross Value Added (GVA) given a public campaign budget while strictly respecting destination hotel capacity ceilings.
                  </p>
                </div>

                {/* Planning Threshold Selector */}
                <div className="flex items-center gap-1.5 bg-stone-100 p-1 rounded-lg border border-stone-200">
                  <span className="text-[11px] text-stone-600 px-1 font-medium">Ceiling:</span>
                  {[75, 80, 85].map(t => (
                    <button
                      key={t}
                      onClick={() => setSelectedOptimizerThreshold(t)}
                      className={`px-2 py-1 rounded text-xs font-semibold transition-all ${
                        selectedOptimizerThreshold === t
                          ? 'bg-indigo-600 text-white shadow-sm'
                          : 'text-stone-600 hover:text-stone-900'
                      }`}
                    >
                      {t}%
                    </button>
                  ))}
                </div>
              </div>

              {/* Budget Selector Pills */}
              <div className="space-y-1.5 border-t border-indigo-100/80 pt-3">
                <label className="text-xs font-bold text-stone-700 uppercase tracking-wider block">
                  Select Campaign Budget Allocation:
                </label>
                <div className="flex flex-wrap gap-2">
                  {[1.0, 2.5, 5.0, 10.0, 20.0].map(b => (
                    <button
                      key={b}
                      onClick={() => setSelectedBudget(b)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                        selectedBudget === b
                          ? 'bg-indigo-600 text-white shadow-sm ring-2 ring-indigo-300'
                          : 'bg-white border border-stone-200 text-stone-700 hover:bg-stone-50'
                      }`}
                    >
                      RM {b.toFixed(1)} Million
                    </button>
                  ))}
                </div>
              </div>

              {/* Top 4 KPI Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5">
                <div className="p-3.5 rounded-xl bg-white border border-indigo-100">
                  <span className="text-[10px] font-semibold text-stone-500 uppercase">Budget Utilized</span>
                  <div className="text-lg font-bold text-stone-900 mt-0.5 font-mono">
                    RM {summary ? summary.total_cost_rm_million.toFixed(2) : '—'}M
                  </div>
                  <span className="text-[10px] text-stone-500 font-mono">
                    {summary ? summary.budget_utilization_pct.toFixed(1) : '—'}% of RM {selectedBudget}M
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-white border border-indigo-100">
                  <span className="text-[10px] font-semibold text-stone-500 uppercase">Expected Incremental GVA</span>
                  <div className="text-lg font-bold text-indigo-700 mt-0.5 font-mono">
                    +RM {summary ? summary.total_expected_gva_rm_million.toFixed(1) : '—'}M
                  </div>
                  <span className="text-[10px] text-indigo-600 font-mono">Macroeconomic yield</span>
                </div>

                <div className="p-3.5 rounded-xl bg-white border border-indigo-100">
                  <span className="text-[10px] font-semibold text-stone-500 uppercase">Portfolio ROI Multiplier</span>
                  <div className="text-lg font-bold text-emerald-700 mt-0.5 font-mono">
                    {summary ? summary.portfolio_roi_multiplier.toFixed(1) : '—'}x
                  </div>
                  <span className="text-[10px] text-emerald-600 font-mono">GVA per RM invested</span>
                </div>

                <div className="p-3.5 rounded-xl bg-white border border-indigo-100">
                  <span className="text-[10px] font-semibold text-stone-500 uppercase">Corridors Funded</span>
                  <div className="text-lg font-bold text-purple-700 mt-0.5 font-mono">
                    {summary ? summary.total_corridors_funded : '—'}
                  </div>
                  <span className="text-[10px] text-purple-600 font-mono">Inter-state routes</span>
                </div>
              </div>
            </div>

            {/* Selected Corridors Table */}
            <div className="glass-panel p-5 border border-indigo-100">
              <h4 className="text-sm font-bold text-stone-900 mb-3 flex items-center justify-between">
                <span>Optimal Corridor Allocations ({corridors.length} Funded)</span>
                <span className="text-xs text-stone-500 font-normal">Ranked by Expected GVA</span>
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-stone-100 text-stone-600 uppercase font-semibold">
                    <tr>
                      <th className="py-2 px-3 rounded-l-lg">Corridor</th>
                      <th className="py-2 px-3">Category</th>
                      <th className="py-2 px-3">Feeder Flow</th>
                      <th className="py-2 px-3">Campaign Cost</th>
                      <th className="py-2 px-3">Expected GVA</th>
                      <th className="py-2 px-3 rounded-r-lg">Additional Nights</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100">
                    {corridors.map((c: any, idx: number) => (
                      <tr key={idx} className="hover:bg-indigo-50/40 transition-colors">
                        <td className="py-2 px-3 font-semibold text-stone-900">{c.origin} ➔ {c.destination}</td>
                        <td className="py-2 px-3">
                          <span className="px-1.5 py-0.5 rounded text-[10px] bg-purple-100 text-purple-800 font-medium">
                            {c.category}
                          </span>
                        </td>
                        <td className="py-2 px-3 font-mono">{c.tourist_flow_thousands.toFixed(1)}k</td>
                        <td className="py-2 px-3 font-mono">RM {(c.cost_rm_million * 1000).toFixed(0)}k</td>
                        <td className="py-2 px-3 font-mono font-bold text-indigo-700">+RM {c.expected_gva_rm_million.toFixed(2)}M</td>
                        <td className="py-2 px-3 font-mono">+{Math.round(c.additional_nights).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
};
