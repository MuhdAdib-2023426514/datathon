export interface TSAMacroYear {
  year: number;
  total_itc: number;
  tdgva: number;
  data_status: string;
}

export interface TourismProductYear {
  year: number;
  product: string;
  industry: string;
  itc: number;
  domestic_supply: number;
  gva: number;
  tourism_ratio: number;
  vai: number;
  estimated_tourism_gva: number;
  data_status: string;
}

export interface ProductSummary {
  product_id: string;
  product: string;
  industry: string;
  itc_2025: number;
  domestic_supply_2025: number;
  gva_2025: number;
  tourism_ratio_2025: number;
  vai_2025: number;
  pre_covid_median_vai: number;
  disruption_median_vai: number;
  post_recovery_median_vai: number;
  post_recovery_cv: number;
  delta_vai_vs_2019: number;
  estimated_tourism_gva_2025: number;
  employment_2025_thousands: number;
  strategic_quadrant: string;
  vai_rank: number;
}

export interface TSAMacroData {
  macro_series?: TSAMacroYear[];
  product_series?: TourismProductYear[];
  product_summary?: ProductSummary[];
  macro_timeseries?: TSAMacroYear[];
  product_timeseries?: TourismProductYear[];
  product_rankings?: ProductSummary[];
  summary?: {
    total_tdgva_2025_b: number;
    tdgva_share_2025_pct: number;
    total_employment_2025_k: number;
    highest_vai_product: string;
    highest_vai_score: number;
  };
  price_index?: PriceIndexItem[];
}

export interface StateDemographics {
  total_population_thousands: number;
  total_population_millions: number;
  adult_15plus_thousands?: number;
  children_0_14_thousands?: number;
  children_pct: number;
  working_age_thousands: number;
  working_age_pct: number;
  elderly_65plus_thousands?: number;
  elderly_pct: number;
  dependency_ratio: number;
  dts_age_classes?: {
    age_15_24_k: number;
    age_15_24_pct: number;
    age_25_39_k: number;
    age_25_39_pct: number;
    age_40_54_k: number;
    age_40_54_pct: number;
    age_55plus_k: number;
    age_55plus_pct: number;
  };
  households_thousands: number;
  median_household_income_rm: number;
  avg_household_size: number;
}

export interface PriceIndexItem {
  year: number;
  index: number;
  base_year: string;
  source: string;
}

export interface StateSDGMetrics {
  tey_rm_per_day: number;
  tvay_rm_per_day?: number;
  accommodation_yield_rm_per_night?: number;
  tourism_gva_intensity_pct?: number;
  mapping_coverage_pct?: number;
  estimated_tourism_gva_rm_million?: number;
  dvr_retention_rate_pct: number;
  real_tey_rm_per_day?: number;
  real_tvay_rm_per_day?: number;
  real_accommodation_yield_rm_per_night?: number;
  epr_ratio: number;
  tir_visitors_per_resident: number;
  ryh_accom_per_household_rm: number;
  yield_typology?: string;
  sdg_diagnosis: string;
  sdg_policy_action: string;
  sdg_status_color: string;
}

export interface StateHotelStars {
  hotels_5star: number;
  rooms_5star: number;
  hotels_4star: number;
  rooms_4star: number;
  hotels_3star: number;
  rooms_3star: number;
  luxury_room_share_pct: number;
  total_hotels: number;
  total_rooms: number;
}

export interface StateLodgingShares {
  unpaid_vfr_pct: number;
  paid_commercial_pct: number;
  hotel_pct: number;
  homestay_pct: number;
  apartment_pct?: number;
}

export interface StateProfile {
  state: string;
  state_code: string;
  region: string;
  archetype_name: string;
  archetype_desc: string;
  archetype_color: string;
  cluster_id: number;
  radar_scores: {
    stay_duration: number;
    nightly_yield: number;
    accom_intensity: number;
    leisure_orientation: number;
    luxury_supply: number;
    resident_affluence: number;
  };
  baseline_2025: {
    visitors_thousands: number;
    tourists_thousands: number;
    excursionists_thousands?: number;
    trips_thousands?: number;
    alos_days: number;
    spend_per_night_rm: number;
    spend_per_tourist_rm: number;
    accommodation_share_pct: number;
    accommodation_expenditure_rm_million: number;
    total_expenditure_rm_million: number;
    hotel_rooms: number | null;
    aor_pct: number | null;
    resident_median_income_rm: number;
    yield_typology?: string;
    policy_prescription?: string;
  };
  clustering_profile?: {
    reference_period: string;
    avg_visitors_thousands: number;
    avg_tourists_thousands: number;
    cluster_id: number;
    archetype_name: string;
  };
  demographics: StateDemographics;
  lodging_shares?: StateLodgingShares;
  sdg_metrics: StateSDGMetrics;
  hotel_stars: StateHotelStars;
  purpose_shares: {
    holiday: number;
    vfr: number;
    shopping: number;
    business: number;
    medical: number;
  };
  tourist_income: {
    b40_pct: number;
    m40_pct: number;
    t20_pct: number;
    affluence_index: number;
  };
  time_series: any[];
}

