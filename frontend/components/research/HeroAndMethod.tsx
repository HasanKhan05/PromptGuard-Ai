import researchResults from "@/lib/research-results.json";
import { SectionIntro } from "./SectionIntro";

export function HeroSection() {
  return (
    <section className="hero-section" aria-labelledby="hero-title">
      <div className="hero-copy">
        <span className="research-pill cyan">AI SECURITY RESEARCH</span>
        <h1 id="hero-title">Cross-Model Evaluation of<br />Prompt-Injection Robustness</h1>
        <p className="hero-lede">
          A paired benchmark studying how selected language models respond to prompt-injection attacks — and what security costs guardrails impose on legitimate use.
        </p>
        <p className="author-line">MUHAMMAD HASAN DAD KHAN&nbsp; · &nbsp;FAST-NUCES&nbsp; · &nbsp;2026</p>
      </div>

      <article className="panel hero-data-card">
        <span className="metric-label purple-text">FINAL FROZEN RESULTS</span>
        <strong className="hero-sequence">33.3 → 30.6 → 22.2 → 0</strong>
        <p>Baseline ASR (%) across Llama 2, Gemma 2, Gemma 3, and Gemini on the fixed 36-case comparable adversarial subset.</p>
        <div className="hero-data-grid">
          <div><strong>36</strong><span>ADVERSARIAL / MODEL</span></div>
          <div><strong>36</strong><span>BENIGN / MODEL</span></div>
        </div>
        <small>Descriptive comparison — not a causal study of release year.</small>
      </article>

      <div className="mini-stat-grid" aria-label="Study overview">
        <MiniStat value="4" label="Models" accent="cyan" />
        <MiniStat value="72" label="Paired cases / model" accent="purple" />
        <MiniStat value="0" label="Defended successes" accent="green" />
      </div>
    </section>
  );
}

function MiniStat({ value, label, accent }: { value: string; label: string; accent: string }) {
  return <div className="mini-stat"><strong className={`${accent}-text`}>{value}</strong><span>{label}</span></div>;
}

export function ResearchQuestionSection() {
  return (
    <section className="research-section" aria-labelledby="question-title">
      <SectionIntro
        index="01"
        label="RESEARCH QUESTION"
        title="What does the benchmark actually test?"
        description="How do selected LLM configurations differ in observed prompt-injection vulnerability, and how do mapped application-level guardrails change both attack success and benign-task utility?"
        accent="purple"
      />
      <article className="panel question-card">
        <div>
          <span className="research-pill cyan">PRIMARY QUESTION</span>
          <blockquote>“Can lightweight guardrails reduce observed attack success without making the assistant meaningfully less useful?”</blockquote>
        </div>
        <aside className="inner-card scope-card">
          <span className="metric-label purple-text">SCOPE</span>
          <p>Fixed attack set<br />Paired baseline/defended runs<br />3 comparable attack families<br />1 supplementary TOOL study</p>
        </aside>
      </article>
    </section>
  );
}

export function ProtocolSection() {
  return (
    <section className="research-section" id="method" aria-labelledby="protocol-title">
      <SectionIntro
        index="02"
        label="PROTOCOL"
        title="One prompt. Two conditions. One variable changed."
        description="Within each model, the approved attack prompt is held constant. The baseline and defended runs use the same task, model settings, and context; only the mapped defense changes."
      />
      <div className="panel protocol-diagram">
        <FlowCard className="frozen-card" label="FROZEN ATTACK" title="Same approved adversarial prompt" accent="purple" />
        <span className="protocol-arrow arrow-one" aria-hidden="true">↗</span>
        <span className="protocol-arrow arrow-two" aria-hidden="true">↘</span>
        <div className="protocol-conditions">
          <FlowCard label="BASELINE" title="No mapped defense" detail="Observed response + evaluator label" accent="pink" />
          <FlowCard label="DEFENDED" title="Mapped defense enabled" detail="Observed response + evaluator label" accent="green" />
        </div>
        <span className="protocol-arrow arrow-three" aria-hidden="true">↘</span>
        <span className="protocol-arrow arrow-four" aria-hidden="true">↗</span>
        <FlowCard className="evaluation-card" label="EVALUATION" title="Security outcome + benign utility + paired transition" accent="cyan" />
        <p className="protocol-footnote">72 comparable cases per model&nbsp; · &nbsp;36 adversarial&nbsp; · &nbsp;36 benign&nbsp; · &nbsp;exact frozen attacks reused</p>
      </div>
    </section>
  );
}

function FlowCard({
  label,
  title,
  detail,
  accent,
  className = "",
}: {
  label: string;
  title: string;
  detail?: string;
  accent: string;
  className?: string;
}) {
  return (
    <article className={`flow-card ${accent}-border ${className}`}>
      <span className={`research-pill ${accent}`}>{label}</span>
      <h3>{title}</h3>
      {detail ? <p>{detail}</p> : null}
    </article>
  );
}

export function ModelTimelineSection() {
  return (
    <section className="research-section" aria-labelledby="timeline-title">
      <SectionIntro
        index="03"
        label="MODEL TIMELINE"
        title="A descriptive shift across selected checkpoints"
        description="Observed baseline ASR decreases across the three open-weight checkpoints, while Gemini records no successes on this fixed subset. This is descriptive only: family, scale, training, alignment, architecture, and runtime all differ."
        accent="teal"
      />
      <div className="panel timeline-panel">
        <div className="timeline-scroll">
          <div className="timeline-track">
            {researchResults.models.map((model) => (
              <article className={`timeline-model ${model.accent}`} key={model.key}>
                <span>{model.year}</span>
                <h3>{model.fullName.replace(" Flash Lite", "")}</h3>
                <strong>{model.baselineAsr}%</strong>
                <i aria-hidden="true" />
                <small>BASELINE ASR</small>
              </article>
            ))}
          </div>
        </div>
        <aside className="causality-note">
          <span>CAUSALITY WARNING</span>
          <p>Release year is not treated as a causal variable. The comparison is across selected model configurations, not controlled model generations.</p>
        </aside>
      </div>
    </section>
  );
}
