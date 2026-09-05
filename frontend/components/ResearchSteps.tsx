const steps = [
  ["1", "Ask normally", "Get a live answer first."],
  ["2", "AI checks attack fit", "Only relevant attack families are suggested."],
  ["3", "Run paired test", "Same attack: baseline vs defended."],
  ["4", "Benchmark", "Store real runs and compare guardrails."],
];

export function ResearchSteps() {
  return (
    <aside className="research-steps">
      <strong>How research mode works</strong>
      <div className="steps-list">
        {steps.map(([n, title, description], index) => (
          <div className="step" key={n}>
            <span className={`step-number s${index + 1}`}>{n}</span>
            <div>
              <b>{title}</b>
              <small>{description}</small>
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}
