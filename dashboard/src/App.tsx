import { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { TourismValueMonitor } from './components/TourismValueMonitor';
import { AccommodationMap } from './components/AccommodationMap';
import { CorridorNetwork } from './components/CorridorNetwork';
import { ScenarioSimulator } from './components/ScenarioSimulator';
import type { 
  TSAMacroData, 
  StateProfile, 
  ODCorridorsData, 
  ScenarioEngineConfig, 
  DriversData 
} from './types';
import { 
  Loader2, 
  AlertOctagon, 
  ShieldCheck, 
  Globe2, 
  BookOpen, 
  FileSpreadsheet,
  Layers
} from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState<'monitor' | 'map' | 'corridors' | 'simulator'>('monitor');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [tsaData, setTsaData] = useState<TSAMacroData | null>(null);
  const [stateProfiles, setStateProfiles] = useState<Record<string, StateProfile> | null>(null);
  const [geoJson, setGeoJson] = useState<any | null>(null);
  const [corridorData, setCorridorData] = useState<ODCorridorsData | null>(null);
  const [scenarioConfig, setScenarioConfig] = useState<ScenarioEngineConfig | null>(null);
  const [driversData, setDriversData] = useState<DriversData | null>(null);

  useEffect(() => {
    async function loadAllDatasets() {
      try {
        setLoading(true);
        setError(null);

        const baseUrl = import.meta.env.BASE_URL || '/';
        const cleanBase = baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`;

        const [
          tsaRes, 
          statesRes, 
          geoRes, 
          corridorsRes, 
          scenarioRes, 
          driversRes
        ] = await Promise.all([
          fetch(`${cleanBase}data/tsa_macro.json`),
          fetch(`${cleanBase}data/state_profiles.json`),
          fetch(`${cleanBase}data/geo_malaysia.json`),
          fetch(`${cleanBase}data/od_corridors.json`),
          fetch(`${cleanBase}data/scenario_engine.json`),
          fetch(`${cleanBase}data/drivers_rq3.json`),
        ]);

        if (!tsaRes.ok || !statesRes.ok || !geoRes.ok || !corridorsRes.ok || !scenarioRes.ok || !driversRes.ok) {
          throw new Error(`Data fetch failed with status: ${tsaRes.status}/${statesRes.status}/${geoRes.status}`);
        }

        const [
          tsaJson,
          statesJson,
          geoData,
          corridorsJson,
          scenarioJson,
          driversJson
        ] = await Promise.all([
          tsaRes.json(),
          statesRes.json(),
          geoRes.json(),
          corridorsRes.json(),
          scenarioRes.json(),
          driversRes.json()
        ]);

        setTsaData(tsaJson);
        setStateProfiles(statesJson);
        setGeoJson(geoData);
        setCorridorData(corridorsJson);
        setScenarioConfig(scenarioJson);
        setDriversData(driversJson);
      } catch (err: any) {
        console.error('Failed to load dataset:', err);
        setError(err.message || 'Error loading dashboard datasets.');
      } finally {
        setLoading(false);
      }
    }

    loadAllDatasets();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-emerald-500/30 selection:text-emerald-300">
      {/* Executive Application Header */}
      <Header 
        activeTab={activeTab} 
        onSelectTab={setActiveTab} 
      />

      {/* Main Content Body */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 py-6">
        {loading && (
          <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
            <div className="relative">
              <Loader2 className="w-12 h-12 text-emerald-400 animate-spin" />
              <div className="absolute inset-0 rounded-full blur-lg bg-emerald-500/20"></div>
            </div>
            <div className="text-center space-y-1.5">
              <h2 className="text-lg font-bold text-white tracking-wide">
                Initializing Tourism Economic Intelligence Engine
              </h2>
              <p className="text-xs text-slate-400 max-w-md">
                Ingesting DOSM TSA 2015–2025, DTS state panels, Demographics, HIES Table 6, and 240 Origin-Destination corridors...
              </p>
            </div>
          </div>
        )}

        {error && (
          <div className="glass-panel p-8 max-w-2xl mx-auto text-center border-rose-500/30 bg-rose-950/10 space-y-4 my-12">
            <div className="inline-flex p-3 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <AlertOctagon className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold text-white">Dataset Load Failed</h3>
            <p className="text-sm text-slate-400">{error}</p>
            <button 
              onClick={() => window.location.reload()}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors"
            >
              Retry Connection
            </button>
          </div>
        )}

        {!loading && !error && (
          <>
            {/* View 1: Macro & Product Value Monitor */}
            {activeTab === 'monitor' && tsaData && (
              <TourismValueMonitor data={tsaData} />
            )}

            {/* View 2: Accommodation Opportunity Map & State Profiles */}
            {activeTab === 'map' && stateProfiles && geoJson && driversData && (
              <AccommodationMap 
                stateProfiles={stateProfiles} 
                geoJson={geoJson}
                driversData={driversData}
              />
            )}

            {/* View 3: Origin-Destination Value Network Corridors */}
            {activeTab === 'corridors' && corridorData && geoJson && (
              <CorridorNetwork 
                corridorData={corridorData} 
                geoJson={geoJson} 
              />
            )}

            {/* View 4: Policy Intervention Scenario Simulator */}
            {activeTab === 'simulator' && scenarioConfig && stateProfiles && (
              <ScenarioSimulator 
                scenarioConfig={scenarioConfig} 
                stateProfiles={stateProfiles} 
              />
            )}
          </>
        )}
      </main>

      {/* Comprehensive Methodological Footer */}
      <footer className="w-full border-t border-slate-800/80 bg-slate-950/90 backdrop-blur-md mt-16 py-10 text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Core Mandate */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-white font-bold">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Analytical Mandate</span>
            </div>
            <p className="text-slate-400 leading-relaxed text-[11px]">
              The core strategic shift of the <strong className="text-slate-200">Malaysia Tourism Value Optimizer</strong> is moving policy focus from volume expansion (<em>"more visitors"</em>) to economic value capture (<em>"more value from existing visitors"</em>) via length of stay extension, accommodation yield, and corridor targeting.
            </p>
            <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/60 text-[11px] text-slate-300">
              <span className="text-emerald-400 font-semibold">Strategic Principle:</span> High visitor volume with low ALOS strains local infrastructure without generating proportional domestic economic retention.
            </div>
          </div>

          {/* Official Sources & Citations */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-white font-bold">
              <BookOpen className="w-4 h-4 text-cyan-400" />
              <span>Official Data Sources</span>
            </div>
            <ul className="space-y-2 text-[11px] text-slate-400">
              <li className="flex items-start gap-1.5">
                <FileSpreadsheet className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
                <span><strong>DOSM Tourism Satellite Account (TSA) 2015–2025:</strong> Official TDGVA, TDGDP, Domestic Supply, Tourism Ratios, and Employment.</span>
              </li>
              <li className="flex items-start gap-1.5">
                <FileSpreadsheet className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
                <span><strong>DOSM Domestic Tourism Survey (DTS) 2018–2025:</strong> State-level visitors, excursionists, tourists, expenditure components, and ALOS.</span>
              </li>
              <li className="flex items-start gap-1.5">
                <FileSpreadsheet className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
                <span><strong>DOSM HIES Table 6 & Open Data Population:</strong> Working-age population, household counts, and median household income panels.</span>
              </li>
            </ul>
          </div>

          {/* SDG Alignment & Guardrails */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-white font-bold">
              <Globe2 className="w-4 h-4 text-emerald-400" />
              <span>SDG Alignment & Guardrails</span>
            </div>
            <p className="text-slate-400 leading-relaxed text-[11px]">
              Aligned with <strong className="text-emerald-300">UN SDG 8.9</strong> (sustainable tourism that creates jobs and promotes local culture) and <strong className="text-cyan-300">UN SDG 12.b</strong> (monitoring sustainable tourism impacts).
            </p>
            <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-200/90 leading-tight">
              <strong>Guardrail:</strong> This decision system measures the <em>economic dimension of sustainable tourism</em>. Environmental and social carryover are analytical extensions. All simulation outputs state: <em>"Scenario estimate, not a causal forecast."</em>
            </div>
          </div>

          {/* System Metadata */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-white font-bold">
              <Layers className="w-4 h-4 text-teal-400" />
              <span>Platform & Governance</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2 text-[11px]">
              <div className="flex justify-between">
                <span className="text-slate-400">Architecture:</span>
                <span className="text-slate-200 font-mono">React 18 + TS + ECharts</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Database:</span>
                <span className="text-slate-200 font-mono">DuckDB Analytical DB</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Corridors Modeled:</span>
                <span className="text-cyan-400 font-mono font-bold">240 Inter-State Pairs</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Data Revision Flags:</span>
                <span className="text-slate-200 font-mono">e (est), p (prelim), r (rev)</span>
              </div>
            </div>
            <p className="text-[10px] text-slate-400 text-right">
              Malaysia Tourism Value Optimizer • Datathon 2026
            </p>
          </div>
        </div>

        {/* Bottom copyright line */}
        <div className="max-w-7xl mx-auto px-4 pt-6 border-t border-slate-800/40 flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] text-slate-400">
          <div>
            © 2026 Malaysia Tourism Value Optimizer (MYTourism Value Intelligence). Built for National Tourism Economic Optimization.
          </div>
          <div className="flex items-center gap-3">
            <span>Powered by DuckDB & Apache ECharts</span>
            <span>•</span>
            <span className="text-emerald-400 font-semibold">Strict AGENTS.md Compliance</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
