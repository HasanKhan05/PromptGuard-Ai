import researchResults from "@/lib/research-results.json";
import { SectionIntro } from "./SectionIntro";

export function FindingGridSection() {
  const findings = [
    {
      accent: "cyan",
      label: "VULNERABILITY",
      title: "Confirmed open-model successes concentrate in canary leakage.",
      text: "DPI and DATA produced no confirmed baseline successes after full-output adjudication.",
    },
    {
      accent: "green",
      label: "UTILITY",
      title: "Guardrail utility cost varies sharply by tested model.",
      text: "Llama 2 falls to 44.4% benign success under layered guardrails; Gemma 2/3 preserve utility in this sample.",
    },
    {
      accent: "purple",
      label: "OUTPUT SCREENING",
      title: "Raw leakage can still occur even when visible leakage is zero.",
      text: "The canary may be generated internally, then removed before it reaches the user-visible response.",
    },
    {
      accent: "amber",
      label: "NULL FINDINGS",
      title: "Not every defense can claim an observed security gain.",
      text: "With zero confirmed DPI/DATA baseline successes, incremental effectiveness cannot be estimated for their mapped defenses.",
    },
  ];

  return (
    <section className="research-section" aria-labelledby="findings-title">
      <SectionIntro
        index="04"
        label="WHAT CHANGED"
        title={'Equal “security” is not the whole story.'}
        description="The most important differences appear where raw outputs actually differ from what the user sees. PromptGuard becomes a security-utility study rather than a simple leaderboard."
        accent="purple"
      />
      <div className="panel finding-grid">
        {findings.map((finding) => (
          <article className={`finding-card ${finding.accent}-border`} key={finding.label}>
            <span className={`research-pill ${finding.accent}`}>{finding.label}</span>
            <h3>{finding.title}</h3>
            <p>{finding.text}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export function AttackFamiliesSection() {
  return (
    <section className="research-section" id="results" aria-labelledby="families-title">
      <SectionIntro
        index="05"
        label="ATTACK FAMILIES"
        title="Where did attacks actually succeed?"
        description="Full-output adjudication leaves a very specific pattern: all confirmed open-model baseline successes occur in system-prompt canary leakage. DPI and DATA are null findings in this benchmark."
        accent="teal"
      />
      <div className="panel matrix-shell" role="region" aria-label="Attack family results" tabIndex={0}>
        <table className="attack-matrix">
          <caption>Baseline successes out of 12 cases per family and model</caption>
          <thead>
            <tr>
              <th scope="col">BASELINE SUCCESSES / 12</th>
              {researchResults.models.map((model) => <th scope="col" key={model.key}>{model.name.toUpperCase()}</th>)}
            </tr>
          </thead>
          <tbody>
            {researchResults.attackFamilies.map((family) => (
              <tr key={family.key} className={family.key}>
                <th scope="row">{family.name.toUpperCase()}</th>
                {family.baselineSuccesses.map((value, index) => <td key={`${family.key}-${index}`}><span>{value}</span></td>)}
              </tr>
            ))}
          </tbody>
        </table>
        <aside className="matrix-note"><span>NULL FINDING</span><p>No confirmed DPI or DATA baseline successes means their mapped defenses cannot claim measured incremental security benefit here.</p></aside>
      </div>
    </section>
  );
}

export function CanarySection() {
  return (
    <section className="research-section" aria-labelledby="canary-title">
      <SectionIntro
        index="06"
        label="CANARY STORY"
        title="Raw leakage is not the same as visible leakage."
        description="Output Screening is the clearest demonstrated defense result: raw models still generated the fake canary in some defended case responses, but none reached the user-visible output."
        accent="purple"
      />
      <div className="panel canary-panel">
        <div className="canary-flow">
          <article className="flow-card pink-border">
            <span className="research-pill pink">RAW MODEL OUTPUT</span>
            <h3>Model may emit<br /><code>DEV_CANARY_8241</code></h3>
          </article>
          <span aria-hidden="true">→</span>
          <article className="flow-card purple-border">
            <span className="research-pill purple">OUTPUT SCREENING</span>
            <h3>Detect and remove exact canary before display</h3>
          </article>
          <span aria-hidden="true">→</span>
          <article className="flow-card green-border">
            <span className="research-pill green">USER-VISIBLE</span>
            <h3>No observed canary disclosure</h3>
          </article>
        </div>
        <div className="canary-stats">
          {researchResults.models.map((model) => (
            <article className={`canary-card ${model.accent}-border`} key={model.key}>
              <h3>{model.name}</h3>
              <span>DEFENDED RAW</span>
              <strong className={`${model.accent}-text`}>{model.defendedRawCanary}/12</strong>
              <span>DEFENDED VISIBLE</span>
              <strong className="green-text">{model.defendedVisibleCanary}/12</strong>
            </article>
          ))}
        </div>
        <aside className="scope-note"><span>SCOPE</span><p>This demonstrates narrow containment of the benchmark canary — not general system-prompt confidentiality or universal secret-leakage prevention.</p></aside>
      </div>
    </section>
  );
}

export function SecurityUtilitySection() {
  return (
    <section className="research-section" aria-labelledby="utility-title">
      <SectionIntro
        index="07"
        label="SECURITY × UTILITY"
        title="Guardrails can protect — and still break the product."
        description="The most striking cross-model difference is not simply attack success. It is whether the assistant remains useful when layered guardrails are present."
        accent="teal"
      />
      <div className="panel utility-panel">
        <div className="utility-grid">
          {researchResults.models.map((model) => (
            <article className={`utility-card ${model.accent}-border`} key={model.key}>
              <h3>{model.name}</h3>
              <span>LEGITIMATE TASK SUCCESS</span>
              <small>BASELINE</small>
              <strong>{model.baselineUtility}%</strong>
              <small>DEFENDED</small>
              <strong className={`${model.accent}-text`}>{model.defendedUtility}%</strong>
              <hr />
              <small>FALSE REFUSAL / DEFENDED</small>
              <strong className={model.defendedFalseRefusal ? "pink-text" : "green-text"}>{model.defendedFalseRefusal}%</strong>
            </article>
          ))}
        </div>
        <article className="utility-finding green-border">
          <span className="research-pill green">CENTRAL FINDING</span>
          <h3>Guardrail security–utility compatibility differed substantially across the tested model configurations.</h3>
          <p>The benchmark does not establish why. Architecture, training, alignment, prompting behavior, and runtime are confounded.</p>
        </article>
      </div>
    </section>
  );
}
