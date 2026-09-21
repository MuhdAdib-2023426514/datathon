import React, { useState } from 'react';
import type { ImplementationMetadata, ImplementationUser, StateProfile } from '../types';
import {
  Users,
  Layers,
  Sparkles,
  ArrowRight,
  Calendar,
  TrendingUp,
  CheckCircle2,
  Compass,
  ShieldCheck,
  MapPin,
  Award
} from 'lucide-react';

interface ImplementationRoadmapProps {
  metadata?: ImplementationMetadata | null;
  stateProfiles?: Record<string, StateProfile>;
  onNavigateTab?: (tab: string) => void;
}

export const ImplementationRoadmap: React.FC<ImplementationRoadmapProps> = ({
  metadata,
  stateProfiles,
  onNavigateTab
}) => {
  const [selectedUser, setSelectedUser] = useState<string>('MOTAC');
  const [activeStep, setActiveStep] = useState<number>(1);
  const [activeQuery, setActiveQuery] = useState<string>('melaka_capacity');
  const [selectedStateQuery, setSelectedStateQuery] = useState<string>('');

  const defaultUsers: ImplementationUser[] = [
    {
      role: 'MOTAC',
      full_name: 'Ministry of Tourism, Arts and Culture Malaysia',
      primary_decisions: [
        'National tourism investment resource allocation across states',
        'Balancing interstate economic yields with cultural & heritage carrying capacity',
        'Monitoring National Tourism Policy (DPN 2020-2030) high-yield indicator targets'
      ],
      recommended_views: ['Tourism Value Monitor', 'Portfolio Optimizer']
    },
    {
      role: 'Tourism Malaysia',
      full_name: 'Malaysia Tourism Promotion Board',
      primary_decisions: [
        'Targeted domestic feeder-market digital campaign design & budget allocation',
        'Converting high-volume day-trippers into multi-day overnight guests',
        'Stimulating midweek and shoulder-season domestic travel via corridor vouchers'
      ],
      recommended_views: ['Corridor Network', 'Scenario Simulator']
    },
    {
      role: 'State Tourism Boards',
      full_name: 'State Tourism Action Councils (e.g. Tourism Selangor, Melaka Heritage)',
      primary_decisions: [
        'State-specific stay-extension packages and evening heritage economy activation',
        'Attracting high-yield overnight visitors rather than volume-only excursionists',
        'Targeting top out-of-state feeder origins with dedicated cooperative marketing'
      ],
      recommended_views: ['Accommodation Opportunity Map', 'State Decision Brief']
    },
    {
      role: 'Local Authorities',
      full_name: 'Pihak Berkuasa Tempatan (PBTs) & Municipal Councils',
      primary_decisions: [
        'Destination carrying-capacity management and peak congestion relief',
        'Local accommodation licensing and zoning (commercial hotels vs homestays)',
        'Municipal tourist tax reinvestment in pedestrian and public infrastructure'
      ],
      recommended_views: ['Accommodation Map', 'Portfolio Optimizer']
    },
    {
      role: 'Hotel Associations',
      full_name: 'Malaysian Association of Hotels (MAH) & MAHO',
      primary_decisions: [
        'Forecasting room-night demand uplift from interstate campaigns',
        'Optimizing Average Room Rates (ARR) and RevPAR yield across star tiers',
        'Mitigating extreme weekend peak vs weekday occupancy imbalances'
      ],
      recommended_views: ['Scenario Simulator', 'Monte Carlo Uncertainty']
    }
  ];

  const targetUsers = metadata?.target_users && metadata.target_users.length > 0
    ? metadata.target_users
    : defaultUsers;

  const operatingSteps = metadata?.operating_model || [
    { step: 1, name: 'Official Data Ingestion', description: 'Automated ingestion of published DOSM TSA, DTS, and Hotel Occupancy statistics.' },
    { step: 2, name: 'Economic Yield Diagnosis', description: 'Computation of constant-price TVAY, TEY, and Value-Added Intensity efficiency.' },
    { step: 3, name: 'Opportunity Detection', description: 'Gravity model residual separation and multi-dimensional corridor classification.' },
    { step: 4, name: 'Scenario Simulation', description: 'Capacity-constrained what-if simulation of campaign reach and length-of-stay extensions.' },
    { step: 5, name: 'Portfolio Optimization', description: 'MILP resource allocation maximizing GVA within fiscal and room inventory limits.' },
    { step: 6, name: 'Intervention Execution', description: 'Pilot deployment of digital campaign bundles across selected feeder corridors.' },
    { step: 7, name: 'Impact Verification', description: 'Post-campaign empirical tracking against counterfactual control corridors.' },
    { step: 8, name: 'Model Recalibration', description: 'Continuous tuning of gravity friction coefficients and spend elasticity.' }
  ];

  const refreshCadence = metadata?.refresh_cadence || [
    { stream: 'TSA National Accounts', frequency: 'Annual (September)', source: 'DOSM Tourism Satellite Account' },
    { stream: 'Domestic Tourism Survey', frequency: 'Annual (June/September)', source: 'DOSM DTS Annual Report' },
    { stream: 'State Tourism Survey', frequency: 'Annual (September)', source: 'DOSM State Domestic Tourism Survey' },
    { stream: 'Hotel Occupancy & Rates', frequency: 'Monthly / Quarterly', source: 'Tourism Malaysia Strategic Planning Division' },
    { stream: 'Corridor Gravity Model', frequency: 'Annual Recalibration', source: 'PPML Fixed-Effects Econometric Engine' },
  ];

  const pilotModel = metadata?.pilot_operating_model || {
    destination: 'Melaka',
    title: 'Melaka 8–12 Week Pilot Deployment Protocol',
    baseline_quarter: {
      destination_alos_days: 2.11,
      national_median_alos: 2.47,
      spend_per_night_rm: 63.00,
      baseline_aor_pct: 63.8,
      planning_ceiling_pct: 80.0,
      available_hotel_rooms: 14782,
      annual_domestic_tourists_millions: 10.1,
      top_feeder_shares: {
        'Selangor': '24.2%',
        'Johor': '17.8%',
        'Negeri Sembilan': '12.1%',
        'W.P. Kuala Lumpur': '11.5%'
      }
    },
    intervention_design: {
      target_corridors: [
        'Selangor -> Melaka',
        'Negeri Sembilan -> Melaka',
        'Johor -> Melaka'
      ],
      package_name: 'Heritage & Culinary 3D2N Midweek Experience Pass',
      campaign_mechanics: 'Co-funded digital stay-extension voucher redeemable exclusively for Sunday–Thursday overnight bookings at registered MAH/MyBHA hotels and licensed homestays.',
      duration_weeks: '8–12 weeks (midweek and shoulder-season activation)'
    },
    outcome_tracking: [
      { indicator: 'Average Length of Stay (ALOS)', cadence: 'Quarterly survey sample', target: '+0.30 to +0.50 days' },
      { indicator: 'Commercial Room Nights', cadence: 'Monthly MOTAC occupancy feed', target: '+12,000 to +18,000 nights/month' },
      { indicator: 'Midweek Occupancy Rate (Sun-Thu)', cadence: 'Bi-weekly hotel association sample', target: 'Lift from 51% to 62%' },
      { indicator: 'Tourism Value-Added Yield (TVAY)', cadence: 'Quarterly synthesis', target: 'Lift from RM 95.8 to >RM 108/day' }
    ],
    evaluation_framework: {
      methodology: 'Difference-in-Differences (DiD) & Matched Control',
      treatment_corridors: ['Selangor -> Melaka', 'Johor -> Melaka'],
      matched_control_corridors: ['Selangor -> Negeri Sembilan', 'Johor -> Pahang'],
      identifying_assumption: 'Parallel trends in pre-intervention length of stay and lodging expenditure across treatment and control corridors.'
    }
  };

  const raciMatrix = metadata?.institutional_raci || [
    {
      function: 'TSA National Supply & VAI Accounts',
      decision_owner: 'MOTAC Strategic Planning',
      data_owner: 'DOSM Services Statistics',
      implementation_owner: 'Automated ETL Pipeline',
      review_cadence: 'Annual (September)'
    },
    {
      function: 'State Campaign Selection & Budget Sizing',
      decision_owner: 'State Tourism Action Councils',
      data_owner: 'DOSM DTS & State Surveys',
      implementation_owner: 'Tourism Malaysia Domestic Division',
      review_cadence: 'Quarterly'
    },
    {
      function: 'Corridor Packaging & Hotel Booking Bundles',
      decision_owner: 'MAH / MyBHA State Chapters',
      data_owner: 'Hotel PMS & Registered Homestays',
      implementation_owner: 'Licensed DMOs & Tour Operators',
      review_cadence: 'Bi-annual (Seasonal)'
    },
    {
      function: 'Carrying Capacity & Municipal Licensing',
      decision_owner: 'Local Authorities (PBTs / MBMB)',
      data_owner: 'MOTAC Licensing Registry',
      implementation_owner: 'City Council Enforcement',
      review_cadence: 'Continuous / Monthly'
    },
    {
      function: 'Econometric Recalibration & Optimization',
      decision_owner: 'MOTAC / Datathon Intelligence Unit',
      data_owner: 'Integrated Tourism Lake (DuckDB)',
      implementation_owner: 'Analytical Decision Engine',
      review_cadence: 'Annual'
    }
  ];

  // Grounded AI Decision Intelligence Knowledge Base
  const groundedQueries: Record<string, {
    title: string;
    question: string;
    answer: string;
    metrics: Record<string, any>;
    recommendation: string;
    source: string;
    confidence: string;
    limitation: string;
  }> = {
    melaka_capacity: {
      title: 'Melaka Capacity Constraint',
      question: 'Why is Melaka classified as capacity-constrained and what policy should be prioritized?',
      answer: 'Melaka exhibits an Average Occupancy Rate (AOR) of 63.8%, leaving limited headroom before breaching peak weekend saturation (80% planning threshold). With an Average Length of Stay (ALOS) of 2.11 days (below the national median of 2.47d) and lodging spend of RM 63.00/night, expanding volume without evening dispersion risks physical hotel room bottlenecks.',
      metrics: {
        'Baseline AOR': '63.8%',
        'Planning Ceiling': '80.0%',
        'Dest ALOS': '2.11 days (National Median: 2.47d)',
        'Spend per Night': 'RM 63.00',
        'Top Feeder': 'Selangor (2.73M tourists)'
      },
      recommendation: 'Prioritize midweek stay-extension promotions, Friday-arrival incentives, and premium experiential heritage trails rather than unconstrained weekend excursion campaigns.',
      source: 'DOSM DTS 2025 & Tourism Malaysia Hotel Survey',
      confidence: 'Very High',
      limitation: 'Annual state-level occupancy (63.8%) may conceal localized peak-period capacity pressure; finer-grained occupancy data would be required to verify sub-state constraints.'
    },
    vai_ranking: {
      title: 'High-Value Product Priority',
      question: 'Which tourism products consistently create the highest domestic Gross Value Added?',
      answer: 'In Malaysia Tourism Satellite Accounts (2015-2025), Accommodation Services consistently achieves the highest Value-Added Intensity among core tourism products with a post-recovery median of 85.8% (2025p VAI: 86.6%), followed by Food & Beverage (65.5%), Recreation & Cultural Services (60.4%), Shopping Retail Margin (47.0%), and Passenger Transport (40.7%). Travel Agencies expanded supply faster than GVA post-recovery, yielding a VAI of 28.5%.',
      metrics: {
        'Accommodation VAI': '85.8% (Post-Recovery Median)',
        'Food & Beverage VAI': '65.5%',
        'Recreation VAI': '60.4%',
        'Shopping Retail Margin': '47.0%',
        'Passenger Transport': '40.7%',
        'Tourism Ratio (Accom)': '96.7%'
      },
      recommendation: 'Redirect public tourism incentives from low-margin retail subsidies toward overnight accommodation, cultural immersion, and multi-day itinerary development.',
      source: 'DOSM Tourism Satellite Account 2015-2025p',
      confidence: 'High',
      limitation: 'National TSA supply tables represent aggregate national input-output relationships.'
    },
    priority_corridors: {
      title: 'Priority Conversion Corridors',
      question: 'Which feeder corridors offer the highest economic return from stay extension?',
      answer: 'Priority Conversion Corridors are high-volume feeder routes whose destination exhibits below-median stay duration (ALOS < 2.47 days) and/or below-median accommodation capture. Major examples include Selangor -> Melaka (2.73M tourists, ALOS 2.11d), Johor -> Melaka (1.42M tourists), and Negeri Sembilan -> Melaka. The non-dominated Pareto frontier identifies 58 optimal inter-state corridors nationwide.',
      metrics: {
        'Selangor -> Melaka': '2.73M tourists | Priority Conversion',
        'Negeri Sembilan -> Melaka': '114k flow gap | Rank 2 Pareto',
        'Selangor -> W.P. KL': '84k stay gap | Rank 1 Pareto',
        'Pareto Frontier': '58 non-dominated corridors nationwide'
      },
      recommendation: 'Deploy joint digital marketing campaigns between origin state transport hubs and destination accommodation providers with 2-night minimum stay incentives.',
      source: 'DOSM DTS 2025 Origin-Destination Matrix & Corridor Opportunity Framework',
      confidence: 'High',
      limitation: 'Origin-destination flows reflect primary destination reported; multi-leg road trips are attributed to main stay.'
    },
    portfolio_budget: {
      title: 'Strategic Budget Allocation',
      question: 'How should a RM 5.0M tourism development budget be allocated across corridors?',
      answer: 'The Mixed-Integer Linear Programming (MILP) portfolio optimizer selects 18 optimal inter-state corridors, generating RM 140.3M in expected incremental GVA (a benchmark multiple of 28.1x) while strictly ensuring no destination breaches its 80% hotel room capacity ceiling. The largest allocations go to high-yield feeder corridors into Pahang, Perak, and Pulau Pinang.',
      metrics: {
        'Budget Allocated': 'RM 5.00M',
        'Budget Utilized': 'RM 4.98M (99.6%)',
        'Expected GVA': 'RM 140.3M',
        'Value-to-Cost Multiple': '28.1x (Scenario Benchmark)',
        'Corridors Funded': '18 inter-state corridors'
      },
      recommendation: 'Execute the optimized 18-corridor campaign portfolio via coordinated digital promotions with state tourism boards and hotel associations.',
      source: 'Portfolio Optimizer MILP Engine (scipy.optimize.milp)',
      confidence: 'Very High',
      limitation: 'GVA returns are scenario estimates assuming 15% target reach and +0.4 night stay extension.'
    }
  };

  // Dynamic Structured State Evidence (Plan Section 13.2 / Sprint E)
  const dynamicStateQueryData = (selectedStateQuery && stateProfiles && stateProfiles[selectedStateQuery]) ? (() => {
    const s = stateProfiles[selectedStateQuery];
    const b = s.baseline_2025;
    const aor = b.aor_pct;
    const alos = b.alos_days;
    const spend = b.spend_per_night_rm;
    const tvay = s.sdg_metrics?.tvay_rm_per_day;
    const rooms = b.hotel_rooms;

    let capTier = 'Ample Capacity Headroom (<70% AOR)';
    let rec = `Target high-volume feeder routes with staycation and weekend extension packages to fill available room capacity in ${s.state}.`;
    if (aor == null) {
      capTier = 'Capacity Unobserved';
      rec = `Improve accommodation survey registration in ${s.state} to verify physical hotel and homestay room capacity.`;
    } else if (aor > 100.0) {
      capTier = 'Physical Capacity Breach (>100% AOR)';
      rec = `Enforce moratorium on mass-arrival marketing; prioritize room supply expansion and off-peak dispersion.`;
    } else if (aor > 80.0) {
      capTier = 'Severe Capacity Saturation (>80% AOR)';
      rec = `Shift campaigns strictly toward midweek and off-peak dispersion in ${s.state}; avoid weekend incentives.`;
    } else if (aor >= 70.0 || (s.state === 'Melaka' && aor >= 63.0)) {
      capTier = 'Planning Watch (70-80% AOR)';
      rec = `Prioritize midweek stay-extension promotions, evening heritage trails, and premium experiential packages rather than mass-market volume campaigns.`;
    }

    return {
      title: `${s.state} Evidence Profile`,
      question: `What are the capacity headroom constraints, length of stay, and economic yield metrics for ${s.state}?`,
      answer: `${s.state} (${s.archetype_name}) recorded ${(b.tourists_thousands / 1000).toFixed(2)}M overnight tourists in 2025 with an Average Length of Stay (ALOS) of ${alos.toFixed(2)} days (national median: 2.47d) and lodging spend of RM ${spend.toFixed(2)}/night. Its baseline Average Occupancy Rate (AOR) stands at ${aor != null ? `${aor.toFixed(1)}%` : 'unobserved'}, classifying its room capacity headroom as '${capTier}'. TVAY is ${tvay != null ? `RM ${tvay.toFixed(1)}/day` : 'under empirical baseline'}.`,
      metrics: {
        'Baseline AOR': aor != null ? `${aor.toFixed(1)}%` : 'N/A',
        'Planning Ceiling': '80.0%',
        'Dest ALOS': `${alos.toFixed(2)} days (Median: 2.47d)`,
        'Spend per Night': `RM ${spend.toFixed(2)}`,
        'TVAY (Value Yield)': tvay != null ? `RM ${tvay.toFixed(1)}/day` : 'N/A',
        'Hotel Rooms': rooms != null ? rooms.toLocaleString() : 'N/A',
        'State Archetype': s.archetype_name
      },
      recommendation: rec,
      source: 'DOSM DTS 2025, TSA 2025, and Tourism Malaysia Hotel Survey',
      confidence: 'High (Official DOSM DTS)',
      limitation: 'Annual state-level occupancy may conceal localized peak-period capacity pressure; finer-grained occupancy data would be required to verify sub-state constraints.'
    };
  })() : null;

  const selectedQueryData = dynamicStateQueryData || groundedQueries[activeQuery] || groundedQueries.melaka_capacity;

  return (
    <div className="space-y-8 animate-fadeIn pb-16">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-purple-900/90 via-indigo-900/80 to-slate-900 border border-purple-500/30 rounded-2xl p-6 shadow-xl relative overflow-hidden text-white">
        <div className="absolute -right-10 -bottom-10 w-72 h-72 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-500/30 text-purple-200 border border-purple-400/40">
                GOVERNANCE & OPERATING ARCHITECTURE
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                COMMERCIAL DECISION INTELLIGENCE
              </span>
            </div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
              MYTourism Value Intelligence — Strategic Implementation Roadmap
            </h1>
            <p className="text-purple-200/80 text-sm mt-1 max-w-3xl">
              An institutional decision-support framework connecting official macroeconomic accounts (DOSM TSA & DTS)
              with state tourism action councils, municipal carrying capacities, and commercial hotel associations.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => onNavigateTab && onNavigateTab('simulator')}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white text-xs font-medium rounded-lg transition-colors flex items-center gap-1.5 shadow"
            >
              <span>Explore Simulator</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Section 1: Target Stakeholder Personas */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-purple-600" />
            <h2 className="text-lg font-bold text-slate-800">Target Stakeholder Personas & Policy Decisions</h2>
          </div>
          <span className="text-xs text-slate-500 font-medium">5 Core Institutional Roles</span>
        </div>

        {/* User Tabs */}
        <div className="flex flex-wrap gap-2 mb-6 border-b border-slate-100 pb-3">
          {targetUsers.map((u) => (
            <button
              key={u.role}
              onClick={() => setSelectedUser(u.role)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                selectedUser === u.role
                  ? 'bg-purple-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {u.role}
            </button>
          ))}
        </div>

        {/* Active User Card */}
        {(() => {
          const user = targetUsers.find((u) => u.role === selectedUser) || targetUsers[0];
          return (
            <div className="bg-slate-50 rounded-xl p-5 border border-slate-200/70">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
                <div>
                  <h3 className="text-base font-bold text-slate-900">{user.full_name}</h3>
                  <span className="text-xs text-purple-700 font-semibold uppercase tracking-wider">Role: {user.role}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500 font-medium">Recommended Modules:</span>
                  {user.recommended_views.map((v, i) => (
                    <span key={i} className="px-2 py-0.5 rounded bg-purple-100 text-purple-800 text-xs font-medium">
                      {v}
                    </span>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider block">Key Decision Use Cases:</span>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {user.primary_decisions.map((dec, i) => (
                    <div key={i} className="bg-white p-3.5 rounded-lg border border-slate-200 text-xs text-slate-700 flex items-start gap-2.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                      <span>{dec}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })()}
      </div>

      {/* Section 2: 8-Step Closed-Loop Operating Model */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-600" />
            <h2 className="text-lg font-bold text-slate-800">8-Step Closed-Loop Operating Architecture</h2>
          </div>
          <span className="text-xs text-slate-500 font-medium">Iterative Policy Cycle</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-8 gap-2 mb-6">
          {operatingSteps.map((step) => (
            <button
              key={step.step}
              onClick={() => setActiveStep(step.step)}
              className={`p-3 rounded-xl text-left border transition-all ${
                activeStep === step.step
                  ? 'bg-indigo-50 border-indigo-500 ring-2 ring-indigo-200'
                  : 'bg-slate-50 border-slate-200 hover:border-slate-300'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className={`text-xs font-bold ${activeStep === step.step ? 'text-indigo-700' : 'text-slate-500'}`}>
                  Step {step.step}
                </span>
                {activeStep === step.step && <div className="w-2 h-2 rounded-full bg-indigo-600" />}
              </div>
              <div className="text-xs font-semibold text-slate-800 line-clamp-2">{step.name}</div>
            </button>
          ))}
        </div>

        {/* Active Step Detail */}
        {(() => {
          const s = operatingSteps.find((x) => x.step === activeStep) || operatingSteps[0];
          return (
            <div className="bg-gradient-to-r from-indigo-50/70 to-slate-50 p-4 rounded-xl border border-indigo-100 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-indigo-600 text-white font-bold flex items-center justify-center text-sm">
                  {s.step}
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900">{s.name}</h4>
                  <p className="text-xs text-slate-600 mt-0.5">{s.description}</p>
                </div>
              </div>
              <span className="px-2.5 py-1 bg-white text-indigo-800 border border-indigo-200 rounded-md text-xs font-medium shrink-0">
                Continuous Governance
              </span>
            </div>
          );
        })()}
      </div>

      {/* Section 3: Data Ingestion & Governance Cadence */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-purple-600" />
            <h2 className="text-lg font-bold text-slate-800">Official Data Refresh & Governance Schedule</h2>
          </div>
          <span className="text-xs text-slate-500 font-medium">Deterministically Recalibrated</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-100 text-slate-600 uppercase font-semibold">
              <tr>
                <th className="py-2.5 px-4 rounded-l-lg">Data Stream</th>
                <th className="py-2.5 px-4">Refresh Frequency</th>
                <th className="py-2.5 px-4">Authoritative Source</th>
                <th className="py-2.5 px-4 rounded-r-lg">Role in Model</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {refreshCadence.map((cad, idx) => (
                <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-4 font-semibold text-slate-800">{cad.stream}</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-medium">
                      {cad.frequency}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-600">{cad.source}</td>
                  <td className="py-3 px-4 text-slate-500">
                    {idx === 0 && 'National supply-side VAI benchmark (85.8% for accommodation)'}
                    {idx === 1 && 'Inter-state origin-destination tourist flow matrix'}
                    {idx === 2 && 'State-level ALOS, spending composition, and purpose breakdown'}
                    {idx === 3 && 'Physical hotel carrying capacity and annual baseline AOR'}
                    {idx === 4 && 'PPML distance decay friction (β = -0.410) and cross-region sea barrier'}
                    {idx === 5 && 'Dynamic what-if calculations, stochastic Monte Carlo & MILP optimization'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Section 4: Concrete Pilot Operating Model: Melaka 8–12 Week Protocol */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-sm space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <Compass className="w-5 h-5 text-indigo-600" />
            <div>
              <h2 className="text-lg font-bold text-slate-800">
                Concrete Pilot Deployment Protocol: {pilotModel.title}
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Operational execution case study converting macroeconomic TSA accounts and corridor gravity metrics into an 8–12 week intervention.
              </p>
            </div>
          </div>
          <span className="px-2.5 py-1 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 text-xs font-semibold shrink-0">
            DESTINATION: {pilotModel.destination.toUpperCase()} (PILOT)
          </span>
        </div>

        {/* 4.1 Baseline Quarter Parameters */}
        <div className="space-y-2.5">
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-purple-600" />
            <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Step 1 — Baseline Quarter Measurement (Verified DTS 2025 & MOTAC Data)
            </h3>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Dest. ALOS</span>
              <div className="text-base font-bold text-slate-900 mt-0.5 font-mono">
                {pilotModel.baseline_quarter.destination_alos_days} days
              </div>
              <span className="text-[10px] text-amber-600">Natl: {pilotModel.baseline_quarter.national_median_alos}d</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Nightly Spend</span>
              <div className="text-base font-bold text-slate-900 mt-0.5 font-mono">
                RM {pilotModel.baseline_quarter.spend_per_night_rm.toFixed(2)}
              </div>
              <span className="text-[10px] text-slate-500">per overnight tourist</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Baseline AOR</span>
              <div className="text-base font-bold text-indigo-700 mt-0.5 font-mono">
                {pilotModel.baseline_quarter.baseline_aor_pct}%
              </div>
              <span className="text-[10px] text-emerald-600 font-medium">Ceiling: {pilotModel.baseline_quarter.planning_ceiling_pct}%</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Hotel Rooms</span>
              <div className="text-base font-bold text-slate-900 mt-0.5 font-mono">
                {pilotModel.baseline_quarter.available_hotel_rooms.toLocaleString()}
              </div>
              <span className="text-[10px] text-slate-500">registered capacity</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Annual Tourists</span>
              <div className="text-base font-bold text-slate-900 mt-0.5 font-mono">
                {pilotModel.baseline_quarter.annual_domestic_tourists_millions}M
              </div>
              <span className="text-[10px] text-slate-500">overnight volume</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Top Feeder</span>
              <div className="text-base font-bold text-purple-700 mt-0.5">
                Selangor (24.2%)
              </div>
              <span className="text-[10px] text-slate-500">Johor: 17.8%</span>
            </div>
          </div>
        </div>

        {/* 4.2 Intervention Package & Mechanics */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gradient-to-br from-indigo-50/70 to-slate-50 p-4 rounded-xl border border-indigo-100 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-indigo-900 uppercase tracking-wider">
                Intervention Package Design
              </span>
              <span className="px-2 py-0.5 rounded bg-indigo-100 text-indigo-800 text-[10px] font-bold">
                {pilotModel.intervention_design.duration_weeks}
              </span>
            </div>
            <h4 className="text-sm font-bold text-slate-900">
              {pilotModel.intervention_design.package_name}
            </h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              {pilotModel.intervention_design.campaign_mechanics}
            </p>
            <div className="pt-2 flex flex-wrap gap-1.5">
              <span className="text-[11px] font-semibold text-slate-600 mr-1">Target Routes:</span>
              {pilotModel.intervention_design.target_corridors.map((tc: string, i: number) => (
                <span key={i} className="px-2 py-0.5 rounded bg-white text-indigo-700 border border-indigo-200 text-xs font-medium">
                  {tc}
                </span>
              ))}
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-50/70 to-slate-50 p-4 rounded-xl border border-purple-100 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-purple-900 uppercase tracking-wider">
                DiD Scientific Evaluation Framework
              </span>
              <span className="px-2 py-0.5 rounded bg-purple-100 text-purple-800 text-[10px] font-bold">
                COUNTERFACTUAL CONTROL
              </span>
            </div>
            <h4 className="text-sm font-bold text-slate-900">
              Methodology: {pilotModel.evaluation_framework.methodology}
            </h4>
            <div className="text-xs text-slate-600 space-y-1">
              <div><strong>Treatment:</strong> {pilotModel.evaluation_framework.treatment_corridors.join(', ')}</div>
              <div><strong>Matched Control:</strong> {pilotModel.evaluation_framework.matched_control_corridors.join(', ')}</div>
              <div className="text-[11px] italic text-slate-500 pt-1">
                <strong>Identifying Assumption:</strong> {pilotModel.evaluation_framework.identifying_assumption}
              </div>
            </div>
          </div>
        </div>

        {/* 4.3 Outcome Tracking Targets */}
        <div className="space-y-2">
          <span className="text-xs font-bold text-slate-700 uppercase tracking-wider block">
            Continuous Outcome Tracking Matrix (Weekly & Monthly Cadence)
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
            {pilotModel.outcome_tracking.map((ot: any, i: number) => (
              <div key={i} className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
                <div>
                  <span className="text-[10px] font-semibold text-indigo-700 uppercase tracking-wider">{ot.cadence}</span>
                  <div className="text-xs font-bold text-slate-900 mt-1">{ot.indicator}</div>
                </div>
                <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-[10px] text-slate-500 font-medium">Target:</span>
                  <span className="text-xs font-mono font-bold text-emerald-700">{ot.target}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Section 5: Institutional Roles & RACI Governance Matrix */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-2.5">
            <ShieldCheck className="w-5 h-5 text-purple-600" />
            <div>
              <h2 className="text-lg font-bold text-slate-800">Institutional Roles & RACI Governance Matrix</h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Clear multi-agency accountability defining decision owners, authoritative data stewards, and operational executors.
              </p>
            </div>
          </div>
          <span className="text-xs text-purple-700 font-semibold px-2.5 py-1 bg-purple-50 border border-purple-200 rounded-lg shrink-0">
            5 CORE GOVERNANCE FUNCTIONS
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-100 text-slate-600 uppercase font-semibold">
              <tr>
                <th className="py-2.5 px-4 rounded-l-lg">Tourism Function</th>
                <th className="py-2.5 px-4">Decision Owner</th>
                <th className="py-2.5 px-4">Data Owner</th>
                <th className="py-2.5 px-4">Implementation Owner</th>
                <th className="py-2.5 px-4 rounded-r-lg">Review Cadence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {raciMatrix.map((row: any, idx: number) => (
                <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-4 font-semibold text-slate-800 flex items-center gap-2">
                    <Award className="w-3.5 h-3.5 text-purple-600 shrink-0" />
                    <span>{row.function}</span>
                  </td>
                  <td className="py-3 px-4 font-medium text-slate-900">
                    <span className="px-2 py-0.5 rounded bg-purple-100 text-purple-800 font-semibold text-[11px]">
                      {row.decision_owner}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-600 font-medium">
                    <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200/60 text-[11px]">
                      {row.data_owner}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-700">{row.implementation_owner}</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-medium text-[11px]">
                      {row.review_cadence}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Section 6: Grounded AI Decision Intelligence Query Assistant */}
      <div className="bg-gradient-to-br from-slate-900 via-indigo-950 to-purple-950 text-white rounded-2xl p-6 border border-purple-500/40 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-6 pb-4 border-b border-purple-800/40">
          <div className="flex items-center gap-2.5">
            <Sparkles className="w-5 h-5 text-amber-400" />
            <div>
              <h2 className="text-lg font-bold text-white">Evidence Query Assistant</h2>
              <p className="text-xs text-purple-200/80 mt-0.5">
                Evidence-grounded structured query assistant strictly synthesizing verified statistics from DuckDB analytical tables.
              </p>
            </div>
          </div>
          <span className="px-2.5 py-1 rounded bg-amber-400/20 text-amber-300 border border-amber-400/30 text-xs font-semibold shrink-0">
            STRUCTURED EVIDENCE GROUNDING
          </span>
        </div>

        {/* Dynamic State Selection Strip (Plan Section 13.2) */}
        {stateProfiles && (
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4 bg-white/5 p-3.5 rounded-xl border border-white/10">
            <div className="flex items-center gap-2">
              <Compass className="w-4 h-4 text-amber-400" />
              <span className="text-xs font-semibold text-purple-200">
                Dynamic State Query Lookup (16 States & FTs):
              </span>
            </div>
            <div className="flex items-center gap-2">
              <select
                value={selectedStateQuery}
                onChange={(e) => {
                  setSelectedStateQuery(e.target.value);
                  if (e.target.value) setActiveQuery('');
                }}
                className="bg-slate-800 text-white text-xs rounded-lg px-3 py-1.5 border border-purple-400/40 focus:outline-none focus:ring-2 focus:ring-purple-400 cursor-pointer"
              >
                <option value="">-- Select Any State for Structured Evidence --</option>
                {Object.keys(stateProfiles).sort().map((st) => (
                  <option key={st} value={st}>{st}</option>
                ))}
              </select>
              {selectedStateQuery && (
                <button
                  onClick={() => {
                    setSelectedStateQuery('');
                    setActiveQuery('melaka_capacity');
                  }}
                  className="text-xs text-amber-300 hover:text-white px-2 py-1 rounded bg-white/10 border border-white/15 transition-all cursor-pointer"
                >
                  Reset to Presets
                </button>
              )}
            </div>
          </div>
        )}

        {/* Preset Query Buttons */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2.5 mb-6">
          {Object.entries(groundedQueries).map(([key, q]) => (
            <button
              key={key}
              onClick={() => {
                setSelectedStateQuery('');
                setActiveQuery(key);
              }}
              className={`p-3 rounded-xl text-left border transition-all text-xs ${
                activeQuery === key && !selectedStateQuery
                  ? 'bg-purple-600/40 border-purple-400 text-white ring-2 ring-purple-400/30 shadow'
                  : 'bg-white/5 border-white/10 text-purple-200 hover:bg-white/10'
              }`}
            >
              <div className="font-semibold text-white mb-1">{q.title}</div>
              <div className="text-purple-200/70 text-[11px] line-clamp-2">{q.question}</div>
            </button>
          ))}
        </div>

        {/* Answer Evidence Box */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl p-5 border border-white/15 space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <span className="text-[11px] font-semibold text-purple-300 uppercase tracking-wider block">Question:</span>
              <h3 className="text-sm font-bold text-white mt-0.5">{selectedQueryData.question}</h3>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 rounded text-xs font-medium">
                Confidence: {selectedQueryData.confidence}
              </span>
            </div>
          </div>

          <div className="bg-black/30 p-4 rounded-lg border border-white/10 text-xs text-purple-100 leading-relaxed">
            {selectedQueryData.answer}
          </div>

          {/* Quantitative Metrics Row */}
          <div>
            <span className="text-[11px] font-semibold text-purple-300 uppercase tracking-wider block mb-2">
              Empirical Fact Evidence:
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
              {Object.entries(selectedQueryData.metrics).map(([k, v], i) => (
                <div key={i} className="bg-white/5 p-2.5 rounded-lg border border-white/10">
                  <div className="text-[10px] text-purple-300/80 truncate">{k}</div>
                  <div className="text-xs font-bold text-amber-300 mt-0.5">{v}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Strategic Recommendation */}
          <div className="bg-amber-500/10 border border-amber-400/30 rounded-lg p-3 text-xs flex items-start gap-2.5">
            <TrendingUp className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-amber-300">Policy Recommendation: </span>
              <span className="text-amber-100">{selectedQueryData.recommendation}</span>
            </div>
          </div>

          {/* Source & Caveat */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between text-[11px] text-purple-300/70 border-t border-white/10 pt-3 gap-2">
            <div><strong>Official Source:</strong> {selectedQueryData.source}</div>
            <div className="italic"><strong>Limitation:</strong> {selectedQueryData.limitation}</div>
          </div>
        </div>
      </div>
    </div>
  );
};
