export type EligibilityLevel = "high" | "medium" | "not_applicable";

export type AttackEligibility = {
  id: string;
  title: string;
  level: EligibilityLevel;
  reason: string;
};
