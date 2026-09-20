import React, { useState } from 'react';
import { 
  X, 
  Search, 
  Database, 
  BookOpen, 
  ShieldCheck, 
  AlertTriangle, 
  FileSpreadsheet
} from 'lucide-react';

export interface ProvenanceMetric {
  id: string;
  name: string;
  category: 'Macro Accounting' | 'State Yield' | 'SDG Sustainability' | 'Network & Gravity' | 'Capacity & Pricing';
  status: 'OFFICIAL' | 'PRELIMINARY' | 'DERIVED' | 'MODEL' | 'SCENARIO';
  definition: string;
  formula: string;
  sources: string[];
  referencePeriod: string;
  unit: string;
  transformation: string;
  limitations: string;
  exampleValue?: string;
}

const PROVENANCE_METRICS: ProvenanceMetric[] = [
  {
    id: 'tvay',
    name: 'Tourism Value-Added Yield (TVAY)',
    category: 'State Yield',
    status: 'DERIVED',
    definition: 'Proportion of gross domestic economic value generated per visitor-day of tourism activity in the destination state.',
    formula: 'TVAY = EstimatedTourismGVA / (Tourists * ALOS + Excursionists)',
    sources: ['DOSM Tourism Satellite Account (TSA) 2025', 'DOSM Domestic Tourism Survey (DTS) 2025 (Jadual 1)'],
    referencePeriod: '2025 (Preliminary TSA / Annual DTS)',
    unit: 'RM / visitor-day',
    transformation: 'Nominal expenditure components multiplied by TSA sector-specific VAI and normalized by total visitor-days.',
    limitations: 'National-level TSA product VAI coefficients applied to state-level expenditure composition; assumes identical gross margin structures across states.',
    exampleValue: 'RM 62.4 / day (National Median: RM 58.1)'
  },
  {
    id: 'tey',
    name: 'Tourism Economic Yield (TEY)',
    category: 'State Yield',
    status: 'DERIVED',
    definition: 'Total domestic visitor expenditure captured per visitor-day across all goods, services, and day-trips.',
    formula: 'TEY = TotalExpenditure / (Tourists * ALOS + Excursionists)',
    sources: ['DOSM Domestic Tourism Survey (DTS) 2025 (Jadual 1)'],
    referencePeriod: '2025',
    unit: 'RM / visitor-day',
    transformation: 'Total gross survey receipts divided by visitor-day equivalent denominator to eliminate day-trip volume distortions.',
    limitations: 'Excursionist duration is standardized at 1.0 day; does not separate multi-day excursion packages.',
    exampleValue: 'RM 104.8 / day'
  },
  {
    id: 'vai',
    name: 'Value-Added Intensity (VAI)',
    category: 'Macro Accounting',
    status: 'OFFICIAL',
    definition: 'Proportion of gross output/supply represented by Gross Value Added in each tourism industry, measuring domestic value retention efficiency.',
    formula: 'VAI[i,t] = GVA[i,t] / DomesticSupply[i,t]',
    sources: ['DOSM Tourism Satellite Account (TSA) 2015–2025 (Jadual 5 & 6)'],
    referencePeriod: '2015–2025 (2025 preliminary)',
    unit: 'Ratio [0, 1] or Percentage (%)',
    transformation: 'Extracted directly from production accounts; 2021 MCO lockdown disruption period isolated from structural baselines.',
    limitations: 'Reflects direct industry accounting; excludes indirect and induced macroeconomic multiplier ripple effects.',
    exampleValue: '85.8% (Accommodation), 58.3% (Food & Beverage)'
  },
  {
    id: 'estimated_gva',
    name: 'Estimated Tourism-Attributable GVA (Proxy)',
    category: 'Macro Accounting',
    status: 'DERIVED',
    definition: 'Analytical proxy estimating domestic gross value added directly attributable to internal tourism consumption.',
    formula: 'EstimatedTourismGVA[i,t] = ITC[i,t] * VAI[i,t] (or IndustryGVA * TourismRatio)',
    sources: ['DOSM TSA 2015–2025 (Jadual 4, 5, 6)'],
    referencePeriod: '2015–2025',
    unit: 'RM Million',
    transformation: 'Proportional allocation of gross value added via Tourism Ratio and VAI. Never double-multiplied.',
    limitations: 'Analytical proxy conforming to AGENTS.md Section 3; not official product-level TDGVA which is only officially compiled at aggregate macro level.',
    exampleValue: 'RM 13,018.4 Million (Accommodation 2025)'
  },
  {
    id: 'accom_yield',
    name: 'Accommodation Spend per Tourist-Night',
    category: 'State Yield',
    status: 'DERIVED',
    definition: 'Average accommodation expenditure incurred per overnight tourist-night in the destination.',
    formula: 'AccomYield = AccommodationExpenditure / (OvernightTourists * ALOS)',
    sources: ['DOSM DTS 2025 (Jadual 1)'],
    referencePeriod: '2025',
    unit: 'RM / night',
    transformation: 'Total accommodation expenditure divided by total domestic tourist-nights.',
    limitations: 'Averages paid commercial hotel guests and unpaid Visiting Friends & Relatives (VFR) stays across the destination.',
    exampleValue: 'RM 63.2 / night'
  },
  {
    id: 'alos',
    name: 'Average Length of Stay (ALOS)',
    category: 'State Yield',
    status: 'OFFICIAL',
    definition: 'Average duration of visit in days/nights spent by domestic overnight tourists within the destination state.',
    formula: 'ALOS = Total Domestic Tourist Nights / Total Domestic Overnight Tourists',
    sources: ['DOSM DTS 2025 (Jadual 1) & DTS Historical State Panels (2018–2025)'],
    referencePeriod: '2018–2025',
    unit: 'Days / Nights',
    transformation: 'Official survey metric directly ingested and validated for positive non-zero domains.',
    limitations: 'Excludes day-trippers (excursionists); survey sampling error across small destination sample sizes.',
    exampleValue: '2.52 days (National Average)'
  },
  {
    id: 'capacity_headroom',
    name: 'Hotel Capacity Headroom (%)',
    category: 'Capacity & Pricing',
    status: 'DERIVED',
    definition: 'Margin of operational room capacity available before reaching sustainable planning ceilings (75%, 80%, or 85% AOR).',
    formula: 'CapacityHeadroom = Max(0, PlanningThreshold - BaselineAOR)',
    sources: ['MOTAC Hotel Statistics 2025 (AOR & Room Inventory)'],
    referencePeriod: '2025',
    unit: 'Percentage Points (%)',
    transformation: 'Difference between policy planning threshold (default 80%) and observed average annual occupancy rate.',
    limitations: 'Annualized state average masks acute weekend, school holiday, and seasonal peak capacity crunches.',
    exampleValue: '28.3% Headroom (Melaka: AOR 51.7%, Ceiling 80%)'
  },
  {
    id: 'gravity_residual',
    name: 'Gravity Flow Residual (Model Gap)',
    category: 'Network & Gravity',
    status: 'MODEL',
    definition: 'Difference between observed inter-state tourist flow and econometric PPML model prediction based on economic mass and spatial friction.',
    formula: 'FlowResidual = ObservedFlow - exp(α_orig + γ_dest + δ_year + β_dist*ln(Dist) + β_borneo*Borneo)',
    sources: ['DOSM DTS Inter-State Flow Matrix (2018–2025)', 'PPML Gravity Engine'],
    referencePeriod: '2018–2025 (Holdout validation: 2025)',
    unit: 'Thousands of tourists (k pax)',
    transformation: 'Two-way clustered standard errors, zero target leakage with destination fixed effects; validated out-of-sample.',
    limitations: 'Model gap represents departure from spatial gravity norm, not guaranteed untapped demand.',
    exampleValue: '+184.2k (Above Model Expected)'
  },
  {
    id: 'feeder_hhi',
    name: 'Destination Feeder Concentration (HHI)',
    category: 'Network & Gravity',
    status: 'DERIVED',
    definition: 'Herfindahl-Hirschman Index measuring market concentration of tourist arrivals across feeder source states.',
    formula: 'HHI = Sum( (OriginMarketShare_pct)^2 )',
    sources: ['DOSM DTS Inter-State Matrix 2025'],
    referencePeriod: '2025',
    unit: 'Index [0, 10000]',
    transformation: 'Sum of squared market shares for all inbound feeder states; categorized into Diversified (<1,500), Moderate (1,500–2,500), and Concentrated (>2,500).',
    limitations: 'Measures source market diversity; does not quantify vulnerability to specific economic shocks.',
    exampleValue: '2,156 (Moderately Concentrated)'
  },
  {
    id: 'tir_sdg',
    name: 'Tourist Intensity Ratio (TIR - SDG 8.9)',
    category: 'SDG Sustainability',
    status: 'DERIVED',
    definition: 'Social carrying capacity indicator measuring annual visitor volume relative to permanent resident population.',
    formula: 'TIR = TotalAnnualVisitors / ResidentPopulation',
    sources: ['DOSM DTS 2025', 'DOSM Population Estimates 2025'],
    referencePeriod: '2025',
    unit: 'Visitors / resident',
    transformation: 'Official survey visitors divided by mid-year district population estimates.',
    limitations: 'Annualized ratio; does not distinguish localized spatial clustering in historic downtown or ecotourism corridors.',
    exampleValue: '12.4 visitors / resident (Melaka)'
  },
  {
    id: 'cpi_deflator',
    name: 'Real RM Constant 2025 Series',
    category: 'Capacity & Pricing',
    status: 'OFFICIAL',
    definition: 'Inflation-adjusted expenditure series evaluated at constant 2025 purchasing power to reflect true economic volume change.',
    formula: 'RealValue_t = NominalValue_t * (CPI_2025 / CPI_t)',
    sources: ['DOSM Consumer Price Index (CPI) 2015–2025 (Base 2010=100)'],
    referencePeriod: '2015–2025 (Base 2025 = 134.6)',
    unit: 'Constant 2025 RM',
    transformation: 'Deflated using official national headline CPI series from 112.1 in 2015 to 134.6 in 2025.',
    limitations: 'Uses national headline CPI; does not isolate sub-state or tourism-specific consumer price baskets.',
    exampleValue: 'Deflator Multiplier 2018: 1.123x'
  }
];

