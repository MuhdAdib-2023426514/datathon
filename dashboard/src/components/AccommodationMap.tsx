import React, { useState, useEffect, useMemo, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';
import type { StateProfile, DriversData, BookingHotelBenchmarksData, BookingHotelItem } from '../types';
import {
  computeStateBenchmarks,
  computeStateDecisionSummary,
  type StateBenchmarks,
} from '../lib/stateDecisionSummary';
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
  Target,
  Layers,
  MapPin,
  TrendingUp,
  Code,
  Eye,
  ArrowRight,
  ChevronDown,
  RotateCcw,
  Info,
  Star,
  ExternalLink,
  Search,
} from 'lucide-react';

interface AccommodationMapProps {
  stateProfiles: Record<string, StateProfile>;
  geoJson: any;
  driversData: DriversData;
  bookingData?: BookingHotelBenchmarksData | null;
  selectedYear?: number;
  initialState?: string | null;
  onSelectState?: (stateName: string) => void;
  onExploreCorridors?: (destinationState: string) => void;
  onTestScenario?: (destinationState: string) => void;
}

type PrimaryMetric = 'accom_share' | 'spend_per_night' | 'alos';
type MoreMetric = 'tvay' | 'tey' | 'gva_intensity' | 'tir' | 'archetype' | 'aor_pct' | 'hotel_rooms' | 'homestay_operators';
type MetricKey = PrimaryMetric | MoreMetric;

interface MetricConfig {
  id: MetricKey;
  label: string;
  shortLabel: string;
  unit: string;
  isPrimary: boolean;
  getValue: (s: StateProfile) => number | null;
  format: (v: number | null | undefined) => string;
  min?: number;
  max?: number;
  colorRange: string[];
  description: string;
}

