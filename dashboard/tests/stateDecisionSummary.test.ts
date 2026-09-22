import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  computeStateBenchmarks,
  computeOccupancyThresholdGap,
  computeStateDecisionSummary,
  type StateBenchmarks,
} from '../src/lib/stateDecisionSummary.ts';
import type { StateProfile } from '../src/types.ts';

const mockState = (overrides: Partial<StateProfile> = {}): StateProfile => {
  return {
    state: 'TestState',
    state_code: 'MY-99',
    region: 'Central',
    archetype_name: 'Test Archetype',
    archetype_desc: 'Test description',
    archetype_color: '#3b82f6',
    cluster_id: 1,
    radar_scores: {
      stay_duration: 50,
      nightly_yield: 50,
      accom_intensity: 50,
      leisure_orientation: 50,
      luxury_supply: 50,
      resident_affluence: 50,
    },
    baseline_2025: {
      visitors_thousands: 1000,
      tourists_thousands: 500,
      excursionists_thousands: 500,
      trips_thousands: 1200,
      alos_days: 2.5,
      spend_per_night_rm: 50,
      spend_per_tourist_rm: 125,
      accommodation_share_pct: 12.0,
      accommodation_expenditure_rm_million: 25.0,
      total_expenditure_rm_million: 200.0,
      hotel_rooms: 5000,
      aor_pct: 60.0,
      resident_median_income_rm: 5000,
      yield_typology: 'Moderate Yield',
      policy_prescription: 'Test prescription',
      ...overrides.baseline_2025,
    },
    demographics: {
      total_population_thousands: 2000,
      total_population_millions: 2.0,
      children_pct: 20,
      working_age_thousands: 1500,
      working_age_pct: 75,
      elderly_pct: 5,
      dependency_ratio: 33,
      households_thousands: 500,
      median_household_income_rm: 5000,
      avg_household_size: 4.0,
      ...overrides.demographics,
    },
    hotel_stars: {
      hotels_5star: 2,
      rooms_5star: 500,
      hotels_4star: 5,
      rooms_4star: 1000,
      hotels_3star: 10,
      rooms_3star: 1500,
      luxury_room_share_pct: 30,
      total_hotels: 30,
      total_rooms: 5000,
      ...overrides.hotel_stars,
    },
    purpose_shares: {
      holiday: 30,
      vfr: 40,
      shopping: 10,
      business: 15,
      medical: 5,
      ...overrides.purpose_shares,
    },
    tourist_income: {
      b40_pct: 40,
      m40_pct: 40,
      t20_pct: 20,
      affluence_index: 100,
      ...overrides.tourist_income,
    },
    time_series: [],
    sdg_metrics: {
      tey_rm_per_day: 200,
      tvay_rm_per_day: 100,
      accommodation_yield_rm_per_night: 50,
      tourism_gva_intensity_pct: 60,
      mapping_coverage_pct: 70,
      estimated_tourism_gva_rm_million: 120,
      dvr_retention_rate_pct: 60,
      real_tey_rm_per_day: 200,
      real_tvay_rm_per_day: 100,
      real_accommodation_yield_rm_per_night: 50,
      epr_ratio: 1.0,
      tir_visitors_per_resident: 5.0,
      ryh_accom_per_household_rm: 500,
      yield_typology: 'Moderate Yield',
      sdg_diagnosis: 'Test diagnosis',
      sdg_policy_action: 'Test action',
      sdg_status_color: '#10b981',
      ...overrides.sdg_metrics,
    },
    ...overrides,
  };
};

