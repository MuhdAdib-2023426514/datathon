import { BarChart3, MapPin, Route, SlidersHorizontal, BookOpen, Layers } from 'lucide-react';

export type Tab = 'monitor' | 'map' | 'corridors' | 'simulator' | 'implementation';

interface HeaderProps {
  activeTab: Tab;
  onSelectTab: (tab: Tab) => void;
  selectedYear: number;
  onSelectYear: (year: number) => void;
  onOpenProvenance?: () => void;
}

const tabs: { id: Tab; label: string; icon: typeof BarChart3 }[] = [
  { id: 'monitor', label: 'Value monitor', icon: BarChart3 },
  { id: 'map', label: 'States & stays', icon: MapPin },
  { id: 'corridors', label: 'Value corridors', icon: Route },
  { id: 'simulator', label: 'Scenario lab', icon: SlidersHorizontal },
  { id: 'implementation', label: 'Roadmap & Ops', icon: Layers },
];

export function Header({ activeTab, onSelectTab, selectedYear, onSelectYear, onOpenProvenance }: HeaderProps) {
  return (
    <header className="app-header">
      <div className="app-header-inner">
        <div className="brand-row">
          <div className="brand-identity">
            <div className="brand-mark" aria-hidden="true">P<span>X</span></div>
            <div>
              <div className="brand-name">PurpleX <span>/ Tourism intelligence</span></div>
              <p className="brand-caption">Malaysia Tourism Value Optimizer</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="header-meta"><span className="header-meta-dot" />DOSM data · 2015–2025</div>
            {onOpenProvenance && (
              <button
                type="button"
                onClick={onOpenProvenance}
                className="header-meta hover:bg-violet-100/70 hover:text-violet-900 transition-all cursor-pointer flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-violet-200/60"
                title="Open Data Provenance & Methodology Audit Registry"
              >
                <BookOpen size={13} strokeWidth={2} />
                <span>Provenance Registry</span>
              </button>
            )}
          </div>
        </div>

        <div className="page-intro">
          <div>
            <p className="eyebrow">Tourism economic decision support</p>
            <h1>From More Tourists to <em>More Value.</em></h1>
            <p className="page-intro-copy">MYTourism Value Intelligence helps Malaysian destinations identify how to generate greater domestic economic value from each visitor-day while respecting destination capacity and market risk.</p>
          </div>
          <div className="intro-note"><span>01 / 05</span><strong>Monitor · Diagnose · Target · Simulate · Optimize</strong></div>
        </div>

        <div className="toolbar-row">
          <nav className="view-nav" aria-label="Dashboard views">
            {tabs.map(({ id, label, icon: Icon }) => (
              <button key={id} type="button" onClick={() => onSelectTab(id)} className={`view-tab ${activeTab === id ? 'active' : ''}`} aria-current={activeTab === id ? 'page' : undefined}>
                <Icon size={16} strokeWidth={1.8} />{label}
              </button>
            ))}
          </nav>
          {activeTab === 'corridors' && (
            <label className="year-control"><span>Data year</span><select value={selectedYear} onChange={(event) => onSelectYear(Number(event.target.value))}>
              {[2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025].map((year) => <option key={year} value={year}>{year}</option>)}
            </select></label>
          )}
        </div>
      </div>
    </header>
  );
}