const STATUS_BADGES: Record<string, { label: string; bg: string; text: string; border: string; desc: string }> = {
  OFFICIAL: {
    label: 'OFFICIAL',
    bg: 'bg-blue-50 text-blue-800',
    text: 'text-blue-700',
    border: 'border-blue-200',
    desc: 'Directly published by official Malaysian government agencies (DOSM, MOTAC).'
  },
  PRELIMINARY: {
    label: 'PRELIMINARY',
    bg: 'bg-amber-50 text-amber-800',
    text: 'text-amber-700',
    border: 'border-amber-200',
    desc: 'Official preliminary release (e.g. TSA 2025p) subject to annual statistical reconciliation.'
  },
  DERIVED: {
    label: 'DERIVED',
    bg: 'bg-purple-50 text-purple-800',
    text: 'text-purple-700',
    border: 'border-purple-200',
    desc: 'Mathematically transformed using standard national accounting identities and ratios.'
  },
  MODEL: {
    label: 'MODEL ESTIMATE',
    bg: 'bg-indigo-50 text-indigo-800',
    text: 'text-indigo-700',
    border: 'border-indigo-200',
    desc: 'Econometric regression parameter or spatial gravity prediction with documented errors.'
  },
  SCENARIO: {
    label: 'SCENARIO',
    bg: 'bg-emerald-50 text-emerald-800',
    text: 'text-emerald-700',
    border: 'border-emerald-200',
    desc: 'What-if policy intervention estimate under transparent user-configured assumptions.'
  }
};

