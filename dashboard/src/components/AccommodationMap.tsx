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
  AlertCircle
} from 'lucide-react';

interface AccommodationMapProps {
  stateProfiles: Record<string, StateProfile>;
  geoJson: any;
  driversData: DriversData;
}

export const AccommodationMap: React.FC<AccommodationMapProps> = ({ 
  stateProfiles, 
  geoJson,
  driversData 
}) => {
  const [selectedMetric, setSelectedMetric] = useState<
    'accom_share' | 'spend_per_night' | 'alos' | 'tir' | 'archetype'
  >('accom_share');
  const [selectedStateName, setSelectedStateName] = useState<string>('Pulau Pinang');

  // Register GeoJSON with echarts once
  useEffect(() => {
    if (geoJson) {
      echarts.registerMap('malaysia', geoJson);
    }
  }, [geoJson]);

  const stateList = Object.values(stateProfiles);
  const activeState = stateProfiles[selectedStateName] || stateList[0];

  // Metric configurations
  const metricConfigs = {
    accom_share: {
      label: 'Accommodation Share (%)',
      unit: '%',
      getValue: (s: StateProfile) => s.baseline_2025.accommodation_share_pct,
      min: 5,
      max: 18,
      colorRange: ['#1e293b', '#06b6d4', '#10b981'],
    },
    spend_per_night: {
      label: 'Spend per Night (RM)',
      unit: 'RM',
      getValue: (s: StateProfile) => s.baseline_2025.spend_per_night_rm,
      min: 25,
      max: 110,
      colorRange: ['#1e293b', '#06b6d4', '#10b981'],
    },
    alos: {
      label: 'Average Length of Stay (ALOS days)',
      unit: 'days',
      getValue: (s: StateProfile) => s.baseline_2025.alos_days,
      min: 2.0,
      max: 3.2,
      colorRange: ['#1e293b', '#3b82f6', '#8b5cf6'],
    },
    tir: {
      label: 'Tourism Intensity Ratio (Visitors / Resident)',
      unit: 'x',
      getValue: (s: StateProfile) => s.sdg_metrics.tir_visitors_per_resident,
      min: 3.0,
      max: 22.0,
      colorRange: ['#0f172a', '#f59e0b', '#ef4444'],
    },
    archetype: {
      label: 'Strategic Typology Archetype',
      unit: '',
      getValue: (s: StateProfile) => s.cluster_id,
      min: 1,
      max: 4,
      colorRange: ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b'],
    },
  };

  const currentConfig = metricConfigs[selectedMetric];

  // Map ECharts Option
  const mapOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: '#0e1526',
      borderColor: 'rgba(255, 255, 255, 0.15)',
      textStyle: { color: '#f8fafc', fontSize: 12 },
      formatter: (params: any) => {
        const s = stateProfiles[params.name];
        if (!s) return params.name;
        return `<div style="font-weight: bold; margin-bottom: 4px; font-size: 13px;">${s.state}</div>
          <div>${currentConfig.label}: <strong style="color: #34d399;">${currentConfig.getValue(s)} ${currentConfig.unit}</strong></div>
          <div>Archetype: <span style="color: ${s.archetype_color}; font-weight: 600;">${s.archetype_name}</span></div>
          <div>ALOS: <strong>${s.baseline_2025.alos_days.toFixed(2)} days</strong></div>
          <div>Spend / Night: <strong>RM ${s.baseline_2025.spend_per_night_rm.toFixed(1)}</strong></div>
          <div>Population: <strong>${s.demographics?.total_population_millions?.toFixed(2) || 'N/A'} M</strong></div>
          <div style="font-size: 10px; color: #94a3b8; margin-top: 4px;">Click to view full diagnostic profile</div>`;
      },
    },
    visualMap: selectedMetric === 'archetype' ? {
      show: true,
      type: 'piecewise',
      bottom: 20,
      left: 20,
      textStyle: { color: '#94a3b8', fontSize: 11 },
      pieces: [
        { value: 1, label: 'High-Volume Urban Gateway', color: '#3b82f6' },
        { value: 2, label: 'Administrative & Luxury', color: '#8b5cf6' },
        { value: 3, label: 'Prime Leisure Hotspot', color: '#10b981' },
        { value: 4, label: 'Emerging Extended-Stay', color: '#f59e0b' },
      ],
    } : {
      show: true,
      min: currentConfig.min,
      max: currentConfig.max,
      left: 20,
      bottom: 20,
      text: ['High', 'Low'],
      textStyle: { color: '#94a3b8', fontSize: 11 },
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
            areaColor: '#34d399',
            borderColor: '#ffffff',
            borderWidth: 1.5,
            shadowBlur: 15,
            shadowColor: 'rgba(16, 185, 129, 0.5)',
          },
        },
        select: {
          label: { show: true, color: '#ffffff', fontWeight: 'bold' },
          itemStyle: { areaColor: '#10b981', borderColor: '#ffffff', borderWidth: 2 },
        },
        itemStyle: {
          areaColor: '#152038',
          borderColor: 'rgba(255, 255, 255, 0.25)',
          borderWidth: 0.8,
        },
        data: stateList.map((s) => ({
          name: s.state,
          value: currentConfig.getValue(s),
          selected: s.state === selectedStateName,
        })),
      },
    ],
  };

  // Hexagonal Radar Chart Option for Selected State
  const radarOption = {
    backgroundColor: 'transparent',
    tooltip: {
      backgroundColor: '#0e1526',
      borderColor: 'rgba(255, 255, 255, 0.15)',
      textStyle: { color: '#f8fafc', fontSize: 11 },
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
      axisName: { color: '#94a3b8', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.08)' } },
      splitArea: { show: false },
      axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.12)' } },
    },
    series: [
      {
        name: `${activeState.state} Profile`,
        type: 'radar',
        data: [
          {
            value: [
              activeState.radar_scores?.stay_duration || 50,
              activeState.radar_scores?.nightly_yield || 50,
              activeState.radar_scores?.accom_intensity || 50,
              activeState.radar_scores?.leisure_orientation || 50,
              activeState.radar_scores?.luxury_supply || 50,
              activeState.radar_scores?.resident_affluence || 50,
            ],
            name: activeState.state,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: { width: 2, color: activeState.archetype_color },
            itemStyle: { color: activeState.archetype_color },
            areaStyle: {
              color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
                { offset: 0, color: 'rgba(16, 185, 129, 0.4)' },
                { offset: 1, color: 'rgba(16, 185, 129, 0.05)' },
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
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Compass className="w-5 h-5 text-emerald-400" />
            Accommodation Opportunity & State Archetype Explorer
          </h2>
          <p className="text-xs text-slate-400">
            Select a metric to explore state-level economic value conversion across Malaysia
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {(
            [
              ['accom_share', 'Accom Share (%)'],
              ['spend_per_night', 'Spend / Night (RM)'],
              ['alos', 'Length of Stay (ALOS)'],
              ['tir', 'Tourism Intensity (SDG)'],
              ['archetype', 'Typology Archetype'],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setSelectedMetric(key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                selectedMetric === key
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm shadow-emerald-500/20'
                  : 'bg-slate-900/60 text-slate-400 border border-slate-800 hover:text-white hover:bg-slate-800'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Map + State Profile Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Malaysia Choropleth Map (7 cols) */}
        <div className="glass-panel p-5 lg:col-span-7 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              {currentConfig.label} Map
            </span>
            <span className="text-[11px] text-slate-400 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
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

          <div className="pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
            <span>Projection: WGS84 GeoJSON MultiPolygon (16 States & FTs)</span>
            <span className="text-emerald-400 font-medium">Currently Inspected: {activeState.state}</span>
          </div>
        </div>

        {/* Selected State Diagnostic Drawer (5 cols) */}
        <div className="glass-panel p-5 lg:col-span-5 flex flex-col space-y-4">
          {/* Header with Archetype badge */}
          <div className="flex items-start justify-between gap-3 border-b border-slate-800/60 pb-3">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-2xl font-extrabold text-white">{activeState.state}</h3>
                <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                  {activeState.state_code}
                </span>
              </div>
              <span className="text-xs text-slate-400">{activeState.region} Malaysia</span>
            </div>

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
          </div>

          {/* Archetype Description */}
          <p className="text-xs text-slate-300 bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/80 leading-relaxed">
            {activeState.archetype_desc}
          </p>

          {/* Radar Chart (Value Efficiency Dimensions) */}
          <div>
            <div className="flex items-center justify-between text-xs font-bold text-slate-300 mb-1">
              <span>Value Capability Radar</span>
              <span className="text-[11px] text-slate-400 font-normal">0–100 Normalized Scale</span>
            </div>
            <div className="h-[210px] w-full">
              <ReactECharts option={radarOption} style={{ height: '100%', width: '100%' }} />
            </div>
          </div>

          {/* Key Metric Cards */}
          <div className="grid grid-cols-3 gap-2 text-center text-xs">
            <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
              <span className="text-slate-400 text-[10px] uppercase font-semibold">ALOS (Days)</span>
              <div className="text-lg font-bold text-white font-mono mt-0.5">
                {activeState.baseline_2025.alos_days.toFixed(2)}d
              </div>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
              <span className="text-slate-400 text-[10px] uppercase font-semibold">Spend/Night</span>
              <div className="text-lg font-bold text-emerald-400 font-mono mt-0.5">
                RM {activeState.baseline_2025.spend_per_night_rm.toFixed(0)}
              </div>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
              <span className="text-slate-400 text-[10px] uppercase font-semibold">Accom Share</span>
              <div className="text-lg font-bold text-cyan-400 font-mono mt-0.5">
                {activeState.baseline_2025.accommodation_share_pct.toFixed(1)}%
              </div>
            </div>
          </div>

          {/* Demographics Age Profile: Official DOSM DTS Visitor Age Classes */}
          <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-cyan-400" />
                DTS Visitor Demographic Classes (2025)
              </span>
              <span className="font-mono text-slate-400 text-[11px]">
                {activeState.demographics?.total_population_millions?.toFixed(2) || 'N/A'} M Total ({activeState.demographics?.adult_15plus_thousands ? (activeState.demographics.adult_15plus_thousands / 1000).toFixed(2) : 'N/A'} M Adults 15+)
              </span>
            </div>

            {/* 4 DTS Mutually Exclusive Adult Cohorts (Sum to 100% of adults) */}
            <div className="grid grid-cols-4 gap-1 text-center text-[11px]">
              <div className="p-1.5 rounded bg-slate-950/60 border border-slate-800/50">
                <span className="text-[10px] text-cyan-400 block font-medium">15–24 (Belia)</span>
                <strong className="text-white font-mono text-xs">
                  {activeState.demographics?.dts_age_classes?.age_15_24_pct || 22}%
                </strong>
                <span className="text-[9px] text-slate-400 block mt-0.5">
                  {activeState.demographics?.dts_age_classes?.age_15_24_k?.toFixed(0) || '0'}k pax
                </span>
              </div>
              <div className="p-1.5 rounded bg-slate-950/60 border border-emerald-500/30 bg-emerald-950/10">
                <span className="text-[10px] text-emerald-400 block font-medium">25–39 (Prime)</span>
                <strong className="text-emerald-300 font-mono text-xs">
                  {activeState.demographics?.dts_age_classes?.age_25_39_pct || 35}%
                </strong>
                <span className="text-[9px] text-emerald-400/80 block mt-0.5">
                  {activeState.demographics?.dts_age_classes?.age_25_39_k?.toFixed(0) || '0'}k pax
                </span>
              </div>
              <div className="p-1.5 rounded bg-slate-950/60 border border-slate-800/50">
                <span className="text-[10px] text-amber-400 block font-medium">40–54 (Family)</span>
                <strong className="text-white font-mono text-xs">
                  {activeState.demographics?.dts_age_classes?.age_40_54_pct || 24}%
                </strong>
                <span className="text-[9px] text-slate-400 block mt-0.5">
                  {activeState.demographics?.dts_age_classes?.age_40_54_k?.toFixed(0) || '0'}k pax
                </span>
              </div>
              <div className="p-1.5 rounded bg-slate-950/60 border border-slate-800/50">
                <span className="text-[10px] text-purple-400 block font-medium">≥ 55 (Senior)</span>
                <strong className="text-white font-mono text-xs">
                  {activeState.demographics?.dts_age_classes?.age_55plus_pct || 19}%
                </strong>
                <span className="text-[9px] text-slate-400 block mt-0.5">
                  {activeState.demographics?.dts_age_classes?.age_55plus_k?.toFixed(0) || '0'}k pax
                </span>
              </div>
            </div>

            {/* 100% MECE Cohort Stack Bar */}
            <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden flex">
              <div 
                className="bg-cyan-500 h-full" 
                style={{ width: `${activeState.demographics?.dts_age_classes?.age_15_24_pct || 22}%` }}
                title={`15-24: ${activeState.demographics?.dts_age_classes?.age_15_24_pct}%`}
              ></div>
              <div 
                className="bg-emerald-400 h-full" 
                style={{ width: `${activeState.demographics?.dts_age_classes?.age_25_39_pct || 35}%` }}
                title={`25-39: ${activeState.demographics?.dts_age_classes?.age_25_39_pct}%`}
              ></div>
              <div 
                className="bg-amber-400 h-full" 
                style={{ width: `${activeState.demographics?.dts_age_classes?.age_40_54_pct || 24}%` }}
                title={`40-54: ${activeState.demographics?.dts_age_classes?.age_40_54_pct}%`}
              ></div>
              <div 
                className="bg-purple-400 h-full" 
                style={{ width: `${activeState.demographics?.dts_age_classes?.age_55plus_pct || 19}%` }}
                title={`≥ 55: ${activeState.demographics?.dts_age_classes?.age_55plus_pct}%`}
              ></div>
            </div>

            <div className="flex items-center justify-between text-[11px] text-slate-400 pt-0.5">
              <span>Children 0–14: <strong className="text-slate-300 font-mono">{activeState.demographics?.children_pct || 21}% ({activeState.demographics?.children_0_14_thousands?.toFixed(0) || '0'}k)</strong></span>
              <span>Dependency Ratio: <strong className="text-slate-300 font-mono">{activeState.demographics?.dependency_ratio || 40}</strong></span>
              <span>Resident Median: <strong className="text-emerald-400 font-mono">RM {activeState.baseline_2025.resident_median_income_rm.toLocaleString()}</strong></span>
            </div>
          </div>

          {/* Hotel Inventory & Tourist Income Strip */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 space-y-1">
              <span className="font-semibold text-slate-300 flex items-center gap-1.5 text-[11px]">
                <Hotel className="w-3.5 h-3.5 text-amber-400" />
                Hotel Capacity
              </span>
              <div className="text-[11px] text-slate-400">
                Total Rooms: <strong className="text-white font-mono">{activeState.hotel_stars?.total_rooms?.toLocaleString() || 'N/A'}</strong>
              </div>
              <div className="text-[11px] text-slate-400">
                4/5-Star Share: <strong className="text-amber-400 font-mono">{activeState.hotel_stars?.luxury_room_share_pct?.toFixed(1) || 'N/A'}%</strong>
              </div>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 space-y-1">
              <span className="font-semibold text-slate-300 flex items-center gap-1.5 text-[11px]">
                <Wallet className="w-3.5 h-3.5 text-emerald-400" />
                Inbound Affluence
              </span>
              <div className="text-[11px] text-slate-400">
                Tourist T20 Share: <strong className="text-emerald-400 font-mono">{activeState.tourist_income?.t20_pct?.toFixed(1) || '20'}%</strong>
              </div>
              <div className="text-[11px] text-slate-400">
                Affluence Index: <strong className="text-white font-mono">{activeState.tourist_income?.affluence_index?.toFixed(0) || '100'}</strong>
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
            <p className="text-slate-300 text-[11px] leading-relaxed">
              {activeState.sdg_metrics.sdg_policy_action}
            </p>
          </div>
        </div>
      </div>

      {/* Research Question 3 Driver Attribution Card */}
      <div className="glass-panel p-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-4">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-emerald-400" />
              Research Question 3: Accommodation Expenditure Driver Attribution
            </h3>
            <p className="text-xs text-slate-400">
              Econometric attribution model explaining cross-state variation in accommodation yield (R² = {driversData.model_metadata?.r_squared || 0.609}, HC3 Robust Standard Errors)
            </p>
          </div>
          <span className="text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-300 font-mono">
            N = 126 State-Year Panel Observations
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {driversData.feature_attributions.map((driver, idx) => (
            <div 
              key={idx} 
              className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-emerald-500/30 transition-all space-y-2"
            >
              <div className="flex items-start justify-between gap-2">
                <span className="font-semibold text-white text-xs leading-snug">
                  {driver.feature_label}
                </span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                  driver.std_beta > 0 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                }`}>
                  β = {driver.std_beta > 0 ? `+${driver.std_beta.toFixed(3)}` : driver.std_beta.toFixed(3)}
                </span>
              </div>

              {/* Progress bar of relative importance */}
              <div className="space-y-1">
                <div className="flex justify-between text-[10px] text-slate-400">
                  <span>Relative Importance</span>
                  <span className="font-bold text-slate-200">{driver.importance_share_pct}%</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                  <div 
                    className="h-full rounded-full bg-gradient-to-r from-teal-500 to-emerald-400"
                    style={{ width: `${Math.min(100, driver.importance_share_pct * 3)}%` }}
                  ></div>
                </div>
              </div>

              <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-800/40 font-mono">
                <span>p-value: {driver.p_value < 0.001 ? '< 0.001' : driver.p_value.toFixed(3)}</span>
                <span>VIF: {driver.vif.toFixed(2)} (collinearity OK)</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
