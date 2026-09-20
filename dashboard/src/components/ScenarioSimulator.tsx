import React, { useState } from 'react';
import ReactECharts from 'echarts-for-react';
import type { ScenarioEngineConfig, StateProfile } from '../types';
import { 
  Sliders, 
  Sparkles, 
  Hotel, 
  ShieldAlert, 
  RotateCcw,
  Home
} from 'lucide-react';

interface ScenarioSimulatorProps {
  scenarioConfig: ScenarioEngineConfig;
  stateProfiles: Record<string, StateProfile>;
}

export const ScenarioSimulator: React.FC<ScenarioSimulatorProps> = ({ 
  scenarioConfig, 
  stateProfiles 
}) => {
  const [selectedState, setSelectedState] = useState<string>('Melaka');
  const [deltaAlos, setDeltaAlos] = useState<number>(0.3); // +0.3 days
  const [conversionRate, setConversionRate] = useState<number>(10); // 10% day-trippers converted
  const [yieldUplift, setYieldUplift] = useState<number>(10); // +10% spend/night uplift
  const [vfrConversionRate, setVfrConversionRate] = useState<number>(5); // 5% VFR to paid lodging

  const stateList = Object.values(stateProfiles);
  const activeProfile = stateProfiles[selectedState] || stateList[0];
  const b = activeProfile.baseline_2025;

  const baselineTouristsK = b.tourists_thousands;
  const baselineExcursionistsK = activeProfile.baseline_2025.visitors_thousands - b.tourists_thousands;
  const baselineAlos = b.alos_days;
  const baselineSpendPerNight = b.spend_per_night_rm;
  const accomVAI = scenarioConfig.constants?.accommodation_vai || 0.858;
  const residentHouseholds = activeProfile.demographics?.households_thousands || 250.0;
  const totalRooms = b.hotel_rooms || 10000;
  const baselineAor = b.aor_pct || 55.0;

  // Real-Time Scenario Calculations (AGENTS.md Stage F Formulas)
  // 1. Additional nights from extending stay of existing tourists
  const addNightsFromAlosK = baselineTouristsK * deltaAlos;

  // 2. Converted excursionists into overnight tourists
  const convertedTouristsK = baselineExcursionistsK * (conversionRate / 100.0);
  const addNightsFromConvertedK = convertedTouristsK * (baselineAlos + deltaAlos);

  // 3. Converted unpaid VFR stays into registered paid lodging/homestays (Recommendation 3)
  const unpaidVfrPct = activeProfile.lodging_shares?.unpaid_vfr_pct ?? 50.0;
  const vfrTouristsK = baselineTouristsK * (unpaidVfrPct / 100.0);
  const convertedVfrTouristsK = vfrTouristsK * (vfrConversionRate / 100.0);
  const vfrNightsK = convertedVfrTouristsK * (baselineAlos + deltaAlos);
  const homestayNightlyRate = Math.max(75, baselineSpendPerNight * 0.85);
  const vfrAccomSpendRM = (vfrNightsK * 1e3 * homestayNightlyRate) / 1e6;

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

  // Capacity Feasibility (AOR impact)
  const availableRoomNightsYearK = (totalRooms * 365) / 1e3;
  const additionalAorPct = (totalAdditionalNightsK / Math.max(1, availableRoomNightsYearK)) * 100;
  const simulatedAor = Math.min(100, baselineAor + additionalAorPct);

  // Reset to default
  const handleReset = () => {
    setDeltaAlos(0.3);
    setConversionRate(10);
    setYieldUplift(10);
    setVfrConversionRate(5);
  };

  // ECharts Comparison Waterfall / Bar
  const impactChartOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#0e1526',
      borderColor: 'rgba(255, 255, 255, 0.15)',
      textStyle: { color: '#f8fafc', fontSize: 12 },
    },
    grid: { left: '3%', right: '4%', bottom: '8%', top: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      data: ['Accom Revenue (Baseline)', 'Simulated Accom Revenue', 'Baseline TDGVA Proxy', 'Simulated TDGVA Proxy'],
      axisLine: { lineStyle: { color: '#334155' } },
      axisLabel: { color: '#94a3b8', fontSize: 10, interval: 0 },
    },
    yAxis: {
      type: 'value',
      name: 'RM Million',
      axisLabel: { color: '#94a3b8' },
      splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } },
    },
    series: [
      {
        name: 'Economic Value',
        type: 'bar',
        barWidth: '40%',
        data: [
          { value: b.accommodation_expenditure_rm_million, itemStyle: { color: '#334155' } },
          { value: b.accommodation_expenditure_rm_million + totalAdditionalAccomSpendMil, itemStyle: { color: '#10b981' } },
          { value: b.accommodation_expenditure_rm_million * accomVAI, itemStyle: { color: '#1e293b' } },
          { value: (b.accommodation_expenditure_rm_million + totalAdditionalAccomSpendMil) * accomVAI, itemStyle: { color: '#06b6d4' } },
        ],
        label: {
          show: true,
          position: 'top',
          color: '#f8fafc',
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
      <div className="glass-panel p-6 border-l-4 border-l-emerald-500">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
                Transparent What-If Policy Lab
              </span>
              <span className="text-xs text-slate-400">Research Question 7 & Policy Simulator</span>
            </div>
            <h2 className="text-2xl font-bold text-white tracking-tight">
              Tourism Economic Value Scenario Simulator
            </h2>
            <p className="text-sm text-slate-300 mt-1 max-w-3xl">
              Simulate the macroeconomic impact of targeted interventions: extending length of stay, converting excursionist day-trippers into overnight guests, and optimizing accommodation yield per night.
            </p>
          </div>

          <button
            onClick={handleReset}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-300 hover:text-white text-xs font-semibold self-start md:self-center transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset to Defaults
          </button>
        </div>

        {/* Mandatory Causal Disclaimer Badge (AGENTS.md Section 7 & 9) */}
        <div className="mt-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center gap-2.5 text-xs text-amber-300">
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            <strong>Mandatory Methodological Guardrail:</strong> <em>"Scenario estimate, not a causal forecast."</em> Calculations rely on TSA 2025 accommodation value-added intensity (85.8%) and Domestic Tourism Survey parameters under transparent proportional assumptions.
          </span>
        </div>
      </div>

      {/* Main Simulator Grid: Controls (5 cols) & Outputs (7 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Policy Lever Controls (5 cols) */}
        <div className="glass-panel p-5 lg:col-span-5 space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800/60 pb-3">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Sliders className="w-4 h-4 text-emerald-400" />
              Policy Levers & Target Selection
            </h3>
            <span className="text-xs text-slate-400">Simulate by Destination</span>
          </div>

          {/* Destination Selector */}
          <div>
            <label className="block text-xs text-slate-400 uppercase font-semibold mb-1.5">
              Target Destination State
            </label>
            <select
              value={selectedState}
              onChange={(e) => setSelectedState(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5 text-sm font-semibold focus:outline-none focus:border-emerald-500"
            >
              {stateList.map((s) => (
                <option key={s.state} value={s.state}>
                  {s.state} ({s.archetype_name})
                </option>
              ))}
            </select>
          </div>

          {/* Baseline Summary Card for Target State */}
          <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs space-y-1">
            <div className="flex justify-between text-slate-400">
              <span>Overnight Tourists:</span>
              <strong className="text-white font-mono">{b.tourists_thousands.toFixed(0)}k</strong>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Excursionists (Day-Trips):</span>
              <strong className="text-amber-400 font-mono">{baselineExcursionistsK.toFixed(0)}k</strong>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Baseline ALOS:</span>
              <strong className="text-cyan-400 font-mono">{baselineAlos.toFixed(2)} days</strong>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Baseline Spend / Night:</span>
              <strong className="text-emerald-400 font-mono">RM {baselineSpendPerNight.toFixed(1)}</strong>
            </div>
          </div>

          {/* Slider 1: Length of Stay (+Delta ALOS) */}
          <div className="space-y-2 pt-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-200">
                1. Length-of-Stay Expansion (+ΔALOS)
              </span>
              <span className="font-mono font-bold text-emerald-400 text-sm">
                +{deltaAlos.toFixed(1)} days (→ {(baselineAlos + deltaAlos).toFixed(2)}d)
              </span>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.5"
              step="0.1"
              value={deltaAlos}
              onChange={(e) => setDeltaAlos(parseFloat(e.target.value))}
            />
            <span className="text-[10px] text-slate-400 block">
              Policy lever: Sunset cultural programming, weekend retreat packages, multi-day attraction passes.
            </span>
          </div>

          {/* Slider 2: Excursionist Conversion (%) */}
          <div className="space-y-2 pt-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-200">
                2. Excursionist Day-Trip Conversion
              </span>
              <span className="font-mono font-bold text-cyan-400 text-sm">
                {conversionRate}% (→ +{convertedTouristsK.toFixed(0)}k tourists)
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="25"
              step="1"
              value={conversionRate}
              onChange={(e) => setConversionRate(parseInt(e.target.value))}
            />
            <span className="text-[10px] text-slate-400 block">
              Policy lever: Evening night markets, weekend hotel discounts for day-trippers from neighboring states.
            </span>
          </div>

          {/* Slider 3: Spend-per-Night Yield Uplift (%) */}
          <div className="space-y-2 pt-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-200">
                3. Nightly Spend Yield Optimization
              </span>
              <span className="font-mono font-bold text-amber-400 text-sm">
                +{yieldUplift}% (→ RM {newSpendPerNight.toFixed(0)}/night)
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="30"
              step="5"
              value={yieldUplift}
              onChange={(e) => setYieldUplift(parseInt(e.target.value))}
            />
            <span className="text-[10px] text-slate-400 block">
              Policy lever: Hotel quality upgrades, premium boutique packages, eco-tourism experiential add-ons.
            </span>
          </div>

          {/* Slider 4: VFR Unpaid to Paid Homestay / Commercial Lodging Conversion (Recommendation 3) */}
          <div className="space-y-2 pt-2 border-t border-slate-800/60">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-200 flex items-center gap-1.5">
                <Home className="w-3.5 h-3.5 text-teal-400" />
                4. VFR to Paid Lodging / Homestay Conversion
              </span>
              <span className="font-mono font-bold text-teal-400 text-sm">
                {vfrConversionRate}% (→ +{convertedVfrTouristsK.toFixed(0)}k stays)
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="20"
              step="1"
              value={vfrConversionRate}
              onChange={(e) => setVfrConversionRate(parseInt(e.target.value))}
            />
            <div className="flex items-center justify-between text-[10px] text-slate-400">
              <span>Unpaid VFR Base: <strong className="text-slate-300 font-mono">{unpaidVfrPct.toFixed(1)}%</strong> ({vfrTouristsK.toFixed(0)}k tourists)</span>
              <span>Rate: <strong className="text-teal-300 font-mono">RM {homestayNightlyRate.toFixed(0)}/night</strong></span>
            </div>
            <span className="text-[10px] text-teal-300/90 block bg-teal-950/30 border border-teal-500/20 p-1.5 rounded">
              UN SDG 8.9 Policy lever: Transition visiting-friends-and-relatives (VFR) into licensed village Kampungstay, certified community homestays, and boutique heritage inns.
            </span>
          </div>
        </div>

        {/* Real-Time Impact Dashboard (7 cols) */}
        <div className="glass-panel p-5 lg:col-span-7 flex flex-col justify-between space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/60 pb-3">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-emerald-400" />
                Simulated Economic Outcomes ({selectedState})
              </h3>
              <p className="text-xs text-slate-400">Projected incremental domestic economic capture</p>
            </div>
            <span className="text-xs px-2.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono">
              VAI = 85.8%
            </span>
          </div>

          {/* Key Impact Outcome Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {/* Additional Tourist Nights */}
            <div className="metric-card p-3 border-l-2 border-l-emerald-400">
              <span className="metric-label">Extra Nights</span>
              <div className="metric-value text-white text-xl">
                +{(totalAdditionalNightsK / 1e3).toFixed(2)}M
              </div>
              <span className="text-[10px] text-emerald-400 font-medium">
                +{totalAdditionalNightsK.toFixed(0)}k nights
              </span>
            </div>

            {/* Additional Accommodation Revenue */}
            <div className="metric-card p-3 border-l-2 border-l-cyan-400">
              <span className="metric-label">Accom Spend</span>
              <div className="metric-value text-cyan-300 text-xl">
                +RM {totalAdditionalAccomSpendMil.toFixed(1)}M
              </div>
              <span className="text-[10px] text-cyan-400 font-medium">
                +{((totalAdditionalAccomSpendMil / Math.max(1, b.accommodation_expenditure_rm_million)) * 100).toFixed(1)}% uplift
              </span>
            </div>

            {/* Potential TDGVA Added */}
            <div className="metric-card p-3 border-l-2 border-l-emerald-500">
              <span className="metric-label">Potential GVA</span>
              <div className="metric-value text-emerald-400 text-xl">
                +RM {potentialAdditionalTdgvaMil.toFixed(1)}M
              </div>
              <span className="text-[10px] text-emerald-300 font-medium">
                85.8% retained value
              </span>
            </div>

            {/* Return per Resident Household */}
            <div className="metric-card p-3 border-l-2 border-l-purple-400">
              <span className="metric-label">Household Yield</span>
              <div className="metric-value text-purple-300 text-xl">
                +RM {yieldPerHouseholdRM.toFixed(0)}
              </div>
              <span className="text-[10px] text-purple-400 font-medium">
                per resident HH
              </span>
            </div>
          </div>

          {/* Direct Community & Homestay Value Retention Strip (SDG 8.9) */}
          {vfrAccomSpendRM > 0 && (
            <div className="p-3 rounded-lg bg-teal-950/20 border border-teal-500/30 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <Home className="w-4 h-4 text-teal-400 shrink-0" />
                <span className="text-slate-300">
                  <strong className="text-teal-300">UN SDG Target 8.9 Community Retained Lodging:</strong>{' '}
                  Converting {vfrConversionRate}% of unpaid VFR stays injects{' '}
                  <strong className="text-white font-mono">+RM {vfrAccomSpendRM.toFixed(1)}M</strong> directly into registered homestay operators and local host households.
                </span>
              </div>
              <span className="px-2 py-0.5 rounded bg-teal-500/20 text-teal-300 font-mono font-bold text-[11px] shrink-0 ml-2">
                +{vfrNightsK.toFixed(0)}k Paid Nights
              </span>
            </div>
          )}

          {/* Comparison Bar Chart */}
          <div className="glass-panel p-3 border-slate-800">
            <span className="text-xs font-bold text-slate-300 block mb-1">
              Economic Revenue & Value-Added Expansion (RM Million)
            </span>
            <div className="h-[200px] w-full">
              <ReactECharts option={impactChartOption} style={{ height: '100%', width: '100%' }} />
            </div>
          </div>

          {/* Hotel Capacity Feasibility Bar */}
          <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                <Hotel className="w-3.5 h-3.5 text-amber-400" />
                Hotel Capacity Feasibility Check
              </span>
              <span className="font-mono text-slate-300 text-xs">
                Simulated AOR: <strong className={simulatedAor > 85 ? 'text-rose-400' : 'text-emerald-400'}>{simulatedAor.toFixed(1)}%</strong> (Baseline: {baselineAor.toFixed(1)}%)
              </span>
            </div>

            <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
              <div 
                className={`h-full rounded-full transition-all duration-300 ${
                  simulatedAor > 85 ? 'bg-rose-500' : simulatedAor > 70 ? 'bg-amber-500' : 'bg-emerald-500'
                }`}
                style={{ width: `${Math.min(100, simulatedAor)}%` }}
              ></div>
            </div>

            <div className="flex items-center justify-between text-[10px] text-slate-400">
              <span>Existing Rooms: {totalRooms.toLocaleString()}</span>
              {simulatedAor > 85 ? (
                <span className="text-rose-400 font-semibold">Caution: High occupancy constraint. New capacity needed.</span>
              ) : (
                <span className="text-emerald-400">Feasible: Sufficient room inventory to absorb simulated stays.</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
