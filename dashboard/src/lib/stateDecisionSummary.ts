import type { StateProfile } from '../types.ts';
import { stateMedian } from './stateComparison.ts';

export interface StateBenchmarks {
  medianAlos: number | null;
  medianSpendPerNight: number | null;
  medianTvay: number | null;
  medianAccomShare: number | null;
  medianTey: number | null;
  medianAor: number | null;
  observedCount: number;
}

export interface ThresholdGap {
  threshold: number;
  actualAor: number | null;
  gapPp: number | null;
  status: 'below' | 'at_or_above' | 'unobserved';
  label: string;
}

export interface StateDecisionSummaryData {
  observedPerformance: {
    alos: number;
    alosDiff: number | null;
    alosStatus: 'above' | 'below' | 'at' | 'unobserved';
    spendPerNight: number | null;
    spendDiff: number | null;
    spendStatus: 'above' | 'below' | 'at' | 'unobserved';
    tvay: number | null;
    tvayDiff: number | null;
    tvayStatus: 'above' | 'below' | 'at' | 'unobserved';
    accomShare: number;
    accomShareDiff: number | null;
    accomShareStatus: 'above' | 'below' | 'at' | 'unobserved';
  };
  primaryConstraint: string;
  primaryOpportunity: string;
  prescription: string;
  evidence: string[];
  hypotheses: string[];
  coverage: string;
  limitations: string;
  thresholdGap: ThresholdGap;
  isFallbackYield: boolean;
  yieldLabel: string;
  yieldBenchmarkLabel: string;
  tvay: number | null;
  tey: number;
  alos: number;
  spendPerNight: number;
  aor: number | null;
  headroomPp: number | null;
}

/**
 * Computes dynamic unweighted benchmark medians across all provided states.
 */
export function computeStateBenchmarks(states: StateProfile[]): StateBenchmarks {
  const alosValues = states.map(s => s.baseline_2025?.alos_days);
  const spendValues = states.map(s => s.baseline_2025?.spend_per_night_rm);
  const tvayValues = states.map(s => s.sdg_metrics?.tvay_rm_per_day);
  const accomShareValues = states.map(s => s.baseline_2025?.accommodation_share_pct);
  const teyValues = states.map(s => s.sdg_metrics?.tey_rm_per_day);
  const aorValues = states.map(s => s.baseline_2025?.aor_pct);

  return {
    medianAlos: stateMedian(alosValues),
    medianSpendPerNight: stateMedian(spendValues),
    medianTvay: stateMedian(tvayValues),
    medianAccomShare: stateMedian(accomShareValues),
    medianTey: stateMedian(teyValues),
    medianAor: stateMedian(aorValues),
    observedCount: states.length,
  };
}

/**
 * Computes the percentage-point threshold gap relative to an illustrative occupancy ceiling.
 */
export function computeOccupancyThresholdGap(aor: number | null | undefined, threshold: number = 80.0): ThresholdGap {
  if (aor == null || !Number.isFinite(aor)) {
    return {
      threshold,
      actualAor: null,
      gapPp: null,
      status: 'unobserved',
      label: 'Occupancy unobserved',
    };
  }

  const diff = threshold - aor;
  if (diff > 0) {
    const gapPp = Number(diff.toFixed(1));
    return {
      threshold,
      actualAor: aor,
      gapPp,
      status: 'below',
      label: `+${gapPp.toFixed(1)} pp below illustrative ${threshold.toFixed(0)}% planning threshold`,
    };
  } else {
    const excessPp = Number(Math.abs(diff).toFixed(1));
    return {
      threshold,
      actualAor: aor,
      gapPp: excessPp,
      status: 'at_or_above',
      label: `${excessPp.toFixed(1)} pp at or above illustrative ${threshold.toFixed(0)}% planning threshold`,
    };
  }
}

function getComparisonStatus(value: number | null | undefined, median: number | null): 'above' | 'below' | 'at' | 'unobserved' {
  if (value == null || !Number.isFinite(value) || median == null || !Number.isFinite(median)) {
    return 'unobserved';
  }
  // Tolerant comparison to avoid floating-point precision jitter
  if (Math.abs(value - median) < 1e-4) return 'at';
  return value > median ? 'above' : 'below';
}

/**
 * Pure function to compute transparent, evidence-based state decision summary.
 * Benchmarks must be passed in rather than hardcoded.
 */