test('computeOccupancyThresholdGap handles below, at, above, and unobserved threshold', () => {
  // Below threshold
  const below = computeOccupancyThresholdGap(54.2, 80.0);
  assert.equal(below.status, 'below');
  assert.equal(below.gapPp, 25.8);
  assert.match(below.label, /\+25\.8 pp below illustrative 80% planning threshold/);

  // Exactly at threshold
  const at = computeOccupancyThresholdGap(80.0, 80.0);
  assert.equal(at.status, 'at_or_above');
  assert.equal(at.gapPp, 0);
  assert.match(at.label, /0\.0 pp at or above illustrative 80% planning threshold/);

  // Above threshold
  const above = computeOccupancyThresholdGap(85.5, 80.0);
  assert.equal(above.status, 'at_or_above');
  assert.equal(above.gapPp, 5.5);
  assert.match(above.label, /5\.5 pp at or above illustrative 80% planning threshold/);

  // Unobserved (null / undefined / NaN)
  const unobsNull = computeOccupancyThresholdGap(null, 80.0);
  assert.equal(unobsNull.status, 'unobserved');
  assert.equal(unobsNull.gapPp, null);
  assert.equal(unobsNull.label, 'Occupancy unobserved');

  const unobsNaN = computeOccupancyThresholdGap(NaN, 80.0);
  assert.equal(unobsNaN.status, 'unobserved');
});

test('computeStateBenchmarks computes unweighted medians and ignores missing values without fabricating zeroes', () => {
  const s1 = mockState({
    baseline_2025: {
      ...mockState().baseline_2025,
      alos_days: 2.0,
      spend_per_night_rm: 40,
      accommodation_share_pct: 10,
    },
    sdg_metrics: {
      ...mockState().sdg_metrics,
      tvay_rm_per_day: 80,
    },
  });

  const s2 = mockState({
    baseline_2025: {
      ...mockState().baseline_2025,
      alos_days: 3.0,
      spend_per_night_rm: 60,
      accommodation_share_pct: 14,
    },
    sdg_metrics: {
      ...mockState().sdg_metrics,
      tvay_rm_per_day: 120,
    },
  });

  const s3 = mockState({
    baseline_2025: {
      ...mockState().baseline_2025,
      alos_days: 2.5,
      spend_per_night_rm: 50,
      accommodation_share_pct: 12,
    },
    sdg_metrics: {
      ...mockState().sdg_metrics,
      tvay_rm_per_day: undefined, // missing TVAY
    },
  });

  const benchmarks = computeStateBenchmarks([s1, s2, s3]);
  assert.equal(benchmarks.medianAlos, 2.5);
  assert.equal(benchmarks.medianSpendPerNight, 50);
  assert.equal(benchmarks.medianTvay, 100); // median of [80, 120] = 100
  assert.equal(benchmarks.medianAccomShare, 12);
  assert.equal(benchmarks.observedCount, 3);
});

test('computeStateDecisionSummary classifies all 4 quadrants accurately against benchmarks', () => {
  const benchmarks: StateBenchmarks = {
    medianAlos: 2.5,
    medianSpendPerNight: 50,
    medianTvay: 100,
    medianAccomShare: 12,
    medianTey: 200,
    medianAor: 60,
    observedCount: 16,
  };

  // Quadrant 1: Short stay (< 2.5d) + High yield (TVAY >= 100)
  const q1State = mockState({
    baseline_2025: { ...mockState().baseline_2025, alos_days: 2.1 },
    sdg_metrics: { ...mockState().sdg_metrics, tvay_rm_per_day: 115 },
  });
  const q1Summary = computeStateDecisionSummary(q1State, benchmarks);
  assert.match(q1Summary.primaryConstraint, /rapid visitor turnover or day-trip transit/);
  assert.match(q1Summary.primaryOpportunity, /Stay-extension incentives/);
  assert.equal(q1Summary.observedPerformance.alosStatus, 'below');
  assert.equal(q1Summary.observedPerformance.tvayStatus, 'above');

  // Quadrant 2: Short stay (< 2.5d) + Low yield (TVAY < 100)
  const q2State = mockState({
    baseline_2025: { ...mockState().baseline_2025, alos_days: 2.2 },
    sdg_metrics: { ...mockState().sdg_metrics, tvay_rm_per_day: 85 },
  });
  const q2Summary = computeStateDecisionSummary(q2State, benchmarks);
  assert.match(q2Summary.primaryConstraint, /Below-median stay duration combined with below-median nightly accommodation expenditure/);
  assert.match(q2Summary.primaryOpportunity, /Experiential tourism upgrades/);
  assert.equal(q2Summary.observedPerformance.alosStatus, 'below');
  assert.equal(q2Summary.observedPerformance.tvayStatus, 'below');

  // Quadrant 3: Long stay (>= 2.5d) + Low yield (TVAY < 100)
  const q3State = mockState({
    baseline_2025: { ...mockState().baseline_2025, alos_days: 2.8 },
    sdg_metrics: { ...mockState().sdg_metrics, tvay_rm_per_day: 75 },
    lodging_shares: { unpaid_vfr_pct: 62.0 },
  });
  const q3Summary = computeStateDecisionSummary(q3State, benchmarks);
  assert.match(q3Summary.primaryConstraint, /Extended stay duration with lower commercial accommodation expenditure/);
  assert.match(q3Summary.primaryOpportunity, /Community homestay formalization/);
  assert.equal(q3Summary.observedPerformance.alosStatus, 'above');
  assert.equal(q3Summary.observedPerformance.tvayStatus, 'below');

  // Quadrant 4: Long stay (>= 2.5d) + High yield (TVAY >= 100)
  const q4State = mockState({
    baseline_2025: { ...mockState().baseline_2025, alos_days: 2.9 },
    sdg_metrics: { ...mockState().sdg_metrics, tvay_rm_per_day: 130 },
  });
  const q4Summary = computeStateDecisionSummary(q4State, benchmarks);
  assert.match(q4Summary.primaryConstraint, /peak-period capacity bottlenecks/);
  assert.match(q4Summary.primaryOpportunity, /Preserve high-yield value capture/);
  assert.equal(q4Summary.observedPerformance.alosStatus, 'above');
  assert.equal(q4Summary.observedPerformance.tvayStatus, 'above');
});

