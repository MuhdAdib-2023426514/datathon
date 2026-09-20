import React, { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
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
  ArrowUpRight
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
  conversionRate: number;
  yieldUplift: number;
  vfrConversionRate: number;
  icon: React.ComponentType<{ className?: string }>;
}

const PRESETS: PolicyPreset[] = [
  {
    key: 'conservative',
    label: 'Conservative',
    sublabel: '+0.2d / 5% conv',
    badge: 'Baseline',
    deltaAlos: 0.2,
    conversionRate: 5,
    yieldUplift: 5,
    vfrConversionRate: 3,
    icon: Shield,
  },
  {
    key: 'moderate',
    label: 'Moderate',
    sublabel: '+0.4d / 10% conv',
    badge: 'Targeted',
    deltaAlos: 0.4,
    conversionRate: 10,
    yieldUplift: 10,
    vfrConversionRate: 5,
    icon: Zap,
  },
  {
    key: 'ambitious',
    label: 'Ambitious',
    sublabel: '+0.6d / 20% conv',
    badge: 'Transform',
    deltaAlos: 0.6,
    conversionRate: 20,
    yieldUplift: 15,
    vfrConversionRate: 10,
    icon: Rocket,
  },
];

interface ScenarioSimulatorProps {
  scenarioConfig: ScenarioEngineConfig;
  stateProfiles: Record<string, StateProfile>;
}

