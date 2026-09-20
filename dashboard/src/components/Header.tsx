import { BarChart3, MapPin, Route, SlidersHorizontal } from 'lucide-react';

type Tab = 'monitor' | 'map' | 'corridors' | 'simulator';

interface HeaderProps {
  activeTab: Tab;
  onSelectTab: (tab: Tab) => void;
  selectedYear: number;
  onSelectYear: (year: number) => void;
}

const tabs: { id: Tab; label: string; icon: typeof BarChart3 }[] = [
  { id: 'monitor', label: 'Value monitor', icon: BarChart3 },
  { id: 'map', label: 'States & stays', icon: MapPin },
  { id: 'corridors', label: 'Value corridors', icon: Route },
  { id: 'simulator', label: 'Scenario lab', icon: SlidersHorizontal },
];

export function Header({ activeTab, onSelectTab, selectedYear, onSelectYear }: HeaderProps) {
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
          <div className="header-meta"><span className="header-meta-dot" />DOSM data · 2015–2025</div>
        </div>

        <div className="page-intro">
          <div>
            <p className="eyebrow">Tourism economic decision support</p>
            <h1>Turn visitor demand into <em>lasting value.</em></h1>
            <p className="page-intro-copy">Explore where longer stays, accommodation spending, and stronger tourism corridors can create more domestic value.</p>
          </div>
          <div className="intro-note"><span>01 / 04</span><strong>Monitor · Diagnose · Target · Simulate</strong></div>
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
