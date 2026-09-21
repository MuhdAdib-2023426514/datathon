import React, { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';
import type { StateProfile, DriversData } from '../types';
import {
  Users,
  Hotel,
  Wallet,
  Compass,
  Sparkles,
  AlertCircle,
  FileText,
  Download,
  Printer,
  X,
  ShieldCheck,
  Check,
  Filter,
  Target
} from 'lucide-react';

interface AccommodationMapProps {
  stateProfiles: Record<string, StateProfile>;
  geoJson: any;
  driversData: DriversData;
  selectedYear?: number;
}

interface StateDecisionSummaryData {
  primaryConstraint: string;
  primaryOpportunity: string;
  prescription: string;
  evidence: string[];
  confidence: string;
  limitations: string;
  tvay: number | null;
  tey: number;
  alos: number;
  spendPerNight: number;
  aor: number | null;
  headroom: number | null;
}

function computeStateDecisionSummary(state: StateProfile): StateDecisionSummaryData {
  const b = state.baseline_2025;
  const sdg = state.sdg_metrics;
  const alos = b.alos_days;
  const tvay: number | null = sdg.tvay_rm_per_day != null ? sdg.tvay_rm_per_day : null;
  const tey = sdg.tey_rm_per_day;
  const spendPerNight = b.spend_per_night_rm;
  const aor = b.aor_pct;
  const headroom = aor != null ? Math.max(0, 80.0 - aor) : null;
  const vfrShare = state.lodging_shares?.unpaid_vfr_pct;

  // Effective yield indicator: prefer TVAY, fall back to spend/night for classification
  const hasYield = tvay != null;
  const yieldHigh = hasYield ? tvay >= 58.0 : (spendPerNight != null && spendPerNight >= 60.0);
  const yieldLabel = hasYield
    ? `TVAY (RM ${tvay!.toFixed(1)}/day)`
    : (spendPerNight != null ? `Spend/Night (RM ${spendPerNight.toFixed(1)})` : 'Yield data unavailable');
  const yieldBenchmark = hasYield ? 'national median (RM 58.0)' : 'national median (RM 60.0)';

  let primaryConstraint = '';
  let primaryOpportunity = '';
  let prescription = '';
  const evidence: string[] = [];

  // National benchmark medians: ALOS: 2.50d, TVAY: 58.0 RM/day, Spend/Night: 60.0 RM
  if (alos < 2.50 && yieldHigh) {
    primaryConstraint = 'Short stay duration and day-trip transit pass-through';
    primaryOpportunity = 'Stay-extension incentive campaigns (+0.3d to +0.5d) and evening leisure economy capture';
    prescription = 'Deploy weekend & corporate staycation incentive vouchers, curate night-time cultural trails, and bundle hotel+attraction passes to convert transit day-trippers into overnight guests.';
    evidence.push(`ALOS (${alos.toFixed(2)}d) below national median (2.50d)`);
    evidence.push(`${yieldLabel} above ${yieldBenchmark}`);
    if (headroom != null) evidence.push(`Hotel capacity headroom (${headroom.toFixed(0)}%) available below 80% threshold`);
  } else if (alos < 2.50 && !yieldHigh) {
    primaryConstraint = 'Low nightly accommodation spend density and transit-dominated routing';
    primaryOpportunity = 'Experiential tourism product upgrades, boutique heritage stays, and in-destination spend capture';
    prescription = 'Upgrade local hospitality product standards, develop premium experiential eco/heritage circuits, and partner with regional transport operators to raise spend per visitor-day.';
    evidence.push(`ALOS (${alos.toFixed(2)}d) below national median (2.50d)`);
    evidence.push(`${yieldLabel} below ${yieldBenchmark}`);
  } else if (alos >= 2.50 && !yieldHigh) {
    primaryConstraint = 'High proportion of unpaid informal VFR lodging with low commercial accommodation capture';
    primaryOpportunity = 'Community homestay formalization (SDG 8.9), artisan retail spend trails, and packaged leisure extensions';
    prescription = 'Expand MOTAC certified Kampungstay/Homestay licensing, develop localized culinary & handicraft retail trails, and incentivize diaspora families to spend on paid recreational experiences.';
    evidence.push(`ALOS (${alos.toFixed(2)}d) above national median (2.50d)`);
    evidence.push(`${yieldLabel} below ${yieldBenchmark}`);
    if (vfrShare != null) evidence.push(`Unpaid VFR lodging share (${vfrShare.toFixed(1)}%) of overnight stays`);
  } else {
    primaryConstraint = 'Peak seasonal capacity constraints and destination environmental/heritage carrying capacity (SDG 12.b)';
    primaryOpportunity = 'Preserve high-yield premium value capture, expand off-peak seasonal demand, and deepen sustainable green eco-certification';
    prescription = 'Target affluent repeat visitors, protect core heritage/ecotourism zones from overcrowding, and implement dynamic seasonal pricing to maintain top-quartile economic yield.';
    evidence.push(`ALOS (${alos.toFixed(2)}d) above national median (2.50d)`);
    evidence.push(`${yieldLabel} above ${yieldBenchmark}`);
    if (aor != null && aor > 65.0) evidence.push(`Annual occupancy (${aor.toFixed(1)}%) indicates periodic weekend capacity pressure`);
  }

  return {
    primaryConstraint,
    primaryOpportunity,
    prescription,
    evidence,
    confidence: 'High (Official DOSM TSA 2025 & DTS Census Sample)',
    limitations: 'National TSA product VAI applied to state expenditure composition. Annual occupancy rate masks localized weekend capacity surges.',
    tvay,
    tey,
    alos,
    spendPerNight,
    aor,
    headroom
  };
}

export const AccommodationMap: React.FC<AccommodationMapProps> = ({
  stateProfiles,
  geoJson,
  driversData,
  selectedYear = 2025
}) => {
  const [selectedMetric, setSelectedMetric] = useState<
    'accom_share' | 'spend_per_night' | 'alos' | 'tey' | 'tvay' | 'gva_intensity' | 'tir' | 'archetype'
  >('accom_share');
  const [selectedStateName, setSelectedStateName] = useState<string>('Pulau Pinang');
  const [sdgFilter, setSdgFilter] = useState<'all' | 'carrying_capacity' | 'high_yield' | 'extended_stay' | 'leisure'>('all');
  const [showBriefModal, setShowBriefModal] = useState<boolean>(false);
  const [copiedBrief, setCopiedBrief] = useState<boolean>(false);

  // Register GeoJSON with echarts once
  useEffect(() => {
    if (geoJson) {
      echarts.registerMap('malaysia', geoJson);
    }
  }, [geoJson]);

  const stateList = Object.values(stateProfiles);
  const activeState = stateProfiles[selectedStateName] || stateList[0];
  const decisionSummary = computeStateDecisionSummary(activeState);

  // Helper to test if a state matches the SDG strategic filter
  const isStateHighlighted = (stateName: string) => {
    if (sdgFilter === 'all') return true;
    const s = stateProfiles[stateName];
    if (!s) return true;
    if (sdgFilter === 'carrying_capacity') {
      return (s.sdg_metrics?.epr_ratio ?? 0) > 1.5 || (s.sdg_metrics?.tir_visitors_per_resident ?? 0) > 15;
    }
    if (sdgFilter === 'high_yield') {
      return s.cluster_id === 1 || s.cluster_id === 2 || s.baseline_2025.spend_per_night_rm > 70;
    }
    if (sdgFilter === 'extended_stay') {
      return s.cluster_id === 4 || ((s.lodging_shares?.unpaid_vfr_pct ?? 0) > 60);
    }
    if (sdgFilter === 'leisure') {
      return s.cluster_id === 3;
    }
    return true;
  };

  // Generate Executive Policy Brief Markdown content
  const generateMarkdownBrief = (state: StateProfile) => {
    const b = state.baseline_2025;
    const d = state.demographics;
    const sdg = state.sdg_metrics;
    const dts = d?.dts_age_classes;
    const summary = computeStateDecisionSummary(state);

    return `# STATE TOURISM ECONOMIC INTELLIGENCE BRIEF: ${state.state.toUpperCase()}
**MYTourism Value Intelligence — State Decision-Support Brief**
*Prototype based on official Malaysian tourism data*
**Date**: ${new Date().toLocaleDateString('en-MY')} | **Status**: Research Prototype Decision Support | **Year**: ${selectedYear}

---

## 1. Executive Decision Summary & Strategic Prescription
- **State Archetype**: ${state.archetype_name} (${state.region})
- **Primary Constraint**: ${summary.primaryConstraint}
- **Primary Opportunity**: ${summary.primaryOpportunity}
- **Confidence Rating**: ${summary.confidence}
- **Hotel Capacity Headroom**: ${summary.headroom != null ? `${summary.headroom.toFixed(0)}% room space below 80% ceiling` : 'N/A'}
- **Rule-Based Policy Action**: ${summary.prescription}
- **Supporting Empirical Evidence**:
${summary.evidence.map(e => `  - ${e}`).join('\n')}

---

## 2. Baseline Economic Performance (${selectedYear})
- **Total Visitors**: ${b.visitors_thousands.toLocaleString()} thousand visitors
- **Overnight Tourists**: ${b.tourists_thousands.toLocaleString()} thousand tourists
- **Average Length of Stay (ALOS)**: ${b.alos_days.toFixed(2)} days
- **Spend per Night**: RM ${b.spend_per_night_rm.toFixed(2)} / night
- **Accommodation Share**: ${b.accommodation_share_pct.toFixed(2)}% of total visitor spending
- **Total Accommodation Receipts**: RM ${b.accommodation_expenditure_rm_million.toFixed(2)} Million
- **Total Tourism Expenditure**: RM ${b.total_expenditure_rm_million.toFixed(2)} Million
- **Hotel Capacity**: ${b.hotel_rooms != null ? b.hotel_rooms.toLocaleString() + ' rooms' : 'N/A (unobserved)'} | **Average Occupancy (AOR)**: ${b.aor_pct != null ? b.aor_pct.toFixed(1) + '%' : 'N/A'}

---

## 3. Demographics & DTS Visitor Age Distribution (100% MECE Non-Overlapping)
- **Total Population**: ${(d.total_population_thousands / 1000).toFixed(2)} Million
- **Adult Population (15+)**: ${d.adult_15plus_thousands ? (d.adult_15plus_thousands / 1000).toFixed(2) : 'N/A'} Million
- **Children (0–14)**: ${d.children_pct != null ? `${d.children_pct.toFixed(1)}%` : 'N/A'} (${d.children_0_14_thousands != null ? `${d.children_0_14_thousands.toFixed(0)}k pax` : '—'})
- **DTS Adult Age Breakdown (Sum = 100%)**:
  - **Ages 15–24 (Belia / Young Adults)**: ${dts?.age_15_24_pct != null ? `${dts.age_15_24_pct.toFixed(1)}%` : 'N/A'} (${dts?.age_15_24_k != null ? `${dts.age_15_24_k.toFixed(0)}k pax` : '—'})
  - **Ages 25–39 (Dewasa Muda / Prime Mobile Travelers)**: ${dts?.age_25_39_pct != null ? `${dts.age_25_39_pct.toFixed(1)}%` : 'N/A'} (${dts?.age_25_39_k != null ? `${dts.age_25_39_k.toFixed(0)}k pax` : '—'})
  - **Ages 40–54 (Pertengahan Umur / Family Travelers)**: ${dts?.age_40_54_pct != null ? `${dts.age_40_54_pct.toFixed(1)}%` : 'N/A'} (${dts?.age_40_54_k != null ? `${dts.age_40_54_k.toFixed(0)}k pax` : '—'})
  - **Ages ≥ 55 (Warga Emas / Seniors & Retirees)**: ${dts?.age_55plus_pct != null ? `${dts.age_55plus_pct.toFixed(1)}%` : 'N/A'} (${dts?.age_55plus_k != null ? `${dts.age_55plus_k.toFixed(0)}k pax` : '—'})
- **Resident Median Household Income**: RM ${b.resident_median_income_rm.toLocaleString()}
- **Unpaid VFR Lodging Share**: ${state.lodging_shares?.unpaid_vfr_pct != null ? `${state.lodging_shares.unpaid_vfr_pct}%` : 'N/A (unobserved)'} of overnight stays
- **Strategic Typology Quadrant**: ${b.yield_typology || sdg.yield_typology || 'N/A'}

---

## 4. UN SDG 8.9 & 12.b Carrying Capacity & Yield Status
- **Tourism Economic Yield (TEY)**: RM ${sdg.tey_rm_per_day.toFixed(1)} / visitor-day
- **Tourism Value-Added Yield (TVAY)**: RM ${(sdg.tvay_rm_per_day ?? 0).toFixed(1)} / visitor-day
- **Tourism GVA Intensity**: ${(sdg.tourism_gva_intensity_pct ?? sdg.dvr_retention_rate_pct).toFixed(1)}% (TSA Mapping Coverage: ${(sdg.mapping_coverage_pct ?? 100).toFixed(1)}%)
- **Tourist Intensity Ratio (TIR)**: ${sdg.tir_visitors_per_resident.toFixed(1)} visitors / resident
- **Excursionist Pressure Ratio (EPR)**: ${sdg.epr_ratio.toFixed(2)} day-trippers per overnight tourist
- **Sustainability Diagnosis**: ${sdg.sdg_diagnosis}
- **Recommended Policy Action**: ${sdg.sdg_policy_action}

---

## 5. Simulated Economic Opportunity (+0.3 Days Stay Extension)
Under a transparent scenario extending Average Length of Stay by +0.3 days:
- **Additional Tourist Nights**: +${(b.tourists_thousands * 0.3).toFixed(1)} thousand nights
- **Incremental Accommodation Expenditure**: +RM ${(b.tourists_thousands * 0.3 * b.spend_per_night_rm / 1000).toFixed(2)} Million
- **Potential Attributable Value-Added Proxy (85.8% VAI)**: +RM ${(b.tourists_thousands * 0.3 * b.spend_per_night_rm / 1000 * 0.858).toFixed(2)} Million
- **Incremental Return per Resident Household**: +RM ${(b.tourists_thousands * 0.3 * b.spend_per_night_rm / Math.max(1, d.households_thousands)).toFixed(0)} / household

> **Mandatory Methodological Notice**: Scenario estimate, not a causal forecast.
> **Official Sources**: Department of Statistics Malaysia (DOSM) Tourism Satellite Account 2015–2025, Domestic Tourism Survey 2018–2025, and HIES Table 6.
`;
  };

  const handleCopyBrief = () => {
    const md = generateMarkdownBrief(activeState);
    navigator.clipboard.writeText(md);
    setCopiedBrief(true);
    setTimeout(() => setCopiedBrief(false), 2500);
  };

  const handleDownloadBrief = () => {
    const md = generateMarkdownBrief(activeState);
    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `state_economic_brief_${activeState.state.toLowerCase().replace(/\s+/g, '_')}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Metric configurations
  const metricConfigs = {
    accom_share: {
      label: 'Accommodation Share (%)',
      unit: '%',
      getValue: (s: StateProfile) => s.baseline_2025.accommodation_share_pct,
      min: 5,
      max: 18,
      colorRange: ['#eee9f6', '#b7a3df', '#6041b0'],
    },
    spend_per_night: {
      label: 'Spend per Night (RM)',
      unit: 'RM',
      getValue: (s: StateProfile) => s.baseline_2025.spend_per_night_rm,
      min: 25,
      max: 110,
      colorRange: ['#eee9f6', '#b7a3df', '#6041b0'],
    },
    alos: {
      label: 'Average Length of Stay (ALOS days)',
      unit: 'days',
      getValue: (s: StateProfile) => s.baseline_2025.alos_days,
      min: 2.0,
      max: 3.2,
      colorRange: ['#eee9f6', '#b7a3df', '#6041b0'],
    },
    tey: {
      label: 'Tourism Economic Yield (TEY)',
      unit: 'RM/day',
      getValue: (s: StateProfile) => s.sdg_metrics.tey_rm_per_day,
      min: 150,
      max: 350,
      colorRange: ['#eee9f6', '#b7a3df', '#6041b0'],
    },
    tvay: {
      label: 'Tourism Value-Added Yield (TVAY)',
      unit: 'RM/day',
      getValue: (s: StateProfile) => s.sdg_metrics.tvay_rm_per_day || 0,
      min: 70,
      max: 180,
      colorRange: ['#eee9f6', '#b7a3df', '#6041b0'],
    },
    gva_intensity: {
      label: 'Tourism GVA Intensity (%)',
      unit: '%',
      getValue: (s: StateProfile) => s.sdg_metrics.tourism_gva_intensity_pct || s.sdg_metrics.dvr_retention_rate_pct,
      min: 55,
      max: 65,
      colorRange: ['#eee9f6', '#b7a3df', '#6041b0'],
    },
    tir: {
      label: 'Tourism Intensity Ratio (Visitors / Resident)',
      unit: 'x',
      getValue: (s: StateProfile) => s.sdg_metrics.tir_visitors_per_resident,
      min: 3.0,
      max: 22.0,
      colorRange: ['#eee9f4', '#b9782f', '#ef4444'],
    },
    archetype: {
      label: 'Strategic Typology Archetype',
      unit: '',
      getValue: (s: StateProfile) => s.cluster_id,
      min: 1,
      max: 4,
      colorRange: ['#3b82f6', '#9673c8', '#6d4bc1', '#b9782f'],
    },
  };

  const currentConfig = metricConfigs[selectedMetric];

  // Map ECharts Option
  const mapOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: '#ffffff',
      borderColor: 'rgba(70, 50, 100, 0.16)',
      textStyle: { color: '#241d32', fontSize: 12 },
      formatter: (params: any) => {
        const s = stateProfiles[params.name];
        if (!s) return params.name;
        return `<div style="font-weight: bold; margin-bottom: 4px; font-size: 13px;">${s.state}</div>
          <div>${currentConfig.label}: <strong style="color: #6d4bc1;">${currentConfig.getValue(s)} ${currentConfig.unit}</strong></div>
          <div>Archetype: <span style="color: ${s.archetype_color}; font-weight: 600;">${s.archetype_name}</span></div>
          <div>ALOS: <strong>${s.baseline_2025.alos_days.toFixed(2)} days</strong></div>
          <div>Spend / Night: <strong>RM ${s.baseline_2025.spend_per_night_rm.toFixed(1)}</strong></div>
          <div>Population: <strong>${s.demographics?.total_population_millions?.toFixed(2) || 'N/A'} M</strong></div>
          <div style="font-size: 10px; color: #746d80; margin-top: 4px;">Click to view full diagnostic profile</div>`;
      },
    },
    visualMap: selectedMetric === 'archetype' ? {
      show: true,
      type: 'piecewise',
      bottom: 20,
      left: 20,
      textStyle: { color: '#746d80', fontSize: 11 },
      pieces: [
        { value: 1, label: 'High-Volume Urban Gateway', color: '#3b82f6' },
        { value: 2, label: 'Administrative & Luxury', color: '#9673c8' },
        { value: 3, label: 'Prime Leisure Hotspot', color: '#6d4bc1' },
        { value: 4, label: 'Emerging Extended-Stay', color: '#b9782f' },
      ],
    } : {
      show: true,
      min: currentConfig.min,
      max: currentConfig.max,
      left: 20,
      bottom: 20,
      text: ['High', 'Low'],
      textStyle: { color: '#746d80', fontSize: 11 },
      inRange: { color: currentConfig.colorRange },
      calculable: true,
    },
    series: [
      {
        name: 'Malaysia States',
        type: 'map',
        map: 'malaysia',
        roam: true,
        scaleLimit: { min: 1.0, max: 4.5 },
        zoom: 1.25,
        center: [108.5, 4.0], // Centered between Peninsular and Borneo
        emphasis: {
          label: { show: true, color: '#ffffff', fontWeight: 'bold', fontSize: 11 },
          itemStyle: {
            areaColor: '#6d4bc1',
            borderColor: '#ffffff',
            borderWidth: 1.5,
            shadowBlur: 15,
            shadowColor: 'rgba(109, 75, 193, 0.18)',
          },
        },
        select: {
          label: { show: true, color: '#ffffff', fontWeight: 'bold' },
          itemStyle: { areaColor: '#6d4bc1', borderColor: '#ffffff', borderWidth: 2 },
        },
        itemStyle: {
          areaColor: '#eee9f4',
          borderColor: '#ffffff',
          borderWidth: 0.8,
        },
        data: stateList.map((s) => {
          const isHighlighted = isStateHighlighted(s.state);
          return {
            name: s.state,
            value: currentConfig.getValue(s),
            selected: s.state === selectedStateName,
            itemStyle: isHighlighted ? undefined : { opacity: 0.22 },
          };
        }),
      },
    ],
  };

  // Hexagonal Radar Chart Option for Selected State
  const radarOption = {
    backgroundColor: 'transparent',
    tooltip: {
      backgroundColor: '#ffffff',
      borderColor: 'rgba(70, 50, 100, 0.16)',
      textStyle: { color: '#241d32', fontSize: 11 },
    },
    radar: {
      indicator: [
        { name: 'Stay Duration (ALOS)', max: 100 },
        { name: 'Nightly Yield (RM)', max: 100 },
        { name: 'Accom Intensity', max: 100 },
        { name: 'Leisure Orientation', max: 100 },
        { name: 'Luxury Supply', max: 100 },
        { name: 'Resident Affluence', max: 100 },
      ],
      shape: 'polygon',
      splitNumber: 4,
      axisName: { color: '#746d80', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(70, 50, 100, 0.10)' } },
      splitArea: { show: false },
      axisLine: { lineStyle: { color: 'rgba(70, 50, 100, 0.14)' } },
    },
    series: [
      {
        name: `${activeState.state} Profile`,
        type: 'radar',
        data: [
          {
            value: [
              activeState.radar_scores?.stay_duration ?? 0,
              activeState.radar_scores?.nightly_yield ?? 0,
              activeState.radar_scores?.accom_intensity ?? 0,
              activeState.radar_scores?.leisure_orientation ?? 0,
              activeState.radar_scores?.luxury_supply ?? 0,
              activeState.radar_scores?.resident_affluence ?? 0,
            ],
            name: activeState.state,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: { width: 2, color: activeState.archetype_color },
            itemStyle: { color: activeState.archetype_color },
            areaStyle: {
              color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
                { offset: 0, color: 'rgba(109, 75, 193, 0.14)' },
                { offset: 1, color: 'rgba(109, 75, 193, 0.02)' },
              ]),
            },
          },
        ],
      },
    ],
  };

  // On chart click handler to select state
  const onChartClick = (params: any) => {
    if (params.name && stateProfiles[params.name]) {
      setSelectedStateName(params.name);
    }
  };

  return (
    <div className="space-y-6">
      {/* Metric Selector Bar */}
      <div className="glass-panel p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-stone-900 tracking-tight flex items-center gap-2">
            <Compass className="w-5 h-5 text-violet-700" />
            Accommodation Opportunity & State Archetype Explorer
          </h2>
          <p className="text-xs text-stone-600">
            Select a metric to explore state-level economic value conversion across Malaysia
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {(
            [
              ['accom_share', 'Accom Share (%)'],
              ['spend_per_night', 'Spend / Night (RM)'],
              ['alos', 'Length of Stay (ALOS)'],
              ['tey', 'TEY (RM/day)'],
              ['tvay', 'TVAY (RM/day)'],
              ['gva_intensity', 'GVA Intensity (%)'],
              ['tir', 'Tourism Intensity (SDG)'],
              ['archetype', 'Typology Archetype'],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setSelectedMetric(key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                selectedMetric === key
                  ? 'bg-violet-600/20 text-violet-700 border border-violet-400/40 shadow-sm shadow-violet-300/20'
                  : 'bg-white/60 text-stone-600 border border-violet-100 hover:text-stone-900 hover:bg-violet-50'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* SDG Carrying Capacity & Volume Pressure Filter Pill Strip (Recommendation 5) */}
      <div className="glass-panel p-3 flex flex-wrap items-center justify-between gap-3 bg-white/80 border border-violet-100">
        <div className="flex items-center gap-2 text-xs font-semibold text-stone-700">
          <Filter className="w-3.5 h-3.5 text-violet-700" />
          <span>SDG Strategic Focus Filter:</span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {[
            { id: 'all', label: 'All 16 States', desc: 'Complete national view' },
            { id: 'carrying_capacity', label: '⚠️ Volume Pressure (EPR > 1.5)', desc: 'Melaka, N.Sembilan high day-trip friction' },
            { id: 'high_yield', label: '💎 High-Yield Urban / Premium', desc: 'KL, Penang, Putrajaya with yield > RM70' },
            { id: 'extended_stay', label: '🔄 Extended-Stay / High VFR', desc: 'Kelantan, Perak, Pahang with VFR > 60%' },
            { id: 'leisure', label: '🌿 Prime Leisure Hotspots', desc: 'Sabah, Terengganu, Pahang nature/coastal' },
          ].map((pill) => (
            <button
              key={pill.id}
              onClick={() => setSdgFilter(pill.id as any)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                sdgFilter === pill.id
                  ? 'bg-violet-600 text-slate-950 font-bold shadow-sm shadow-violet-300/30'
                  : 'bg-violet-50/80 text-stone-700 hover:bg-violet-100 hover:text-stone-900 border border-violet-200/60'
              }`}
              title={pill.desc}
            >
              {pill.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Map + State Profile Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Malaysia Choropleth Map (7 cols) */}
        <div className="glass-panel p-5 lg:col-span-7 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-stone-700 uppercase tracking-wider">
              {currentConfig.label} Map
            </span>
            <span className="text-[11px] text-stone-600 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-violet-500"></span>
              Click any state polygon to inspect
            </span>
          </div>

          <div className="h-[480px] w-full">
            <ReactECharts
              option={mapOption}
              style={{ height: '100%', width: '100%' }}
              onEvents={{ click: onChartClick }}
            />
          </div>

          <div className="pt-3 border-t border-violet-100/60 flex items-center justify-between text-xs text-stone-600">
            <span>Projection: WGS84 GeoJSON MultiPolygon (16 States & FTs)</span>
            <span className="text-violet-700 font-medium">Currently Inspected: {activeState.state}</span>
          </div>
        </div>

        {/* Selected State Diagnostic Drawer (5 cols) */}
        <div className="glass-panel p-5 lg:col-span-5 flex flex-col space-y-4">
          {/* Header with Archetype badge & Executive Brief button */}
          <div className="flex items-start justify-between gap-3 border-b border-violet-100/60 pb-3">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-2xl font-extrabold text-stone-900">{activeState.state}</h3>
                <span className="text-xs px-2 py-0.5 rounded bg-violet-50 text-stone-700 font-mono">
                  {activeState.state_code}
                </span>
              </div>
              <span className="text-xs text-stone-600">{activeState.region} Malaysia</span>
            </div>

            <div className="flex flex-col items-end gap-1.5">
              <div
                className="px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1.5 shadow-sm"
                style={{
                  backgroundColor: `${activeState.archetype_color}20`,
                  borderColor: `${activeState.archetype_color}60`,
                  color: activeState.archetype_color,
                  borderWidth: '1px'
                }}
              >
                <Sparkles className="w-3.5 h-3.5" />
                {activeState.archetype_name}
              </div>
              <button
                onClick={() => setShowBriefModal(true)}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-violet-600/20 hover:bg-violet-600/30 text-violet-700 border border-violet-400/40 text-[11px] font-bold transition-all shadow-sm shadow-violet-300/10 cursor-pointer"
                title="Generate printable Executive Policy Brief"
              >
                <FileText className="w-3.5 h-3.5" />
                Executive Brief
              </button>
            </div>
          </div>

          {/* Archetype Description */}
          <p className="text-xs text-stone-700 bg-white/50 p-2.5 rounded-lg border border-violet-100/80 leading-relaxed">
            {activeState.archetype_desc}
          </p>

          {/* Executive State Decision Summary (Sprint 7 Phase 32 & 33) */}
          <div className="p-3.5 rounded-xl bg-gradient-to-br from-violet-50/90 via-white to-purple-50/60 border border-violet-200/80 shadow-sm space-y-2.5">
            <div className="flex items-center justify-between border-b border-violet-100 pb-2">
              <div className="flex items-center gap-1.5 text-xs font-extrabold text-stone-900 uppercase tracking-wider">
                <Target className="w-3.5 h-3.5 text-violet-700" />
                <span>Executive Decision Summary</span>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 font-bold border border-emerald-200">
                Confidence: High (DOSM DTS)
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <div className="p-2 rounded-lg bg-amber-50/70 border border-amber-200/60">
                <span className="text-[10px] font-bold text-amber-900 uppercase block">Primary Constraint</span>
                <strong className="text-stone-900 text-xs block mt-0.5 leading-snug">{decisionSummary.primaryConstraint}</strong>
              </div>
              <div className="p-2 rounded-lg bg-emerald-50/70 border border-emerald-200/60">
                <span className="text-[10px] font-bold text-emerald-900 uppercase block">Primary Opportunity</span>
                <strong className="text-stone-900 text-xs block mt-0.5 leading-snug">{decisionSummary.primaryOpportunity}</strong>
              </div>
            </div>

            {/* Headline KPI Hierarchy (Plan Section 28 / Sprint E) */}
            <div className="p-3 rounded-xl bg-purple-900 text-white flex items-center justify-between shadow-sm">
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] font-bold tracking-wider uppercase px-2 py-0.5 rounded bg-purple-500/30 text-purple-200 border border-purple-400/40">
                    Primary North-Star KPI
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/20 text-blue-200 font-mono">
                    Official Derived Proxy
                  </span>
                </div>
                <div className="text-xs font-semibold text-purple-200 mt-1">Tourism Value-Added Yield (TVAY)</div>
                <div className="text-[10px] text-purple-300/80">Estimated GVA per visitor-day</div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-black font-mono text-amber-300">
                  {decisionSummary.tvay != null ? `RM ${decisionSummary.tvay.toFixed(1)}` : 'N/A'}
                </div>
                <span className="text-[10px] text-purple-200 font-medium">/ visitor-day</span>
              </div>
            </div>

            {/* Secondary Drivers & Physical Constraints Breakdown */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[10px] font-bold text-stone-500 uppercase tracking-wider px-0.5">
                <span>Secondary Drivers</span>
                <span>Physical Constraints</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 text-center text-[11px]">
                <div className="p-1.5 rounded bg-white border border-violet-100">
                  <span className="text-[9px] text-stone-500 block">Gross Yield (TEY)</span>
                  <strong className="font-mono text-xs text-stone-800">RM {decisionSummary.tey.toFixed(1)}</strong>
                  <span className="text-[9px] text-stone-400 block">per day</span>
                </div>
                <div className="p-1.5 rounded bg-white border border-violet-100">
                  <span className="text-[9px] text-stone-500 block">Stay Duration (ALOS)</span>
                  <strong className="font-mono text-xs text-stone-800">{decisionSummary.alos.toFixed(2)}d</strong>
                  <span className="text-[9px] text-stone-400 block">Median: 2.47d</span>
                </div>
                <div className="p-1.5 rounded bg-white border border-violet-100">
                  <span className="text-[9px] text-stone-500 block">Hotel AOR</span>
                  <strong className="font-mono text-xs text-indigo-700">{decisionSummary.aor != null ? `${decisionSummary.aor.toFixed(1)}%` : 'N/A'}</strong>
                  <span className="text-[9px] text-stone-400 block">Occupancy</span>
                </div>
                <div className="p-1.5 rounded bg-white border border-violet-100">
                  <span className="text-[9px] text-stone-500 block">Room Headroom</span>
                  <strong className={`font-mono text-xs ${decisionSummary.headroom != null && decisionSummary.headroom < 10 ? 'text-amber-700' : 'text-emerald-700'}`}>
                    {decisionSummary.headroom != null ? `${decisionSummary.headroom.toFixed(0)}%` : 'N/A'}
                  </strong>
                  <span className="text-[9px] text-stone-400 block">Below 80% ceiling</span>
                </div>
              </div>
            </div>

            {/* Strategic Prescription */}
            <div className="p-2.5 rounded-lg bg-violet-600/10 border border-violet-300/60 text-[11px] text-stone-800 space-y-1">
              <span className="font-bold text-violet-900 block flex items-center gap-1">
                <Compass className="w-3 h-3 text-violet-700" />
                Rule-Based Strategic Recommendation:
              </span>
              <p className="text-stone-700 leading-relaxed">{decisionSummary.prescription}</p>
            </div>
          </div>

          {/* Radar Chart (Value Efficiency Dimensions) */}
          <div>
            <div className="flex items-center justify-between text-xs font-bold text-stone-700 mb-1">
              <span>Value Capability Radar</span>
              <span className="text-[11px] text-stone-600 font-normal">0–100 Normalized Scale</span>
            </div>
            <div className="h-[210px] w-full">
              <ReactECharts option={radarOption} style={{ height: '100%', width: '100%' }} />
            </div>
          </div>

          {/* Typology Quadrant & Mapping Coverage Strip */}
          <div className="flex items-center justify-between p-2.5 rounded-lg bg-violet-50/80 border border-violet-200/60 text-xs">
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] uppercase font-semibold text-stone-600">Typology Quadrant:</span>
              <span className="font-bold text-violet-800">
                {activeState.baseline_2025.yield_typology || activeState.sdg_metrics?.yield_typology || 'N/A'}
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-[11px] font-mono">
              <span className="text-stone-500">TSA Mapping Coverage:</span>
              <span className="px-1.5 py-0.5 rounded bg-white text-violet-700 font-semibold border border-violet-100">
                {activeState.sdg_metrics?.mapping_coverage_pct != null ? `${activeState.sdg_metrics.mapping_coverage_pct.toFixed(1)}%` : 'N/A'}
              </span>
            </div>
          </div>

          {/* Key Metric Cards with Visible Data Status Badges (Phase 30) */}
          <div className="grid grid-cols-4 gap-2 text-center text-xs">
            <div className="p-2 rounded-lg bg-white/80 border border-violet-100">
              <div className="flex items-center justify-between text-[10px] text-stone-600 font-semibold">
                <span>ALOS</span>
                <span className="px-1 py-0.2 rounded text-[8px] font-bold bg-blue-50 text-blue-700 border border-blue-200">OFFICIAL</span>
              </div>
              <div className="text-base font-bold text-stone-900 font-mono mt-0.5">
                {activeState.baseline_2025.alos_days.toFixed(2)}d
              </div>
            </div>

            <div className="p-2 rounded-lg bg-white/80 border border-violet-100">
              <div className="flex items-center justify-between text-[10px] text-stone-600 font-semibold">
                <span>Spend/Night</span>
                <span className="px-1 py-0.2 rounded text-[8px] font-bold bg-purple-50 text-purple-700 border border-purple-200">DERIVED</span>
              </div>
              <div className="text-base font-bold text-violet-700 font-mono mt-0.5">
                RM {activeState.baseline_2025.spend_per_night_rm.toFixed(0)}
              </div>
            </div>

            <div className="p-2 rounded-lg bg-white/80 border border-violet-100">
              <div className="flex items-center justify-between text-[10px] text-stone-600 font-semibold">
                <span>TEY (Yield)</span>
                <span className="px-1 py-0.2 rounded text-[8px] font-bold bg-purple-50 text-purple-700 border border-purple-200">DERIVED</span>
              </div>
              <div className="text-base font-bold text-indigo-600 font-mono mt-0.5">
                RM {(activeState.sdg_metrics?.tey_rm_per_day ?? 0).toFixed(0)}
              </div>
            </div>

            <div className="p-2 rounded-lg bg-white/80 border border-violet-100">
              <div className="flex items-center justify-between text-[10px] text-stone-600 font-semibold">
                <span>TVAY (GVA)</span>
                <span className="px-1 py-0.2 rounded text-[8px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">PROXY</span>
              </div>
              <div className="text-base font-bold text-emerald-700 font-mono mt-0.5">
                RM {(activeState.sdg_metrics?.tvay_rm_per_day ?? 0).toFixed(0)}
              </div>
            </div>
          </div>

          {/* Demographics Age Profile: Official DOSM DTS Visitor Age Classes */}
          <div className="p-3 rounded-lg bg-white/60 border border-violet-100/80 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-stone-700 flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-indigo-600" />
                DTS Visitor Demographic Classes (2025)
              </span>
              <span className="font-mono text-stone-600 text-[11px]">
                {activeState.demographics?.total_population_millions?.toFixed(2) || 'N/A'} M Total ({activeState.demographics?.adult_15plus_thousands ? (activeState.demographics.adult_15plus_thousands / 1000).toFixed(2) : 'N/A'} M Adults 15+)
              </span>
            </div>

            {/* 4 DTS Mutually Exclusive Adult Cohorts (Sum to 100% of adults) */}
            <div className="grid grid-cols-4 gap-1 text-center text-[11px]">
              <div className="p-1.5 rounded bg-stone-50/60 border border-violet-100/50">
                <span className="text-[10px] text-indigo-600 block font-medium">15–24 (Belia)</span>
                <strong className="text-stone-900 font-mono text-xs">
                  {activeState.demographics?.dts_age_classes?.age_15_24_pct != null ? `${activeState.demographics.dts_age_classes.age_15_24_pct}%` : 'N/A'}
                </strong>
                <span className="text-[9px] text-stone-600 block mt-0.5">
                  {activeState.demographics?.dts_age_classes?.age_15_24_k != null ? `${activeState.demographics.dts_age_classes.age_15_24_k.toFixed(0)}k pax` : '—'}
                </span>
              </div>
              <div className="p-1.5 rounded bg-stone-50/60 border border-violet-400/30 bg-violet-50/10">
                <span className="text-[10px] text-violet-700 block font-medium">25–39 (Prime)</span>
                <strong className="text-violet-700 font-mono text-xs">
                  {activeState.demographics?.dts_age_classes?.age_25_39_pct != null ? `${activeState.demographics.dts_age_classes.age_25_39_pct}%` : 'N/A'}
                </strong>
                <span className="text-[9px] text-violet-700/80 block mt-0.5">
                  {activeState.demographics?.dts_age_classes?.age_25_39_k != null ? `${activeState.demographics.dts_age_classes.age_25_39_k.toFixed(0)}k pax` : '—'}
                </span>
              </div>
              <div className="p-1.5 rounded bg-stone-50/60 border border-violet-100/50">
                <span className="text-[10px] text-amber-700 block font-medium">40–54 (Family)</span>
                <strong className="text-stone-900 font-mono text-xs">
                  {activeState.demographics?.dts_age_classes?.age_40_54_pct != null ? `${activeState.demographics.dts_age_classes.age_40_54_pct}%` : 'N/A'}
                </strong>
                <span className="text-[9px] text-stone-600 block mt-0.5">
                  {activeState.demographics?.dts_age_classes?.age_40_54_k != null ? `${activeState.demographics.dts_age_classes.age_40_54_k.toFixed(0)}k pax` : '—'}
                </span>
              </div>
              <div className="p-1.5 rounded bg-stone-50/60 border border-violet-100/50">
                <span className="text-[10px] text-violet-700 block font-medium">≥ 55 (Senior)</span>
                <strong className="text-stone-900 font-mono text-xs">
                  {activeState.demographics?.dts_age_classes?.age_55plus_pct != null ? `${activeState.demographics.dts_age_classes.age_55plus_pct}%` : 'N/A'}
                </strong>
                <span className="text-[9px] text-stone-600 block mt-0.5">
                  {activeState.demographics?.dts_age_classes?.age_55plus_k != null ? `${activeState.demographics.dts_age_classes.age_55plus_k.toFixed(0)}k pax` : '—'}
                </span>
              </div>
            </div>

            {/* 100% MECE Cohort Stack Bar */}
            {activeState.demographics?.dts_age_classes ? (
              <div className="w-full h-1.5 rounded-full bg-violet-50 overflow-hidden flex">
                <div
                  className="bg-indigo-400 h-full"
                  style={{ width: `${activeState.demographics.dts_age_classes.age_15_24_pct || 0}%` }}
                  title={`15-24: ${activeState.demographics.dts_age_classes.age_15_24_pct}%`}
                ></div>
                <div
                  className="bg-violet-500 h-full"
                  style={{ width: `${activeState.demographics.dts_age_classes.age_25_39_pct || 0}%` }}
                  title={`25-39: ${activeState.demographics.dts_age_classes.age_25_39_pct}%`}
                ></div>
                <div
                  className="bg-amber-400 h-full"
                  style={{ width: `${activeState.demographics.dts_age_classes.age_40_54_pct || 0}%` }}
                  title={`40-54: ${activeState.demographics.dts_age_classes.age_40_54_pct}%`}
                ></div>
                <div
                  className="bg-purple-400 h-full"
                  style={{ width: `${activeState.demographics.dts_age_classes.age_55plus_pct || 0}%` }}
                  title={`≥ 55: ${activeState.demographics.dts_age_classes.age_55plus_pct}%`}
                ></div>
              </div>
            ) : (
              <div className="text-[10px] text-stone-400 italic py-0.5">Age cohort distribution unobserved</div>
            )}

            <div className="flex items-center justify-between text-[11px] text-stone-600 pt-0.5">
              <span>Children 0–14: <strong className="text-stone-700 font-mono">{activeState.demographics?.children_pct != null ? `${activeState.demographics.children_pct}% (${activeState.demographics.children_0_14_thousands?.toFixed(0) || '0'}k)` : 'N/A'}</strong></span>
              <span>Dependency Ratio: <strong className="text-stone-700 font-mono">{activeState.demographics?.dependency_ratio != null ? activeState.demographics.dependency_ratio : 'N/A'}</strong></span>
              <span>Resident Median: <strong className="text-violet-700 font-mono">{activeState.baseline_2025.resident_median_income_rm != null ? `RM ${activeState.baseline_2025.resident_median_income_rm.toLocaleString()}` : 'N/A'}</strong></span>
            </div>
          </div>

          {/* Hotel Inventory & Tourist Income Strip */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2.5 rounded-lg bg-white/60 border border-violet-100/80 space-y-1">
              <span className="font-semibold text-stone-700 flex items-center gap-1.5 text-[11px]">
                <Hotel className="w-3.5 h-3.5 text-amber-700" />
                Hotel Capacity
              </span>
              <div className="text-[11px] text-stone-600">
                Total Rooms: <strong className="text-stone-900 font-mono">{activeState.hotel_stars?.total_rooms?.toLocaleString() || 'N/A'}</strong>
              </div>
              <div className="text-[11px] text-stone-600">
                4/5-Star Share: <strong className="text-amber-700 font-mono">{activeState.hotel_stars?.luxury_room_share_pct?.toFixed(1) || 'N/A'}%</strong>
              </div>
            </div>

            <div className="p-2.5 rounded-lg bg-white/60 border border-violet-100/80 space-y-1">
              <span className="font-semibold text-stone-700 flex items-center gap-1.5 text-[11px]">
                <Wallet className="w-3.5 h-3.5 text-violet-700" />
                Inbound Affluence
              </span>
              <div className="text-[11px] text-stone-600">
                Tourist T20 Share: <strong className="text-violet-700 font-mono">{activeState.tourist_income?.t20_pct != null ? `${activeState.tourist_income.t20_pct.toFixed(1)}%` : 'N/A'}</strong>
              </div>
              <div className="text-[11px] text-stone-600">
                Affluence Index: <strong className="text-stone-900 font-mono">{activeState.tourist_income?.affluence_index != null ? activeState.tourist_income.affluence_index.toFixed(0) : 'N/A'}</strong>
              </div>
            </div>
          </div>

          {/* SDG Policy Action Box */}
          <div
            className="p-3 rounded-lg border text-xs space-y-1"
            style={{
              backgroundColor: `${activeState.sdg_metrics.sdg_status_color}10`,
              borderColor: `${activeState.sdg_metrics.sdg_status_color}40`,
            }}
          >
            <div className="font-bold flex items-center gap-1.5" style={{ color: activeState.sdg_metrics.sdg_status_color }}>
              <AlertCircle className="w-3.5 h-3.5" />
              SDG 8.9 Diagnosis: {activeState.sdg_metrics.sdg_diagnosis}
            </div>
            <p className="text-stone-700 text-[11px] leading-relaxed">
              {activeState.sdg_metrics.sdg_policy_action}
            </p>
          </div>
        </div>
      </div>

      {/* Research Question 3 Driver Attribution Card */}
      <div className="glass-panel p-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-4">
          <div>
            <h3 className="text-base font-bold text-stone-900 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-violet-700" />
              Research Question 3: Accommodation Expenditure Driver Attribution
            </h3>
            <p className="text-xs text-stone-600">
              Econometric attribution model explaining cross-state variation in accommodation yield (R² = {driversData.model_metadata?.r_squared != null ? driversData.model_metadata.r_squared.toFixed(3) : '—'}, HC3 Robust Standard Errors)
            </p>
          </div>
          <span className="text-xs px-2.5 py-1 rounded bg-violet-50 text-stone-700 font-mono">
            N = 126 State-Year Panel Observations
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {driversData.feature_attributions.map((driver, idx) => (
            <div
              key={idx}
              className="p-3 rounded-lg bg-white/80 border border-violet-100 hover:border-violet-400/30 transition-all space-y-2"
            >
              <div className="flex items-start justify-between gap-2">
                <span className="font-semibold text-stone-900 text-xs leading-snug">
                  {driver.feature_label}
                </span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                  driver.std_beta > 0 ? 'bg-violet-600/20 text-violet-700' : 'bg-rose-500/20 text-rose-700'
                }`}>
                  β = {driver.std_beta > 0 ? `+${driver.std_beta.toFixed(3)}` : driver.std_beta.toFixed(3)}
                </span>
              </div>

              {/* Progress bar of relative importance */}
              <div className="space-y-1">
                <div className="flex justify-between text-[10px] text-stone-600">
                  <span>Relative Importance</span>
                  <span className="font-bold text-stone-800">{driver.importance_share_pct}%</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-violet-50 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-violet-400 to-violet-400"
                    style={{ width: `${Math.min(100, driver.importance_share_pct * 3)}%` }}
                  ></div>
                </div>
              </div>

              <div className="flex items-center justify-between text-[10px] text-stone-600 pt-1 border-t border-violet-100/40 font-mono">
                <span>p-value: {driver.p_value < 0.001 ? '< 0.001' : driver.p_value.toFixed(3)}</span>
                <span>VIF: {driver.vif.toFixed(2)} (collinearity OK)</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Executive Policy Brief Modal (Recommendation 1) */}
      {showBriefModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white border border-violet-200/80 rounded-2xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-4 px-6 border-b border-violet-100 flex items-center justify-between bg-stone-50/60">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-violet-700" />
                <div>
                  <h3 className="text-base font-bold text-stone-900">
                    Executive Policy Brief: {activeState.state}
                  </h3>
                  <p className="text-xs text-stone-600">
                    Decision-Support Dossier • DOSM TSA & DTS Official Baseline ({selectedYear})
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => window.print()}
                  className="p-1.5 rounded-lg bg-violet-50 hover:bg-violet-100 text-stone-700 hover:text-stone-900 text-xs flex items-center gap-1 transition-all cursor-pointer"
                  title="Print / Save as PDF"
                >
                  <Printer className="w-4 h-4" />
                  <span className="hidden sm:inline">Print</span>
                </button>
                <button
                  onClick={handleDownloadBrief}
                  className="p-1.5 rounded-lg bg-violet-50 hover:bg-violet-100 text-stone-700 hover:text-stone-900 text-xs flex items-center gap-1 transition-all cursor-pointer"
                  title="Download Markdown (.md)"
                >
                  <Download className="w-4 h-4" />
                  <span className="hidden sm:inline">Download .md</span>
                </button>
                <button
                  onClick={handleCopyBrief}
                  className="px-2.5 py-1.5 rounded-lg bg-violet-700 hover:bg-violet-600 text-stone-900 text-xs font-semibold flex items-center gap-1 transition-all cursor-pointer"
                  title="Copy formatted markdown to clipboard"
                >
                  {copiedBrief ? <Check className="w-4 h-4" /> : <FileText className="w-4 h-4" />}
                  <span>{copiedBrief ? 'Copied!' : 'Copy Markdown'}</span>
                </button>
                <button
                  onClick={() => setShowBriefModal(false)}
                  className="p-1.5 rounded-lg bg-violet-50/80 hover:bg-violet-100 text-stone-600 hover:text-stone-900 transition-all ml-1 cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-5 text-sm text-stone-800 print:p-0 print:text-black">
              <div className="space-y-4">
                <div className="border-b border-violet-100 pb-3">
                  <span className="text-xs uppercase tracking-wider text-violet-700 font-bold">
                    MYTourism Value Intelligence State Decision-Support Brief
                  </span>
                  <span className="text-[10px] text-stone-500 block">
                    Prototype based on official Malaysian tourism data
                  </span>
                  <h1 className="text-2xl font-black text-stone-900 mt-1">{activeState.state} Tourism Economic Profile</h1>
                  <p className="text-xs text-stone-600 mt-0.5">
                    Strategic Mandate: Converting Visitor Volume to Domestic Economic Yield • UN SDG 8.9 & 12.b
                  </p>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3 rounded-lg bg-stone-50/60 border border-violet-100">
                    <span className="text-[10px] uppercase text-stone-600 block font-semibold">Classification</span>
                    <strong className="text-violet-700 text-xs">{activeState.archetype_name}</strong>
                  </div>
                  <div className="p-3 rounded-lg bg-stone-50/60 border border-violet-100">
                    <span className="text-[10px] uppercase text-stone-600 block font-semibold">ALOS Duration</span>
                    <strong className="text-stone-900 text-sm font-mono">{activeState.baseline_2025.alos_days.toFixed(2)} days</strong>
                  </div>
                  <div className="p-3 rounded-lg bg-stone-50/60 border border-violet-100">
                    <span className="text-[10px] uppercase text-stone-600 block font-semibold">Nightly Spend</span>
                    <strong className="text-stone-900 text-sm font-mono">RM {activeState.baseline_2025.spend_per_night_rm.toFixed(2)}</strong>
                  </div>
                  <div className="p-3 rounded-lg bg-stone-50/60 border border-violet-100">
                    <span className="text-[10px] uppercase text-stone-600 block font-semibold">Accom Share</span>
                    <strong className="text-indigo-600 text-sm font-mono">{activeState.baseline_2025.accommodation_share_pct.toFixed(1)}%</strong>
                  </div>
                </div>

                {/* Markdown text preview container */}
                <div className="p-4 rounded-xl bg-stone-50/80 border border-violet-100/80 font-mono text-xs leading-relaxed text-stone-700 max-h-[380px] overflow-y-auto whitespace-pre-wrap select-all">
                  {generateMarkdownBrief(activeState)}
                </div>

                <div className="text-[11px] text-stone-600 italic bg-amber-950/20 border border-amber-500/30 p-2.5 rounded-lg">
                  ⚠️ <strong>Mandatory Methodological Notice</strong>: Scenario estimate, not a causal forecast. Derived from official DOSM Tourism Satellite Account (TSA) 2015–2025, Domestic Tourism Survey (DTS) 2018–2025, and Household Income Survey Table 6.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
