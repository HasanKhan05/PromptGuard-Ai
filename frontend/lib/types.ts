export type EligibilityLevel = "high" | "medium" | "not_applicable";

export type AttackEligibility = {
  id: string;
  title: string;
  level: EligibilityLevel;
  reason: string;
};

export type AttackFamily =
  | "direct_prompt_injection"
  | "system_prompt_canary_leakage"
  | "tool_misuse_manipulation"
  | "untrusted_code_text_injection";

export type DefenseName =
  | "input_screening"
  | "output_screening"
  | "tool_authorization_least_privilege"
  | "instruction_data_separation";

export type EligibilityStatus = "HIGH" | "MEDIUM" | "NOT_APPLICABLE";

export type AttackEligibilityItem = {
  family: AttackFamily;
  status: EligibilityStatus;
  reason: string;
};

export type AttackEligibilityResponse = {
  results: AttackEligibilityItem[];
};

export type AttackGenerationResult = {
  attack_family: AttackFamily;
  attack_prompt: string;
};

export type ConditionStatus = "completed" | "failed";
export type ExperimentStatus = "completed" | "partial" | "failed";

export type ExperimentConditionResponse = {
  status: ConditionStatus;
  raw_output?: string | null;
  visible_output?: string | null;
  actual_model?: string | null;
  provider_metadata?: Record<string, unknown> | null;
  defense_evidence: Record<string, unknown>;
  tool_evidence?: Record<string, unknown> | null;
  latency_ms?: number | null;
  input_tokens?: number | null;
  output_tokens?: number | null;
  cost?: number | null;
  error?: string | null;
};

export type ExperimentRunResponse = {
  experiment_id: string;
  created_at: string;
  status: ExperimentStatus;
  original_task: string;
  attack_prompt: string;
  attack_family: AttackFamily;
  mapped_defense: DefenseName;
  model: string;
  temperature: number;
  max_output_tokens: number;
  generation_source: string;
  attack_edited: boolean;
  baseline: ExperimentConditionResponse;
  defended: ExperimentConditionResponse;
};

export type EvaluationResponse = {
  experiment_id: string;
  attack_family: AttackFamily;
  mapped_defense: DefenseName;
  baseline_attack_success?: boolean | null;
  defended_attack_success?: boolean | null;
  baseline_legitimate_task_success?: boolean | null;
  defended_legitimate_task_success?: boolean | null;
  baseline_false_refusal?: boolean | null;
  defended_false_refusal?: boolean | null;
  baseline_canary_leakage_raw?: boolean | null;
  baseline_canary_leakage_visible?: boolean | null;
  defended_canary_leakage_raw?: boolean | null;
  defended_canary_leakage_visible?: boolean | null;
  baseline_unauthorized_tool_attempted?: boolean | null;
  baseline_unauthorized_tool_executed?: boolean | null;
  defended_unauthorized_tool_attempted?: boolean | null;
  defended_unauthorized_tool_executed?: boolean | null;
  evaluator_method: string;
  evaluator_rationale: string;
  latency_baseline_ms?: number | null;
  latency_defended_ms?: number | null;
  tokens_baseline_input?: number | null;
  tokens_baseline_output?: number | null;
  tokens_defended_input?: number | null;
  tokens_defended_output?: number | null;
  cost_baseline?: number | null;
  cost_defended?: number | null;
};

export type RateMetric = {
  rate: number | null;
  count: number;
  denominator: number;
};

export type OperationalMetric = {
  avg: number | null;
  sum: number | null;
  count: number;
};

export type FamilyBenchmarkMetrics = {
  family: AttackFamily;
  mapped_defense: DefenseName;
  total_runs: number;
  evaluated_runs: number;
  baseline_asr: RateMetric;
  defended_asr: RateMetric;
  asr_reduction?: number | null;
  canary_leakage_raw_baseline?: RateMetric | null;
  canary_leakage_visible_baseline?: RateMetric | null;
  canary_leakage_raw_defended?: RateMetric | null;
  canary_leakage_visible_defended?: RateMetric | null;
  tool_attempted_baseline?: RateMetric | null;
  tool_executed_baseline?: RateMetric | null;
  tool_attempted_defended?: RateMetric | null;
  tool_executed_defended?: RateMetric | null;
};

export type UtilityBenchmarkMetrics = {
  baseline_legitimate_task_success: RateMetric;
  defended_legitimate_task_success: RateMetric;
  baseline_false_refusal: RateMetric;
  defended_false_refusal: RateMetric;
};

export type OperationalBenchmarkMetrics = {
  latency_baseline_ms: OperationalMetric;
  latency_defended_ms: OperationalMetric;
  input_tokens_baseline: OperationalMetric;
  input_tokens_defended: OperationalMetric;
  output_tokens_baseline: OperationalMetric;
  output_tokens_defended: OperationalMetric;
  cost_baseline: OperationalMetric;
  cost_defended: OperationalMetric;
};

export type BenchmarkMetricsResponse = {
  total_runs_count: number;
  evaluated_runs_count: number;
  unevaluated_runs_count: number;
  status_counts: Record<string, number>;
  overall_baseline_asr: RateMetric;
  overall_defended_asr: RateMetric;
  overall_asr_reduction?: number | null;
  defense_effectiveness?: number | null;
  by_family: FamilyBenchmarkMetrics[];
  utility: UtilityBenchmarkMetrics;
  operational: OperationalBenchmarkMetrics;
};

export type ResearchSummaryResponse = {
  benchmark_target: {
    target_runs: number;
    actual_runs: number;
    completion_percentage: number;
  };
  overall_security: {
    baseline_asr: RateMetric;
    defended_asr: RateMetric;
    asr_reduction?: number | null;
    defense_effectiveness?: number | null;
  };
  family_breakdown: FamilyBenchmarkMetrics[];
  utility_tradeoff: UtilityBenchmarkMetrics;
  operational_impact: OperationalBenchmarkMetrics;
  structured_findings: string[];
};

export type ExperimentRunDetailResponse = ExperimentRunResponse & {
  evaluation?: EvaluationResponse | null;
};

export const FAMILY_DISPLAY_CONFIG: Record<
  AttackFamily,
  { title: string; shortTitle: string; mappedDefense: string; mappedDefenseName: DefenseName }
> = {
  direct_prompt_injection: {
    title: "Direct Prompt Injection",
    shortTitle: "Direct injection",
    mappedDefense: "Input Screening",
    mappedDefenseName: "input_screening",
  },
  system_prompt_canary_leakage: {
    title: "System Prompt / Canary Leakage",
    shortTitle: "Canary leakage",
    mappedDefense: "Output Screening",
    mappedDefenseName: "output_screening",
  },
  tool_misuse_manipulation: {
    title: "Tool Misuse / Manipulation",
    shortTitle: "Tool misuse",
    mappedDefense: "Tool Authorization",
    mappedDefenseName: "tool_authorization_least_privilege",
  },
  untrusted_code_text_injection: {
    title: "Untrusted Code/Text Injection",
    shortTitle: "Untrusted content",
    mappedDefense: "Instruction/Data Separation",
    mappedDefenseName: "instruction_data_separation",
  },
};

