import React, { useState } from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import { ArrowRight, Info, TrendingUp } from 'lucide-react';
import type { TSAMacroData } from '../types';

interface TourismValueMonitorProps {
  data: TSAMacroData;
  onExploreMap?: () => void;
}

const percent = (value: number | undefined) =>
  value != null && Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : 'Unavailable';
const billion = (value: number | undefined) =>
  value != null && Number.isFinite(value) ? `RM ${(value / 1000).toFixed(1)}B` : 'Unavailable';
const currency = (value: number | undefined) =>
  value != null && Number.isFinite(value) ? `RM ${Math.round(value).toLocaleString()}` : 'Unavailable';
const shortNames: Record<string, string> = {
  accommodation: 'Accommodation',
  country_specific_goods: 'Tourism goods / retail',
  food_beverage: 'Food & beverage',
  passenger_transport: 'Passenger transport',
  travel_agency: 'Travel agencies',
  cultural_sports_recreation: 'Culture, sports & recreation',
  country_specific_services: 'Other tourism services',
  automotive_fuel: 'Automotive fuel retail',
};
const chartBase: EChartsOption = {
  backgroundColor: 'transparent',
  textStyle: { fontFamily: 'Inter, sans-serif', color: '#57534e' },
  aria: { enabled: true },
  tooltip: { trigger: 'axis', confine: true, backgroundColor: '#fff', borderColor: '#e8e3ed', textStyle: { color: '#251d32' } },
};