export interface Corridor {
  year: number;
  origin: string;
  origin_code: string;
  origin_region: string;
  origin_lat?: number;
  origin_lon?: number;
  orig_lat?: number;
  orig_lon?: number;
  destination: string;
  destination_code: string;
  destination_region: string;
  destination_lat?: number;
  destination_lon?: number;
  dest_lat?: number;
  dest_lon?: number;
  is_interstate: boolean;
  tourist_flow_thousands: number;
  dest_alos: number;
  dest_spend_per_tourist: number;
  dest_spend_per_night: number;
  dest_accom_share: number;
  dest_accom_expenditure_m: number;
  corridor_category: string;
  corridor_tier?: string;
  origin_share_of_dest_pct: number;
  gravity_flow_thousands?: number | null;
  gravity_residual?: number | null;
  performance_ratio?: number | null;
  gravity_performance_ratio?: number | null;
  distance_km?: number;
  is_cross_region?: boolean;
  corridor_gravity_category?: string;
}

export interface DestinationConcentration {
  year: number;
  destination: string;
  total_inbound_thousands?: number;
  total_tourists_thousands?: number;
  interstate_inbound_thousands?: number;
  intrastate_tourists_thousands?: number;
  intrastate_share_pct?: number;
  top_feeder_origin?: string;
  top_feeder_state?: string;
  top_feeder_share_pct?: number;
  interstate_origin_hhi?: number | null;
  all_origin_hhi?: number | null;
  hhi?: number | null;
  concentration_tier?: string;
}

export interface ODCorridorsData {
  corridors_2025: Corridor[];
  corridors_by_year?: Record<string | number, Corridor[]>;
  destination_concentration?: DestinationConcentration[];
  destination_concentration_2025?: DestinationConcentration[];
  destination_concentration_by_year?: Record<string | number, DestinationConcentration[]>;
  category_summary?: Record<string, number>;
  category_summary_2025?: Record<string, number>;
}

export interface ScenarioEngineConfig {
  constants: {
    accommodation_vai: number;
    fnb_vai?: number;
    overall_tourism_vai?: number;
    disclaimer: string;
    average_guests_per_room?: number;
    saturation_thresholds?: {
      watch: number;
      severe: number;
      physical: number;
    };
  };
  state_baselines: Record<string, {
    alos: number;
    spend_per_night: number;
    tourists_k: number;
    excursionists_k?: number;
    hotel_rooms: number | null;
    aor: number | null;
  }>;
  gravity_elasticities?: Record<string, number>;
  gravity_models?: any;
}

export interface DriverAttribution {
  feature_name: string;
  feature_label: string;
  std_beta: number;
  std_error: number;
  t_statistic: number;
  p_value: number;
  is_significant_5pct: boolean;
  vif: number;
  direction: string;
  coefficient_weight_pct?: number;
  importance_share_pct: number;
}

export interface DriversData {
  model_metadata: {
    r_squared: number;
    adj_r_squared: number;
    f_statistic: number;
    n_observations: number;
    dependent_variable: string;
    covariance_type: string;
    description: string;
  };
  feature_attributions: DriverAttribution[];
  panel_regressions?: any[];
  recovery_trajectories?: any[];
  leave_one_out_stability?: Record<string, any>;
  influence_diagnostics?: Record<string, any>;
  disclaimer?: string;
}

export interface ModelMetricsData {
  gravity: {
    model: string;
    specification: string;
    train_period: string;
    test_period: string;
    train_observations: number;
    test_observations: number;
    total_panel_observations: number;
    r2_oos: number;
    correlation: number;
    squared_correlation: number;
    mae: number;
    rmse: number;
    rmsle: number;
    smape: number;
    distance_decay_friction: number;
    distance_decay_se: number;
    distance_decay_pval: number;
    cross_region_barrier: number;
    cross_region_se: number;
    target_leakage_status?: string;
    structural_change_test?: {
      interaction_variable: string;
      interaction_coef: number;
      std_error: number;
      t_statistic: number;
      p_value: number;
      h0_rejected_5pct: boolean;
      conclusion: string;
    };
    naive_baselines: Array<{
      name: string;
      r2_oos: number;
      mae: number;
      rmse: number;
      rmsle: number;
      smape: number;
    }>;
  };
  panel: {
    primary_model: string;
    sample_period: string;
    observations: number;
    states: number;
    years: number;
    alos_elasticity: number;
    alos_pvalue: number;
    tourist_elasticity: number;
    tourist_pvalue: number;
    yield_model?: {
      id: string;
      r_squared: number;
      aor_elasticity: number;
      foreign_share_coef: number;
      holiday_share_coef: number;
    };
  };
}