export const AccommodationMap: React.FC<AccommodationMapProps> = ({
  stateProfiles,
  geoJson,
  driversData,
  bookingData,
  selectedYear = 2025,
  initialState,
  onSelectState,
  onExploreCorridors,
  onTestScenario,
}) => {
  const stateList = useMemo(() => Object.values(stateProfiles), [stateProfiles]);
  const defaultState = (initialState && stateProfiles[initialState]) ? initialState : 'Pulau Pinang';

  const [selectedMetric, setSelectedMetric] = useState<MetricKey>('accom_share');
  const [selectedStateName, setSelectedStateName] = useState<string>(defaultState);
  const [sdgFilter, setSdgFilter] = useState<'all' | 'high_volume_pressure' | 'high_yield' | 'high_vfr' | 'prime_leisure'>('all');
  const [secondaryTab, setSecondaryTab] = useState<'lodging' | 'booking' | 'demographics' | 'radar'>('lodging');
  const [showMoreMetrics, setShowMoreMetrics] = useState<boolean>(false);
  const [mapRevision, setMapRevision] = useState(0);
  const [showBriefModal, setShowBriefModal] = useState<boolean>(false);
  const [briefViewMode, setBriefViewMode] = useState<'dossier' | 'markdown'>('dossier');
  const [copiedBrief, setCopiedBrief] = useState<boolean>(false);

  // OTA Booking.com Supporting Data states
  const [selectedSubdestSlug, setSelectedSubdestSlug] = useState<string | null>(null);
  const [hotelSearchQuery, setHotelSearchQuery] = useState<string>('');
  const [hotelStarFilter, setHotelStarFilter] = useState<'all' | 'luxury' | '3' | 'budget'>('all');
  const [hotelSortBy, setHotelSortBy] = useState<'rating' | 'price_asc' | 'price_desc' | 'reviews'>('rating');
  const [showAllDestModal, setShowAllDestModal] = useState<boolean>(false);

  const modalRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  // Sync state if initialState changes externally
  useEffect(() => {
    if (initialState && stateProfiles[initialState] && initialState !== selectedStateName) {
      setSelectedStateName(initialState);
    }
    setSelectedSubdestSlug(null);
    setHotelSearchQuery('');
    setHotelStarFilter('all');
  }, [initialState, stateProfiles, selectedStateName]);

  // Register GeoJSON with echarts once
  useEffect(() => {
    if (geoJson) {
      echarts.registerMap('malaysia', geoJson);
    }
  }, [geoJson]);

  // Benchmarks calculated dynamically across all 16 states (independent of filters)
  const benchmarks: StateBenchmarks = useMemo(
    () => computeStateBenchmarks(stateList),
    [stateList]
  );

  const activeState = stateProfiles[selectedStateName] || stateList[0];

  const decisionSummary = useMemo(
    () => computeStateDecisionSummary(activeState, benchmarks),
    [activeState, benchmarks]
  );

  const handleSelectState = (name: string) => {
    if (stateProfiles[name]) {
      setSelectedStateName(name);
      onSelectState?.(name);
    }
  };

  // Keyboard accessibility for modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && showBriefModal) {
        setShowBriefModal(false);
      }
    };
    if (showBriefModal) {
      window.addEventListener('keydown', handleKeyDown);
      closeButtonRef.current?.focus();
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showBriefModal]);

  // Strategic economic focus filters
  const filterDefinitions = [
    {
      id: 'all' as const,
      label: 'All States & Territories',
      criteria: 'Complete national view (16 states and FTs)',
      test: () => true,
    },
    {
      id: 'high_volume_pressure' as const,
      label: 'High Volume Pressure',
      criteria: 'Excursionist Pressure Ratio > 1.5 or Tourism Intensity > 15 visitors/resident',
      test: (s: StateProfile) => (s.sdg_metrics?.epr_ratio ?? 0) > 1.5 || (s.sdg_metrics?.tir_visitors_per_resident ?? 0) > 15,
    },
    {
      id: 'high_yield' as const,
      label: 'High-Yield / Premium',
      criteria: 'Nightly accommodation spend >= national median or core urban/luxury clusters',
      test: (s: StateProfile) =>
        (benchmarks.medianSpendPerNight != null && s.baseline_2025.spend_per_night_rm >= benchmarks.medianSpendPerNight) ||
        s.cluster_id === 1 ||
        s.cluster_id === 2,
    },
    {
      id: 'high_vfr' as const,
      label: 'Extended Stay / High VFR',
      criteria: 'Unpaid informal lodging (VFR) share > 50% of overnight stays',
      test: (s: StateProfile) => (s.lodging_shares?.unpaid_vfr_pct ?? 0) >= 50,
    },
    {
      id: 'prime_leisure' as const,
      label: 'Prime Leisure Hotspots',
      criteria: 'Archetype Cluster 3 (Prime Leisure) or holiday purpose share > 25%',
      test: (s: StateProfile) => s.cluster_id === 3 || (s.purpose_shares?.holiday ?? 0) > 25,
    },
  ];

  const currentFilter = filterDefinitions.find(f => f.id === sdgFilter) || filterDefinitions[0];
  const matchingStates = useMemo(() => stateList.filter(currentFilter.test), [stateList, currentFilter]);
  const isSelectedStateMatching = currentFilter.test(activeState);

  // Metric configurations
  const metricConfigs: Record<MetricKey, MetricConfig> = {
    accom_share: {
      id: 'accom_share',
      label: 'Accommodation Share (% of Total Spending)',
      shortLabel: 'Accommodation Share',
      unit: '%',
      isPrimary: true,
      getValue: (s: StateProfile) => s.baseline_2025.accommodation_share_pct,
      format: (v) => v != null && Number.isFinite(v) ? `${v.toFixed(1)}%` : 'Unavailable',
      min: 5,
      max: 18,
      colorRange: ['#eee9f6', '#b7a3df', '#6041b0'],
      description: 'Commercial accommodation expenditure as a percentage of total domestic visitor spending in destination',
    },
    spend_per_night: {
      id: 'spend_per_night',
      label: 'Nightly Spend per Tourist (RM/night)',
      shortLabel: 'Spend / Night',
      unit: 'RM',
      isPrimary: true,
      getValue: (s: StateProfile) => s.baseline_2025.spend_per_night_rm,
      format: (v) => v != null && Number.isFinite(v) ? `RM ${v.toFixed(1)}` : 'Unavailable',
      min: 25,
      max: 110,
      colorRange: ['#eee9f6', '#b7a3df', '#6041b0'],
      description: 'Commercial lodging expenditure per domestic overnight tourist-night (expenditure / tourist-nights)',
    },
    alos: {
      id: 'alos',
      label: 'Average Length of Stay (ALOS days)',
      shortLabel: 'Stay Duration (ALOS)',
      unit: 'days',
      isPrimary: true,
      getValue: (s: StateProfile) => s.baseline_2025.alos_days,
      format: (v) => v != null && Number.isFinite(v) ? `${v.toFixed(2)} days` : 'Unavailable',
      min: 2.0,
      max: 3.2,
      colorRange: ['#eee9f6', '#b7a3df', '#6041b0'],
      description: 'Official average duration of stay for domestic overnight tourists (days per tourist)',
    },
    tvay: {
      id: 'tvay',
      label: 'Tourism Value-Added Yield (TVAY proxy)',
      shortLabel: 'TVAY (Value Yield)',
      unit: 'RM/day',
      isPrimary: false,
      getValue: (s: StateProfile) => s.sdg_metrics?.tvay_rm_per_day ?? null,
      format: (v) => v != null && Number.isFinite(v) ? `RM ${v.toFixed(1)}/day` : 'Unavailable',
      min: 70,
      max: 180,
      colorRange: ['#eee9f6', '#b7a3df', '#6041b0'],
      description: 'Derived analytical proxy of Gross Value Added generated per domestic visitor-day (ITC × product VAI)',
    },
    tey: {
      id: 'tey',
      label: 'Tourism Economic Yield (TEY gross)',
      shortLabel: 'TEY (Gross Yield)',
      unit: 'RM/day',
      isPrimary: false,
      getValue: (s: StateProfile) => s.sdg_metrics?.tey_rm_per_day ?? null,
      format: (v) => v != null && Number.isFinite(v) ? `RM ${v.toFixed(1)}/day` : 'Unavailable',
      min: 150,
      max: 350,
      colorRange: ['#eee9f6', '#b7a3df', '#6041b0'],
      description: 'Gross domestic expenditure generated per domestic visitor-day (total spending / visitor-days)',
    },
    gva_intensity: {
      id: 'gva_intensity',
      label: 'Tourism GVA Intensity (%)',
      shortLabel: 'GVA Intensity',
      unit: '%',
      isPrimary: false,
      getValue: (s: StateProfile) => s.sdg_metrics?.tourism_gva_intensity_pct ?? s.sdg_metrics?.dvr_retention_rate_pct ?? null,
      format: (v) => v != null && Number.isFinite(v) ? `${v.toFixed(1)}%` : 'Unavailable',
      min: 55,
      max: 65,
      colorRange: ['#eee9f6', '#b7a3df', '#6041b0'],
      description: 'Estimated proportion of destination tourism expenditure retained as domestic Gross Value Added',
    },
    tir: {
      id: 'tir',
      label: 'Tourism Intensity Ratio (Visitors / Resident)',
      shortLabel: 'Tourism Pressure (TIR)',
      unit: 'x',
      isPrimary: false,
      getValue: (s: StateProfile) => s.sdg_metrics?.tir_visitors_per_resident ?? null,
      format: (v) => v != null && Number.isFinite(v) ? `${v.toFixed(1)}x` : 'Unavailable',
      min: 3.0,
      max: 22.0,
      colorRange: ['#eee9f4', '#b9782f', '#ef4444'],
      description: 'Annual domestic visitor arrivals per local resident, indicating relative visitor volume pressure',
    },
    archetype: {
      id: 'archetype',
      label: 'Strategic Typology Archetype',
      shortLabel: 'State Archetype',
      unit: '',
      isPrimary: false,
      getValue: (s: StateProfile) => s.cluster_id,
      format: (_v) => activeState.archetype_name,
      min: 1,
      max: 4,
      colorRange: ['#3b82f6', '#9673c8', '#6d4bc1', '#b9782f'],
      description: 'Ward hierarchical clustering classification based on 6 core economic and lodging dimensions',
    },
    aor_pct: {
      id: 'aor_pct',
      label: 'Hotel Average Occupancy Rate (AOR %, MOTAC 2024)',
      shortLabel: 'Hotel Occupancy (AOR)',
      unit: '%',
      isPrimary: false,
      getValue: (s: StateProfile) => s.motac_hotel_operations_2024?.aor_pct ?? s.baseline_2025?.aor_pct ?? null,
      format: (v) => v != null && Number.isFinite(v) ? `${v.toFixed(1)}%` : 'Unavailable',
      min: 35,
      max: 70,
      colorRange: ['#eee9f6', '#b7a3df', '#6041b0'],
      description: 'Official average hotel room occupancy rate across licensed commercial establishments (MOTAC 2024 Record)',
    },
    hotel_rooms: {
      id: 'hotel_rooms',
      label: 'Total Hotel Room Inventory (MOTAC 2024)',
      shortLabel: 'Hotel Rooms',
      unit: 'rooms',
      isPrimary: false,
      getValue: (s: StateProfile) => s.motac_hotel_operations_2024?.rooms_count ?? s.baseline_2025?.hotel_rooms ?? null,
      format: (v) => v != null && Number.isFinite(v) ? `${v.toLocaleString()} rooms` : 'Unavailable',
      min: 2000,
      max: 65000,
      colorRange: ['#eee9f6', '#b7a3df', '#6041b0'],
      description: 'Official total licensed commercial hotel room supply (MOTAC 2024 Record)',
    },
    homestay_operators: {
      id: 'homestay_operators',
      label: 'Registered Community Homestay Operators (MOTAC 2024)',
      shortLabel: 'Homestay Operators',
      unit: 'operators',
      isPrimary: false,
      getValue: (s: StateProfile) => s.motac_homestay_operations_2024?.no_of_operators ?? null,
      format: (v) => v != null && Number.isFinite(v) ? `${v.toLocaleString()} operators` : '0 (Urban FT)',
      min: 0,
      max: 850,
      colorRange: ['#ecfdf5', '#6ee7b7', '#047857'],
      description: 'Official registered rural homestay operators under Program Pengalaman Homestay Malaysia (MOTAC 2024 Record, SDG 8.9)',
    },
  };

  const currentConfig = metricConfigs[selectedMetric];

  // Comparisons for benchmark bars
  const primaryComparisons = (['alos', 'accom_share', 'spend_per_night'] as const).map(metric => {
    const config = metricConfigs[metric];
    const values = stateList.map(config.getValue).filter((v): v is number => v != null && Number.isFinite(v));
    const selected = config.getValue(activeState);
    const median = metric === 'alos' ? benchmarks.medianAlos
      : metric === 'accom_share' ? benchmarks.medianAccomShare
      : benchmarks.medianSpendPerNight;
    const max = values.length ? Math.max(1, ...values) : 100;
    return { metric, config, selected, median, max };
  });

  // Map ECharts Option
  const mapOption = useMemo(() => {
    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        confine: true,
        backgroundColor: '#ffffff',
        borderColor: 'rgba(70, 50, 100, 0.16)',
        textStyle: { color: '#241d32', fontSize: 12 },
        formatter: (params: any) => {
          const s = stateProfiles[params.name];
          if (!s) return params.name;
          const val = currentConfig.getValue(s);
          const valStr = currentConfig.format(val);
          return `<div style="font-weight: bold; margin-bottom: 4px; font-size: 13px;">${s.state} (${s.region})</div>
            <div>${currentConfig.label}: <strong style="color: #6d4bc1;">${valStr}</strong></div>
            <div>Archetype: <span style="color: ${s.archetype_color}; font-weight: 600;">${s.archetype_name}</span></div>
            <div>Stay Duration (ALOS): <strong>${s.baseline_2025.alos_days.toFixed(2)} days</strong></div>
            <div>Spend / Night: <strong>RM ${s.baseline_2025.spend_per_night_rm.toFixed(1)}</strong></div>
            <div>Tourists: <strong>${s.baseline_2025.tourists_thousands.toLocaleString()}k pax</strong></div>
            <div style="font-size: 10px; color: #746d80; margin-top: 4px;">Click state polygon to inspect full decision profile</div>`;
        },
      },
      visualMap: selectedMetric === 'archetype' ? {
        show: true,
        type: 'piecewise',
        bottom: 0,
        left: 0,
        itemWidth: 10,
        itemHeight: 8,
        textStyle: { color: '#746d80', fontSize: 11 },
        pieces: [
          { value: 1, label: 'Urban Gateway', color: '#3b82f6' },
          { value: 2, label: 'Administrative & Luxury', color: '#9673c8' },
          { value: 3, label: 'Prime Leisure Hotspot', color: '#6d4bc1' },
          { value: 4, label: 'Emerging Extended-Stay', color: '#b9782f' },
        ],
      } : {
        show: true,
        min: currentConfig.min ?? 0,
        max: currentConfig.max ?? 100,
        left: 'center',
        bottom: 0,
        orient: 'horizontal',
        itemWidth: 10,
        itemHeight: 120,
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
          zoom: 1,
          layoutCenter: ['50%', '43%'],
          layoutSize: '92%',
          selectedMode: false,
          emphasis: {
            label: { show: true, color: '#0f172a', fontWeight: 'bold', fontSize: 11 },
            itemStyle: {
              borderColor: '#0f172a',
              borderWidth: 2.0,
              shadowBlur: 10,
              shadowColor: 'rgba(15, 23, 42, 0.25)',
            },
          },
          itemStyle: {
            areaColor: '#eee9f4',
            borderColor: '#ffffff',
            borderWidth: 0.8,
          },
          data: stateList.map((s) => {
            const isSelected = s.state === selectedStateName;
            const isHighlighted = currentFilter.test(s);
            const val = currentConfig.getValue(s);
            return {
              name: s.state,
              value: val != null && Number.isFinite(val) ? val : undefined,
              itemStyle: {
                opacity: isHighlighted ? 1.0 : 0.22,
                borderColor: isSelected ? '#0f172a' : '#ffffff',
                borderWidth: isSelected ? 2.4 : 0.8,
                shadowBlur: isSelected ? 8 : 0,
                shadowColor: isSelected ? 'rgba(15, 23, 42, 0.35)' : 'transparent',
                ...(val == null ? { areaColor: '#e2e8f0' } : {}),
              },
              label: {
                show: isSelected,
                color: '#0f172a',
                fontWeight: 'bold',
                fontSize: 11,
              },
            };
          }),
        },
      ],
    };
  }, [selectedMetric, currentConfig, stateList, selectedStateName, currentFilter, stateProfiles]);

  // Hexagonal Radar Chart Option for Selected State
  const radarOption = useMemo(() => {
    return {
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
  }, [activeState]);

  const onChartClick = (params: any) => {
    if (params.name && stateProfiles[params.name]) {
      handleSelectState(params.name);
    }
  };

  // Generate Executive Policy Brief Markdown content
  const generateMarkdownBrief = (state: StateProfile) => {
    const b = state.baseline_2025;
    const d = state.demographics;
    const sdg = state.sdg_metrics;
    const dts = d?.dts_age_classes;
    const summary = decisionSummary;
    const perf = summary.observedPerformance;
    const hotelOps = state.motac_hotel_operations_2024;
    const homestayOps = state.motac_homestay_operations_2024;

    return `# STATE TOURISM ECONOMIC INTELLIGENCE BRIEF: ${state.state.toUpperCase()}
**MYTourism Value Intelligence — Decision-Support Dossier**
*Official Baseline: DOSM TSA 2015–2025 and DTS 2025*
**Date**: ${new Date().toLocaleDateString('en-MY')} | **Baseline Year**: ${selectedYear}

---

## 1. Executive Decision Summary & Diagnostic Synthesis
- **State Archetype**: ${state.archetype_name} (${state.region} Region)
- **Primary Constraint**: ${summary.primaryConstraint}
- **Primary Opportunity**: ${summary.primaryOpportunity}
- **Action to Test**: ${summary.prescription}
- **Data Coverage & Status**: ${summary.coverage}
- **Analytical Limitations**: ${summary.limitations}

### Empirical Evidence Base (vs Unweighted Medians, N = ${benchmarks.observedCount}):
${summary.evidence.map(e => `- ${e}`).join('\n')}

### Qualified Hypotheses:
${summary.hypotheses.map(h => `- ${h}`).join('\n')}

---

## 2. Core Economic Yield Performance (${selectedYear} Baseline)
- **Total Visitors**: ${b.visitors_thousands.toLocaleString()} thousand visitors
- **Overnight Tourists**: ${b.tourists_thousands.toLocaleString()} thousand tourists
- **Average Length of Stay (ALOS)**: ${b.alos_days.toFixed(2)} days (${perf.alosDiff != null ? (perf.alosDiff > 0 ? `+${perf.alosDiff.toFixed(2)}d above` : perf.alosDiff < 0 ? `${perf.alosDiff.toFixed(2)}d below` : 'at') : ''} benchmark median ${benchmarks.medianAlos?.toFixed(2)}d)
- **Nightly Spend per Tourist**: RM ${b.spend_per_night_rm.toFixed(1)} / night (${perf.spendDiff != null ? (perf.spendDiff > 0 ? `+RM ${perf.spendDiff.toFixed(1)} above` : perf.spendDiff < 0 ? `-RM ${Math.abs(perf.spendDiff).toFixed(1)} below` : 'at') : ''} benchmark median RM ${benchmarks.medianSpendPerNight?.toFixed(1)})
- **Accommodation Share**: ${b.accommodation_share_pct.toFixed(1)}% of visitor expenditure (${perf.accomShareDiff != null ? (perf.accomShareDiff > 0 ? `+${perf.accomShareDiff.toFixed(1)} pp above` : perf.accomShareDiff < 0 ? `${perf.accomShareDiff.toFixed(1)} pp below` : 'at') : ''} benchmark median ${benchmarks.medianAccomShare?.toFixed(1)}%)
- **Tourism Value-Added Yield (TVAY proxy)**: ${perf.tvay != null ? `RM ${perf.tvay.toFixed(1)}/day` : 'Unavailable'}
- **Gross Tourism Economic Yield (TEY)**: RM ${sdg.tey_rm_per_day.toFixed(1)}/day

---

## 3. Physical Lodging Capacity & Operations (MOTAC 2024 Audited Record)
- **Commercial Hotels**: ${hotelOps?.hotels_count ?? 'Unobserved'} hotels | **Total Room Supply**: ${hotelOps?.rooms_count?.toLocaleString() ?? b.hotel_rooms?.toLocaleString() ?? 'Unobserved'} rooms
- **Average Occupancy (AOR)**: ${hotelOps?.aor_pct?.toFixed(1) ?? b.aor_pct?.toFixed(1) ?? 'Unobserved'}% (${summary.thresholdGap.label})
- **Hotel Guest Registrations**: ${hotelOps?.total_hotel_guests != null ? hotelOps.total_hotel_guests.toLocaleString() : 'N/A'} total guests
  - Domestic Hotel Guests: ${hotelOps?.domestic_hotel_guests != null ? hotelOps.domestic_hotel_guests.toLocaleString() : 'N/A'}
  - Foreign Hotel Guests: ${hotelOps?.foreign_hotel_guests != null ? `${hotelOps.foreign_hotel_guests.toLocaleString()} (${hotelOps.foreign_guest_share_pct?.toFixed(1)}% foreign share)` : 'N/A'}
- **MOTAC Community Homestay Program (SDG 8.9)**:
  - Registered Operators: ${homestayOps?.no_of_operators ?? 0} operators in ${homestayOps?.no_of_villages ?? 0} villages (${homestayOps?.no_of_rooms ?? 0} rooms)
  - Homestay Guest Arrivals: ${homestayOps?.total_homestay_guests != null ? homestayOps.total_homestay_guests.toLocaleString() : '0'} total arrivals (${homestayOps?.domestic_homestay_guests?.toLocaleString() ?? '0'} domestic, ${homestayOps?.foreign_homestay_guests?.toLocaleString() ?? '0'} international)
  - Direct Community Income: RM ${homestayOps?.total_income_rm != null ? homestayOps.total_income_rm.toLocaleString() : '0.00'}

---

## 4. Demographics & Visitor Profile (MECE Non-Overlapping)
- **Total Population**: ${d?.total_population_millions != null ? `${d.total_population_millions.toFixed(2)} Million` : 'N/A'}
- **Resident Median Household Income**: RM ${b.resident_median_income_rm.toLocaleString()}
- **Unpaid VFR Lodging Share**: ${state.lodging_shares?.unpaid_vfr_pct != null ? `${state.lodging_shares.unpaid_vfr_pct.toFixed(1)}%` : 'Unobserved'} of overnight stays
- **DTS Adult Age Distribution**:
  - Ages 15–24 (Belia): ${dts?.age_15_24_pct != null ? `${dts.age_15_24_pct.toFixed(1)}%` : 'N/A'}
  - Ages 25–39 (Prime): ${dts?.age_25_39_pct != null ? `${dts.age_25_39_pct.toFixed(1)}%` : 'N/A'}
  - Ages 40–54 (Family): ${dts?.age_40_54_pct != null ? `${dts.age_40_54_pct.toFixed(1)}%` : 'N/A'}
  - Ages ≥ 55 (Senior): ${dts?.age_55plus_pct != null ? `${dts.age_55plus_pct.toFixed(1)}%` : 'N/A'}

---

## 5. Simulated Opportunity (+0.3 Days Stay Extension)
Under a transparent scenario extending Average Length of Stay by +0.3 days:
- **Additional Tourist Nights**: +${(b.tourists_thousands * 0.3).toFixed(1)} thousand nights
- **Incremental Accommodation Expenditure**: +RM ${(b.tourists_thousands * 0.3 * b.spend_per_night_rm / 1000).toFixed(2)} Million
- **Potential Attributable Value-Added Proxy (85.8% TSA Accommodation VAI)**: +RM ${(b.tourists_thousands * 0.3 * b.spend_per_night_rm / 1000 * 0.858).toFixed(2)} Million

> **Mandatory Notice**: Scenario estimate, not a causal forecast.
> This prototype focuses on the economic dimension of sustainable tourism. Environmental and broader social dimensions are future extensions.
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
    a.download = `state_brief_${activeState.state.toLowerCase().replace(/\s+/g, '_')}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Metric Selector Bar: Clean 3-Metric Primary IA + Progressive Disclosure */}
      <div className="glass-panel p-4 flex flex-col gap-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-violet-100/60 pb-3">
          <div>
            <h2 className="text-xl font-bold text-stone-900 tracking-tight flex items-center gap-2">
              <Compass className="w-5 h-5 text-violet-700" />
              Accommodation Opportunity & State Archetype Explorer
            </h2>
            <p className="text-xs text-stone-600 mt-0.5">
              {currentConfig.description}
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-stone-600 font-medium bg-stone-50 px-2.5 py-1 rounded-full border border-stone-200">
            <span className="w-2 h-2 rounded-full bg-violet-600"></span>
            <span>2025 National Baseline</span>
          </div>
        </div>

        {/* Primary 3 Yield Levers + More Indicators Progressive Disclosure */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-bold text-stone-500 uppercase tracking-wider mr-1">
              Primary Levers:
            </span>
            {(['alos', 'accom_share', 'spend_per_night'] as const).map((key) => {
              const cfg = metricConfigs[key];
              const isSelected = selectedMetric === key;
              return (
                <button
                  key={key}
                  type="button"
                  id={`metric-btn-${key}`}
                  aria-pressed={isSelected}
                  onClick={() => setSelectedMetric(key)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-violet-700 text-white shadow-md shadow-violet-300/30'
                      : 'bg-white text-stone-700 border border-violet-100 hover:text-stone-900 hover:bg-violet-50'
                  }`}
                >
                  {cfg.shortLabel}
                </button>
              );
            })}

            {/* Toggle More Indicators */}
            <button
              type="button"
              id="toggle-more-metrics"
              aria-expanded={showMoreMetrics}
              onClick={() => setShowMoreMetrics(!showMoreMetrics)}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                showMoreMetrics || !['alos', 'accom_share', 'spend_per_night'].includes(selectedMetric)
                  ? 'bg-violet-100 text-violet-900 border border-violet-300'
                  : 'bg-stone-50 text-stone-600 border border-stone-200 hover:bg-stone-100'
              }`}
            >
              <span>More Indicators</span>
              <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showMoreMetrics ? 'rotate-180' : ''}`} />
            </button>
          </div>

          <div className="text-[11px] text-stone-500">
            Click map polygon or quick-select to inspect state evidence
          </div>
        </div>

        {/* Secondary Indicators Drawer */}
        {showMoreMetrics && (
          <div className="pt-2 border-t border-violet-100 flex flex-wrap items-center gap-2 animate-fadeIn">
            <span className="text-[11px] font-bold text-stone-500 uppercase tracking-wider mr-1 flex items-center gap-1">
              <Layers className="w-3.5 h-3.5 text-stone-500" />
              Advanced Indicators:
            </span>
            {(['tvay', 'tey', 'gva_intensity', 'tir', 'archetype', 'aor_pct', 'hotel_rooms', 'homestay_operators'] as const).map((key) => {
              const cfg = metricConfigs[key];
              const isSelected = selectedMetric === key;
              return (
                <button
                  key={key}
                  type="button"
                  id={`metric-btn-${key}`}
                  aria-pressed={isSelected}
                  onClick={() => setSelectedMetric(key)}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-violet-600 text-white font-bold shadow-sm'
                      : 'bg-white text-stone-700 border border-stone-200 hover:bg-violet-50'
                  }`}
                >
                  {cfg.shortLabel}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Strategic Focus Filter Strip with Criteria and Count */}
      <div className="glass-panel p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white/90 border border-violet-100">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-bold text-stone-700 flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5 text-violet-700" />
            Economic Focus:
          </span>
          {filterDefinitions.map((pill) => {
            const isSelected = sdgFilter === pill.id;
            return (
              <button
                key={pill.id}
                type="button"
                id={`filter-pill-${pill.id}`}
                aria-pressed={isSelected}
                onClick={() => setSdgFilter(pill.id)}
                className={`px-3 py-1 rounded-full text-xs font-semibold transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-violet-700 text-white shadow-sm'
                    : 'bg-violet-50/80 text-stone-700 hover:bg-violet-100 border border-violet-200/60'
                }`}
                title={pill.criteria}
              >
                {pill.label}
              </button>
            );
          })}
        </div>

        <div className="flex items-center gap-3 text-xs text-stone-600">
          <span className="tabular-nums font-semibold">
            {matchingStates.length} of {stateList.length} states match
          </span>
          {sdgFilter !== 'all' && (
            <button
              type="button"
              onClick={() => setSdgFilter('all')}
              className="text-xs text-violet-700 hover:underline flex items-center gap-1 cursor-pointer"
            >
              <RotateCcw className="w-3 h-3" />
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Outside-Focus Notice if Selected State is Dimmed */}
      {!isSelectedStateMatching && (
        <div className="p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-700 shrink-0" />
            <span>
              <strong>{activeState.state}</strong> does not match the active focus ({currentFilter.label}). It is dimmed on the map but remains selected for inspection.
            </span>
          </div>
          <button
            type="button"
            onClick={() => setSdgFilter('all')}
            className="px-2 py-0.5 rounded bg-amber-200 text-amber-900 font-bold hover:bg-amber-300 text-[11px] shrink-0 cursor-pointer"
          >
            Show All
          </button>
        </div>
      )}

      {/* Main Map + State Profile Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 items-start gap-6">
        {/* Malaysia Choropleth Map (7 cols) */}
        <div className="min-w-0 space-y-4 lg:col-span-7">
          <div className="glass-panel p-4 sm:p-5">
            {/* Map Header with Quick-Selector Dropdown */}
            <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-stone-800 uppercase tracking-wider flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-violet-700" />
                  {currentConfig.label}
                </span>
                <span className="text-[11px] text-stone-500 hidden sm:inline">• Click polygon or pick:</span>
              </div>

              {/* State Quick-Selector Dropdown */}
              <div className="flex items-center gap-2">
                <select
                  id="state-quick-select"
                  value={selectedStateName}
                  onChange={(e) => handleSelectState(e.target.value)}
                  className="text-xs font-bold text-stone-800 bg-white border border-violet-200 rounded-lg px-2.5 py-1 focus:outline-none focus:ring-2 focus:ring-violet-400 shadow-sm cursor-pointer"
                  aria-label="Quick-select Malaysian state or federal territory"
                >
                  {stateList.map((s) => (
                    <option key={s.state} value={s.state}>
                      {s.state} ({s.archetype_name.split(' ')[0]})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="h-[320px] sm:h-[440px] w-full">
              <ReactECharts
                key={mapRevision}
                option={mapOption}
                notMerge={true}
                lazyUpdate={false}
                style={{ height: '100%', width: '100%' }}
                onEvents={{ click: onChartClick }}
              />
            </div>

            <div className="mt-3 pt-3 border-t border-violet-100/60 flex flex-wrap items-center justify-between gap-2 text-xs text-stone-600">
              <button
                id="state-map-reset"
                type="button"
                onClick={() => setMapRevision((v) => v + 1)}
                className="rounded border border-violet-200 px-2 py-1 text-violet-800 hover:bg-violet-50 cursor-pointer"
              >
                Reset map zoom
              </button>
              <div className="flex items-center gap-2">
                <span className="text-xs text-stone-500">Currently Inspected:</span>
                <span className="px-2 py-0.5 rounded bg-violet-100 text-violet-900 font-bold">
                  {activeState.state}
                </span>
              </div>
            </div>
          </div>

          {/* Benchmark Comparison Bars */}
          <section className="glass-panel p-4 sm:p-5" aria-labelledby="state-comparison-heading">
            <h3 id="state-comparison-heading" className="text-base font-bold text-stone-900">
              How does {activeState.state} compare?
            </h3>
            <p className="mt-1 text-xs text-stone-600">
              2025 baseline · Unweighted median across available states and federal territories (N = {benchmarks.observedCount}); not a national aggregate. Filters do not change this benchmark.
            </p>
            <div className="mt-4 space-y-5">
              {primaryComparisons.map(({ metric, config, selected, median, max }) => (
                <div key={metric}>
                  <div className="flex flex-wrap items-baseline justify-between gap-2 text-xs">
                    <span className="font-semibold text-stone-800">{config.label}</span>
                    <span className="font-bold tabular-nums text-violet-800">
                      {config.format(selected)}
                    </span>
                  </div>
                  <div className="relative mt-2 h-2 rounded-full bg-stone-100" aria-hidden="true">
                    <div
                      className="h-full rounded-full bg-violet-600"
                      style={{
                        width: `${selected != null && Number.isFinite(selected) ? Math.max(0, Math.min(100, (selected / max) * 100)) : 0}%`,
                      }}
                    />
                    {median != null && (
                      <span
                        className="absolute -top-1 h-4 w-0.5 bg-stone-700"
                        style={{ left: `${Math.min(100, (median / max) * 100)}%` }}
                        title={`Median benchmark: ${config.format(median)}`}
                      />
                    )}
                  </div>
                  <p className="mt-2 text-xs text-stone-600 flex justify-between">
                    <span>Median benchmark: {config.format(median)}</span>
                    <span>Bar scale: 0–{config.format(max)}</span>
                  </p>
                </div>
              ))}
            </div>
            <p className="mt-4 border-t border-stone-100 pt-3 text-xs text-stone-600">
              Higher values describe performance, not automatically a policy priority. Consider tourist volume demand, paid lodging capture, and physical capacity together.
            </p>
          </section>
        </div>

        {/* Selected State Diagnostic Panel (5 cols) */}
        <div className="glass-panel min-w-0 p-4 sm:p-5 lg:col-span-5 flex flex-col space-y-4">
          {/* Header with Archetype badge & Executive Brief button */}
          <div className="flex flex-wrap items-start justify-between gap-3 border-b border-violet-100/60 pb-3">
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
                  borderWidth: '1px',
                }}
              >
                <Sparkles className="w-3.5 h-3.5" />
                {activeState.archetype_name}
              </div>
              <button
                type="button"
                id="btn-open-brief"
                onClick={() => setShowBriefModal(true)}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-violet-600/20 hover:bg-violet-600/30 text-violet-700 border border-violet-400/40 text-[11px] font-bold transition-all shadow-sm cursor-pointer"
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

          {/* Lead Insight Sentence & 3 Benchmarked Primary Metrics */}
          <div className="p-3.5 rounded-xl bg-gradient-to-br from-violet-50/90 via-white to-purple-50/60 border border-violet-200/80 shadow-sm space-y-3">
            <div className="text-xs font-bold text-stone-900 leading-snug">
              {activeState.state} averages{' '}
              <span className="text-violet-800 font-extrabold">{activeState.baseline_2025.alos_days.toFixed(2)} days</span> stay duration{' '}
              ({decisionSummary.observedPerformance.alosDiff != null ? (
                decisionSummary.observedPerformance.alosDiff > 0
                  ? `+${decisionSummary.observedPerformance.alosDiff.toFixed(2)}d above`
                  : decisionSummary.observedPerformance.alosDiff < 0
                  ? `${decisionSummary.observedPerformance.alosDiff.toFixed(2)}d below`
                  : 'at'
              ) : ''} median) with{' '}
              <span className="text-violet-800 font-extrabold">RM {activeState.baseline_2025.spend_per_night_rm.toFixed(1)}/night</span> accommodation spend.
            </div>

            {/* 3 Core Primary Cards with Benchmarked Differences */}
            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div className="p-2 rounded-lg bg-white border border-violet-100">
                <span className="text-[10px] text-stone-500 block">Stay Duration</span>
                <strong className="text-sm font-bold text-stone-900 block font-mono">
                  {activeState.baseline_2025.alos_days.toFixed(2)}d
                </strong>
                <span className={`text-[10px] font-semibold block mt-0.5 ${
                  decisionSummary.observedPerformance.alosStatus === 'above' ? 'text-emerald-700' : decisionSummary.observedPerformance.alosStatus === 'below' ? 'text-amber-700' : 'text-stone-600'
                }`}>
                  {decisionSummary.observedPerformance.alosDiff != null && decisionSummary.observedPerformance.alosDiff > 0 ? '+' : ''}
                  {decisionSummary.observedPerformance.alosDiff != null ? `${decisionSummary.observedPerformance.alosDiff.toFixed(2)}d vs med` : '—'}
                </span>
              </div>

              <div className="p-2 rounded-lg bg-white border border-violet-100">
                <span className="text-[10px] text-stone-500 block">Accom Share</span>
                <strong className="text-sm font-bold text-violet-800 block font-mono">
                  {activeState.baseline_2025.accommodation_share_pct.toFixed(1)}%
                </strong>
                <span className={`text-[10px] font-semibold block mt-0.5 ${
                  decisionSummary.observedPerformance.accomShareStatus === 'above' ? 'text-emerald-700' : decisionSummary.observedPerformance.accomShareStatus === 'below' ? 'text-amber-700' : 'text-stone-600'
                }`}>
                  {decisionSummary.observedPerformance.accomShareDiff != null && decisionSummary.observedPerformance.accomShareDiff > 0 ? '+' : ''}
                  {decisionSummary.observedPerformance.accomShareDiff != null ? `${decisionSummary.observedPerformance.accomShareDiff.toFixed(1)} pp vs med` : '—'}
                </span>
              </div>

              <div className="p-2 rounded-lg bg-white border border-violet-100">
                <span className="text-[10px] text-stone-500 block">Spend / Night</span>
                <strong className="text-sm font-bold text-indigo-800 block font-mono">
                  RM {activeState.baseline_2025.spend_per_night_rm.toFixed(0)}
                </strong>
                <span className={`text-[10px] font-semibold block mt-0.5 ${
                  decisionSummary.observedPerformance.spendStatus === 'above' ? 'text-emerald-700' : decisionSummary.observedPerformance.spendStatus === 'below' ? 'text-amber-700' : 'text-stone-600'
                }`}>
                  {decisionSummary.observedPerformance.spendDiff != null && decisionSummary.observedPerformance.spendDiff > 0 ? '+' : ''}
                  {decisionSummary.observedPerformance.spendDiff != null ? `RM ${decisionSummary.observedPerformance.spendDiff.toFixed(0)} vs med` : '—'}
                </span>
              </div>
            </div>

            {/* Scale Context */}
            <div className="flex items-center justify-between text-[11px] text-stone-600 pt-1 border-t border-violet-100">
              <span>Visitor Scale: <strong className="text-stone-800">{activeState.baseline_2025.visitors_thousands.toLocaleString()}k</strong> arrivals</span>
              <span>Tourists: <strong className="text-stone-800">{activeState.baseline_2025.tourists_thousands.toLocaleString()}k</strong> overnight</span>
            </div>
          </div>

          {/* Diagnostic Evidence & Actions to Test */}
          <div className="p-3.5 rounded-xl bg-white border border-violet-200/80 shadow-sm space-y-3">
            <div className="flex items-center justify-between border-b border-violet-100 pb-2">
              <span className="text-xs font-extrabold text-stone-900 uppercase tracking-wider flex items-center gap-1.5">
                <Target className="w-3.5 h-3.5 text-violet-700" />
                Strategic Diagnosis & Action
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-50 text-violet-800 font-bold border border-violet-200">
                Official DTS 2025
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <div className="p-2 rounded-lg bg-amber-50/70 border border-amber-200/60">
                <span className="text-[10px] font-bold text-amber-900 uppercase block">Primary Constraint</span>
                <p className="text-stone-900 text-xs mt-0.5 leading-snug">{decisionSummary.primaryConstraint}</p>
              </div>
              <div className="p-2 rounded-lg bg-emerald-50/70 border border-emerald-200/60">
                <span className="text-[10px] font-bold text-emerald-900 uppercase block">Primary Opportunity</span>
                <p className="text-stone-900 text-xs mt-0.5 leading-snug">{decisionSummary.primaryOpportunity}</p>
              </div>
            </div>

            <div className="p-2.5 rounded-lg bg-violet-50/80 border border-violet-200 text-[11px] text-stone-800 space-y-1">
              <span className="font-bold text-violet-900 flex items-center gap-1">
                <Compass className="w-3 h-3 text-violet-700" />
                Proposed Action to Test:
              </span>
              <p className="text-stone-700 leading-relaxed">{decisionSummary.prescription}</p>
            </div>

            {/* Empirical Evidence bullets */}
            <div className="space-y-1 text-[11px] text-stone-600">
              <span className="font-bold text-stone-800 block">Empirical Benchmark Evidence:</span>
              <ul className="list-disc list-inside space-y-0.5">
                {decisionSummary.evidence.map((ev, i) => (
                  <li key={i}>{ev}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Connected Decision Navigation (Phase 4) */}
          <div className="p-3 rounded-xl bg-violet-900 text-white space-y-2.5 shadow-md">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-purple-200 flex items-center gap-1.5">
                <TrendingUp className="w-3.5 h-3.5 text-purple-300" />
                Connected Policy Actions
              </span>
              <span className="text-[10px] text-purple-300">Destination: {activeState.state}</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {onExploreCorridors && (
                <button
                  type="button"
                  id="btn-explore-corridors"
                  onClick={() => onExploreCorridors(activeState.state)}
                  className="flex items-center justify-between px-3 py-2 rounded-lg bg-white/10 hover:bg-white/20 border border-white/20 text-xs font-semibold text-white transition-all cursor-pointer"
                >
                  <span>Explore Corridors</span>
                  <ArrowRight className="w-3.5 h-3.5 text-purple-200" />
                </button>
              )}
              {onTestScenario && (
                <button
                  type="button"
                  id="btn-test-scenario"
                  onClick={() => onTestScenario(activeState.state)}
                  className="flex items-center justify-between px-3 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 border border-violet-400 text-xs font-semibold text-white transition-all cursor-pointer"
                >
                  <span>Simulate Stay Extension</span>
                  <ArrowRight className="w-3.5 h-3.5 text-white" />
                </button>
              )}
            </div>
          </div>

          {/* Secondary Expandable Tabs: Lodging, Demographics, Radar */}
          <div className="space-y-3">
            <div className="flex rounded-lg p-1 bg-stone-100 border border-violet-100">
              <button
                type="button"
                id="tab-lodging"
                onClick={() => setSecondaryTab('lodging')}
                className={`flex-1 py-1 text-xs font-bold rounded-md transition-all cursor-pointer ${
                  secondaryTab === 'lodging'
                    ? 'bg-white text-violet-900 shadow-sm'
                    : 'text-stone-600 hover:text-stone-900'
                }`}
              >
                Lodging & Capacity
              </button>
              <button
                type="button"
                id="tab-booking"
                onClick={() => setSecondaryTab('booking')}
                className={`flex-1 py-1 text-xs font-bold rounded-md transition-all cursor-pointer flex items-center justify-center gap-1 ${
                  secondaryTab === 'booking'
                    ? 'bg-white text-violet-900 shadow-sm'
                    : 'text-stone-600 hover:text-stone-900'
                }`}
              >
                <span>OTA Market Sample</span>
                <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
                  2026
                </span>
              </button>
              <button
                type="button"
                id="tab-demographics"
                onClick={() => setSecondaryTab('demographics')}
                className={`flex-1 py-1 text-xs font-bold rounded-md transition-all cursor-pointer ${
                  secondaryTab === 'demographics'
                    ? 'bg-white text-violet-900 shadow-sm'
                    : 'text-stone-600 hover:text-stone-900'
                }`}
              >
                Demographics
              </button>
              <button
                type="button"
                id="tab-radar"
                onClick={() => setSecondaryTab('radar')}
                className={`flex-1 py-1 text-xs font-bold rounded-md transition-all cursor-pointer ${
                  secondaryTab === 'radar'
                    ? 'bg-white text-violet-900 shadow-sm'
                    : 'text-stone-600 hover:text-stone-900'
                }`}
              >
                Radar Profile
              </button>
            </div>

            {/* TAB: LODGING & CAPACITY (MOTAC 2024 CENSUS + DTS QUALITY) */}
            {secondaryTab === 'lodging' && (() => {
              const hotelOps = activeState.motac_hotel_operations_2024;
              const homestayOps = activeState.motac_homestay_operations_2024;

              return (
                <div className="space-y-3 text-xs animate-fadeIn">
                  {/* Pillar 1: Commercial Hotel Sector (MOTAC 2024 Record) */}
                  <div className="p-3 rounded-xl bg-white border border-violet-100 shadow-xs space-y-2.5">
                    <div className="flex items-center justify-between border-b border-violet-100 pb-2">
                      <div className="flex items-center gap-1.5 font-bold text-stone-900 text-xs">
                        <Hotel className="w-4 h-4 text-violet-700" />
                        <span>Commercial Hotel Supply & Operations</span>
                      </div>
                      <span className="px-1.5 py-0.5 rounded text-[9.5px] font-bold bg-violet-50 text-violet-800 border border-violet-200">
                        MOTAC 2024 Record
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <div className="p-2 rounded-lg bg-stone-50 border border-stone-200/70 space-y-0.5">
                        <span className="text-[10px] text-stone-500 block">Total Room Supply</span>
                        <strong className="text-sm font-bold text-stone-900 font-mono block">
                          {(hotelOps?.rooms_count ?? activeState.hotel_stars?.total_rooms)?.toLocaleString() || 'Unobserved'}
                          <span className="text-[10px] font-normal text-stone-500 ml-1">rooms</span>
                        </strong>
                        <span className="text-[9.5px] text-stone-500 block">
                          Across {hotelOps?.hotels_count ?? activeState.hotel_stars?.total_hotels ?? '—'} hotels
                        </span>
                      </div>

                      <div className="p-2 rounded-lg bg-stone-50 border border-stone-200/70 space-y-0.5">
                        <span className="text-[10px] text-stone-500 block">Average Occupancy (AOR)</span>
                        <strong className="text-sm font-bold text-indigo-800 font-mono block">
                          {(hotelOps?.aor_pct ?? activeState.baseline_2025.aor_pct) != null
                            ? `${(hotelOps?.aor_pct ?? activeState.baseline_2025.aor_pct)!.toFixed(1)}%`
                            : 'N/A'}
                        </strong>
                        <span className={`text-[9.5px] font-semibold block ${decisionSummary.thresholdGap.status === 'below' ? 'text-emerald-700' : 'text-amber-700'}`}>
                          {decisionSummary.thresholdGap.gapPp != null ? `${decisionSummary.thresholdGap.gapPp.toFixed(1)} pp gap to 80% ceiling` : 'Ceiling gap unobserved'}
                        </span>
                      </div>
                    </div>

                    {/* Hotel Guest Volume: Domestic vs Foreign */}
                    <div className="p-2.5 rounded-lg bg-violet-50/50 border border-violet-100/80 space-y-1.5">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-semibold text-stone-700 flex items-center gap-1">
                          <Users className="w-3.5 h-3.5 text-violet-700" />
                          Hotel Guest Registrations:
                        </span>
                        <strong className="font-mono text-violet-950 font-bold">
                          {hotelOps?.total_hotel_guests != null ? `${(hotelOps.total_hotel_guests / 1000).toFixed(1)}k total pax` : 'Unobserved'}
                        </strong>
                      </div>

                      {hotelOps?.total_hotel_guests != null && hotelOps.total_hotel_guests > 0 && (
                        <>
                          <div className="w-full h-1.5 rounded-full flex overflow-hidden bg-stone-200">
                            <div
                              className="bg-violet-600 h-full"
                              style={{ width: `${Math.max(0, 100 - (hotelOps.foreign_guest_share_pct || 0))}%` }}
                              title={`Domestic Guests: ${(hotelOps.domestic_hotel_guests || 0).toLocaleString()}`}
                            />
                            <div
                              className="bg-amber-500 h-full"
                              style={{ width: `${Math.min(100, hotelOps.foreign_guest_share_pct || 0)}%` }}
                              title={`Foreign Guests: ${(hotelOps.foreign_hotel_guests || 0).toLocaleString()}`}
                            />
                          </div>
                          <div className="flex items-center justify-between text-[10px] text-stone-600 pt-0.5">
                            <span className="flex items-center gap-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-violet-600 inline-block" />
                              Domestic: <strong className="font-mono text-stone-800">{hotelOps.domestic_hotel_guests?.toLocaleString()}</strong>
                            </span>
                            <span className="flex items-center gap-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 inline-block" />
                              Foreign: <strong className="font-mono text-amber-900">{hotelOps.foreign_hotel_guests?.toLocaleString()} ({hotelOps.foreign_guest_share_pct?.toFixed(1)}%)</strong>
                            </span>
                          </div>
                        </>
                      )}
                    </div>

                    {/* DTS Survey Star Composition Context */}
                    <div className="flex items-center justify-between text-[10.5px] text-stone-500 pt-1 border-t border-stone-100">
                      <span>4/5★ Luxury Room Share: <strong className="text-amber-700 font-mono">{activeState.hotel_stars?.luxury_room_share_pct?.toFixed(1) || 'N/A'}%</strong></span>
                      <span className="text-[9.5px] text-stone-400">Inventory mix via DOSM DTS</span>
                    </div>
                  </div>

                  {/* Pillar 2: Community Homestay Program (MOTAC 2024 Record, SDG 8.9) */}
                  <div className="p-3 rounded-xl bg-gradient-to-br from-emerald-50/70 via-white to-teal-50/40 border border-emerald-200/80 shadow-xs space-y-2.5">
                    <div className="flex items-center justify-between border-b border-emerald-100 pb-2">
                      <div className="flex items-center gap-1.5 font-bold text-emerald-950 text-xs">
                        <Sparkles className="w-4 h-4 text-emerald-700" />
                        <span>MOTAC Community Homestay Program (SDG 8.9)</span>
                      </div>
                      <span className="px-1.5 py-0.5 rounded text-[9.5px] font-bold bg-emerald-100 text-emerald-900 border border-emerald-300">
                        MOTAC 2024 Record
                      </span>
                    </div>

                    {homestayOps && homestayOps.no_of_operators > 0 ? (
                      <div className="space-y-2">
                        <div className="grid grid-cols-2 gap-2">
                          <div className="p-2 rounded-lg bg-white border border-emerald-100 space-y-0.5">
                            <span className="text-[10px] text-stone-500 block">Registered Operators</span>
                            <strong className="text-sm font-bold text-emerald-900 font-mono block">
                              {homestayOps.no_of_operators.toLocaleString()}
                              <span className="text-[10px] font-normal text-stone-500 ml-1">operators</span>
                            </strong>
                            <span className="text-[9.5px] text-stone-500 block">
                              In {homestayOps.no_of_villages} villages ({homestayOps.no_of_rooms} rooms)
                            </span>
                          </div>

                          <div className="p-2 rounded-lg bg-white border border-emerald-100 space-y-0.5">
                            <span className="text-[10px] text-stone-500 block">Homestay Tourist Arrivals</span>
                            <strong className="text-sm font-bold text-teal-800 font-mono block">
                              {homestayOps.total_homestay_guests.toLocaleString()}
                              <span className="text-[10px] font-normal text-stone-500 ml-1">pax</span>
                            </strong>
                            <span className="text-[9.5px] text-stone-500 block">
                              {homestayOps.domestic_homestay_guests.toLocaleString()} dom • {homestayOps.foreign_homestay_guests.toLocaleString()} int'l
                            </span>
                          </div>
                        </div>

                        {/* Direct Rural Revenue */}
                        <div className="p-2 rounded-lg bg-emerald-100/60 border border-emerald-200 flex items-center justify-between text-[11px]">
                          <div>
                            <span className="text-stone-600 block text-[10px]">Direct Community Receipts:</span>
                            <strong className="text-emerald-900 font-bold font-mono text-xs">
                              RM {homestayOps.total_income_rm.toLocaleString()}
                            </strong>
                          </div>
                          <div className="text-right">
                            <span className="text-stone-600 block text-[10px]">Yield / Guest:</span>
                            <strong className="text-emerald-800 font-mono text-[11px]">
                              RM {(homestayOps.total_income_rm / Math.max(1, homestayOps.total_homestay_guests)).toFixed(1)} / pax
                            </strong>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="p-2.5 rounded-lg bg-stone-50 border border-stone-200 text-center text-[11px] text-stone-600 space-y-0.5">
                        <p className="font-semibold text-stone-800">Urban Federal Territory</p>
                        <p className="text-[10px] text-stone-500">
                          No rural village homestays registered under MOTAC Program Homestay. Visitor demand is absorbed through commercial hotels and urban serviced suites.
                        </p>
                      </div>
                    )}

                    {/* Policy Linkage: Homestay vs Unpaid VFR */}
                    <div className="p-2 rounded-lg bg-stone-50 border border-stone-200 text-[10.5px] text-stone-600 space-y-0.5">
                      <div className="flex justify-between items-center">
                        <span>Unpaid Informal (VFR) Stays:</span>
                        <strong className="font-mono text-stone-900">
                          {activeState.lodging_shares?.unpaid_vfr_pct != null ? `${activeState.lodging_shares.unpaid_vfr_pct.toFixed(1)}% of stays` : 'Unobserved'}
                        </strong>
                      </div>
                      <p className="text-[9.5px] text-stone-500 italic pt-0.5">
                        Policy Lever: Certified homestay expansion formalizes informal family lodging into direct rural household revenue (SDG 8.9).
                      </p>
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* TAB: OTA MARKET SAMPLE (BOOKING.COM SUPPORTING DATA) */}
            {secondaryTab === 'booking' && (() => {
              const stateBooking = bookingData?.states?.[selectedStateName];
              const activeBooking = (selectedSubdestSlug && bookingData?.destinations?.[selectedSubdestSlug])
                ? bookingData.destinations[selectedSubdestSlug]
                : stateBooking;

              if (!bookingData || !activeBooking) {
                return (
                  <div className="p-4 rounded-lg bg-white border border-violet-100 text-center text-xs text-stone-500 space-y-1">
                    <p className="font-semibold text-stone-700">Commercial OTA sample data not loaded</p>
                    <p className="text-[11px] text-stone-400">Supporting Booking.com 2026 dataset is unavailable for {selectedStateName}.</p>
                  </div>
                );
              }

              // Filter & sort hotels in this destination
              const hotels = (activeBooking.hotels || []).filter((h: BookingHotelItem) => {
                if (hotelSearchQuery) {
                  const q = hotelSearchQuery.toLowerCase();
                  const matchName = h.hotel_name.toLowerCase().includes(q);
                  const matchAddr = (h.address || '').toLowerCase().includes(q);
                  if (!matchName && !matchAddr) return false;
                }
                if (hotelStarFilter === 'luxury') return h.stars >= 4;
                if (hotelStarFilter === '3') return h.stars === 3;
                if (hotelStarFilter === 'budget') return h.stars < 3;
                return true;
              }).sort((a: BookingHotelItem, b: BookingHotelItem) => {
                if (hotelSortBy === 'price_asc') return (a.price_myr || 0) - (b.price_myr || 0);
                if (hotelSortBy === 'price_desc') return (b.price_myr || 0) - (a.price_myr || 0);
                if (hotelSortBy === 'reviews') return (b.review_count || 0) - (a.review_count || 0);
                return (b.rating_score || 0) - (a.rating_score || 0);
              });

              return (
                <div className="space-y-3 text-xs animate-fadeIn">
                  {/* Supporting Data & ML Exclusion Banner */}
                  <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-[11px] text-amber-900 space-y-1">
                    <div className="flex items-center justify-between gap-1.5 font-bold text-amber-800">
                      <span className="flex items-center gap-1.5">
                        <AlertCircle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                        Supporting OTA Market Intelligence (Booking.com 2026)
                      </span>
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-200/80 text-amber-900 border border-amber-300">
                        Unvalidated / Non-ML
                      </span>
                    </div>
                    <p className="text-[10.5px] leading-relaxed text-amber-800/90">
                      Sample of commercial online listings (N={activeBooking.sample_size} in {selectedSubdestSlug ? activeBooking.destination_name : selectedStateName}).
                      <strong> Not official DOSM data and excluded from econometric/ML training.</strong> Serves as a commercial rate benchmark.
                    </p>
                  </div>

                  {/* Sub-destination Switcher (e.g. Cameron Highlands / Langkawi Island) */}
                  {stateBooking?.has_subdestinations && (
                    <div className="flex items-center gap-1.5 p-1 bg-stone-100 rounded-lg text-[11px]">
                      <span className="text-stone-500 font-semibold px-1.5">Zone:</span>
                      <button
                        type="button"
                        onClick={() => setSelectedSubdestSlug(null)}
                        className={`px-2.5 py-1 rounded font-semibold transition-all cursor-pointer ${
                          selectedSubdestSlug === null
                            ? 'bg-white text-violet-900 shadow-xs'
                            : 'text-stone-600 hover:text-stone-900'
                        }`}
                      >
                        All {selectedStateName} (N={stateBooking?.sample_size || activeBooking.sample_size})
                      </button>
                      {stateBooking?.subdestinations?.map((slug: string) => {
                        const sub = bookingData.destinations[slug];
                        if (!sub) return null;
                        return (
                          <button
                            key={slug}
                            type="button"
                            onClick={() => setSelectedSubdestSlug(slug)}
                            className={`px-2.5 py-1 rounded font-semibold transition-all cursor-pointer ${
                              selectedSubdestSlug === slug
                                ? 'bg-white text-violet-900 shadow-xs'
                                : 'text-stone-600 hover:text-stone-900'
                            }`}
                          >
                            {sub.destination_name} (N={sub.sample_size})
                          </button>
                        );
                      })}
                    </div>
                  )}

                  {/* Primary Rate & Quality Comparison Grid */}
                  <div className="grid grid-cols-2 gap-2">
                    {/* Commercial Room Rate */}
                    <div className="p-2.5 rounded-lg bg-white border border-violet-100 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-stone-700 flex items-center gap-1 text-[11px]">
                          <Wallet className="w-3.5 h-3.5 text-emerald-600" />
                          Commercial Room Rate
                        </span>
                        <span className="text-[10px] text-stone-400 font-mono">Median</span>
                      </div>
                      <div className="text-base font-bold text-emerald-800 font-mono">
                        RM {activeBooking.median_price_myr?.toFixed(0) || '—'}
                        <span className="text-[10px] font-normal text-stone-500 ml-1">/ room-night</span>
                      </div>
                      <div className="text-[10px] text-stone-500 pt-1 border-t border-stone-100 flex justify-between items-center">
                        <span>DTS Survey Baseline:</span>
                        <strong className="text-stone-700 font-mono">
                          RM {activeState.baseline_2025.spend_per_night_rm?.toFixed(1) || '—'}
                        </strong>
                      </div>
                      <p className="text-[9.5px] text-stone-400 italic leading-tight">
                        DTS covers all stays (including free VFR & budget lodges); Booking.com reflects commercial online inventory.
                      </p>
                    </div>

                    {/* Price Range & Spread */}
                    <div className="p-2.5 rounded-lg bg-white border border-violet-100 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-stone-700 flex items-center gap-1 text-[11px]">
                          <TrendingUp className="w-3.5 h-3.5 text-indigo-600" />
                          Price Spread (IQR)
                        </span>
                        <span className="text-[10px] text-stone-400 font-mono">
                          Mean: RM {activeBooking.mean_price_myr?.toFixed(0)}
                        </span>
                      </div>
                      <div className="text-xs font-bold text-stone-900 font-mono">
                        RM {activeBooking.p25_price_myr?.toFixed(0)} – RM {activeBooking.p75_price_myr?.toFixed(0)}
                      </div>
                      <div className="text-[10px] text-stone-500 pt-1 border-t border-stone-100 flex justify-between items-center">
                        <span>Sample Min – Max:</span>
                        <span className="font-mono text-stone-700">
                          RM {activeBooking.min_price_myr?.toFixed(0)} – {activeBooking.max_price_myr?.toFixed(0)}
                        </span>
                      </div>
                      <div className="text-[10px] text-stone-500 flex justify-between items-center">
                        <span>National OTA Median:</span>
                        <span className="font-mono font-semibold text-violet-900">
                          RM {bookingData.national_benchmark.median_price_myr?.toFixed(0)}
                        </span>
                      </div>
                    </div>

                    {/* Guest Rating & Volume */}
                    <div className="p-2.5 rounded-lg bg-white border border-violet-100 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-stone-700 flex items-center gap-1 text-[11px]">
                          <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
                          Guest Review Score
                        </span>
                        <span className="text-[10px] text-amber-700 font-bold font-mono">
                          {activeBooking.mean_rating?.toFixed(1)} / 10
                        </span>
                      </div>
                      <div className="text-[11px] text-stone-600 flex justify-between">
                        <span>Total Sample Reviews:</span>
                        <strong className="text-stone-900 font-mono">
                          {activeBooking.total_reviews_sample?.toLocaleString()}
                        </strong>
                      </div>
                      <div className="text-[11px] text-stone-600 flex justify-between">
                        <span>National Rating Avg:</span>
                        <strong className="text-violet-900 font-mono">
                          {bookingData.national_benchmark.mean_rating?.toFixed(1)} / 10
                        </strong>
                      </div>
                    </div>

                    {/* Star Tier Composition */}
                    <div className="p-2.5 rounded-lg bg-white border border-violet-100 space-y-1">
                      <span className="font-semibold text-stone-700 flex items-center gap-1 text-[11px]">
                        <Hotel className="w-3.5 h-3.5 text-violet-700" />
                        Sample Star Breakdown
                      </span>
                      <div className="w-full h-2 rounded-full flex overflow-hidden bg-stone-100 mt-1">
                        <div
                          className="bg-amber-500 h-full"
                          style={{ width: `${activeBooking.star_breakdown.luxury_4_5_star_pct}%` }}
                          title={`4-5★ Luxury: ${activeBooking.star_breakdown.luxury_4_5_star_pct}%`}
                        />
                        <div
                          className="bg-indigo-500 h-full"
                          style={{ width: `${activeBooking.star_breakdown.midscale_3_star_pct}%` }}
                          title={`3★ Midscale: ${activeBooking.star_breakdown.midscale_3_star_pct}%`}
                        />
                        <div
                          className="bg-stone-400 h-full"
                          style={{ width: `${activeBooking.star_breakdown.budget_unrated_pct}%` }}
                          title={`Budget / Unrated: ${activeBooking.star_breakdown.budget_unrated_pct}%`}
                        />
                      </div>
                      <div className="grid grid-cols-3 text-[9.5px] text-stone-600 pt-1 font-mono">
                        <div><span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-500 mr-1" />4-5★: {activeBooking.star_breakdown.luxury_4_5_star_pct}%</div>
                        <div><span className="inline-block w-1.5 h-1.5 rounded-full bg-indigo-500 mr-1" />3★: {activeBooking.star_breakdown.midscale_3_star_pct}%</div>
                        <div><span className="inline-block w-1.5 h-1.5 rounded-full bg-stone-400 mr-1" />Other: {activeBooking.star_breakdown.budget_unrated_pct}%</div>
                      </div>
                    </div>
                  </div>

                  {/* Guest Experience Subscores Breakdown */}
                  <div className="p-2.5 rounded-lg bg-white border border-violet-100 space-y-2">
                    <span className="font-semibold text-stone-700 text-[11px] block">
                      Guest Experience Subscores (Sample Average out of 10)
                    </span>
                    <div className="grid grid-cols-3 gap-2">
                      {[
                        { label: 'Cleanliness', val: activeBooking.subscores_avg.cleanliness },
                        { label: 'Comfort', val: activeBooking.subscores_avg.comfort },
                        { label: 'Location', val: activeBooking.subscores_avg.location },
                        { label: 'Value / Money', val: activeBooking.subscores_avg.value_for_money },
                        { label: 'Facilities', val: activeBooking.subscores_avg.facilities },
                        { label: 'Staff Service', val: activeBooking.subscores_avg.staff },
                      ].map((sub, sidx) => (
                        <div key={sidx} className="p-1.5 rounded bg-stone-50 border border-stone-200/60 text-[10px]">
                          <div className="flex justify-between text-stone-600 mb-0.5">
                            <span>{sub.label}</span>
                            <span className="font-bold text-stone-900 font-mono">
                              {sub.val != null ? sub.val.toFixed(1) : '—'}
                            </span>
                          </div>
                          <div className="w-full h-1 rounded-full bg-stone-200 overflow-hidden">
                            <div
                              className="h-full rounded-full bg-violet-600"
                              style={{ width: `${Math.min(100, ((sub.val || 0) / 10) * 100)}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Top Amenities Chips */}
                  {Object.keys(activeBooking.top_amenities || {}).length > 0 && (
                    <div className="p-2 rounded-lg bg-stone-50 border border-stone-200 space-y-1 text-[11px]">
                      <span className="text-stone-600 font-semibold">Top Amenities in Market Sample:</span>
                      <div className="flex flex-wrap gap-1 pt-1">
                        {Object.entries(activeBooking.top_amenities).map(([fac, count], fidx) => (
                          <span
                            key={fidx}
                            className="px-2 py-0.5 rounded-full text-[10px] bg-white text-stone-700 border border-stone-200 font-medium"
                          >
                            {fac} <span className="text-stone-400 font-mono">({count})</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Interactive Sample Hotel Explorer */}
                  <div className="p-3 rounded-lg bg-white border border-violet-100 space-y-2.5">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-stone-900 text-xs flex items-center gap-1.5">
                        <Hotel className="w-3.5 h-3.5 text-violet-700" />
                        Sampled Hotel Listings ({hotels.length} of {activeBooking.sample_size})
                      </span>
                      <button
                        type="button"
                        onClick={() => setShowAllDestModal(true)}
                        className="text-[11px] font-semibold text-violet-700 hover:text-violet-900 hover:underline cursor-pointer flex items-center gap-1"
                      >
                        <span>Compare All 18 Destinations</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </div>

                    {/* Search and Filters */}
                    <div className="flex flex-wrap gap-2 text-[11px]">
                      <div className="relative flex-1 min-w-[140px]">
                        <Search className="w-3 h-3 text-stone-400 absolute left-2 top-2.5" />
                        <input
                          type="text"
                          placeholder="Search hotel name or area..."
                          value={hotelSearchQuery}
                          onChange={(e) => setHotelSearchQuery(e.target.value)}
                          className="w-full pl-7 pr-2 py-1 rounded bg-stone-50 border border-stone-200 text-stone-800 text-[11px] focus:outline-none focus:border-violet-500"
                        />
                      </div>

                      <select
                        value={hotelStarFilter}
                        onChange={(e) => setHotelStarFilter(e.target.value as any)}
                        className="px-2 py-1 rounded bg-stone-50 border border-stone-200 text-stone-700 text-[11px] cursor-pointer"
                      >
                        <option value="all">All Stars</option>
                        <option value="luxury">Luxury (4-5★)</option>
                        <option value="3">Midscale (3★)</option>
                        <option value="budget">Budget / Other</option>
                      </select>

                      <select
                        value={hotelSortBy}
                        onChange={(e) => setHotelSortBy(e.target.value as any)}
                        className="px-2 py-1 rounded bg-stone-50 border border-stone-200 text-stone-700 text-[11px] cursor-pointer"
                      >
                        <option value="rating">Sort: Highest Rated</option>
                        <option value="price_asc">Sort: Price Low → High</option>
                        <option value="price_desc">Sort: Price High → Low</option>
                        <option value="reviews">Sort: Most Reviews</option>
                      </select>
                    </div>

                    {/* Hotel Items Scrollable List */}
                    <div className="max-h-[260px] overflow-y-auto space-y-1.5 pr-1 divide-y divide-stone-100">
                      {hotels.length === 0 ? (
                        <p className="text-center text-stone-400 py-4 text-[11px]">No hotels match the selected filter.</p>
                      ) : (
                        hotels.map((hotel: BookingHotelItem) => (
                          <div
                            key={hotel.hotel_id}
                            className="pt-2 first:pt-0 pb-1.5 flex items-start justify-between gap-2 hover:bg-stone-50/60 p-1.5 rounded transition-colors"
                          >
                            <div className="space-y-0.5 flex-1 min-w-0">
                              <div className="flex items-center gap-1.5 flex-wrap">
                                <span className="font-semibold text-stone-900 text-xs truncate max-w-[260px]" title={hotel.hotel_name}>
                                  {hotel.hotel_name}
                                </span>
                                {hotel.stars > 0 && (
                                  <span className="px-1.5 py-0.2 rounded text-[9.5px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                                    {hotel.stars}★
                                  </span>
                                )}
                                {hotel.sustainable_badge && (
                                  <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                                    Sustainable
                                  </span>
                                )}
                              </div>
                              <p className="text-[10px] text-stone-500 truncate" title={hotel.address || ''}>
                                {hotel.address || hotel.distance_downtown || 'Malaysia'}
                              </p>
                              {hotel.popular_facilities && hotel.popular_facilities.length > 0 && (
                                <div className="flex flex-wrap gap-1 pt-0.5">
                                  {hotel.popular_facilities.slice(0, 3).map((f, fidx) => (
                                    <span key={fidx} className="text-[9px] text-stone-500 bg-stone-100 px-1.5 py-0.2 rounded">
                                      {f}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>

                            <div className="text-right shrink-0 space-y-1">
                              <div className="text-xs font-bold text-emerald-800 font-mono">
                                {hotel.price_myr ? `RM ${hotel.price_myr.toFixed(0)}` : '—'}
                              </div>
                              {hotel.rating_score != null && (
                                <div className="text-[10px] text-stone-600 font-mono">
                                  <span className="font-bold text-stone-900">{hotel.rating_score.toFixed(1)}</span>
                                  <span className="text-stone-400">/10</span>
                                  {hotel.review_count != null && (
                                    <span className="text-stone-400 block text-[9px]">
                                      ({hotel.review_count.toLocaleString()} rev)
                                    </span>
                                  )}
                                </div>
                              )}
                              {hotel.booking_url && (
                                <a
                                  href={hotel.booking_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1 text-[9.5px] text-violet-700 hover:text-violet-900 font-medium hover:underline pt-0.5 cursor-pointer"
                                >
                                  <span>View listing</span>
                                  <ExternalLink className="w-2.5 h-2.5" />
                                </a>
                              )}
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* TAB: DEMOGRAPHICS */}
            {secondaryTab === 'demographics' && (
              <div className="p-3 rounded-lg bg-white border border-violet-100 space-y-2 text-xs animate-fadeIn">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-stone-700 flex items-center gap-1.5">
                    <Users className="w-3.5 h-3.5 text-indigo-600" />
                    DTS Visitor Age Classes (100% MECE)
                  </span>
                  <span className="font-mono text-stone-600 text-[11px]">
                    Pop: {activeState.demographics?.total_population_millions?.toFixed(2) || 'N/A'}M
                  </span>
                </div>

                <div className="grid grid-cols-4 gap-1 text-center text-[11px]">
                  <div className="p-1.5 rounded bg-stone-50 border border-stone-200">
                    <span className="text-[9px] text-stone-500 block">15–24 (Belia)</span>
                    <strong className="text-stone-900 font-mono text-xs">
                      {activeState.demographics?.dts_age_classes?.age_15_24_pct != null ? `${activeState.demographics.dts_age_classes.age_15_24_pct}%` : 'N/A'}
                    </strong>
                  </div>
                  <div className="p-1.5 rounded bg-violet-50 border border-violet-200">
                    <span className="text-[9px] text-violet-700 block font-semibold">25–39 (Prime)</span>
                    <strong className="text-violet-800 font-mono text-xs">
                      {activeState.demographics?.dts_age_classes?.age_25_39_pct != null ? `${activeState.demographics.dts_age_classes.age_25_39_pct}%` : 'N/A'}
                    </strong>
                  </div>
                  <div className="p-1.5 rounded bg-stone-50 border border-stone-200">
                    <span className="text-[9px] text-stone-500 block">40–54 (Family)</span>
                    <strong className="text-stone-900 font-mono text-xs">
                      {activeState.demographics?.dts_age_classes?.age_40_54_pct != null ? `${activeState.demographics.dts_age_classes.age_40_54_pct}%` : 'N/A'}
                    </strong>
                  </div>
                  <div className="p-1.5 rounded bg-stone-50 border border-stone-200">
                    <span className="text-[9px] text-stone-500 block">≥ 55 (Senior)</span>
                    <strong className="text-stone-900 font-mono text-xs">
                      {activeState.demographics?.dts_age_classes?.age_55plus_pct != null ? `${activeState.demographics.dts_age_classes.age_55plus_pct}%` : 'N/A'}
                    </strong>
                  </div>
                </div>

                <div className="flex items-center justify-between text-[11px] text-stone-600 pt-1 border-t border-stone-100">
                  <span>Resident Median Income: <strong className="text-violet-700 font-mono">RM {activeState.baseline_2025.resident_median_income_rm.toLocaleString()}</strong></span>
                  <span>Avg Household: <strong className="text-stone-800 font-mono">{activeState.demographics?.avg_household_size?.toFixed(1) || 'N/A'} pax</strong></span>
                </div>
              </div>
            )}

            {/* TAB: RADAR */}
            {secondaryTab === 'radar' && (
              <div className="p-3 rounded-xl bg-white border border-violet-100 animate-fadeIn">
                <div className="flex items-center justify-between text-xs font-bold text-stone-700 mb-1">
                  <span className="flex items-center gap-1">
                    <Sparkles className="w-3.5 h-3.5 text-violet-700" />
                    Value Capability Radar
                  </span>
                  <span className="text-[11px] text-stone-500 font-normal">0–100 Normalized Scale</span>
                </div>
                <div className="h-[200px] w-full">
                  <ReactECharts option={radarOption} style={{ height: '100%', width: '100%' }} />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Research Question 3 Driver Attribution Card (Phase 5 Truthful Scales) */}
      <div className="glass-panel p-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-4">
          <div>
            <h3 className="text-base font-bold text-stone-900 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-violet-700" />
              Factors Associated with Accommodation Spending (RQ3 Panel Model)
            </h3>
            <p className="text-xs text-stone-600">
              Dependent variable: <span className="font-mono font-semibold">{driversData.model_metadata?.dependent_variable || 'ln(Accom Spend per Tourist RM)'}</span> (R² = {driversData.model_metadata?.r_squared != null ? driversData.model_metadata.r_squared.toFixed(3) : '—'}, HC3 Robust Standard Errors)
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs px-2.5 py-1 rounded bg-violet-50 text-stone-700 font-mono">
              N = {driversData.model_metadata?.n_observations || 126} State-Year Panel Observations
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {driversData.feature_attributions.map((driver, idx) => {
            const importancePct = Math.min(100, Math.max(0, driver.importance_share_pct));

            return (
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

                {/* Progress bar of relative importance (TRUTHFUL 1:1 SCALE) */}
                <div className="space-y-1">
                  <div className="flex justify-between text-[10px] text-stone-600">
                    <span>Relative Importance Share</span>
                    <span className="font-bold text-stone-800">{driver.importance_share_pct.toFixed(1)}%</span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-stone-100 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-violet-400 to-violet-600"
                      style={{ width: `${importancePct}%` }}
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between text-[10px] text-stone-500 pt-1 border-t border-violet-100/40 font-mono">
                  <span>p-value: {driver.p_value < 0.001 ? '< 0.001' : driver.p_value.toFixed(3)}</span>
                  <span>VIF: {driver.vif.toFixed(2)}</span>
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-3 text-[11px] text-stone-500 flex items-start gap-1.5">
          <Info className="w-3.5 h-3.5 text-stone-400 shrink-0 mt-0.5" />
          <span>
            Attributions represent standardized regression coefficients (relative share based on |β| weights) explaining cross-state accommodation spending. Associations describe historical empirical relationships and do not imply causal guarantees.
          </span>
        </div>
      </div>

      {/* Accessible Executive Policy Brief Modal Dialog */}
      {showBriefModal && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="brief-title"
          aria-describedby="brief-desc"
          ref={modalRef}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn"
        >
          <div className="bg-white border border-violet-200 rounded-2xl w-full max-w-4xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-4 px-6 border-b border-violet-100 flex flex-wrap items-center justify-between gap-3 bg-stone-50">
              <div className="flex items-center gap-2.5">
                <ShieldCheck className="w-5 h-5 text-violet-700" />
                <div>
                  <h3 id="brief-title" className="text-base font-bold text-stone-900 flex items-center gap-2">
                    <span>Executive Policy Brief: {activeState.state}</span>
                    <span className="text-[11px] px-2 py-0.5 rounded-full bg-violet-100 text-violet-800 font-semibold">
                      {activeState.archetype_name}
                    </span>
                  </h3>
                  <p id="brief-desc" className="text-xs text-stone-500">
                    Decision-Support Dossier • Official DOSM Baseline ({selectedYear})
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {/* View Mode Toggle: Formatted Dossier vs Raw Markdown */}
                <div className="flex rounded-lg p-0.5 bg-stone-200 border border-stone-300 mr-1">
                  <button
                    type="button"
                    onClick={() => setBriefViewMode('dossier')}
                    className={`px-2.5 py-1 text-xs font-bold rounded-md flex items-center gap-1 transition-all cursor-pointer ${
                      briefViewMode === 'dossier'
                        ? 'bg-white text-violet-900 shadow-sm'
                        : 'text-stone-600 hover:text-stone-900'
                    }`}
                  >
                    <Eye className="w-3.5 h-3.5 text-violet-700" />
                    <span>Dossier</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setBriefViewMode('markdown')}
                    className={`px-2.5 py-1 text-xs font-bold rounded-md flex items-center gap-1 transition-all cursor-pointer ${
                      briefViewMode === 'markdown'
                        ? 'bg-white text-violet-900 shadow-sm'
                        : 'text-stone-600 hover:text-stone-900'
                    }`}
                  >
                    <Code className="w-3.5 h-3.5 text-stone-500" />
                    <span>Raw MD</span>
                  </button>
                </div>

                <button
                  type="button"
                  onClick={() => window.print()}
                  className="p-1.5 rounded-lg bg-stone-100 hover:bg-stone-200 text-stone-700 text-xs flex items-center gap-1 transition-all cursor-pointer"
                  title="Print / Save as PDF"
                >
                  <Printer className="w-4 h-4" />
                  <span className="hidden sm:inline">Print</span>
                </button>
                <button
                  type="button"
                  onClick={handleDownloadBrief}
                  className="p-1.5 rounded-lg bg-stone-100 hover:bg-stone-200 text-stone-700 text-xs flex items-center gap-1 transition-all cursor-pointer"
                  title="Download Markdown (.md)"
                >
                  <Download className="w-4 h-4" />
                  <span className="hidden sm:inline">Download</span>
                </button>
                <button
                  type="button"
                  onClick={handleCopyBrief}
                  className="btn-primary gap-1 px-2.5 py-1.5 text-xs cursor-pointer"
                  title="Copy markdown to clipboard"
                >
                  {copiedBrief ? <Check className="w-4 h-4" /> : <FileText className="w-4 h-4" />}
                  <span>{copiedBrief ? 'Copied!' : 'Copy MD'}</span>
                </button>
                <button
                  type="button"
                  ref={closeButtonRef}
                  onClick={() => setShowBriefModal(false)}
                  aria-label="Close Executive Policy Brief"
                  className="p-1.5 rounded-lg bg-stone-100 hover:bg-stone-200 text-stone-600 hover:text-stone-900 transition-all ml-1 cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-5 text-sm text-stone-800">
              {briefViewMode === 'dossier' ? (
                <div className="space-y-6">
                  <div className="border-b border-violet-200 pb-4">
                    <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-stone-500 mb-1">
                      <span className="font-bold text-violet-800 uppercase tracking-wider">
                        MYTourism Value Intelligence — Decision-Support Brief
                      </span>
                      <span>Date: {new Date().toLocaleDateString('en-MY')} · Baseline Year: {selectedYear}</span>
                    </div>
                    <h1 className="text-2xl font-black text-stone-900">
                      {activeState.state} State Tourism Economic Dossier
                    </h1>
                    <p className="text-xs text-stone-600 mt-1">
                      Objective: Identifying Opportunities to Convert Demand into Overnight Economic Value
                    </p>
                  </div>

                  {/* Section 1: Strategic Synthesis */}
                  <div className="p-4 rounded-xl bg-violet-50 border border-violet-200 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-extrabold text-violet-900 uppercase tracking-wider flex items-center gap-1.5">
                        <Target className="w-4 h-4 text-violet-700" />
                        1. Diagnostic Synthesis & Proposed Action
                      </span>
                      <span className="text-[11px] font-mono font-semibold text-stone-700 bg-white px-2 py-0.5 rounded border border-violet-100">
                        {decisionSummary.coverage}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                      <div className="p-2.5 rounded-lg bg-white border border-amber-200">
                        <span className="text-[10px] font-bold text-amber-900 uppercase block">Primary Constraint</span>
                        <strong className="text-stone-900 text-xs block mt-0.5">{decisionSummary.primaryConstraint}</strong>
                      </div>
                      <div className="p-2.5 rounded-lg bg-white border border-emerald-200">
                        <span className="text-[10px] font-bold text-emerald-900 uppercase block">Primary Opportunity</span>
                        <strong className="text-stone-900 text-xs block mt-0.5">{decisionSummary.primaryOpportunity}</strong>
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-white border border-violet-200 text-xs space-y-1">
                      <span className="font-bold text-violet-900 flex items-center gap-1">
                        <Compass className="w-3.5 h-3.5 text-violet-700" />
                        Action to Test:
                      </span>
                      <p className="text-stone-700 leading-relaxed">{decisionSummary.prescription}</p>
                    </div>

                    <div className="text-xs text-stone-600">
                      <span className="font-bold text-stone-800">Empirical Evidence Base (vs Medians):</span>
                      <ul className="list-disc list-inside mt-1 space-y-0.5 text-[11px]">
                        {decisionSummary.evidence.map((ev, i) => (
                          <li key={i}>{ev}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Section 2: Baseline Performance & Opportunity */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold text-stone-900 uppercase tracking-wider flex items-center gap-1.5">
                      <TrendingUp className="w-4 h-4 text-violet-700" />
                      2. Economic Yield & Simulated Opportunity (+0.3d Stay Extension)
                    </h4>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center text-xs">
                      <div className="p-3 rounded-lg bg-stone-50 border border-violet-100">
                        <span className="text-[10px] text-stone-500 uppercase block">Stay Duration (ALOS)</span>
                        <strong className="text-stone-900 text-base font-mono block mt-0.5">
                          {activeState.baseline_2025.alos_days.toFixed(2)}d
                        </strong>
                        <span className="text-[10px] text-stone-500">Median: {benchmarks.medianAlos?.toFixed(2)}d</span>
                      </div>
                      <div className="p-3 rounded-lg bg-stone-50 border border-violet-100">
                        <span className="text-[10px] text-stone-500 uppercase block">Nightly Spend</span>
                        <strong className="text-stone-900 text-base font-mono block mt-0.5">
                          RM {activeState.baseline_2025.spend_per_night_rm.toFixed(1)}
                        </strong>
                        <span className="text-[10px] text-stone-500">Median: RM {benchmarks.medianSpendPerNight?.toFixed(1)}</span>
                      </div>
                      <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200">
                        <span className="text-[10px] text-emerald-800 uppercase block font-bold">Incremental Spend (+0.3d)</span>
                        <strong className="text-emerald-900 text-base font-mono block mt-0.5">
                          +RM {(activeState.baseline_2025.tourists_thousands * 0.3 * activeState.baseline_2025.spend_per_night_rm / 1000).toFixed(2)}M
                        </strong>
                        <span className="text-[10px] text-emerald-700">Additional Lodging Receipts</span>
                      </div>
                      <div className="p-3 rounded-lg bg-purple-50 border border-purple-200">
                        <span className="text-[10px] text-purple-800 uppercase block font-bold">Potential Value Added</span>
                        <strong className="text-purple-900 text-base font-mono block mt-0.5">
                          +RM {(activeState.baseline_2025.tourists_thousands * 0.3 * activeState.baseline_2025.spend_per_night_rm / 1000 * 0.858).toFixed(2)}M
                        </strong>
                        <span className="text-[10px] text-purple-700">85.8% TSA Accommodation VAI</span>
                      </div>
                    </div>
                  </div>

                  {/* Section 3: Physical Lodging Capacity & Operations (MOTAC 2024 Record) */}
                  <div className="p-3.5 rounded-xl bg-stone-50 border border-violet-100 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-stone-900 uppercase tracking-wider flex items-center gap-1.5">
                        <Hotel className="w-4 h-4 text-violet-700" />
                        3. Physical Lodging Capacity & Operations
                      </span>
                      <span className="text-[10px] font-bold text-violet-800 bg-white px-2 py-0.5 rounded border border-violet-200">
                        MOTAC 2024 Audited Record
                      </span>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                      <div className="p-2 rounded-lg bg-white border border-stone-200">
                        <span className="text-[10px] text-stone-500 block">Hotel Room Supply</span>
                        <strong className="text-stone-900 font-mono font-bold block mt-0.5">
                          {(activeState.motac_hotel_operations_2024?.rooms_count ?? activeState.baseline_2025.hotel_rooms)?.toLocaleString() || 'Unobserved'}
                        </strong>
                        <span className="text-[9px] text-stone-400">rooms ({activeState.motac_hotel_operations_2024?.hotels_count || '—'} hotels)</span>
                      </div>
                      <div className="p-2 rounded-lg bg-white border border-stone-200">
                        <span className="text-[10px] text-stone-500 block">Average Occupancy (AOR)</span>
                        <strong className="text-indigo-800 font-mono font-bold block mt-0.5">
                          {(activeState.motac_hotel_operations_2024?.aor_pct ?? activeState.baseline_2025.aor_pct) != null
                            ? `${(activeState.motac_hotel_operations_2024?.aor_pct ?? activeState.baseline_2025.aor_pct)!.toFixed(1)}%`
                            : 'N/A'}
                        </strong>
                        <span className="text-[9px] text-stone-400">Annual AOR</span>
                      </div>
                      <div className="p-2 rounded-lg bg-white border border-stone-200">
                        <span className="text-[10px] text-stone-500 block">Hotel Guests</span>
                        <strong className="text-stone-900 font-mono font-bold block mt-0.5">
                          {activeState.motac_hotel_operations_2024?.total_hotel_guests != null
                            ? `${(activeState.motac_hotel_operations_2024.total_hotel_guests / 1000).toFixed(1)}k`
                            : 'N/A'}
                        </strong>
                        <span className="text-[9px] text-stone-400">{activeState.motac_hotel_operations_2024?.foreign_guest_share_pct?.toFixed(1) || '0'}% foreign</span>
                      </div>
                      <div className="p-2 rounded-lg bg-emerald-50 border border-emerald-200">
                        <span className="text-[10px] text-emerald-800 font-bold block">Homestays (SDG 8.9)</span>
                        <strong className="text-emerald-900 font-mono font-bold block mt-0.5">
                          {activeState.motac_homestay_operations_2024?.no_of_operators || 0}
                          <span className="text-[10px] font-normal text-stone-600 ml-1">operators</span>
                        </strong>
                        <span className="text-[9px] text-emerald-700">RM {(activeState.motac_homestay_operations_2024?.total_income_rm || 0).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>

                  {/* Mandatory Methodological Notice */}
                  <div className="text-[11px] text-stone-600 bg-amber-50 border border-amber-300 p-3 rounded-xl flex items-start gap-2">
                    <span className="text-amber-700 font-bold">⚠️</span>
                    <div>
                      <strong>Mandatory Methodological Notice</strong>: Scenario estimate, not a causal forecast. Attributable Value-Added Proxy applies national TSA accommodation VAI (85.8%) to simulated incremental expenditure. This prototype focuses on the economic dimension of sustainable tourism. Environmental and broader social dimensions are future extensions.
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-xs text-stone-500">
                    <span>Exportable Markdown format</span>
                    <span>{generateMarkdownBrief(activeState).length} characters</span>
                  </div>
                  <div className="p-4 rounded-xl bg-stone-50 border border-violet-100 font-mono text-xs leading-relaxed text-stone-700 max-h-[420px] overflow-y-auto whitespace-pre-wrap select-all">
                    {generateMarkdownBrief(activeState)}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* All 18 Destinations Comparison Modal Dialog */}
      {showAllDestModal && bookingData && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="ota-dest-modal-title"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn"
        >
          <div className="bg-white border border-violet-200 rounded-2xl w-full max-w-5xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="px-6 py-4 bg-gradient-to-r from-violet-900 to-indigo-900 text-white flex items-center justify-between">
              <div>
                <h3 id="ota-dest-modal-title" className="text-base font-bold flex items-center gap-2">
                  <Hotel className="w-5 h-5 text-amber-400" />
                  National OTA Market Benchmark (Booking.com 2026 Sample)
                </h3>
                <p className="text-xs text-violet-200 mt-0.5">
                  Comparative room rates, guest ratings, and luxury composition across all 18 sampled Malaysian destinations.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowAllDestModal(false)}
                className="p-1.5 rounded-lg hover:bg-white/10 text-white/80 hover:text-white transition-colors cursor-pointer"
                aria-label="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto space-y-4">
              {/* National Benchmark Summary Bar */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 rounded-xl bg-violet-50/70 border border-violet-100">
                <div>
                  <span className="text-[10px] text-stone-500 uppercase tracking-wide block">National Median Rate</span>
                  <strong className="text-lg font-bold text-violet-900 font-mono">
                    RM {bookingData.national_benchmark.median_price_myr?.toFixed(0)}
                  </strong>
                  <span className="text-[10px] text-stone-400 block">/ room-night</span>
                </div>
                <div>
                  <span className="text-[10px] text-stone-500 uppercase tracking-wide block">National Mean Rate</span>
                  <strong className="text-lg font-bold text-stone-800 font-mono">
                    RM {bookingData.national_benchmark.mean_price_myr?.toFixed(0)}
                  </strong>
                  <span className="text-[10px] text-stone-400 block">Spread: RM {bookingData.national_benchmark.p25_price_myr?.toFixed(0)} – {bookingData.national_benchmark.p75_price_myr?.toFixed(0)}</span>
                </div>
                <div>
                  <span className="text-[10px] text-stone-500 uppercase tracking-wide block">National Rating Avg</span>
                  <strong className="text-lg font-bold text-amber-700 font-mono">
                    {bookingData.national_benchmark.mean_rating?.toFixed(1)} / 10
                  </strong>
                  <span className="text-[10px] text-stone-400 block">({bookingData.national_benchmark.total_reviews_sample?.toLocaleString()} reviews)</span>
                </div>
                <div>
                  <span className="text-[10px] text-stone-500 uppercase tracking-wide block">Luxury Mix (4-5★)</span>
                  <strong className="text-lg font-bold text-emerald-800 font-mono">
                    {bookingData.national_benchmark.star_breakdown.luxury_4_5_star_pct}%
                  </strong>
                  <span className="text-[10px] text-stone-400 block">360 total sampled properties</span>
                </div>
              </div>

              {/* Disclaimer */}
              <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-900 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <span>
                  <strong>Supporting Reference Only</strong>: This dataset is cross-sectional scraped market intelligence from Booking.com (20 hotels per destination). It is not officially collected or validated by DOSM and is <strong>strictly excluded from econometric or ML model estimation</strong>.
                </span>
              </div>

              {/* Destinations Table */}
              <div className="border border-stone-200 rounded-xl overflow-hidden">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-stone-100/80 text-stone-600 border-b border-stone-200 text-[11px]">
                    <tr>
                      <th className="p-3 font-semibold">Destination / Zone</th>
                      <th className="p-3 font-semibold">State</th>
                      <th className="p-3 font-semibold text-right">Median Price</th>
                      <th className="p-3 font-semibold text-right">Mean Price</th>
                      <th className="p-3 font-semibold text-right">Avg Rating</th>
                      <th className="p-3 font-semibold text-right">4-5★ Luxury</th>
                      <th className="p-3 font-semibold text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100">
                    {Object.entries(bookingData.destinations)
                      .sort((a, b) => (b[1].median_price_myr || 0) - (a[1].median_price_myr || 0))
                      .map(([slug, dest]) => {
                        const isSelectedState = dest.state_name === selectedStateName;
                        const natMedian = bookingData.national_benchmark.median_price_myr;
                        const diffPct = (natMedian && dest.median_price_myr)
                          ? Math.round(((dest.median_price_myr - natMedian) / natMedian) * 100)
                          : 0;

                        return (
                          <tr
                            key={slug}
                            className={`hover:bg-violet-50/40 transition-colors ${
                              isSelectedState ? 'bg-violet-50/60 font-semibold' : ''
                            }`}
                          >
                            <td className="p-3 flex items-center gap-2">
                              <span className="font-bold text-stone-900">{dest.destination_name}</span>
                              {dest.is_subdestination && (
                                <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-purple-100 text-purple-800 border border-purple-200">
                                  Tourist Zone
                                </span>
                              )}
                            </td>
                            <td className="p-3 text-stone-600">{dest.state_name}</td>
                            <td className="p-3 text-right font-mono">
                              <div className="font-bold text-emerald-800">
                                RM {dest.median_price_myr?.toFixed(0)}
                              </div>
                              <span className={`text-[10px] ${diffPct >= 0 ? 'text-amber-700' : 'text-emerald-700'}`}>
                                {diffPct >= 0 ? `+${diffPct}%` : `${diffPct}%`} vs natl
                              </span>
                            </td>
                            <td className="p-3 text-right font-mono text-stone-700">
                              RM {dest.mean_price_myr?.toFixed(0)}
                            </td>
                            <td className="p-3 text-right font-mono">
                              <span className="font-bold text-stone-900">{dest.mean_rating?.toFixed(1)}</span>
                              <span className="text-stone-400 text-[10px]"> / 10</span>
                            </td>
                            <td className="p-3 text-right font-mono">
                              <span className="font-bold text-stone-800">{dest.star_breakdown.luxury_4_5_star_pct}%</span>
                            </td>
                            <td className="p-3 text-center">
                              <button
                                type="button"
                                onClick={() => {
                                  if (dest.state_name && stateProfiles[dest.state_name]) {
                                    setSelectedStateName(dest.state_name);
                                    if (onSelectState) onSelectState(dest.state_name);
                                    if (dest.is_subdestination) {
                                      setSelectedSubdestSlug(slug);
                                    } else {
                                      setSelectedSubdestSlug(null);
                                    }
                                    setSecondaryTab('booking');
                                    setShowAllDestModal(false);
                                  }
                                }}
                                className="px-2.5 py-1 rounded bg-violet-100 hover:bg-violet-200 text-violet-900 text-[11px] font-semibold transition-colors cursor-pointer"
                              >
                                View in Map
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-3 bg-stone-50 border-t border-stone-200 flex justify-end">
              <button
                type="button"
                onClick={() => setShowAllDestModal(false)}
                className="px-4 py-2 rounded-lg bg-stone-200 hover:bg-stone-300 text-stone-800 text-xs font-semibold transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