export const ScenarioSimulator: React.FC<ScenarioSimulatorProps> = ({ 
  scenarioConfig, 
  stateProfiles 
}) => {
  const [selectedState, setSelectedState] = useState<string>('Melaka');
  const [activePreset, setActivePreset] = useState<PresetKey>('moderate');
  const [deltaAlos, setDeltaAlos] = useState<number>(0.4); // Moderate default
  const [conversionRate, setConversionRate] = useState<number>(10); // 10% day-trippers converted
  const [yieldUplift, setYieldUplift] = useState<number>(10); // +10% spend/night uplift
  const [vfrConversionRate, setVfrConversionRate] = useState<number>(5); // 5% VFR to paid lodging

  const handleSelectPreset = (preset: PolicyPreset) => {
    setActivePreset(preset.key);
    setDeltaAlos(preset.deltaAlos);
    setConversionRate(preset.conversionRate);
    setYieldUplift(preset.yieldUplift);
    setVfrConversionRate(preset.vfrConversionRate);
  };

  const handleReset = () => {
    handleSelectPreset(PRESETS[1]); // Reset to moderate preset
  };

  const stateList = Object.values(stateProfiles);
  const activeProfile = stateProfiles[selectedState] || stateList[0];
  const b = activeProfile.baseline_2025;

  const baselineTouristsK = b.tourists_thousands;
  const baselineExcursionistsK = activeProfile.baseline_2025.visitors_thousands - b.tourists_thousands;
  const baselineAlos = b.alos_days;
  const baselineSpendPerNight = b.spend_per_night_rm;
  const accomVAI = scenarioConfig.constants?.accommodation_vai || 0.858;
  const residentHouseholds = activeProfile.demographics?.households_thousands || 250.0;
  const hasCapacityData = b.hotel_rooms != null && b.aor_pct != null;
  const totalRooms = b.hotel_rooms;
  const baselineAor = b.aor_pct;

  // Real-Time Scenario Calculations (AGENTS.md Stage F Formulas)
  // 1. Additional nights from extending stay of existing tourists
  const addNightsFromAlosK = baselineTouristsK * deltaAlos;

  // 2. Converted excursionists into overnight tourists
  const convertedTouristsK = baselineExcursionistsK * (conversionRate / 100.0);
  const addNightsFromConvertedK = convertedTouristsK * (baselineAlos + deltaAlos);

  // 3. Converted unpaid VFR stays into registered paid lodging/homestays (Recommendation 3)
  const hasVfrData = activeProfile.lodging_shares?.unpaid_vfr_pct != null;
  const unpaidVfrPct = hasVfrData ? activeProfile.lodging_shares!.unpaid_vfr_pct : 0.0;
  const vfrTouristsK = baselineTouristsK * (unpaidVfrPct / 100.0);
  const convertedVfrTouristsK = vfrTouristsK * (vfrConversionRate / 100.0);
  const vfrNightsK = convertedVfrTouristsK * (baselineAlos + deltaAlos);
  const homestayNightlyRate = Math.max(75, baselineSpendPerNight * 0.85);
  const vfrAccomSpendRM = hasVfrData ? (vfrNightsK * 1e3 * homestayNightlyRate) / 1e6 : 0.0;

  // Total additional tourist nights (thousands)
  const totalAdditionalNightsK = addNightsFromAlosK + addNightsFromConvertedK;

  // New spend per night (RM)
  const newSpendPerNight = baselineSpendPerNight * (1 + yieldUplift / 100.0);

  // Additional accommodation expenditure (RM Million)
  // New nights spend + uplift on existing nights + VFR converted lodging spend
  const existingNightsK = baselineTouristsK * baselineAlos;
  const newNightsSpendRM = (totalAdditionalNightsK * 1e3 * newSpendPerNight) / 1e6;
  const existingNightsUpliftRM = (existingNightsK * 1e3 * (newSpendPerNight - baselineSpendPerNight)) / 1e6;
  const totalAdditionalAccomSpendMil = newNightsSpendRM + existingNightsUpliftRM + vfrAccomSpendRM;

  // Potential Additional Tourism Value Added Proxy (RM Million at 85.8% VAI)
  const potentialAdditionalTdgvaMil = totalAdditionalAccomSpendMil * accomVAI;

  // Incremental Yield per Resident Household (RM / Household)
  const yieldPerHouseholdRM = (totalAdditionalAccomSpendMil * 1e6) / (residentHouseholds * 1e3);

  // Capacity Feasibility (AOR impact) - Strict non-arbitrary computation
  const availableRoomNightsYearK = (hasCapacityData && totalRooms && totalRooms > 0) ? (totalRooms * 365) / 1e3 : null;
  const additionalAorPct = (hasCapacityData && availableRoomNightsYearK && availableRoomNightsYearK > 0)
    ? (totalAdditionalNightsK / availableRoomNightsYearK) * 100
    : null;
  const simulatedAor = (hasCapacityData && baselineAor != null && additionalAorPct != null)
    ? baselineAor + additionalAorPct
    : null;

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
              Simulate the macroeconomic impact of targeted interventions: extending length of stay, converting excursionist day-trippers into overnight guests, and optimizing accommodation yield per night.
            </p>
          </div>

          <button
            onClick={handleReset}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white border border-violet-200 text-stone-700 hover:text-stone-900 text-xs font-semibold self-start md:self-center transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset to Defaults
          </button>
        </div>

        {/* Mandatory Causal Disclaimer Badge (AGENTS.md Section 7 & 9) */}
        <div className="mt-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center gap-2.5 text-xs text-amber-800">
          <ShieldAlert className="w-4 h-4 text-amber-700 shrink-0" />
          <span>
            <strong>Mandatory Methodological Guardrail:</strong> <em>"Scenario estimate, not a causal forecast."</em> Calculations rely on TSA 2025 accommodation value-added intensity (85.8%) and Domestic Tourism Survey parameters under transparent proportional assumptions.
          </span>
        </div>
      </div>

      {/* Main Simulator Grid: Controls (5 cols) & Outputs (7 cols) */}
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

          {/* Slider 2: Excursionist Conversion (%) */}
          <div className="space-y-2 pt-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-stone-800">
                2. Excursionist Day-Trip Conversion
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

          {/* Slider 3: Spend-per-Night Yield Uplift (%) */}
          <div className="space-y-2 pt-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-stone-800">
                3. Nightly Spend Yield Optimization
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

          {/* Slider 4: VFR Unpaid to Paid Homestay / Commercial Lodging Conversion (Recommendation 3) */}
          <div className="space-y-2 pt-2 border-t border-violet-100/60">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-stone-800 flex items-center gap-1.5">
                <Home className="w-3.5 h-3.5 text-violet-700" />
                4. VFR to Paid Lodging / Homestay Conversion
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
        </div>

        {/* Real-Time Impact Dashboard (7 cols) */}
        <div className="glass-panel p-5 lg:col-span-7 flex flex-col justify-between space-y-4">
          <div className="flex items-center justify-between border-b border-violet-100/60 pb-3">
            <div>
              <h3 className="text-base font-bold text-stone-900 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-violet-700" />
                Simulated Economic Outcomes ({selectedState})
              </h3>
              <p className="text-xs text-stone-600">Projected incremental domestic economic capture</p>
            </div>
            <span className="text-xs px-2.5 py-0.5 rounded bg-violet-600/20 text-violet-700 font-mono">
              VAI = 85.8%
            </span>
          </div>

          {/* Key Impact Outcome Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {/* Additional Tourist Nights */}
            <div className="metric-card p-3 border-l-2 border-l-violet-400">
              <span className="metric-label">Extra Nights</span>
              <div className="metric-value text-stone-900 text-xl">
                +<AnimatedCounter value={totalAdditionalNightsK / 1e3} decimals={2} />M
              </div>
              <div className="mt-1 flex flex-col gap-0.5">
                <span className="text-[10px] text-violet-700 font-medium">
                  +<AnimatedCounter value={totalAdditionalNightsK} decimals={0} />k nights
                </span>
                <div className="inline-flex items-center gap-0.5 text-[10px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded-full border border-emerald-200/60 w-fit">
                  <ArrowUpRight className="w-3 h-3" />
                  <span>+<AnimatedCounter value={totalAdditionalNightsK} decimals={0} />k</span>
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
                  85.8% retained value
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

          {/* Hotel Capacity Feasibility Bar with 4 Saturation Tiers */}
          <div className="p-3 rounded-lg bg-white/80 border border-violet-100 space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-stone-700 flex items-center gap-1.5">
                <Hotel className="w-3.5 h-3.5 text-amber-700" />
                Hotel Capacity Feasibility Check
              </span>
              {hasCapacityData && simulatedAor != null && baselineAor != null ? (
                <span className="font-mono text-stone-700 text-xs">
                  Simulated AOR: <strong className={
                    simulatedAor > 100 ? 'text-rose-700' :
                    simulatedAor > 80 ? 'text-amber-700' :
                    simulatedAor > 70 ? 'text-indigo-600' : 'text-violet-700'
                  }>{simulatedAor.toFixed(1)}%</strong> (Baseline: {baselineAor.toFixed(1)}%)
                </span>
              ) : (
                <span className="text-[10px] px-2 py-0.5 rounded bg-stone-100 text-stone-600 font-mono">
                  Capacity Unobserved
                </span>
              )}
            </div>

            {hasCapacityData && simulatedAor != null ? (
              <>
                <div className="w-full h-2 rounded-full bg-violet-50 overflow-hidden">
                  <div 
                    className={`h-full rounded-full transition-all duration-300 ${
                      simulatedAor > 100 ? 'bg-rose-600' :
                      simulatedAor > 80 ? 'bg-amber-500' :
                      simulatedAor > 70 ? 'bg-indigo-500' : 'bg-violet-600'
                    }`}
                    style={{ width: `${Math.min(100, simulatedAor)}%` }}
                  ></div>
                </div>

                <div className="flex items-center justify-between text-[10px] text-stone-600">
                  <span>Existing Rooms: {totalRooms ? totalRooms.toLocaleString() : 'N/A'}</span>
                  {simulatedAor > 100 ? (
                    <span className="text-rose-700 font-bold">Severe Deficit (&gt;100%): Room inventory physically exceeded.</span>
                  ) : simulatedAor > 80 ? (
                    <span className="text-amber-700 font-semibold">High Saturation (&gt;80%): Severe peak season bottleneck.</span>
                  ) : simulatedAor > 70 ? (
                    <span className="text-indigo-600 font-semibold">Moderate Saturation (70-80%): Capacity tight during surges.</span>
                  ) : (
                    <span className="text-violet-700 font-semibold">Optimal (&lt;70%): Ample room inventory to absorb simulated stays.</span>
                  )}
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
    </div>
  );
};
