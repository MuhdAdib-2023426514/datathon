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
  AlertOctagon
} from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState<'monitor' | 'map' | 'corridors' | 'simulator'>('monitor');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedYear, setSelectedYear] = useState<number>(2025);

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
    <div className="app-shell">
      {/* Executive Application Header */}
      <Header 
        activeTab={activeTab} 
        onSelectTab={setActiveTab} 
        selectedYear={selectedYear}
        onSelectYear={setSelectedYear}
      />

      {/* Main Content Body */}
      <main className="main-content">
        {loading && (
          <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
            <div className="relative">
              <Loader2 className="w-12 h-12 text-violet-700 animate-spin" />
              <div className="absolute inset-0 rounded-full blur-lg bg-violet-600/20"></div>
            </div>
            <div className="text-center space-y-1.5">
              <h2 className="text-lg font-bold text-stone-900 tracking-wide">
                Initializing Tourism Economic Intelligence Engine
              </h2>
              <p className="text-xs text-stone-600 max-w-md">
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
            <h3 className="text-xl font-bold text-stone-900">Dataset Load Failed</h3>
            <p className="text-sm text-stone-600">{error}</p>
            <button 
              onClick={() => window.location.reload()}
              className="px-4 py-2 rounded-lg bg-violet-50 hover:bg-violet-100 text-stone-800 text-xs font-semibold transition-colors"
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
                selectedYear={2025}
              />
            )}

            {/* View 3: Origin-Destination Value Network Corridors */}
            {activeTab === 'corridors' && corridorData && geoJson && (
              <CorridorNetwork 
                corridorData={corridorData} 
                geoJson={geoJson} 
                stateProfiles={stateProfiles || undefined}
                selectedYear={selectedYear}
                onSelectCorridorForScenario={(_dest) => {
                  setActiveTab('simulator');
                }}
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

      <footer className="site-footer">
        <div><strong>PurpleX</strong> · Malaysia Tourism Value Optimizer</div>
        <p>Sources: DOSM Tourism Satellite Account, Domestic Tourism Survey, and HIES. This prototype focuses on the economic dimension of sustainable tourism. Scenario estimates are not causal forecasts.</p>
      </footer>
    </div>
  );
}

export default App;
