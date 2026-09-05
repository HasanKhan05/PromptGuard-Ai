import Link from "next/link";
import type { AttackEligibility } from "@/lib/types";

const labels = {
  high: "HIGH RELEVANCE",
  medium: "MEDIUM RELEVANCE",
  not_applicable: "NOT APPLICABLE",
};

export function AttackCard({ item }: { item: AttackEligibility }) {
  return (
    <div className="attack-card">
      <strong>{item.title}</strong>
      <span className={`pill ${item.level}`}>{labels[item.level]}</span>
      <p>{item.reason}</p>
      {item.level === "not_applicable" ? (
        <button type="button" className="text-action" title={item.reason}>Why not?</button>
      ) : (
        <Link href={`/experiments?attack=${item.id}`} className="text-action">Generate attack →</Link>
      )}
    </div>
  );
}