export function computeStateDecisionSummary(
  state: StateProfile,
  benchmarks: StateBenchmarks
): StateDecisionSummaryData {
  const b = state.baseline_2025;
  const sdg = state.sdg_metrics;
  const alos = b.alos_days;
  const tvay = sdg?.tvay_rm_per_day != null && Number.isFinite(sdg.tvay_rm_per_day) ? sdg.tvay_rm_per_day : null;
  const tey = sdg?.tey_rm_per_day ?? 0;
  const spendPerNight = b.spend_per_night_rm;
  const aor = b.aor_pct != null && Number.isFinite(b.aor_pct) ? b.aor_pct : null;
  const vfrShare = state.lodging_shares?.unpaid_vfr_pct;
  const holidayShare = state.purpose_shares?.holiday;

  const thresholdGap = computeOccupancyThresholdGap(aor, 80.0);

  // Benchmarked differences
  const alosDiff = benchmarks.medianAlos != null ? Number((alos - benchmarks.medianAlos).toFixed(2)) : null;
  const alosStatus = getComparisonStatus(alos, benchmarks.medianAlos);

  const spendDiff = spendPerNight != null && benchmarks.medianSpendPerNight != null
    ? Number((spendPerNight - benchmarks.medianSpendPerNight).toFixed(1))
    : null;
  const spendStatus = getComparisonStatus(spendPerNight, benchmarks.medianSpendPerNight);

  const tvayDiff = tvay != null && benchmarks.medianTvay != null
    ? Number((tvay - benchmarks.medianTvay).toFixed(1))
    : null;
  const tvayStatus = getComparisonStatus(tvay, benchmarks.medianTvay);

  const accomShare = b.accommodation_share_pct;
  const accomShareDiff = benchmarks.medianAccomShare != null
    ? Number((accomShare - benchmarks.medianAccomShare).toFixed(1))
    : null;
  const accomShareStatus = getComparisonStatus(accomShare, benchmarks.medianAccomShare);

  // Yield evaluation: prefer TVAY, fall back to spend/night if TVAY is unobserved
  const hasTvay = tvay != null && benchmarks.medianTvay != null;
  const isFallbackYield = !hasTvay;

  let yieldHigh = false;
  let yieldLabel = '';
  let yieldBenchmarkLabel = '';

  if (hasTvay) {
    yieldHigh = tvay >= benchmarks.medianTvay!;
    yieldLabel = `TVAY (RM ${tvay.toFixed(1)}/day)`;
    yieldBenchmarkLabel = `unweighted median TVAY (RM ${benchmarks.medianTvay!.toFixed(1)})`;
  } else if (spendPerNight != null && benchmarks.medianSpendPerNight != null) {
    yieldHigh = spendPerNight >= benchmarks.medianSpendPerNight;
    yieldLabel = `Spend/Night (RM ${spendPerNight.toFixed(1)}/night) [TVAY unobserved]`;
    yieldBenchmarkLabel = `unweighted median Spend/Night (RM ${benchmarks.medianSpendPerNight.toFixed(1)})`;
  } else {
    yieldLabel = 'Yield unobserved';
    yieldBenchmarkLabel = 'benchmark unavailable';
  }

  const alosMedian = benchmarks.medianAlos ?? 2.50;
  const isLongStay = alos >= alosMedian;

  let primaryConstraint = '';
  let primaryOpportunity = '';
  let prescription = '';
  const evidence: string[] = [];
  const hypotheses: string[] = [];

  // Factual evidence base
  if (benchmarks.medianAlos != null) {
    const diffText = alosDiff !== null
      ? alosDiff > 0 ? `+${alosDiff.toFixed(2)}d above` : alosDiff < 0 ? `${alosDiff.toFixed(2)}d below` : 'at'
      : '';
    evidence.push(`Stay duration (${alos.toFixed(2)}d) ${diffText} benchmark median (${benchmarks.medianAlos.toFixed(2)}d)`);
  }

  if (hasTvay) {
    const diffText = tvayDiff !== null
      ? tvayDiff > 0 ? `+RM ${tvayDiff.toFixed(1)} above` : tvayDiff < 0 ? `-RM ${Math.abs(tvayDiff).toFixed(1)} below` : 'at'
      : '';
    evidence.push(`${yieldLabel} ${diffText} ${yieldBenchmarkLabel}`);
  } else if (spendPerNight != null && benchmarks.medianSpendPerNight != null) {
    const diffText = spendDiff !== null
      ? spendDiff > 0 ? `+RM ${spendDiff.toFixed(1)} above` : spendDiff < 0 ? `-RM ${Math.abs(spendDiff).toFixed(1)} below` : 'at'
      : '';
    evidence.push(`${yieldLabel} ${diffText} ${yieldBenchmarkLabel}`);
  }

  if (thresholdGap.status !== 'unobserved') {
    evidence.push(`Annual hotel occupancy at ${aor!.toFixed(1)}% (${thresholdGap.label})`);
  }

  if (vfrShare != null && Number.isFinite(vfrShare)) {
    evidence.push(`Unpaid VFR lodging share: ${vfrShare.toFixed(1)}% of overnight stays`);
  }

  // Four-quadrant transparent strategy with qualified hypotheses and actions to test
  if (!isLongStay && yieldHigh) {
    primaryConstraint = 'Below-median stay duration with rapid visitor turnover or day-trip transit routing';
    primaryOpportunity = 'Stay-extension incentives (+0.3d to +0.5d) and evening leisure economy capture';
    prescription = 'Evaluate weekend staycation incentive vouchers, night-time cultural trails, and attraction bundle passes to test converting short trips into overnight stays.';
    hypotheses.push(`Shorter stays (${alos.toFixed(2)}d) despite above-median nightly spend density indicate transit pass-through or short weekend travel.`);
    if (holidayShare != null && holidayShare > 25) {
      hypotheses.push(`High holiday share (${holidayShare.toFixed(1)}%) suggests existing leisure intent that could support extended overnight packages.`);
    }
  } else if (!isLongStay && !yieldHigh) {
    primaryConstraint = 'Below-median stay duration combined with below-median nightly accommodation expenditure';
    primaryOpportunity = 'Experiential tourism upgrades, boutique heritage accommodation, and in-destination spend capture';
    prescription = 'Upgrade local hospitality standards, pilot curated cultural/ecotourism circuits, and partner with regional transport operators to test raising accommodation spend per visitor-day.';
    hypotheses.push(`Both duration and expenditure density are below median, indicating brief visits with low commercial lodging penetration.`);
  } else if (isLongStay && !yieldHigh) {
    primaryConstraint = 'Extended stay duration with lower commercial accommodation expenditure capture';
    primaryOpportunity = 'Community homestay formalization (SDG 8.9), artisan retail spend trails, and packaged recreational activities';
    prescription = 'Expand MOTAC certified homestay/kampungstay licensing, promote localized culinary & handicraft trails, and test packaged leisure experiences to monetize longer visits.';
    if (vfrShare != null && vfrShare > 50) {
      hypotheses.push(`High unpaid VFR share (${vfrShare.toFixed(1)}%) indicates visitors predominantly stay with friends/relatives rather than commercial hotels.`);
    } else {
      hypotheses.push(`Visitors stay longer than median but commercial lodging yield remains modest.`);
    }
  } else {
    // isLongStay && yieldHigh
    primaryConstraint = 'Potential peak-period capacity bottlenecks and destination carrying capacity management';
    primaryOpportunity = 'Preserve high-yield value capture, encourage off-peak seasonal dispersion, and expand certified sustainable ecotourism';
    prescription = 'Pilot off-peak seasonal incentives, target high-yield repeat visitor segments, and safeguard core cultural/nature assets through visitor dispersion strategies.';
    if (aor != null && aor > 65) {
      hypotheses.push(`Annual occupancy (${aor.toFixed(1)}%) indicates periodic capacity tightening during holiday peaks.`);
    } else {
      hypotheses.push(`Strong performance across both duration and expenditure density with capacity headroom for targeted off-peak growth.`);
    }
  }

  return {
    observedPerformance: {
      alos,
      alosDiff,
      alosStatus,
      spendPerNight,
      spendDiff,
      spendStatus,
      tvay,
      tvayDiff,
      tvayStatus,
      accomShare,
      accomShareDiff,
      accomShareStatus,
    },
    primaryConstraint,
    primaryOpportunity,
    prescription,
    evidence,
    hypotheses,
    coverage: 'Official DOSM DTS 2025 & TSA 2025 Baseline',
    limitations: 'TSA product-level VAI applied to state expenditure composition. Annual occupancy rate masks localized weekend or seasonal surges. 80% planning ceiling is an illustrative benchmark, not an engineering or environmental limit.',
    thresholdGap,
    isFallbackYield,
    yieldLabel,
    yieldBenchmarkLabel,
    tvay,
    tey,
    alos,
    spendPerNight,
    aor,
    headroomPp: thresholdGap.gapPp,
  };
}
