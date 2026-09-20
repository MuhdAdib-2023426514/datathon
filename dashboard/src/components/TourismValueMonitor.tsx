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

  // Macro Timeline ECharts Option
  const macroTimelineOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0e1526',
      borderColor: 'rgba(255, 255, 255, 0.15)',
      textStyle: { color: '#f8fafc', fontSize: 12 },
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
      textStyle: { color: '#94a3b8' },
      top: 0,
      right: 10,
    },
    grid: { left: '3%', right: '3%', bottom: '5%', top: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      data: macroSeries.map((d) => d.year),
      axisLine: { lineStyle: { color: '#334155' } },
      axisLabel: { color: '#94a3b8' },
    },
    yAxis: {
      type: 'value',
      name: 'RM Billion',
      nameTextStyle: { color: '#94a3b8', padding: [0, 0, 0, 20] },
      splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } },
      axisLabel: { color: '#94a3b8' },
    },
    series: [
      {
        name: 'Internal Tourism Consumption (ITC)',
        type: 'line',
        smooth: true,
        data: macroSeries.map((d) => d.itc),
        itemStyle: { color: '#06b6d4' },
        lineStyle: { width: 3 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(6, 182, 212, 0.3)' },
              { offset: 1, color: 'rgba(6, 182, 212, 0.0)' },
            ],
          },
        },
      },
      {
        name: 'Tourism Direct GVA (TDGVA)',
        type: 'line',
        smooth: true,
        data: macroSeries.map((d) => d.tdgva),
        itemStyle: { color: '#10b981' },
        lineStyle: { width: 3 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
              { offset: 1, color: 'rgba(16, 185, 129, 0.0)' },
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
      backgroundColor: '#0e1526',
      borderColor: 'rgba(255, 255, 255, 0.15)',
      textStyle: { color: '#f8fafc', fontSize: 12 },
      formatter: (params: any) => {
        const item = params[0];
        const pObj = productSummary.find((p) => p.product === item.name);
        return `<div style="font-weight: bold; margin-bottom: 4px;">${item.name}</div>
          <div>VAI (2025): <strong style="color: #34d399;">${(item.value * 100).toFixed(1)}%</strong></div>
          <div>ITC Scale: <strong style="color: #38bdf8;">RM ${(pObj?.itc_2025 || 0).toFixed(1)} B</strong></div>
          <div>Quadrant: <span style="color: #f59e0b;">${pObj?.strategic_quadrant || 'N/A'}</span></div>`;
      },
    },
    grid: { left: '3%', right: '8%', bottom: '5%', top: '5%', containLabel: true },
    xAxis: {
      type: 'value',
      name: 'Value-Added Intensity (VAI)',
      axisLabel: { 
        color: '#94a3b8',
        formatter: (val: number) => `${(val * 100).toFixed(0)}%` 
      },
      splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } },
    },
    yAxis: {
      type: 'category',
      data: sortedByVAI.map((p) => p.product),
      axisLabel: { color: '#f8fafc', fontSize: 11 },
      axisLine: { lineStyle: { color: '#334155' } },
    },
    series: [
      {
        name: 'VAI 2025',
        type: 'bar',
        data: sortedByVAI.map((p) => ({
          value: p.vai_2025,
          itemStyle: {
            color: p.product.includes('Accommodation')
              ? '#10b981'
              : p.vai_2025 > 0.6
              ? '#06b6d4'
              : p.vai_2025 > 0.4
              ? '#f59e0b'
              : '#64748b',
          },
        })),
        label: {
          show: true,
          position: 'right',
          color: '#f8fafc',
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
      backgroundColor: '#0e1526',
      borderColor: 'rgba(255, 255, 255, 0.15)',
      textStyle: { color: '#f8fafc', fontSize: 12 },
      formatter: (params: any) => {
        const d = params.data;
        return `<div style="font-weight: bold; margin-bottom: 4px;">${d[2]}</div>
          <div>VAI (Efficiency): <strong>${(d[1] * 100).toFixed(1)}%</strong></div>
          <div>ITC (Scale): <strong>RM ${d[0].toFixed(1)} Billion</strong></div>
          <div>Quadrant: <strong style="color: #10b981;">${d[3]}</strong></div>`;
      },
    },
    grid: { left: '8%', right: '8%', bottom: '10%', top: '10%' },
    xAxis: {
      type: 'value',
      name: 'Internal Consumption Scale (RM Billion)',
      nameLocation: 'middle',
      nameGap: 30,
      nameTextStyle: { color: '#94a3b8' },
      axisLabel: { color: '#94a3b8' },
      splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } },
    },
    yAxis: {
      type: 'value',
      name: 'Value-Added Intensity (VAI)',
      nameTextStyle: { color: '#94a3b8' },
      axisLabel: { 
        color: '#94a3b8',
        formatter: (val: number) => `${(val * 100).toFixed(0)}%` 
      },
      splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } },
      min: 0.2,
      max: 0.95,
    },
    series: [
      {
        type: 'scatter',
        symbolSize: (data: any) => Math.max(14, Math.sqrt(data[0]) * 7),
        data: productSummary.map((p) => [
          p.itc_2025,
          p.vai_2025,
          p.product,
          p.strategic_quadrant,
        ]),
        itemStyle: {
          color: (param: any) => {
            const name = param.data[2];
            if (name.includes('Accommodation')) return '#10b981';
            if (param.data[1] >= 0.5 && param.data[0] >= 10) return '#06b6d4';
            if (param.data[1] < 0.5 && param.data[0] >= 10) return '#f59e0b';
            return '#8b5cf6';
          },
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)',
        },
        label: {
          show: true,
          formatter: (param: any) => param.data[2].split(' ')[0],
          position: 'top',
          color: '#f8fafc',
          fontSize: 10,
        },
      },
    ],
  };

  return (
    <div className="space-y-6">
      {/* Top Value Headline */}
      <div className="glass-panel p-6 border-l-4 border-l-emerald-500">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
                Core Empirical Finding
              </span>
              <span className="text-xs text-slate-400">Research Question 1 & 2</span>
            </div>
            <h2 className="text-2xl font-bold text-white tracking-tight">
              Accommodation is Malaysia's Most Value-Efficient Tourism Product
            </h2>
            <p className="text-sm text-slate-300 mt-1 max-w-3xl">
              From 2015 to 2025, <strong>Accommodation Services</strong> consistently achieved the highest Value-Added Intensity in Malaysia's Tourism Satellite Account at <strong>85.8%</strong>. Every RM 1,000 spent on accommodation generates approximately <strong>RM 858 in Gross Value Added (GVA)</strong>, far exceeding transport (28.5%) and food services (43.2%).
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="p-4 rounded-xl bg-slate-900/90 border border-emerald-500/30 text-center min-w-[140px]">
              <span className="text-xs text-slate-400 uppercase font-semibold">Accom VAI</span>
              <div className="text-3xl font-extrabold text-emerald-400 font-mono">85.8%</div>
              <span className="text-[10px] text-emerald-300">Rank #1 across all 8 sectors</span>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/90 border border-cyan-500/30 text-center min-w-[140px]">
              <span className="text-xs text-slate-400 uppercase font-semibold">2025 TDGVA</span>
              <div className="text-3xl font-extrabold text-cyan-400 font-mono">RM 59.4B</div>
              <span className="text-[10px] text-cyan-300">52.8% of Total ITC</span>
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
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                TSA Macro Trajectory (2015–2025)
              </h3>
              <p className="text-xs text-slate-400">Internal Consumption vs. Direct Economic Value Added</p>
            </div>
            <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
              Pre-COVID → Recovery → Equilibrium
            </span>
          </div>

          <div className="h-[320px]">
            <ReactECharts option={macroTimelineOption} style={{ height: '100%', width: '100%' }} />
          </div>

          <div className="mt-3 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
            <span>2015 Baseline: RM 67.2B ITC / RM 35.8B TDGVA</span>
            <span className="text-emerald-400 font-medium">2025 Recovery: +67.4% ITC Expansion</span>
          </div>
        </div>

        {/* Product VAI Ranking */}
        <div className="glass-panel p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-cyan-400" />
                Value-Added Intensity (VAI) by Product (2025)
              </h3>
              <p className="text-xs text-slate-400">Proportion of industry gross output represented by GVA</p>
            </div>
            <span className="text-[11px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-medium">
              VAI = GVA / Supply
            </span>
          </div>

          <div className="h-[320px]">
            <ReactECharts option={vaiRankingOption} style={{ height: '100%', width: '100%' }} />
          </div>

          <div className="mt-3 pt-3 border-t border-slate-800/60 text-xs text-slate-400 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
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
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <PieChart className="w-4 h-4 text-amber-400" />
                Strategic Product Portfolio Matrix (VAI vs. ITC Scale)
              </h3>
              <p className="text-xs text-slate-400">Classifies tourism products into strategic intervention priority quadrants</p>
            </div>
            <div className="flex items-center gap-2 text-[11px]">
              <span className="flex items-center gap-1 text-emerald-400"><span className="w-2 h-2 rounded-full bg-emerald-500"></span> Core Activity</span>
              <span className="flex items-center gap-1 text-cyan-400"><span className="w-2 h-2 rounded-full bg-cyan-500"></span> Growth Opp</span>
              <span className="flex items-center gap-1 text-amber-400"><span className="w-2 h-2 rounded-full bg-amber-500"></span> Efficiency Priority</span>
            </div>
          </div>

          <div className="h-[300px]">
            <ReactECharts option={quadrantScatterOption} style={{ height: '100%', width: '100%' }} />
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-4 pt-3 border-t border-slate-800/60 text-xs">
            <div className="p-2 rounded bg-slate-900/60 border border-emerald-500/20">
              <div className="font-bold text-emerald-400">Core High-Value</div>
              <div className="text-[11px] text-slate-400">High VAI + High Scale (Accommodation, Food & Beverage)</div>
            </div>
            <div className="p-2 rounded bg-slate-900/60 border border-cyan-500/20">
              <div className="font-bold text-cyan-400">Growth Opportunity</div>
              <div className="text-[11px] text-slate-400">High VAI + Emerging Scale (Cultural & Eco-Tourism)</div>
            </div>
            <div className="p-2 rounded bg-slate-900/60 border border-amber-500/20">
              <div className="font-bold text-amber-400">Efficiency Priority</div>
              <div className="text-[11px] text-slate-400">High Scale + Lower VAI (Transport, Retail Shopping)</div>
            </div>
            <div className="p-2 rounded bg-slate-900/60 border border-purple-500/20">
              <div className="font-bold text-purple-400">Niche / Specialized</div>
              <div className="text-[11px] text-slate-400">Lower immediate macro priority</div>
            </div>
          </div>
        </div>

        {/* Travel Agency & Statistical Guardrails (1 col) */}
        <div className="glass-panel p-5 flex flex-col justify-between space-y-4">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2 mb-1">
              <Info className="w-4 h-4 text-cyan-400" />
              Accounting Guardrail Note
            </h3>
            <span className="text-[11px] text-slate-400 uppercase font-semibold">AGENTS.md Section 10 Guidance</span>

            <div className="mt-3 p-3 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2 text-xs text-slate-300">
              <div className="font-semibold text-white flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                Travel Agencies & Reservation Services:
              </div>
              <p>
                In 2025, Travel Agency VAI moderated not because industry output contracted, but because <strong>gross supply increased significantly faster (+24%) than value added (+8%)</strong>.
              </p>
              <p className="text-slate-400 text-[11px]">
                Underlying factors: Aggressive digital platform bookings, foreign travel intermediary fees, and OTA transaction margins.
              </p>
            </div>

            <div className="mt-3 p-3 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1.5 text-xs text-slate-300">
              <div className="font-semibold text-white">Definition of Value-Added Intensity:</div>
              <p className="font-mono text-emerald-400 text-[11px]">
                VAI[i,t] = GVA[i,t] / DomesticSupply[i,t]
              </p>
              <p className="text-slate-400 text-[11px]">
                Measures the proportion of industry output retained as direct domestic economic value.
              </p>
            </div>
          </div>

          <div className="p-2.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-[11px] text-emerald-300">
            <strong>Strategic Takeaway:</strong> Prioritizing accommodation expenditure produces the greatest economic ripple per ringgit of visitor spend in Malaysia.
          </div>
        </div>
      </div>
    </div>
  );
};
