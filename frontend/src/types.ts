export interface Occupation {
  soc_code: string;
  occupation_title: string;
  ai_intensity: number;
  ai_skill_share: number;
  annual_median_wage: number | null;
  employment: number | null;
  bachelors_plus_share: number | null;
  job_zone: number | null;
  signal_occupation_titles: string;
}

export interface OccupationExplorerRow {
  soc_code: string;
  occupation_title: string;
  ai_intensity: number;
  ai_skill_share: number;
  annual_median_wage: number | null;
  employment: number | null;
  bachelors_plus_share: number | null;
  job_zone: number | null;
}

export interface Mover {
  soc_code: string;
  occupation_title: string;
  previous_ai_intensity: number;
  current_ai_intensity: number;
  intensity_change: number;
}

export interface TaskComplement {
  task_category: string;
  comparison_share: number;
  high_ai_share: number;
  lift: number;
}

export interface Geography {
  soc_code: string;
  area_name: string;
  employment: number | null;
  annual_median_wage: number | null;
  national_median_wage: number | null;
  wage_index: number | null;
  occupation_title: string;
  ai_intensity: number;
}

export interface ObservatorySummary {
  title: string;
  generated_at: string;
  releases: {
    previous: string;
    current: string;
    bls_oews: string;
  };
  coverage: {
    onet_occupations: number;
    wage_model_occupations: number;
    states: number;
    featured_geographic_occupations: number;
  };
  headline_metrics: {
    highest_ai_intensity: number;
    occupations_with_ai_signal: number;
    median_ai_intensity: number;
    wage_model_r_squared: number;
  };
  wage_model: {
    observations: number;
    coefficient: number;
    standard_error: number;
    p_value: number;
    r_squared: number;
    interpretation: string;
  };
  top_occupations: Occupation[];
  fastest_movers: Mover[];
  task_complements: TaskComplement[];
  geography: Geography[];
  skill_mix: Array<{
    category: string;
    skills: number;
    description: string;
  }>;
  methodology_notes: string[];
}
