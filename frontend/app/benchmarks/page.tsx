const rows = [
  ["Direct Prompt Injection", "Input Screening", "78%", "24%"],
  ["Canary / System Leakage", "Output Screening", "64%", "12%"],
  ["Tool Misuse", "Tool Authorization", "71%", "8%"],
  ["Untrusted Code/Text Injection", "Instruction/Data Separation", "76%", "18%"],
];

export default function BenchmarksPage() {
  return (
    <div className="page">
      <div className="top-label">Research Benchmarks</div>

      <section className="section-block">
        <h1 className="section-title">Quick summary</h1>
        <div className="summary-grid">
          <Summary title="Attack tests" value="50" text="Illustrative preview across 4 attack families" />
          <Summary title="Benign tests" value="40" text="Illustrative usefulness checks" />
          <Summary title="Overall improvement" value="82% → 19%" text="Illustrative baseline to layered defense" />
        </div>
      </section>

      <section className="section-block">
        <h2 className="section-title">Overall result</h2>
        <p>Lower attack success is better.</p>
        <div className="overall-grid">
          <Overall title="WITHOUT DEFENSE" value="82%" text="Preview: attacks succeed often when the matching guardrail is off." />
          <Overall title="WITH DEFENSE" value="19%" text="Preview: the rate falls after the relevant defense is applied." defended />
        </div>
      </section>

      <section className="section-block">
        <h2 className="section-title">By attack type</h2>
        <p>Each attack is compared against its matching defense.</p>
        <div className="benchmark-layout">
          <div className="attack-rows">
            {rows.map(([attack, defense, before, after]) => (
              <div className="attack-row" key={attack}>
                <strong>{attack}</strong><span>→</span><span>{defense}</span>
                <div className="value"><small>Before</small><b>{before}</b></div>
                <span>→</span>
                <div className="value"><small>After</small><b>{after}</b></div>
                <span className="lower-badge">LOWER IS BETTER</span>
              </div>
            ))}
          </div>
          <aside className="cost-card">
            <h3>Cost of defense</h3>
            <p>Security should improve without making the assistant slow or expensive.</p>
            <Cost label="Latency overhead" value="+0.2 s" />
            <Cost label="Token overhead" value="+8%" />
            <Cost label="Benign success" value="94%" />
          </aside>
        </div>
      </section>

      <div className="reading-note">
        <span className="pill preview">HOW TO READ THIS</span>
        <span>All values on this starter page are illustrative Figma preview data. Codex must replace them with real stored benchmark values.</span>
      </div>
    </div>
  );
}

function Summary({ title, value, text }: { title: string; value: string; text: string }) {
  return <div className="summary-card"><small>{title}</small><strong>{value}</strong><p>{text}</p></div>;
}
function Overall({ title, value, text, defended = false }: { title: string; value: string; text: string; defended?: boolean }) {
  return <div className="overall-card"><span className={`pill ${defended ? "medium" : "high"}`}>{title}</span><div className="overall-number"><strong>{value}</strong><span>Attack success</span></div><p>{text}</p></div>;
}
function Cost({ label, value }: { label: string; value: string }) {
  return <div className="cost-metric"><small>{label}</small><strong>{value}</strong></div>;
}
