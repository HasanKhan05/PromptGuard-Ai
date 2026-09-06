"use client";

import { useEffect, useState } from "react";
import { fetchBenchmarks } from "@/lib/api";
import { type BenchmarkMetricsResponse, FAMILY_DISPLAY_CONFIG } from "@/lib/types";

export default function BenchmarksPage() {
  const [metrics, setMetrics] = useState<BenchmarkMetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    fetchBenchmarks()
      .then((data) => {
        if (active) setMetrics(data);
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : "Failed to load benchmarks.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const blRate = metrics?.overall_baseline_asr.rate;
  const dfRate = metrics?.overall_defended_asr.rate;
  const reduction = metrics?.overall_asr_reduction;

  let overallImprovementText = "—";
  let overallImprovementSubtext = "No evaluated runs yet";
  if (blRate != null && dfRate != null) {
    overallImprovementText = `${(blRate * 100).toFixed(0)}% → ${(dfRate * 100).toFixed(0)}%`;
    overallImprovementSubtext = `${((reduction || 0) * 100).toFixed(0)}% absolute ASR reduction`;
  }

  return (
    <div className="page">
      <div className="top-label">Research Benchmarks</div>

      {error ? <p className="error-text" style={{ marginTop: "1rem" }}>{error}</p> : null}

      <section className="section-block">
        <h1 className="section-title">Quick summary</h1>
        <div className="summary-grid">
          <Summary
            title="Evaluated pairs"
            value={loading ? "…" : `${metrics?.evaluated_runs_count ?? 0}`}
            text={`${metrics?.total_runs_count ?? 0} total runs stored (${metrics?.unevaluated_runs_count ?? 0} unevaluated)`}
          />
          <Summary
            title="Dataset target"
            value={loading ? "…" : `${metrics?.total_runs_count ?? 0} / 90`}
            text="Actual runs completed toward ~90 target benchmark"
          />
          <Summary
            title="Overall improvement"
            value={loading ? "…" : overallImprovementText}
            text={loading ? "Loading telemetry…" : overallImprovementSubtext}
          />
        </div>
      </section>

      <section className="section-block">
        <h2 className="section-title">Overall result</h2>
        <p>Lower attack success is better.</p>
        <div className="overall-grid">
          <Overall
            title="WITHOUT DEFENSE"
            value={blRate != null ? `${(blRate * 100).toFixed(0)}%` : "—"}
            text={
              metrics?.overall_baseline_asr.denominator
                ? `${metrics.overall_baseline_asr.count} of ${metrics.overall_baseline_asr.denominator} evaluated baseline attacks succeeded.`
                : "No evaluated baseline attacks recorded yet."
            }
          />
          <Overall
            title="WITH DEFENSE"
            value={dfRate != null ? `${(dfRate * 100).toFixed(0)}%` : "—"}
            text={
              metrics?.overall_defended_asr.denominator
                ? `${metrics.overall_defended_asr.count} of ${metrics.overall_defended_asr.denominator} evaluated defended attacks succeeded.`
                : "No evaluated defended attacks recorded yet."
            }
            defended
          />
        </div>
      </section>

      <section className="section-block">
        <h2 className="section-title">By attack type</h2>
        <p>Each attack is compared against its matching defense.</p>
        <div className="benchmark-layout">
          <div className="attack-rows">
            {metrics?.by_family && metrics.by_family.length > 0 ? (
              metrics.by_family.map((fam) => {
                const config = FAMILY_DISPLAY_CONFIG[fam.family];
                const beforeStr = fam.baseline_asr.rate != null ? `${(fam.baseline_asr.rate * 100).toFixed(0)}%` : "—";
                const afterStr = fam.defended_asr.rate != null ? `${(fam.defended_asr.rate * 100).toFixed(0)}%` : "—";
                return (
                  <div className="attack-row" key={fam.family}>
                    <strong>{config ? config.title : fam.family}</strong>
                    <span>→</span>
                    <span>{config ? config.mappedDefense : fam.mapped_defense}</span>
                    <div className="value">
                      <small>Before ({fam.baseline_asr.count}/{fam.baseline_asr.denominator})</small>
                      <b>{beforeStr}</b>
                    </div>
                    <span>→</span>
                    <div className="value">
                      <small>After ({fam.defended_asr.count}/{fam.defended_asr.denominator})</small>
                      <b>{afterStr}</b>
                    </div>
                    <span className="lower-badge">LOWER IS BETTER</span>
                  </div>
                );
              })
            ) : (
              <div className="note" style={{ padding: "16px" }}>
                {loading ? "Loading family metrics…" : "No evaluated attack runs stored yet."}
              </div>
            )}
          </div>
          <aside className="cost-card">
            <h3>Cost of defense</h3>
            <p>Security should improve without making the assistant slow or expensive.</p>
            <Cost
              label="Latency (defended avg)"
              value={
                metrics?.operational.latency_defended_ms.avg != null
                  ? `${metrics.operational.latency_defended_ms.avg.toFixed(0)} ms`
                  : "—"
              }
            />
            <Cost
              label="Output tokens (defended avg)"
              value={
                metrics?.operational.output_tokens_defended.avg != null
                  ? `${metrics.operational.output_tokens_defended.avg.toFixed(0)} tok`
                  : "—"
              }
            />
            <Cost
              label="Legitimate task success"
              value={
                metrics?.utility.defended_legitimate_task_success.rate != null
                  ? `${(metrics.utility.defended_legitimate_task_success.rate * 100).toFixed(0)}%`
                  : "—"
              }
            />
          </aside>
        </div>
      </section>

      <div className="reading-note">
        <span className="pill preview">DATA SOURCE</span>
        <span>
          Metrics above are calculated deterministically by <code>/api/benchmarks</code> from stored experiment runs in SQLite.
        </span>
      </div>
    </div>
  );
}

function Summary({ title, value, text }: { title: string; value: string; text: string }) {
  return (
    <div className="summary-card">
      <small>{title}</small>
      <strong>{value}</strong>
      <p>{text}</p>
    </div>
  );
}

function Overall({
  title,
  value,
  text,
  defended = false,
}: {
  title: string;
  value: string;
  text: string;
  defended?: boolean;
}) {
  return (
    <div className="overall-card">
      <span className={`pill ${defended ? "medium" : "high"}`}>{title}</span>
      <div className="overall-number">
        <strong>{value}</strong>
        <span>Attack success</span>
      </div>
      <p>{text}</p>
    </div>
  );
}

function Cost({ label, value }: { label: string; value: string }) {
  return (
    <div className="cost-metric">
      <small>{label}</small>
      <strong>{value}</strong>
    </div>
  );
}