test('computeStateDecisionSummary handles missing TVAY via explicit fallback to spend/night', () => {
  const benchmarks: StateBenchmarks = {
    medianAlos: 2.5,
    medianSpendPerNight: 50,
    medianTvay: 100,
    medianAccomShare: 12,
    medianTey: 200,
    medianAor: 60,
    observedCount: 16,
  };

  const stateWithoutTvay = mockState({
    baseline_2025: { ...mockState().baseline_2025, alos_days: 2.2, spend_per_night_rm: 65 },
    sdg_metrics: { ...mockState().sdg_metrics, tvay_rm_per_day: undefined },
  });

  const summary = computeStateDecisionSummary(stateWithoutTvay, benchmarks);
  assert.equal(summary.isFallbackYield, true);
  assert.match(summary.yieldLabel, /Spend\/Night/);
  assert.match(summary.yieldLabel, /\[TVAY unobserved\]/);
  assert.equal(summary.observedPerformance.tvay, null);
  assert.equal(summary.observedPerformance.tvayStatus, 'unobserved');
  assert.equal(summary.observedPerformance.spendStatus, 'above');
});

test('exact equality with benchmark is classified as "at" the median', () => {
  const benchmarks: StateBenchmarks = {
    medianAlos: 2.5,
    medianSpendPerNight: 50,
    medianTvay: 100,
    medianAccomShare: 12,
    medianTey: 200,
    medianAor: 60,
    observedCount: 16,
  };

  const stateAtMedian = mockState({
    baseline_2025: { ...mockState().baseline_2025, alos_days: 2.5, spend_per_night_rm: 50, accommodation_share_pct: 12 },
    sdg_metrics: { ...mockState().sdg_metrics, tvay_rm_per_day: 100 },
  });

  const summary = computeStateDecisionSummary(stateAtMedian, benchmarks);
  assert.equal(summary.observedPerformance.alosStatus, 'at');
  assert.equal(summary.observedPerformance.spendStatus, 'at');
  assert.equal(summary.observedPerformance.tvayStatus, 'at');
  assert.equal(summary.observedPerformance.accomShareStatus, 'at');
  assert.equal(summary.observedPerformance.alosDiff, 0);
  assert.equal(summary.observedPerformance.spendDiff, 0);
  assert.equal(summary.observedPerformance.tvayDiff, 0);
  assert.equal(summary.observedPerformance.accomShareDiff, 0);
});