interface ProvenanceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  metadata?: any;
}

export const ProvenanceDrawer: React.FC<ProvenanceDrawerProps> = ({ isOpen, onClose, metadata }) => {
  const [activeTab, setActiveTab] = useState<'metrics' | 'sources' | 'guardrails'>('metrics');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');

  if (!isOpen) return null;

  const filteredMetrics = PROVENANCE_METRICS.filter((m) => {
    const matchesSearch = 
      m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.definition.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.formula.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = selectedStatus === 'ALL' || m.status === selectedStatus;
    return matchesSearch && matchesStatus;
  });

  const sourcesList = metadata?.sources ? Object.entries(metadata.sources) : [];

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-fadeIn">
      {/* Slide-over Container */}
      <div className="bg-white w-full max-w-3xl h-full flex flex-col shadow-2xl border-l border-violet-100 overflow-hidden animate-slideLeft">
        {/* Header */}
        <div className="p-5 border-b border-violet-100 flex items-center justify-between bg-stone-50/80">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-violet-600/10 text-violet-700 border border-violet-200/60">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-extrabold text-stone-900 tracking-tight">
                  Data Provenance & Audit Registry
                </h2>
                <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-violet-100 text-violet-800">
                  Sprint 7 Integrity
                </span>
              </div>
              <p className="text-xs text-stone-600">
                Authoritative methodology, mathematical formulas, data statuses, and official source catalog
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-stone-100 hover:bg-stone-200 text-stone-600 hover:text-stone-900 transition-all cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="flex border-b border-violet-100 px-5 bg-white">
          <button
            onClick={() => setActiveTab('metrics')}
            className={`py-3 px-4 text-xs font-bold border-b-2 flex items-center gap-1.5 transition-all ${
              activeTab === 'metrics'
                ? 'border-violet-700 text-violet-700'
                : 'border-transparent text-stone-600 hover:text-stone-900'
            }`}
          >
            <BookOpen className="w-4 h-4" />
            Key Performance Indicators ({PROVENANCE_METRICS.length})
          </button>
          <button
            onClick={() => setActiveTab('sources')}
            className={`py-3 px-4 text-xs font-bold border-b-2 flex items-center gap-1.5 transition-all ${
              activeTab === 'sources'
                ? 'border-violet-700 text-violet-700'
                : 'border-transparent text-stone-600 hover:text-stone-900'
            }`}
          >
            <FileSpreadsheet className="w-4 h-4" />
            Official Sources Registry ({sourcesList.length || 7})
          </button>
          <button
            onClick={() => setActiveTab('guardrails')}
            className={`py-3 px-4 text-xs font-bold border-b-2 flex items-center gap-1.5 transition-all ${
              activeTab === 'guardrails'
                ? 'border-violet-700 text-violet-700'
                : 'border-transparent text-stone-600 hover:text-stone-900'
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            Analytical Guardrails & SDG
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {/* TAB 1: METRICS & FORMULAS */}
          {activeTab === 'metrics' && (
            <div className="space-y-4">
              {/* Search and Status Filters */}
              <div className="flex flex-col sm:flex-row items-center gap-3">
                <div className="relative flex-1 w-full">
                  <Search className="w-4 h-4 absolute left-3 top-2.5 text-stone-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search KPI, formula, or definition..."
                    className="w-full pl-9 pr-3 py-2 rounded-lg bg-stone-50 border border-violet-100 text-xs text-stone-900 placeholder-stone-400 focus:outline-none focus:border-violet-400"
                  />
                </div>
                <div className="flex flex-wrap items-center gap-1.5 w-full sm:w-auto">
                  {['ALL', 'OFFICIAL', 'DERIVED', 'MODEL', 'SCENARIO'].map((status) => (
                    <button
                      key={status}
                      onClick={() => setSelectedStatus(status)}
                      className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all ${
                        selectedStatus === status
                          ? 'bg-violet-700 text-white shadow-sm'
                          : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
                      }`}
                    >
                      {status}
                    </button>
                  ))}
                </div>
              </div>

              {/* Status Classification Legend */}
              <div className="p-3 rounded-lg bg-violet-50/60 border border-violet-100/80 text-[11px] space-y-1.5">
                <span className="font-bold text-stone-800 block text-xs">Visible Data Status Taxonomy:</span>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {Object.entries(STATUS_BADGES).map(([k, v]) => (
                    <div key={k} className="flex items-center gap-1.5">
                      <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold border ${v.bg} ${v.border}`}>
                        [{v.label}]
                      </span>
                      <span className="text-[10px] text-stone-600 truncate" title={v.desc}>
                        {v.desc}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Metric Cards List */}
              <div className="space-y-3">
                {filteredMetrics.map((m) => {
                  const badge = STATUS_BADGES[m.status] || STATUS_BADGES.DERIVED;
                  return (
                    <div
                      key={m.id}
                      className="p-4 rounded-xl border border-violet-100/90 bg-white hover:border-violet-300 transition-all shadow-sm space-y-2.5"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <h3 className="text-sm font-bold text-stone-900">{m.name}</h3>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${badge.bg} ${badge.border}`}>
                              [{badge.label}]
                            </span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-stone-100 text-stone-600 font-mono">
                              {m.unit}
                            </span>
                          </div>
                          <span className="text-[10px] text-violet-700 font-semibold">{m.category}</span>
                        </div>
                        {m.exampleValue && (
                          <div className="text-right">
                            <span className="text-[10px] text-stone-400 uppercase block">Sample Value</span>
                            <span className="text-xs font-mono font-bold text-stone-800">{m.exampleValue}</span>
                          </div>
                        )}
                      </div>

                      <p className="text-xs text-stone-700 leading-relaxed">{m.definition}</p>

                      {/* Formula display box */}
                      <div className="p-2.5 rounded-lg bg-stone-50 border border-stone-200/80 font-mono text-xs text-violet-900 overflow-x-auto">
                        <strong>Formula:</strong> {m.formula}
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] pt-1">
                        <div>
                          <span className="text-stone-500 font-semibold block">Official Source(s):</span>
                          <span className="text-stone-800">{m.sources.join(' • ')}</span>
                        </div>
                        <div>
                          <span className="text-stone-500 font-semibold block">Reference Period:</span>
                          <span className="text-stone-800 font-mono">{m.referencePeriod}</span>
                        </div>
                      </div>

                      {/* Limitations Alert Box */}
                      <div className="p-2.5 rounded-lg bg-amber-50/70 border border-amber-200/70 text-[11px] text-amber-900 flex items-start gap-2">
                        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                        <div>
                          <strong className="font-semibold">Methodological Limitation:</strong> {m.limitations}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 2: OFFICIAL SOURCE CATALOG */}
          {activeTab === 'sources' && (
            <div className="space-y-4">
              <p className="text-xs text-stone-600">
                Official publications and longitudinal panels registered in the Malaysia Tourism Value Optimizer data ingestion pipeline:
              </p>

              <div className="space-y-3">
                {sourcesList.map(([key, s]: [string, any]) => (
                  <div
                    key={key}
                    className="p-4 rounded-xl border border-violet-100 bg-white space-y-2 shadow-sm"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="text-[10px] uppercase font-bold text-violet-700 block font-mono">
                          {s.id || key}
                        </span>
                        <h3 className="text-sm font-bold text-stone-900">{s.publication}</h3>
                        <span className="text-xs text-stone-600">{s.organization}</span>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
                        {s.data_status?.toUpperCase() || 'OFFICIAL'}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[11px] py-1">
                      <div>
                        <span className="text-stone-500 block">Reference Period</span>
                        <strong className="font-mono text-stone-800">{s.reference_period}</strong>
                      </div>
                      <div>
                        <span className="text-stone-500 block">Geography</span>
                        <strong className="text-stone-800">{s.geography}</strong>
                      </div>
                      <div>
                        <span className="text-stone-500 block">Publication Date</span>
                        <strong className="font-mono text-stone-800">{s.publication_date || 'Annual'}</strong>
                      </div>
                    </div>

                    {s.tables && (
                      <div className="text-[11px] space-y-0.5 pt-1 border-t border-stone-100">
                        <span className="text-stone-500 font-semibold block">Source Tables / Sheets:</span>
                        <ul className="list-disc list-inside text-stone-700 space-y-0.5">
                          {s.tables.map((t: string, idx: number) => (
                            <li key={idx}>{t}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {s.transformation && (
                      <div className="text-[11px] text-stone-600 bg-stone-50 p-2 rounded border border-stone-100 font-mono">
                        <strong>Pipeline Target:</strong> {s.transformation}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 3: ANALYTICAL GUARDRAILS & SDG */}
          {activeTab === 'guardrails' && (
            <div className="space-y-4 text-xs text-stone-700">
              <div className="p-4 rounded-xl bg-violet-50/70 border border-violet-200 space-y-2">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-violet-700" />
                  <h3 className="text-sm font-bold text-stone-900">Mandatory Analytical Guardrails (AGENTS.md)</h3>
                </div>
                <p className="leading-relaxed">
                  The Malaysia Tourism Value Optimizer is an economic decision-support platform designed to assist federal and state tourism authorities. To maintain academic and policy credibility, all outputs adhere to non-negotiable principles:
                </p>
                <ul className="space-y-1.5 list-disc list-inside pt-1">
                  <li><strong>Core Paradigm Shift:</strong> Shift policy orientation from <em>visitor volume expansion</em> to <em>domestic economic value capture from existing visitors</em>.</li>
                  <li><strong>Causal Humility:</strong> Correlation does not prove causation. All scenario calculations carry the explicit notice: <em>"Scenario estimate, not a causal forecast."</em></li>
                  <li><strong>Economic Dimension of Sustainable Tourism:</strong> This prototype evaluates the economic dimension under UN SDG 8.9 and 12.b. Environmental and broader social carrying capacities are future extensions.</li>
                  <li><strong>No Invented Empirical Data:</strong> Zero synthetic imputation for unobserved survey cells; missing values explicitly propagate as null/N/A.</li>
                  <li><strong>TDGVA Proxy Attribution:</strong> Tourism value-added estimates at the state and product level represent analytical proxies (<code className="bg-white px-1 py-0.5 rounded border text-violet-800">ITC * VAI</code>), not official product-level TDGVA.</li>
                </ul>
              </div>

              <div className="p-4 rounded-xl border border-stone-200 bg-white space-y-2">
                <h3 className="text-sm font-bold text-stone-900">UN Sustainable Development Goals Alignment</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                  <div className="p-3 rounded-lg bg-stone-50 border border-stone-200/80 space-y-1">
                    <span className="text-xs font-bold text-indigo-700 block">SDG Target 8.9</span>
                    <p className="text-[11px] text-stone-600 leading-relaxed">
                      "By 2030, devise and implement policies to promote sustainable tourism that creates jobs and promotes local culture and products." Measured via <strong>Tourism Value-Added Yield (TVAY)</strong> and community homestay integration.
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-stone-50 border border-stone-200/80 space-y-1">
                    <span className="text-xs font-bold text-emerald-700 block">SDG Target 12.b</span>
                    <p className="text-[11px] text-stone-600 leading-relaxed">
                      "Develop and implement tools to monitor sustainable development impacts for sustainable tourism that creates jobs." Monitored via <strong>Excursionist Pressure Ratio (EPR)</strong> and hotel carrying capacity headroom.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-violet-100 bg-stone-50/60 flex items-center justify-between text-xs text-stone-500">
          <span>Malaysia Tourism Value Optimizer • Research Prototype</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-violet-700 hover:bg-violet-600 text-white font-semibold transition-all cursor-pointer shadow-sm"
          >
            Close Drawer
          </button>
        </div>
      </div>
    </div>
  );
};
