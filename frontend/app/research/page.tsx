"use client";

import { useEffect, useState } from "react";
import { fetchResearchSummary } from "@/lib/api";
import { type ResearchSummaryResponse, FAMILY_DISPLAY_CONFIG } from "@/lib/types";

export default function ResearchPage() {
  const [research, setResearch] = useState<ResearchSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    fetchResearchSummary()
      .then((data) => {
        if (active) setResearch(data);
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : "Failed to load research summary.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const blRate = research?.overall_security.baseline_asr.rate;
  const dfRate = research?.overall_security.defended_asr.rate;
  const blPct = blRate != null ? Math.round(blRate * 100) : null;
  const dfPct = dfRate != null ? Math.round(dfRate * 100) : null;

  return (
    <div className="page">
      <div className="top-label">Research</div>
      <header className="page-header">
        <h1>What do the benchmark results mean?</h1>
      </header>

      {error ? <p className="error-text" style={{ marginTop: "1rem" }}>{error}</p> : null}

      <section className="question-card">
        <div className="eyebrow">RESEARCH QUESTION</div>
        <p>
          How effective are lightweight application-level guardrails at reducing LLM attacks while preserving the usefulness of a software-development assistant?
        </p>
      </section>

      <div className="research-grid">
        <section className="research-panel">
          <h2>Overall attack success</h2>
          <small>Lower is better</small>
          <BarLine label="Without defense" value={blPct} defended={false} />
          <BarLine label="With defense" value={dfPct} defended />
          <div className="preview-note">
            {loading
              ? "Loading aggregate data…"
              : research
              ? `Benchmark progress: ${research.benchmark_target.actual_runs} of ~${research.benchmark_target.target_runs} target runs completed (${research.benchmark_target.completion_percentage}%).`
              : "No experiment runs available."}
          </div>
        </section>

        <section className="research-panel">
          <h2>By attack type</h2>
          <small>Before → after matching defense</small>
          {research?.family_breakdown && research.family_breakdown.length > 0 ? (
            research.family_breakdown.map((fam) => {
              const config = FAMILY_DISPLAY_CONFIG[fam.family];
              const beforePct = fam.baseline_asr.rate != null ? Math.round(fam.baseline_asr.rate * 100) : null;
              const afterPct = fam.defended_asr.rate != null ? Math.round(fam.defended_asr.rate * 100) : null;
              return (
                <div className="attack-type-row" key={fam.family}>
                  <span>{config ? config.shortTitle : fam.family}</span>
                  <b>{beforePct != null ? `${beforePct}%` : "—"}</b>
                  <span>→</span>
                  <b>{afterPct != null ? `${afterPct}%` : "—"}</b>
                  <div className="mini-track">
                    <span className="mini-before" style={{ width: `${beforePct || 0}%` }} />
                    <span className="mini-after" style={{ width: `${afterPct || 0}%` }} />
                  </div>
                </div>
              );
            })
          ) : (
            <div className="note" style={{ marginTop: "20px" }}>
              {loading ? "Loading breakdown…" : "No evaluated families yet."}
            </div>
          )}
        </section>
      </div>

      <div className="findings-grid">
        <section>
          <h2 className="section-title">Key findings</h2>
          <div className="findings-card">
            {research?.structured_findings && research.structured_findings.length > 0 ? (
              research.structured_findings.map((text, idx) => <Finding key={idx} text={text} />)
            ) : (
              <Finding text={loading ? "Analyzing findings…" : "No evaluated experimental findings recorded yet."} />
            )}
          </div>
        </section>
        <section>
          <h2 className="section-title">Research answer</h2>
          <div className="answer-card">
            <div className="eyebrow">BENCHMARK-GROUNDED SUMMARY</div>
            <p>
              {blPct != null && dfPct != null
                ? `Across ${research?.overall_security.baseline_asr.denominator} evaluated pairs, application-level defenses reduced Attack Success Rate from ${blPct}% to ${dfPct}% (absolute reduction of ${Math.round((research?.overall_security.asr_reduction || 0) * 100)}%).`
                : "Awaiting sufficient evaluated benchmark experiment runs. Conclusions will be derived deterministically from stored paired-experiment evidence in /api/research."}
            </p>
            <small>Data sourced deterministically from <code>/api/research</code> — zero LLM interpretation added.</small>
          </div>
        </section>
      </div>

      <div className="reading-note">
        <span className="pill preview">HOW THIS PAGE WORKS</span>
        <span>
          Benchmarks provide raw statistical counts. Research turns those exact stored results into structured findings answering the research question.
        </span>
      </div>
    </div>
  );
}

function BarLine({
  label,
  value,
  defended,
}: {
  label: string;
  value: number | null;
  defended: boolean;
}) {
  return (
    <div className="bar-line">
      <span>{label}</span>
      <div className="bar-track">
        <div
          className={`bar-fill ${defended ? "defended" : ""}`}
          style={{ width: `${value != null ? value : 0}%` }}
        />
      </div>
      <strong>{value != null ? `${value}%` : "—"}</strong>
    </div>
  );
}

function Finding({ text }: { text: string }) {
  return (
    <div className="finding">
      <span className="finding-dot" />
      <span>{text}</span>
    </div>
  );
}

