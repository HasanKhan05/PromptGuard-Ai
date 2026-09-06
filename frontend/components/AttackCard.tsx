import Link from "next/link";
import { type AttackFamily, type EligibilityStatus, FAMILY_DISPLAY_CONFIG } from "@/lib/types";

export interface AttackCardItem {
  family: AttackFamily;
  status: EligibilityStatus;
  reason: string;
}

const statusPillClass: Record<EligibilityStatus, string> = {
  HIGH: "high",
  MEDIUM: "medium",
  NOT_APPLICABLE: "not_applicable",
};

const statusLabels: Record<EligibilityStatus, string> = {
  HIGH: "HIGH RELEVANCE",
  MEDIUM: "MEDIUM RELEVANCE",
  NOT_APPLICABLE: "NOT APPLICABLE",
};

export function AttackCard({
  item,
  task,
}: {
  item: AttackCardItem;
  task?: string;
}) {
  const config = FAMILY_DISPLAY_CONFIG[item.family] || {
    title: item.family,
    mappedDefense: "Standard Defense",
  };
  const pillClass = statusPillClass[item.status] || "medium";
  const label = statusLabels[item.status] || item.status;

  const targetUrl = `/experiments?family=${encodeURIComponent(item.family)}${
    task ? `&task=${encodeURIComponent(task)}` : ""
  }`;

  return (
    <div className="attack-card">
      <strong>{config.title}</strong>
      <span className={`pill ${pillClass}`}>{label}</span>
      <p>{item.reason}</p>
      {item.status === "NOT_APPLICABLE" ? (
        <button type="button" className="text-action" title={item.reason}>
          Why not?
        </button>
      ) : (
        <Link href={targetUrl} className="text-action">
          Generate attack →
        </Link>
      )}
    </div>
  );
}

