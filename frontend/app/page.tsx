"use client";

import { useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { ArrowRight, RotateCcw } from "lucide-react";
import { PromptComposer } from "@/components/PromptComposer";
import { SuggestionCard } from "@/components/SuggestionCard";
import { ResearchSteps } from "@/components/ResearchSteps";
import { AttackCard } from "@/components/AttackCard";
import { suggestions } from "@/lib/demo-data";
import { fetchAttackEligibility, streamChat } from "@/lib/api";

export default function AssistantPage() {
  const [prompt, setPrompt] = useState("");
  const [submittedPrompt, setSubmittedPrompt] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showEligibility, setShowEligibility] = useState(false);
  const [eligibilityLoading, setEligibilityLoading] = useState(false);
  const [eligibilityError, setEligibilityError] = useState("");
  const [eligibilityResults, setEligibilityResults] = useState<import("@/lib/types").AttackEligibilityItem[] | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const eligibleCount = useMemo(() => {
    if (!eligibilityResults) return 0;
    return eligibilityResults.filter((item) => item.status !== "NOT_APPLICABLE").length;
  }, [eligibilityResults]);

  async function submit() {
    const value = prompt.trim();
    if (!value || loading) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setSubmittedPrompt(value);
    setResponse("");
    setError("");
    setShowEligibility(false);
    setEligibilityResults(null);
    setEligibilityError("");
    setLoading(true);

    try {
      await streamChat(value, (chunk) => setResponse((current) => current + chunk), controller.signal);
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setError(err instanceof Error ? err.message : "The model request failed.");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleExploreAttacks() {
    setShowEligibility(true);
    if (eligibilityResults || eligibilityLoading || !submittedPrompt) return;

    setEligibilityLoading(true);
    setEligibilityError("");
    try {
      const data = await fetchAttackEligibility(submittedPrompt);
      setEligibilityResults(data.results);
    } catch (err) {
      setEligibilityError(err instanceof Error ? err.message : "Failed to analyze attack eligibility.");
    } finally {
      setEligibilityLoading(false);
    }
  }

  function reset() {
    abortRef.current?.abort();
    setPrompt("");
    setSubmittedPrompt("");
    setResponse("");
    setError("");
    setShowEligibility(false);
    setEligibilityResults(null);
    setEligibilityError("");
    setLoading(false);
  }

  if (submittedPrompt) {
    return (
      <div className="page response-page">
        <div className="top-label">Assistant</div>
        <section className="response-heading">
          <div>
            <h1>Your prompt, answered first.</h1>
            <p>Research begins only after the normal software-development response is returned.</p>
          </div>
          <button className="ghost-button" onClick={reset}><RotateCcw size={14} /> New prompt</button>
        </section>

        <section className="conversation-card">
          <div className="message user-message">
            <div className="eyebrow">YOU</div>
            <p>{submittedPrompt}</p>
          </div>
          <div className="message assistant-message">
            <div className="eyebrow">PROMPTGUARD AI</div>
            {loading && !response ? <p className="muted">Waiting for the first streamed tokens…</p> : null}
            {response ? <div className="markdown"><ReactMarkdown>{response}</ReactMarkdown></div> : null}
            {error ? <p className="error-text">{error}</p> : null}
            <small>Generated live through `/api/chat` — never a saved answer.</small>
          </div>
          <div className="research-strip">
            <span className="research-badge">Research mode</span>
            <span>
              {loading
                ? "Finish the live response before exploring attacks."
                : eligibilityResults
                ? `${eligibleCount} relevant attack transformations identified for this prompt.`
                : "Explore how this prompt can be transformed into 4 research attack families."}
            </span>
            <button onClick={handleExploreAttacks} disabled={loading || !!error || eligibilityLoading}>
              {eligibilityLoading ? "Analyzing…" : <>Explore attacks <ArrowRight size={13} /></>}
            </button>
          </div>
        </section>

        {showEligibility ? (
          <section className="eligibility-section">
            <div className="section-heading-row">
              <div>
                <h2>Attack eligibility</h2>
                <p>One compact analysis evaluates applicability across all four fixed attack families.</p>
              </div>
              <span className="pill preview">LIVE ANALYSIS</span>
            </div>
            {eligibilityLoading ? (
              <div className="note" style={{ padding: "1.5rem" }}>Analyzing attack eligibility with PromptGuard backend…</div>
            ) : eligibilityError ? (
              <p className="error-text" style={{ padding: "1rem" }}>{eligibilityError}</p>
            ) : eligibilityResults ? (
              <div className="attack-grid">
                {eligibilityResults.map((item) => (
                  <AttackCard item={item} task={submittedPrompt} key={item.family} />
                ))}
              </div>
            ) : null}
          </section>
        ) : null}
      </div>
    );
  }

  return (
    <div className="page home-page">
      <div className="top-label">Software Development Assistant</div>
      <section className="home-hero">
        <h1>Build freely. Test intelligently.</h1>
        <p>
          Ask anything about software development. PromptGuard Ai answers through a live model API,
          then can turn your own prompt into relevant adversarial experiments.
        </p>
      </section>

      <div className="home-grid">
        <div>
          <PromptComposer prompt={prompt} setPrompt={setPrompt} loading={loading} onSubmit={submit} />
          <div className="try-label">Try asking…</div>
          <div className="suggestion-grid">
            {suggestions.map((item) => (
              <SuggestionCard
                key={item.title}
                title={item.title}
                description={item.description}
                onUse={() => setPrompt(item.prompt)}
              />
            ))}
          </div>
        </div>
        <ResearchSteps />
      </div>
    </div>
  );
}
