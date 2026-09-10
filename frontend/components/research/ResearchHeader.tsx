const githubUrl = "https://github.com/HasanKhan05/PromptGuard-Ai";

const navigation = [
  { href: "#method", label: "Method" },
  { href: "#results", label: "Results" },
  { href: "#limitations", label: "Limitations" },
  { href: "#reproducibility", label: "Reproducibility" },
];

export function ResearchHeader() {
  return (
    <header className="research-header" aria-label="Primary navigation">
      <a className="research-brand" href="#top" aria-label="PromptGuard Ai — back to top">
        <strong>PromptGuard Ai</strong>
        <span>LLM GUARDRAIL RESEARCH</span>
      </a>
      <nav aria-label="Research sections">
        {navigation.map((item) => <a href={item.href} key={item.href}>{item.label}</a>)}
      </nav>
      <a className="github-button" href={githubUrl} target="_blank" rel="noreferrer">
        GitHub <span aria-hidden="true">↗</span>
      </a>
    </header>
  );
}

export function ResearchFooter() {
  return (
    <footer className="research-footer">
      <p>PROMPTGUARD AI / FINAL FROZEN RESEARCH</p>
      <nav aria-label="Footer navigation">
        <a href={githubUrl} target="_blank" rel="noreferrer">GitHub ↗</a>
        <a href="#method">Methodology</a>
        <a href="#results">Results</a>
      </nav>
    </footer>
  );
}