export const TourismValueMonitor: React.FC<TourismValueMonitorProps> = ({ data, onExploreMap }) => {
  const [contextOpen, setContextOpen] = useState(false);
  const [comparisonMode, setComparisonMode] = useState<'value' | 'labor'>('value');
  const macro = [...(data.macro_series || data.macro_timeseries || [])].sort((a, b) => a.year - b.year);
  const series = data.product_series || data.product_timeseries || [];
  const products = data.product_summary || data.product_rankings || [];
  const accommodation = products.find(p => p.product_id === 'accommodation');
  const latest = macro.find(p => p.year === 2025);

  const rankedByValue = [...products].filter(p => Number.isFinite(p.vai_2025)).sort((a, b) => b.vai_2025 - a.vai_2025);
  const vaiRank = rankedByValue.findIndex(p => p.product_id === 'accommodation') + 1;
  const maxITC = Math.max(1, ...products.map(p => Number.isFinite(p.itc_2025) ? p.itc_2025 : 0));

  const productsWithLabor = products.map(p => {
    const empK = p.employment_2025_thousands;
    const gvaM = p.gva_2025;
    const laborProd = (empK && empK > 0 && Number.isFinite(gvaM)) ? (gvaM / empK) * 1000 : 0;
    const empIntensity = (gvaM && gvaM > 0 && Number.isFinite(empK)) ? (empK * 1000) / gvaM : 0;
    return { ...p, laborProd, empIntensity, empK: empK || 0 };
  });

  const rankedByLabor = [...productsWithLabor].sort((a, b) => b.laborProd - a.laborProd);
  const laborRank = rankedByLabor.findIndex(p => p.product_id === 'accommodation') + 1;
  const maxLaborProd = Math.max(1, ...productsWithLabor.map(p => p.laborProd));
  const maxEmpIntensity = Math.max(1, ...productsWithLabor.map(p => p.empIntensity));

  const ranked = comparisonMode === 'value' ? rankedByValue : rankedByLabor;

  const years = [...new Set(series.map(p => p.year))].sort((a, b) => a - b);
  const accommodationSeries = series.filter(p => p.product_id === 'accommodation');
  const anomalies = accommodationSeries.filter(p => p.vai > 1);
  const comparisonIds = ['accommodation', 'country_specific_goods', 'food_beverage', 'passenger_transport'];
  const colors = ['#6544b5', '#047857', '#b45309', '#64748b'];

  const preCovidMacro = macro.find(p => p.year === 2019);
  const preCovidRetention = preCovidMacro && preCovidMacro.total_itc > 0
    ? (preCovidMacro.tdgva / preCovidMacro.total_itc) * 100
    : null;
  const latestRetention = latest && latest.total_itc > 0
    ? (latest.tdgva / latest.total_itc) * 100
    : null;
  const retentionDelta = (latestRetention != null && preCovidRetention != null)
    ? latestRetention - preCovidRetention
    : null;

  const trend: EChartsOption = {
    ...chartBase,
    legend: { bottom: 0, type: 'scroll', textStyle: { color: '#57534e', fontSize: 11 } },
    grid: { left: 12, right: 20, top: 32, bottom: 60, containLabel: true },
    xAxis: { type: 'category', data: years.map(String), boundaryGap: false, axisLabel: { color: '#57534e' } },
    yAxis: { type: 'value', min: 0, name: 'VAI (%)', axisLabel: { formatter: '{value}%' }, splitLine: { lineStyle: { color: '#eeeaf2' } } },
    series: comparisonIds.map((id, index) => ({
      name: shortNames[id], type: 'line', connectNulls: false, symbolSize: index === 0 ? 7 : 4,
      lineStyle: { width: index === 0 ? 3 : 1.5, type: index === 0 ? 'solid' : 'dashed' },
      itemStyle: { color: colors[index] },
      data: years.map(year => {
        const row = series.find(p => p.product_id === id && p.year === year);
        return row && Number.isFinite(row.vai) ? Number((row.vai * 100).toFixed(1)) : null;
      }),
      ...(index === 0 ? {
        markArea: { silent: true, itemStyle: { color: '#fef3c7', opacity: 0.45 }, label: { color: '#92400e', fontSize: 10 }, data: [[{ name: '2020–2022 disruption', xAxis: '2020' }, { xAxis: '2022' }]] },
      } : {}),
    })),
  };

  const macroChart: EChartsOption = {
    ...chartBase,
    legend: { bottom: 0, textStyle: { color: '#57534e', fontSize: 11 } },
    grid: { left: 12, right: 38, top: 32, bottom: 45, containLabel: true },
    xAxis: { type: 'category', data: macro.map(p => String(p.year)), boundaryGap: false },
    yAxis: [
      {
        type: 'value',
        name: 'RM billion',
        splitLine: { lineStyle: { color: '#eeeaf2' } },
        axisLabel: { formatter: 'RM {value}B' },
      },
      {
        type: 'value',
        name: 'TDGVA / ITC (%)',
        min: 45,
        max: 70,
        interval: 5,
        splitLine: { show: false },
        axisLabel: { formatter: '{value}%' },
      },
    ],
    tooltip: {
      trigger: 'axis',
      confine: true,
      backgroundColor: '#fff',
      borderColor: '#e8e3ed',
      textStyle: { color: '#251d32' },
      formatter: (params: any) => {
        if (!Array.isArray(params) || params.length === 0) return '';
        const title = `<strong>Year ${params[0].name}</strong>`;
        const lines = params.map((item: any) => {
          const isPct = item.seriesIndex === 2;
          const val = item.value != null ? (isPct ? `${Number(item.value).toFixed(1)}%` : `RM ${Number(item.value).toFixed(1)}B`) : 'N/A';
          return `<div style="display:flex;justify-content:space-between;gap:16px;font-size:12px;margin-top:3px;">
            <span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background-color:${item.color};margin-right:6px;"></span>${item.seriesName}</span>
            <span style="font-weight:600;font-variant-numeric:tabular-nums;">${val}</span>
          </div>`;
        });
        return `${title}<div style="margin-top:4px;">${lines.join('')}</div>`;
      },
    },
    series: [
      {
        name: 'Internal tourism consumption (ITC)',
        type: 'line',
        data: macro.map(p => Number.isFinite(p.total_itc) ? Number((p.total_itc / 1000).toFixed(1)) : null),
        itemStyle: { color: '#78716c' },
        lineStyle: { width: 1.8, type: 'dashed' },
      },
      {
        name: 'Tourism direct GVA (TDGVA)',
        type: 'line',
        data: macro.map(p => Number.isFinite(p.tdgva) ? Number((p.tdgva / 1000).toFixed(1)) : null),
        itemStyle: { color: '#6544b5' },
        lineStyle: { width: 2.2 },
      },
      {
        name: 'Value retention (TDGVA / ITC)',
        type: 'line',
        yAxisIndex: 1,
        data: macro.map(p => (p.total_itc > 0 && Number.isFinite(p.tdgva)) ? Number(((p.tdgva / p.total_itc) * 100).toFixed(1)) : null),
        itemStyle: { color: '#d97706' },
        lineStyle: { width: 2.5 },
        symbol: 'circle',
        symbolSize: 6,
      },
    ],
  };

  if (!products.length) return (
    <div className="glass-panel p-8 text-stone-700" role="status">
      <h2 className="text-lg font-bold">Tourism value evidence is unavailable</h2>
      <p className="mt-2 text-sm">Product data is needed to compare accommodation with other tourism activities. Please reload or check the data source.</p>
    </div>
  );

  return (
    <div className="space-y-6">
      <section className="glass-panel overflow-hidden border-t-4 border-t-violet-600 p-5 sm:p-7" aria-labelledby="monitor-title">
        <div className="flex flex-wrap items-center gap-2 text-xs font-semibold">
          <span className="rounded-full bg-violet-100 px-3 py-1 text-violet-900">01 / Monitor · The economic case</span>
          <span className="rounded-full bg-amber-50 px-3 py-1 text-amber-900">2025p · preliminary</span>
        </div>
        <h2 id="monitor-title" className="mt-4 max-w-3xl text-2xl font-bold tracking-tight text-stone-900 sm:text-3xl">Why accommodation deserves a closer look</h2>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-stone-600">The policy question is how to generate more economic value from existing tourism demand. Compare the value-added intensity, consumption scale and historical performance of accommodation before deciding where to intervene.</p>
        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          {[
            { label: 'Value-added intensity · 2025', value: percent(accommodation?.vai_2025), note: vaiRank ? `Rank ${vaiRank} of ${rankedByValue.length} compared activities · GVA / domestic supply` : 'Accommodation ranking unavailable' },
            { label: 'Accommodation consumption · 2025', value: billion(accommodation?.itc_2025), note: 'Internal tourism consumption · domestic and inbound scope' },
            { label: 'Post-recovery median VAI', value: percent(accommodation?.post_recovery_median_vai), note: `2023–2025 · pre-COVID median ${percent(accommodation?.pre_covid_median_vai)}` },
          ].map(card => (
            <div key={card.label} className="rounded-xl border border-violet-100 bg-white/80 p-4">
              <p className="text-xs font-medium text-stone-600">{card.label}</p>
              <p className="mt-2 text-3xl font-bold tabular-nums text-violet-800">{card.value}</p>
              <p className="mt-2 text-xs leading-relaxed text-stone-600">{card.note}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="glass-panel p-5 sm:p-6" aria-labelledby="sector-comparison-title">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-violet-700">01 · Compare the alternatives</p>
            <h3 id="sector-comparison-title" className="mt-2 text-xl font-bold text-stone-900">
              {comparisonMode === 'value'
                ? 'High intensity matters. So does the size of the activity.'
                : 'Labor productivity vs. employment capacity'}
            </h3>
          </div>
          <div className="inline-flex rounded-lg bg-stone-100 p-1 self-start sm:self-auto" role="tablist" aria-label="Sector comparison metric view">
            <button
              type="button"
              role="tab"
              aria-selected={comparisonMode === 'value'}
              onClick={() => setComparisonMode('value')}
              className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-all ${
                comparisonMode === 'value'
                  ? 'bg-white text-violet-900 shadow-sm'
                  : 'text-stone-600 hover:text-stone-900'
              }`}
            >
              Value & Scale (VAI & ITC)
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={comparisonMode === 'labor'}
              onClick={() => setComparisonMode('labor')}
              className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-all ${
                comparisonMode === 'labor'
                  ? 'bg-white text-violet-900 shadow-sm'
                  : 'text-stone-600 hover:text-stone-900'
              }`}
            >
              Labor & Jobs Profile
            </button>
          </div>
        </div>

        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-stone-600">
          {comparisonMode === 'value'
            ? 'Read across each row: the left bar shows value-added intensity; the right shows tourism consumption. Activities are ordered by 2025 VAI. Purple identifies accommodation.'
            : 'Read across each row: the left bar shows labor productivity (GVA / worker); the right shows employment intensity (jobs generated per RM 1M GVA). Ordered by labor productivity.'}
        </p>

        <div className="mt-5 hidden grid-cols-[minmax(150px,1fr)_minmax(0,1fr)_minmax(0,1fr)] gap-6 border-b border-stone-200 pb-3 text-xs font-semibold text-stone-600 sm:grid" aria-hidden="true">
          <span>Tourism activity</span>
          <span>{comparisonMode === 'value' ? 'Value-added intensity (%)' : 'Labor productivity (RM / worker)'}</span>
          <span>{comparisonMode === 'value' ? 'Internal tourism consumption (RM B)' : 'Employment intensity (Jobs / RM 1M GVA)'}</span>
        </div>

        <ul className="mt-2 space-y-1" aria-label={comparisonMode === 'value' ? '2025 activity comparison, ordered by value-added intensity' : '2025 activity comparison, ordered by labor productivity'}>
          {ranked.map(p => {
            const selected = p.product_id === 'accommodation';
            const empK = p.employment_2025_thousands;
            const gvaM = p.gva_2025;
            const laborProd = (empK && empK > 0 && Number.isFinite(gvaM)) ? (gvaM / empK) * 1000 : 0;
            const empIntensity = (gvaM && gvaM > 0 && Number.isFinite(empK)) ? (empK * 1000) / gvaM : 0;

            return (
              <li key={p.product_id} className={`grid gap-3 rounded-lg px-3 py-3 sm:grid-cols-[minmax(150px,1fr)_minmax(0,1fr)_minmax(0,1fr)] sm:items-center sm:gap-6 ${selected ? 'bg-violet-50 ring-1 ring-inset ring-violet-200' : 'border-b border-stone-100'}`}>
                <div className="flex flex-col">
                  <span title={p.product} className={`text-sm ${selected ? 'font-bold text-violet-900' : 'font-medium text-stone-700'}`}>
                    {shortNames[p.product_id] || p.product}
                  </span>
                  {comparisonMode === 'labor' && (
                    <span className="text-[11px] text-stone-500">
                      {empK ? `${empK.toFixed(1)}k workers` : 'Workforce n/a'}
                    </span>
                  )}
                </div>

                {comparisonMode === 'value' ? (
                  <>
                    <div>
                      <div className="mb-1 flex justify-between gap-2 text-xs tabular-nums"><span className="text-stone-500 sm:sr-only">VAI</span><span className="font-semibold text-stone-800">{percent(p.vai_2025)}</span></div>
                      <div className="h-2 rounded-full bg-stone-100" aria-hidden="true"><div className={`h-full rounded-full ${selected ? 'bg-violet-600' : 'bg-stone-400'}`} style={{ width: `${Math.max(0, Math.min(100, p.vai_2025 * 100))}%` }} /></div>
                    </div>
                    <div>
                      <div className="mb-1 flex justify-between gap-2 text-xs tabular-nums"><span className="text-stone-500 sm:sr-only">ITC</span><span className="font-semibold text-stone-800">{billion(p.itc_2025)}</span></div>
                      <div className="h-2 rounded-full bg-stone-100" aria-hidden="true"><div className={`h-full rounded-full ${selected ? 'bg-violet-600' : 'bg-stone-400'}`} style={{ width: `${Number.isFinite(p.itc_2025) ? Math.max(0, p.itc_2025 / maxITC * 100) : 0}%` }} /></div>
                    </div>
                  </>
                ) : (
                  <>
                    <div>
                      <div className="mb-1 flex justify-between gap-2 text-xs tabular-nums"><span className="text-stone-500 sm:sr-only">Labor Productivity</span><span className="font-semibold text-stone-800">{currency(laborProd)}/worker</span></div>
                      <div className="h-2 rounded-full bg-stone-100" aria-hidden="true"><div className={`h-full rounded-full ${selected ? 'bg-violet-600' : 'bg-stone-400'}`} style={{ width: `${Math.max(0, Math.min(100, (laborProd / maxLaborProd) * 100))}%` }} /></div>
                    </div>
                    <div>
                      <div className="mb-1 flex justify-between gap-2 text-xs tabular-nums"><span className="text-stone-500 sm:sr-only">Employment Intensity</span><span className="font-semibold text-stone-800">{empIntensity.toFixed(1)} jobs / RM 1M</span></div>
                      <div className="h-2 rounded-full bg-stone-100" aria-hidden="true"><div className={`h-full rounded-full ${selected ? 'bg-violet-600' : 'bg-stone-400'}`} style={{ width: `${Math.max(0, Math.min(100, (empIntensity / maxEmpIntensity) * 100))}%` }} /></div>
                    </div>
                  </>
                )}
              </li>
            );
          })}
        </ul>

        {comparisonMode === 'value' ? (
          <p className="mt-4 rounded-lg bg-stone-50 p-3 text-sm leading-relaxed text-stone-700">
            <strong>What this tells us:</strong> {accommodation && vaiRank > 0 ? `Accommodation ranks ${vaiRank} of ${rankedByValue.length} activities for VAI, with ${billion(accommodation.itc_2025)} in tourism consumption. ` : ''}Compare both columns before choosing a priority: high intensity and large consumption are different strengths. Bar lengths use separate scales for each column.
          </p>
        ) : (
          <p className="mt-4 rounded-lg border border-violet-100 bg-violet-50/70 p-3 text-sm leading-relaxed text-stone-700">
            <strong>Strategic labor takeaway (Balanced Pillar):</strong> Accommodation ranks <strong>{laborRank} of {rankedByLabor.length}</strong> in labor productivity ({currency(accommodation ? (accommodation.gva_2025 / accommodation.employment_2025_thousands) * 1000 : 0)}/worker) while sustaining <strong>241.4k jobs</strong> (8.0 jobs per RM 1M GVA). It acts as a balanced economic anchor—avoiding the workforce sparsity of niche high-productivity sectors (Culture: 58.6k; Travel: 30.2k) and the lower value-retention of high-job sectors like F&B (RM 39,430/worker). <em>Note: Reported industry employment; not proof of job quality or causality.</em>
          </p>
        )}
      </section>

      <section className="glass-panel p-5 sm:p-6" aria-labelledby="persistence-title">
        <p className="text-xs font-bold uppercase tracking-wider text-violet-700">02 · Check the pattern over time</p>
        <h3 id="persistence-title" className="mt-2 text-xl font-bold text-stone-900">Does accommodation’s strength persist beyond one year?</h3>
        <p className="mt-2 text-sm leading-relaxed text-stone-600">Compare period medians first, then use the annual chart to see changes and disruption. The chart shows accommodation and three major consumption activities.</p>
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          {[
            ['Pre-COVID · 2015–2019', accommodation?.pre_covid_median_vai],
            ['Disruption · 2020–2022', accommodation?.disruption_median_vai],
            ['Post-recovery · 2023–2025', accommodation?.post_recovery_median_vai],
          ].map(([label, value]) => (
            <div key={String(label)} className="rounded-lg border border-stone-200 p-4">
              <p className="text-xs font-medium text-stone-600">{label}</p>
              <p className="mt-1 text-2xl font-bold tabular-nums text-violet-800">{percent(value as number | undefined)}</p>
              <p className="mt-1 text-xs text-stone-500">Accommodation median VAI</p>
            </div>
          ))}
        </div>
        {years.length ? <div className="mt-4" role="img" aria-label="Annual value-added intensity of accommodation, retail goods, food and beverage, and passenger transport. Period medians are listed above; disruption years are shaded."><ReactECharts option={trend} style={{ height: 330, width: '100%' }} /></div> : <p className="py-8 text-sm text-stone-600">Annual product data is unavailable.</p>}
        {anomalies.length > 0 && <div className="mt-3 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs leading-relaxed text-amber-950"><Info className="mt-0.5 h-4 w-4 shrink-0" /><p><strong>Data caveat:</strong> Accommodation VAI exceeds 100% in {anomalies.map(p => `${p.year} (${percent(p.vai)})`).join(', ')}. Values are shown without capping. This requires source and accounting-scope review; it should not be interpreted as exceptional value retention.</p></div>}
        <p className="mt-3 text-xs leading-relaxed text-stone-600">Accommodation VAI coefficient of variation, 2023–2025: <strong>{percent(accommodation?.post_recovery_cv)}</strong>. This describes variation in the ratio across three years, not investment risk or employment resilience.</p>
      </section>

      <section className="rounded-2xl border border-violet-200 bg-violet-50 p-5 sm:p-6" aria-labelledby="policy-next-title">
        <p className="text-xs font-bold uppercase tracking-wider text-violet-700">03 · Turn the evidence into a targeting question</p>
        <h3 id="policy-next-title" className="mt-2 text-xl font-bold text-violet-950">Where could existing demand support more paid nights?</h3>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-stone-700">The sector evidence supports investigating accommodation. A domestic intervention also needs destination evidence: overnight tourist demand, length of stay, paid accommodation use and available capacity.</p>
        <ol className="mt-5 grid gap-3 md:grid-cols-3">
          {[
            ['Find the opportunity', 'Identify states with substantial tourist flows and relatively short stays or weak accommodation spending.'],
            ['Check feasibility', 'Examine paid lodging use and room capacity before proposing packages, events or longer-stay itineraries.'],
            ['Test the potential', 'Use the corridor and scenario views to estimate additional nights and spending under explicit assumptions.'],
          ].map(([title, description], i) => <li key={title} className="rounded-xl bg-white/80 p-4"><span className="text-xs font-bold text-violet-700">0{i + 1}</span><h4 className="mt-1 text-sm font-bold text-stone-900">{title}</h4><p className="mt-2 text-xs leading-relaxed text-stone-600">{description}</p></li>)}
        </ol>
        {onExploreMap && <button id="monitor-explore-accommodation" type="button" onClick={onExploreMap} className="btn-primary mt-5 px-4 py-3">Explore state accommodation opportunities <ArrowRight className="h-4 w-4 shrink-0" /></button>}
        <p className="mt-4 text-xs text-stone-600">Scenario estimate, not a causal forecast. High average VAI does not establish the marginal return or cost-effectiveness of a policy.</p>
      </section>

      <details id="monitor-national-context" className="glass-panel p-5 sm:p-6" onToggle={event => setContextOpen(event.currentTarget.open)}>
        <summary className="cursor-pointer text-sm font-bold text-stone-800 focus-visible:outline-2 focus-visible:outline-violet-700">Supporting evidence · national context, employment and definitions</summary>
        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          {[
            ['2025 internal tourism consumption', billion(latest?.total_itc)],
            ['2025 tourism direct GVA', billion(latest?.tdgva)],
            ['2025 TDGVA / ITC', latest && latest.total_itc > 0 ? percent(latest.tdgva / latest.total_itc) : 'Unavailable'],
          ].map(([label, value]) => <div key={label} className="rounded-lg bg-stone-50 p-4"><p className="text-xs text-stone-600">{label}</p><p className="mt-2 text-xl font-bold tabular-nums text-stone-900">{value}</p></div>)}
        </div>

        <div className="mt-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <h3 className="flex items-center gap-2 text-sm font-bold text-stone-800">
            <TrendingUp className="h-4 w-4 text-violet-700" />
            National tourism consumption, direct value added & retention trend (2015–2025)
          </h3>
          <span className="text-xs text-stone-500 font-medium">Dual-axis: RM Billion (Left) vs. TDGVA / ITC % (Right)</span>
        </div>

        {contextOpen && (macro.length > 0 ? <ReactECharts option={macroChart} style={{ height: 290, width: '100%' }} /> : <p className="py-5 text-sm text-stone-600">National time series is unavailable.</p>)}

        <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50/60 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="flex h-2 w-2 rounded-full bg-amber-500" />
              <span className="text-xs font-bold uppercase tracking-wider text-amber-900">Macro Value Retention Gap (2015–2025)</span>
            </div>
            {preCovidRetention != null && latestRetention != null && (
              <span className="text-xs font-semibold text-amber-800">
                Pre-COVID (2019): {preCovidRetention.toFixed(1)}% → 2025p: {latestRetention.toFixed(1)}% ({retentionDelta != null && retentionDelta < 0 ? `${retentionDelta.toFixed(1)} pp` : `+${retentionDelta?.toFixed(1)} pp`})
              </span>
            )}
          </div>
          <p className="mt-2 text-xs leading-relaxed text-stone-700">
            Between 2019 and 2025, visitor expenditure (ITC) expanded rapidly (+30.1% to RM 236.9B), but Tourism Direct GVA grew at a slower rate (+20.8% to RM 123.5B). Consequently, national direct value retention fell by 4.1 percentage points. This illustrates why visitor volume and spending expansion alone experiences diminishing value capture unless directed toward high-retention activities such as accommodation.
          </p>
        </div>

        <div className="mt-4 grid gap-4 text-sm sm:grid-cols-2">
          <div className="rounded-lg border border-stone-200 p-4"><h4 className="font-semibold text-stone-900">Accommodation employment · 2025</h4><p className="mt-2 text-2xl font-bold text-violet-800">{accommodation && Number.isFinite(accommodation.employment_2025_thousands) ? `${accommodation.employment_2025_thousands.toFixed(1)}k` : 'Unavailable'}</p><p className="mt-2 text-xs leading-relaxed text-stone-600">Reported industry employment. This is not evidence of worker nationality, job quality or jobs caused by a tourism policy.</p></div>
          <div className="rounded-lg border border-stone-200 p-4"><h4 className="font-semibold text-stone-900">Accommodation tourism ratio · 2025</h4><p className="mt-2 text-2xl font-bold text-violet-800">{percent(accommodation?.tourism_ratio_2025)}</p><p className="mt-2 text-xs leading-relaxed text-stone-600">Share of relevant domestic supply consumed by visitors. This includes inbound demand and does not isolate domestic tourists.</p></div>
        </div>
        <p className="mt-4 text-xs leading-relaxed text-stone-600">VAI = industry GVA / corresponding domestic supply. Estimated tourism-attributable GVA = ITC × VAI under a proportional allocation assumption; it is not official product-level TDGVA. National TDGVA / ITC is a separate aggregate ratio. The difference between ITC and TDGVA is not a measure of local income leakage.</p>
      </details>
      <footer className="space-y-2 px-1 text-xs leading-relaxed text-stone-600">
        <p>Source: dashboard TSA export, 2015–2025. 2025p = preliminary; e = estimate; r = revised. {accommodationSeries.filter(p => p.data_status !== 'actual').map(p => `${p.year}: ${p.data_status}`).join(' · ')}. VAI and period summaries are derived indicators. Monetary values are shown as reported, without inflation adjustment.</p>
        <p>TSA internal tourism consumption and Domestic Tourism Survey expenditure have different scopes and should not be treated as interchangeable.</p>
        <p>This prototype focuses on the economic dimension of sustainable tourism. Environmental and broader social dimensions are future extensions.</p>
      </footer>
    </div>
  );
};
