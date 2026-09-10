import researchResults from "@/lib/research-results.json";
import { SectionIntro } from "./SectionIntro";

export function DefenseVerdictSection() {
  const verdicts = Object.values(researchResults.defenseVerdicts);

  return (
    <section className="research-section" aria-labelledby="verdict-title">
      <SectionIntro
        index="08"
        label="DEFENSE VERDICT"
        title="What did each defense actually prove?"
        description="A research result is stronger when null findings stay visible. The final report separates demonstrated mitigation from defenses whose incremental effect could not be estimated."
      />
      <div className="panel verdict-grid">
        {verdicts.map((verdict) => {
          const demonstrated = verdict.status === "demonstrated";
          return (
            <article className={`verdict-card ${demonstrated ? "green-border" : "amber-border"}`} key={verdict.title}>
              <span className={`research-pill ${demonstrated ? "green" : "amber"}`}>{demonstrated ? "DEMONSTRATED" : "NULL FINDING"}</span>
              <h3>{verdict.title.toUpperCase()}</h3>
              <p>{verdict.description}</p>
              <small className={demonstrated ? "green-text" : "amber-text"}><i aria-hidden="true" />{verdict.evidence}</small>
            </article>
          );
        })}
      </div>
    </section>
  );
}

export function LimitationsSection() {
  return (
    <section className="research-section" id="limitations" aria-labelledby="limitations-title">
      <SectionIntro index="09" label="LIMITATIONS" title="What this study does not establish." accent="amber" />
      <div className="limitations-grid">
        <article className="panel limitations-panel">
          <ol>
            {researchResults.limitations.map((limitation, index) => (
              <li key={limitation}><span>{String(index + 1).padStart(2, "0")}</span><p>{limitation}</p></li>
            ))}
          </ol>
        </article>
        <article className="panel reproducibility-panel" id="reproducibility">
          <span className="research-pill cyan">REPRODUCIBLE</span>
          <h3>Evidence preserved, not overwritten.</h3>
          <p>The final analysis keeps source experiment databases immutable and applies corrected labels through a separate adjudication overlay.</p>
          <div className="repro-stats">
            <MiniEvidence value="4" label="MODELS" text="Compared on one frozen subset" accent="cyan" />
            <MiniEvidence value="72" label="CASES" text="Comparable paired cases / model" accent="purple" />
            <MiniEvidence value="106" label="TESTS" text="Backend tests passing" accent="green" />
          </div>
          <div className="artifact-list">FROZEN MANIFESTS<br />SQLITE RESULT DATABASES<br />SHA-256 SOURCE CHECKSUMS<br />FULL-OUTPUT ADJUDICATION OVERLAY<br />REPRODUCIBLE ANALYSIS SCRIPT</div>
        </article>
      </div>
    </section>
  );
}

function MiniEvidence({ value, label, text, accent }: { value: string; label: string; text: string; accent: string }) {
  return (
    <div className={`mini-evidence ${accent}-border`}>
      <span className={`${accent}-text`}>{label}</span>
      <strong>{value}</strong>
      <p>{text}</p>
    </div>
  );
}

export function ConclusionSection() {
  return (
    <section className="panel conclusion-panel" aria-labelledby="conclusion-title">
      <span className="research-pill purple">CONCLUSION</span>
      <h2 id="conclusion-title">Guardrails are a security problem — and a utility problem.</h2>
      <p>PromptGuard Ai shows why both must be measured together: observed leakage can fall while legitimate usability changes dramatically across model configurations.</p>
      <small>MUHAMMAD HASAN DAD KHAN&nbsp; · &nbsp;BS COMPUTER SCIENCE, FAST-NUCES&nbsp; · &nbsp;AI SECURITY / LLM SECURITY</small>
    </section>
  );
}
