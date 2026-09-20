import React from 'react';
import ReactECharts from 'echarts-for-react';
import type { TSAMacroData } from '../types';
import { 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle2, 
  BarChart3, 
  PieChart, 
  Info
} from 'lucide-react';

interface TourismValueMonitorProps {
  data: TSAMacroData;
}

export const TourismValueMonitor: React.FC<TourismValueMonitorProps> = ({ data }) => {
  const macroSeries = data.macro_series || [];
  const productSummary = data.product_summary || [];
  const latest = macroSeries.find((year) => year.year === 2025);
  const baseline = macroSeries.find((year) => year.year === 2015);
  const accommodation = productSummary.find((product) => product.product_id === 'accommodation');
  const transport = productSummary.find((product) => product.product_id === 'passenger_transport');
  const food = productSummary.find((product) => product.product_id === 'food_beverage');
  const formatBillion = (million: number) => (million / 1000).toFixed(1);

  // Macro Timeline ECharts Option
  const macroTimelineOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: '#b5a5d7', width: 1 } },
      backgroundColor: '#ffffff',
      borderColor: 'rgba(70, 50, 100, 0.16)',
      textStyle: { color: '#241d32', fontSize: 12 },
      formatter: (params: any) => {
        let res = `<div style="font-weight: bold; margin-bottom: 4px;">Year ${params[0].name}</div>`;
        params.forEach((item: any) => {
          res += `<div style="display: flex; justify-content: space-between; gap: 12px;">
            <span>${item.marker} ${item.seriesName}:</span>
            <span style="font-family: monospace; font-weight: bold;">RM ${item.value.toFixed(1)} B</span>
          </div>`;
        });
        return res;
      },
    },
    legend: {
      data: ['Internal Tourism Consumption (ITC)', 'Tourism Direct GVA (TDGVA)'],
      textStyle: { color: '#746d80' },
      top: 0,
      right: 10,
    },
    grid: { left: '3%', right: '3%', bottom: '5%', top: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      data: macroSeries.map((d) => d.year),
      axisLine: { lineStyle: { color: '#d6d0df' } },
      axisLabel: { color: '#746d80' },
    },
    yAxis: {
      type: 'value',
      name: 'RM Billion',
      nameTextStyle: { color: '#746d80', padding: [0, 0, 0, 20] },
      splitLine: { lineStyle: { color: 'rgba(70, 50, 100, 0.09)' } },
      axisLabel: { color: '#746d80' },
    },
    series: [
      {
        name: 'Internal Tourism Consumption (ITC)',
        type: 'line',
        smooth: true,
        data: macroSeries.map((d) => d.total_itc / 1000),
        itemStyle: { color: '#8b8798' },
        lineStyle: { width: 3 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(139, 135, 152, 0.10)' },
              { offset: 1, color: 'rgba(139, 135, 152, 0)' },
            ],
          },
        },
      },
      {
        name: 'Tourism Direct GVA (TDGVA)',
        type: 'line',
        smooth: true,
        data: macroSeries.map((d) => d.tdgva / 1000),
        itemStyle: { color: '#6d4bc1' },
        lineStyle: { width: 3 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(109, 75, 193, 0.10)' },
              { offset: 1, color: 'rgba(109, 75, 193, 0)' },
            ],
          },
        },
      },
    ],
  };

  // Product VAI Ranking ECharts Option
  const sortedByVAI = [...productSummary].sort((a, b) => a.vai_2025 - b.vai_2025);
  const vaiRankingOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#ffffff',
      borderColor: 'rgba(70, 50, 100, 0.16)',
      textStyle: { color: '#241d32', fontSize: 12 },
      formatter: (params: any) => {
        const item = params[0];
        const pObj = productSummary.find((p) => p.product === item.name);
        return `<div style="font-weight: bold; margin-bottom: 4px;">${item.name}</div>
          <div>VAI (2025): <strong style="color: #6544b5;">${(item.value * 100).toFixed(1)}%</strong></div>
          <div>ITC Scale: <strong>RM ${formatBillion(pObj?.itc_2025 || 0)} B</strong></div>
          <div>Quadrant: <span style="color: #b9782f;">${pObj?.strategic_quadrant || 'N/A'}</span></div>`;
      },
    },
    grid: { left: '3%', right: '8%', bottom: '5%', top: '5%', containLabel: true },
    xAxis: {
      type: 'value',
      min: 0,
      max: 1,
      axisLabel: { 
        color: '#746d80',
        formatter: (val: number) => `${(val * 100).toFixed(0)}%` 
      },
      splitLine: { lineStyle: { color: 'rgba(70, 50, 100, 0.09)' } },
    },
    yAxis: {
      type: 'category',
      data: sortedByVAI.map((p) => p.product),
      axisLabel: { color: '#241d32', fontSize: 11 },
      axisLine: { lineStyle: { color: '#d6d0df' } },
    },
    series: [
      {
        name: 'VAI 2025',
        type: 'bar',
        data: sortedByVAI.map((p) => ({
          value: p.vai_2025,
          itemStyle: {
            color: p.product.includes('Accommodation')
              ? '#6d4bc1'
              : '#b8b1c0',
          },
        })),
        label: {
          show: true,
          position: 'right',
          color: '#241d32',
          formatter: (params: any) => `${(params.value * 100).toFixed(1)}%`,
          fontSize: 11,
          fontWeight: 'bold',
        },
      },
    ],
  };

  // Strategic Quadrant Scatter Option (VAI vs ITC Scale)
  const quadrantScatterOption = {
    backgroundColor: 'transparent',
    tooltip: {
      backgroundColor: '#ffffff',
      borderColor: 'rgba(70, 50, 100, 0.16)',
      textStyle: { color: '#241d32', fontSize: 12 },
      formatter: (params: any) => {
        const d = params.data;
        return `<div style="font-weight: bold; margin-bottom: 4px;">${d[2]}</div>
          <div>VAI (Efficiency): <strong>${(d[1] * 100).toFixed(1)}%</strong></div>
          <div>ITC (Scale): <strong>RM ${d[0].toFixed(1)} Billion</strong></div>
          <div>Quadrant: <strong style="color: #6d4bc1;">${d[3]}</strong></div>`;
      },
    },
    grid: { left: '8%', right: '8%', bottom: '10%', top: '10%' },
    xAxis: {
      type: 'value',
      name: 'Internal Consumption Scale (RM Billion)',
      nameLocation: 'middle',
      nameGap: 30,
      nameTextStyle: { color: '#746d80' },
      axisLabel: { color: '#746d80' },
      splitLine: { lineStyle: { color: 'rgba(70, 50, 100, 0.09)' } },
    },
    yAxis: {
      type: 'value',
      name: 'Value-Added Intensity (VAI)',
      nameTextStyle: { color: '#746d80' },
      axisLabel: { 
        color: '#746d80',
        formatter: (val: number) => `${(val * 100).toFixed(0)}%` 
      },
      splitLine: { lineStyle: { color: 'rgba(70, 50, 100, 0.09)' } },
      min: 0.2,
      max: 0.95,
    },
    series: [
      {
        type: 'scatter',
        symbolSize: (data: any) => Math.max(13, Math.sqrt(data[0]) * 4),
        data: productSummary.map((p) => [
          p.itc_2025 / 1000,
          p.vai_2025,
          p.product,
          p.strategic_quadrant,
        ]),
        itemStyle: {
          color: (param: any) => {
            const name = param.data[2];
            if (name.includes('Accommodation')) return '#6d4bc1';
            if (param.data[1] >= 0.5 && param.data[0] >= 10) return '#8b8798';
            if (param.data[1] < 0.5 && param.data[0] >= 10) return '#b9782f';
            return '#9673c8';
          },
          shadowBlur: 0,
        },
        label: {
          show: true,
          formatter: (param: any) => param.data[2].split(' ')[0],
          position: 'top',
          color: '#241d32',
          fontSize: 10,
        },
      },
    ],
  };

  return (
    <div className="space-y-6">
      {/* Top Value Headline */}
      <div className="glass-panel p-6 border-l-4 border-l-violet-400">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-violet-600/20 text-violet-700">
                Core Empirical Finding
              </span>
              <span className="text-xs text-stone-600">Research Question 1 & 2</span>
            </div>
            <h2 className="text-2xl font-bold text-stone-900 tracking-tight">
              Accommodation is Malaysia's Most Value-Efficient Tourism Product
            </h2>
            <p className="text-sm text-stone-700 mt-1 max-w-3xl">
              In the 2025 Tourism Satellite Account, accommodation has the highest value-added intensity at <strong>{((accommodation?.vai_2025 || 0) * 100).toFixed(1)}%</strong>. This is the share of its domestic supply represented by GVA, compared with <strong>{((food?.vai_2025 || 0) * 100).toFixed(1)}%</strong> for food services and <strong>{((transport?.vai_2025 || 0) * 100).toFixed(1)}%</strong> for passenger transport.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="p-4 rounded-xl bg-white/90 border border-violet-400/30 text-center min-w-[140px]">
              <span className="text-xs text-stone-600 uppercase font-semibold">Accom VAI</span>
              <div className="text-3xl font-extrabold text-violet-700 font-mono">{((accommodation?.vai_2025 || 0) * 100).toFixed(1)}%</div>
              <span className="text-[10px] text-violet-700">Rank #1 across all 8 sectors</span>
            </div>
            <div className="p-4 rounded-xl bg-white/90 border border-indigo-300/30 text-center min-w-[140px]">
              <span className="text-xs text-stone-600 uppercase font-semibold">2025 TDGVA</span>
              <div className="text-3xl font-extrabold text-indigo-600 font-mono">RM {formatBillion(latest?.tdgva || 0)}B</div>
              <span className="text-[10px] text-indigo-600">{latest ? ((latest.tdgva / latest.total_itc) * 100).toFixed(1) : '—'}% of total ITC</span>
            </div>
          </div>
        </div>
      </div>

      {/* Grid: Macro Timeline & VAI Ranking */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Macro Timeline */}
        <div className="glass-panel p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-stone-900 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-violet-700" />
                TSA Macro Trajectory (2015–2025)
              </h3>
              <p className="text-xs text-stone-600">Internal Consumption vs. Direct Economic Value Added</p>
            </div>
            <span className="text-[11px] px-2 py-0.5 rounded bg-violet-50 text-stone-700 font-mono">
              Pre-COVID → Recovery → Equilibrium
            </span>
          </div>

          <div className="h-[320px]">
            <ReactECharts option={macroTimelineOption} style={{ height: '100%', width: '100%' }} />
          </div>

          <div className="mt-3 pt-3 border-t border-violet-100/60 flex items-center justify-between text-xs text-stone-600">
            <span>2015 baseline: RM {formatBillion(baseline?.total_itc || 0)}B ITC / RM {formatBillion(baseline?.tdgva || 0)}B TDGVA</span>
            <span className="text-violet-700 font-medium">2025 ITC: RM {formatBillion(latest?.total_itc || 0)}B</span>
          </div>
        </div>

        {/* Product VAI Ranking */}
        <div className="glass-panel p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-stone-900 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-indigo-600" />
                Value-Added Intensity (VAI) by Product (2025)
              </h3>
              <p className="text-xs text-stone-600">Proportion of industry gross output represented by GVA</p>
            </div>
            <span className="text-[11px] px-2 py-0.5 rounded bg-violet-600/20 text-violet-700 font-medium">
              VAI = GVA / Supply
            </span>
          </div>

          <div className="h-[320px]">
            <ReactECharts option={vaiRankingOption} style={{ height: '100%', width: '100%' }} />
          </div>

          <div className="mt-3 pt-3 border-t border-violet-100/60 text-xs text-stone-600 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-violet-700 shrink-0" />
            <span>Accommodation retains the highest local economic value; transport and fuel suffer high leakage.</span>
          </div>
        </div>
      </div>

      {/* Grid: Strategic Quadrant & Travel Agency Interpretation Guardrail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Strategic Quadrant Matrix (2 cols) */}
        <div className="glass-panel p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-base font-bold text-stone-900 flex items-center gap-2">
                <PieChart className="w-4 h-4 text-amber-700" />
                Strategic Product Portfolio Matrix (VAI vs. ITC Scale)
              </h3>
              <p className="text-xs text-stone-600">Classifies tourism products into strategic intervention priority quadrants</p>
            </div>
            <div className="flex items-center gap-2 text-[11px]">
              <span className="flex items-center gap-1 text-violet-700"><span className="w-2 h-2 rounded-full bg-violet-600"></span> Core Activity</span>
              <span className="flex items-center gap-1 text-indigo-600"><span className="w-2 h-2 rounded-full bg-indigo-400"></span> Growth Opp</span>
              <span className="flex items-center gap-1 text-amber-700"><span className="w-2 h-2 rounded-full bg-amber-500"></span> Efficiency Priority</span>
            </div>
          </div>

          <div className="h-[300px]">
            <ReactECharts option={quadrantScatterOption} style={{ height: '100%', width: '100%' }} />
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-4 pt-3 border-t border-violet-100/60 text-xs">
            <div className="p-2 rounded bg-white/60 border border-violet-400/20">
              <div className="font-bold text-violet-700">Core High-Value</div>
              <div className="text-[11px] text-stone-600">High VAI + High Scale (Accommodation, Food & Beverage)</div>
            </div>
            <div className="p-2 rounded bg-white/60 border border-indigo-300/20">
              <div className="font-bold text-indigo-600">Growth Opportunity</div>
              <div className="text-[11px] text-stone-600">High VAI + Emerging Scale (Cultural & Eco-Tourism)</div>
            </div>
            <div className="p-2 rounded bg-white/60 border border-amber-500/20">
              <div className="font-bold text-amber-700">Efficiency Priority</div>
              <div className="text-[11px] text-stone-600">High Scale + Lower VAI (Transport, Retail Shopping)</div>
            </div>
            <div className="p-2 rounded bg-white/60 border border-purple-500/20">
              <div className="font-bold text-violet-700">Niche / Specialized</div>
              <div className="text-[11px] text-stone-600">Lower immediate macro priority</div>
            </div>
          </div>
        </div>

        {/* Travel Agency & Statistical Guardrails (1 col) */}
        <div className="glass-panel p-5 flex flex-col justify-between space-y-4">
          <div>
            <h3 className="text-base font-bold text-stone-900 flex items-center gap-2 mb-1">
              <Info className="w-4 h-4 text-indigo-600" />
              Accounting Guardrail Note
            </h3>
            <span className="text-[11px] text-stone-600 uppercase font-semibold">AGENTS.md Section 10 Guidance</span>

            <div className="mt-3 p-3 rounded-lg bg-white/80 border border-violet-100 space-y-2 text-xs text-stone-700">
              <div className="font-semibold text-stone-900 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
                Travel Agencies & Reservation Services:
              </div>
              <p>
                In 2025, Travel Agency VAI moderated not because industry output contracted, but because <strong>gross supply increased significantly faster (+24%) than value added (+8%)</strong>.
              </p>
              <p className="text-stone-600 text-[11px]">
                Underlying factors: Aggressive digital platform bookings, foreign travel intermediary fees, and OTA transaction margins.
              </p>
            </div>

            <div className="mt-3 p-3 rounded-lg bg-white/80 border border-violet-100 space-y-1.5 text-xs text-stone-700">
              <div className="font-semibold text-stone-900">Definition of Value-Added Intensity:</div>
              <p className="font-mono text-violet-700 text-[11px]">
                VAI[i,t] = GVA[i,t] / DomesticSupply[i,t]
              </p>
              <p className="text-stone-600 text-[11px]">
                Measures the proportion of industry output retained as direct domestic economic value.
              </p>
            </div>
          </div>

          <div className="p-2.5 rounded bg-violet-600/10 border border-violet-400/30 text-[11px] text-violet-700">
            <strong>Strategic Takeaway:</strong> Prioritizing accommodation expenditure produces the greatest economic ripple per ringgit of visitor spend in Malaysia.
          </div>
        </div>
      </div>
    </div>
  );
};
