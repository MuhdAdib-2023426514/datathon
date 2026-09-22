import { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { TourismValueMonitor } from './components/TourismValueMonitor';
import { AccommodationMap } from './components/AccommodationMap';
import { CorridorNetwork } from './components/CorridorNetwork';
import { ScenarioSimulator } from './components/ScenarioSimulator';
import { ProvenanceDrawer } from './components/ProvenanceDrawer';
import { ImplementationRoadmap } from './components/ImplementationRoadmap';
import type { 
  TSAMacroData, 
  StateProfile, 
  ODCorridorsData, 
  ScenarioEngineConfig, 
  DriversData,
  ModelMetricsData,
  BookingHotelBenchmarksData
} from './types';
import { 
  Loader2, 
  AlertOctagon
} from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState<'monitor' | 'map' | 'corridors' | 'simulator' | 'implementation'>('monitor');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedYear, setSelectedYear] = useState<number>(2025);
  const [selectedDestination, setSelectedDestination] = useState<string | null>(null);
  const [selectedOrigin, setSelectedOrigin] = useState<string | null>(null);
  const [showProvenanceDrawer, setShowProvenanceDrawer] = useState<boolean>(false);

  // Data states
  const [tsaData, setTsaData] = useState<TSAMacroData | null>(null);
  const [stateProfiles, setStateProfiles] = useState<Record<string, StateProfile> | null>(null);
  const [geoJson, setGeoJson] = useState<any | null>(null);
  const [corridorData, setCorridorData] = useState<ODCorridorsData | null>(null);
  const [scenarioConfig, setScenarioConfig] = useState<ScenarioEngineConfig | null>(null);
  const [driversData, setDriversData] = useState<DriversData | null>(null);
  const [modelMetrics, setModelMetrics] = useState<ModelMetricsData | null>(null);
  const [bookingData, setBookingData] = useState<BookingHotelBenchmarksData | null>(null);
  const [sourceMetadata, setSourceMetadata] = useState<any | null>(null);
  const [implementationMetadata, setImplementationMetadata] = useState<any | null>(null);

  // URL query parameter synchronization (Phase 28 shareable / bookmarkable)
  const updateUrlParams = (tab: string, dest?: string | null, origin?: string | null, year?: number) => {
    try {
      const url = new URL(window.location.href);
      url.searchParams.set('tab', tab);
      if (dest) {
        url.searchParams.set('dest', dest);
      } else {
        url.searchParams.delete('dest');
        url.searchParams.delete('destination');
      }
      if (origin) {
        url.searchParams.set('origin', origin);
      } else {
        url.searchParams.delete('origin');
      }
      if (year && year !== 2025) {
        url.searchParams.set('year', year.toString());
      } else {
        url.searchParams.delete('year');
      }
      window.history.pushState(null, '', url.toString());
    } catch (e) {
      console.warn('Could not update URL parameters', e);
    }
  };

  const handleTabChange = (tab: 'monitor' | 'map' | 'corridors' | 'simulator' | 'implementation') => {
    setActiveTab(tab);
    updateUrlParams(tab, selectedDestination, selectedOrigin, selectedYear);
  };

  const handleYearChange = (year: number) => {
    setSelectedYear(year);
    updateUrlParams(activeTab, selectedDestination, selectedOrigin, year);
  };

  const handleSelectCorridorForScenario = (dest: string, origin?: string) => {
    setSelectedDestination(dest);
    setSelectedOrigin(origin || null);
    setActiveTab('simulator');
    updateUrlParams('simulator', dest, origin || null, selectedYear);
  };

  const handleExploreCorridorsForState = (dest: string) => {
    setSelectedDestination(dest);
    setActiveTab('corridors');
    updateUrlParams('corridors', dest, selectedOrigin, selectedYear);
  };

  const handleTestScenarioForState = (dest: string) => {
    setSelectedDestination(dest);
    setSelectedOrigin(null);
    setActiveTab('simulator');
    updateUrlParams('simulator', dest, null, selectedYear);
  };

  // Parse URL query parameters on initial page load
  useEffect(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const tabParam = params.get('tab') as 'monitor' | 'map' | 'corridors' | 'simulator' | null;
      const destParam = params.get('dest') || params.get('destination');
      const originParam = params.get('origin');
      const yearParam = params.get('year');

      if (tabParam && ['monitor', 'map', 'corridors', 'simulator', 'implementation'].includes(tabParam)) {
        setActiveTab(tabParam as any);
      }
      if (destParam) {
        setSelectedDestination(destParam);
      }
      if (originParam) {
        setSelectedOrigin(originParam);
      }
      if (yearParam && !isNaN(Number(yearParam))) {
        setSelectedYear(Number(yearParam));
      }
    } catch (e) {
      console.warn('Could not parse URL query parameters', e);
    }
  }, []);

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
          driversRes,
          metricsRes,
          bookingRes,
          sourceMetaRes,
          implMetaRes
        ] = await Promise.all([
          fetch(`${cleanBase}data/tsa_macro.json`),
          fetch(`${cleanBase}data/state_profiles.json`),
          fetch(`${cleanBase}data/geo_malaysia.json`),
          fetch(`${cleanBase}data/od_corridors.json`),
          fetch(`${cleanBase}data/scenario_engine.json`),
          fetch(`${cleanBase}data/drivers_rq3.json`),
          fetch(`${cleanBase}data/model_metrics.json`),
          fetch(`${cleanBase}data/booking_hotel_benchmarks.json`).catch(() => ({ ok: false })),
          fetch(`${cleanBase}data/source_metadata.json`),
          fetch(`${cleanBase}data/implementation_metadata.json`).catch(() => ({ ok: false })),
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
          driversJson,
          metricsJson,
          bookingJson,
          sourceMetaJson,
          implMetaJson
        ] = await Promise.all([
          tsaRes.json(),
          statesRes.json(),
          geoRes.json(),
          corridorsRes.json(),
          scenarioRes.json(),
          driversRes.json(),
          metricsRes.ok ? metricsRes.json() : null,
          ('ok' in bookingRes && bookingRes.ok) ? (bookingRes as any).json() : null,
          sourceMetaRes.ok ? sourceMetaRes.json() : null,
          ('ok' in implMetaRes && implMetaRes.ok) ? (implMetaRes as any).json() : null,
        ]);

        setTsaData(tsaJson);
        setStateProfiles(statesJson);
        setGeoJson(geoData);
        setCorridorData(corridorsJson);
        setScenarioConfig(scenarioJson);
        setDriversData(driversJson);
        setModelMetrics(metricsJson);
        setBookingData(bookingJson);
        setSourceMetadata(sourceMetaJson);
        setImplementationMetadata(implMetaJson || scenarioJson?.implementation_roadmap || null);
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
        onSelectTab={handleTabChange} 
        selectedYear={selectedYear}
        onSelectYear={handleYearChange}
        onOpenProvenance={() => setShowProvenanceDrawer(true)}
      />

      {/* Main Content Body */}
      <main className="main-content">
        {loading && (
          <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
            <Loader2 className="w-10 h-10 animate-spin text-violet-900" />
            <p className="text-sm text-stone-500 font-medium animate-pulse">
              Hydrating analytical datasets from DuckDB cache...
            </p>
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
              <TourismValueMonitor data={tsaData} onExploreMap={() => handleTabChange('map')} />
            )}

            {/* View 2: Accommodation Opportunity Map & State Profiles */}
            {activeTab === 'map' && stateProfiles && geoJson && driversData && (
              <AccommodationMap 
                stateProfiles={stateProfiles} 
                geoJson={geoJson}
                driversData={driversData}
                bookingData={bookingData}
                selectedYear={2025}
                initialState={selectedDestination}
                onSelectState={(stateName) => {
                  setSelectedDestination(stateName);
                  updateUrlParams('map', stateName, selectedOrigin, 2025);
                }}
                onExploreCorridors={handleExploreCorridorsForState}
                onTestScenario={handleTestScenarioForState}
              />
            )}

            {/* View 3: Origin-Destination Value Network Corridors */}
            {activeTab === 'corridors' && corridorData && geoJson && (
              <CorridorNetwork 
                corridorData={corridorData} 
                geoJson={geoJson} 
                stateProfiles={stateProfiles || undefined}
                selectedYear={selectedYear}
                modelMetrics={modelMetrics}
                onSelectCorridorForScenario={handleSelectCorridorForScenario}
                initialDestination={selectedDestination}
              />
            )}

            {/* View 4: Policy Intervention Scenario Simulator */}
            {activeTab === 'simulator' && scenarioConfig && stateProfiles && (
              <ScenarioSimulator 
                scenarioConfig={scenarioConfig} 
                stateProfiles={stateProfiles} 
                initialDestination={selectedDestination || undefined}
                initialOrigin={selectedOrigin || undefined}
              />
            )}

            {/* View 5: Strategic Implementation Roadmap & Grounded AI Assistant */}
            {activeTab === 'implementation' && (
              <ImplementationRoadmap
                metadata={implementationMetadata || scenarioConfig?.implementation_roadmap}
                stateProfiles={stateProfiles || undefined}
                onNavigateTab={(tab) => handleTabChange(tab as any)}
              />
            )}
          </>
        )}
      </main>

      {/* Global Data Provenance Drawer (Phase 29) */}
      <ProvenanceDrawer 
        isOpen={showProvenanceDrawer} 
        onClose={() => setShowProvenanceDrawer(false)} 
        metadata={sourceMetadata} 
      />

      <footer className="site-footer">
        <div><strong>PurpleX</strong> · Malaysia Tourism Value Optimizer</div>
        <p>Sources: DOSM Tourism Satellite Account, Domestic Tourism Survey, and HIES. This prototype focuses on the economic dimension of sustainable tourism. Scenario estimates are not causal forecasts.</p>
      </footer>
    </div>
  );
}

export default App;
