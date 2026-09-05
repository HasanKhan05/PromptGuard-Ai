const attackTypes = [
  ["Direct injection", 78, 24],
  ["Canary leakage", 64, 12],
  ["Tool misuse", 71, 8],
  ["Untrusted content", 76, 18],
] as const;

export default function ResearchPage() {
  return (
    <div className="page">
      <div className="top-label">Research</div>
      <header className="page-header">
        <h1>What do the benchmark results mean?</h1>
      </header>

      <section className="question-card">
        <div className="eyebrow">RESEARCH QUESTION</div>
        <p>How effective are lightweight application-level guardrails at reducing LLM attacks while preserving the usefulness of a software-development assistant?</p>
      </section>

      <div className="research-grid">
        <section className="research-panel">
          <h2>Overall attack success</h2>
          <small>Lower is better</small>
          <BarLine label="Without defense" value={82} defended={false} />
          <BarLine label="With defense" value={19} defended />
          <div className="preview-note">Illustrative preview — replace with real aggregate values from `/api/benchmarks`.</div>
        </section>

        <section className="research-panel">
          <h2>By attack type</h2>
          <small>Before → after matching defense</small>
          {attackTypes.map(([label, before, after]) => (
            <div className="attack-type-row" key={label}>
              <span>{label}</span><b>{before}%</b><span>→</span><b>{after}%</b>
              <div className="mini-track"><span className="mini-before" style={{ width: `${before}%` }} /><span className="mini-after" style={{ width: `${after}%` }} /></div>
            </div>
          ))}
        </section>
      </div>

      <div className="findings-grid">
        <section>
          <h2 className="section-title">Key findings</h2>
          <div className="findings-card">
            <Finding text="Attack success decreases when the relevant guardrail is enabled." />
            <Finding text="Different attack families benefit from different application-level defenses." />
            <Finding text="Benign success should remain high so normal developer questions still work." />
          </div>
        </section>
        <section>
          <h2 className="section-title">Research answer</h2>
          <div className="answer-card">
            <div className="eyebrow">BENCHMARK-GROUNDED SUMMARY</div>
            <p>Preview only: lightweight guardrails appear to reduce attack success while preserving developer usefulness. The final wording must be generated from real stored benchmark results only.</p>
            <small>Codex will wire `/api/research` and remove unsupported preview wording.</small>
          </div>
        </section>
      </div>

      <div className="reading-note">
        <span className="pill preview">HOW THIS PAGE WORKS</span>
        <span>Benchmarks provide the numbers. Research turns those same stored results into a short visual explanation and answer to the research question.</span>
      </div>
    </div>
  );
}

function BarLine({ label, value, defended }: { label: string; value: number; defended: boolean }) {
  return <div className="bar-line"><span>{label}</span><div className="bar-track"><div className={`bar-fill ${defended ? "defended" : ""}`} style={{ width: `${value}%` }} /></div><strong>{value}%</strong></div>;
}
function Finding({ text }: { text: string }) {
  return <div className="finding"><span className="finding-dot" /><span>{text}</span></div>;
}
