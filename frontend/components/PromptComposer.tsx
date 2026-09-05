"use client";

import { ArrowRight, LoaderCircle } from "lucide-react";

export function PromptComposer({
  prompt,
  setPrompt,
  loading,
  onSubmit,
}: {
  prompt: string;
  setPrompt: (value: string) => void;
  loading: boolean;
  onSubmit: () => void;
}) {
  return (
    <div className="prompt-card">
      <label htmlFor="prompt" className="prompt-label">Ask PromptGuard Ai</label>
      <textarea
        id="prompt"
        value={prompt}
        onChange={(event) => setPrompt(event.target.value)}
        placeholder="Type any software-development prompt..."
        rows={4}
        disabled={loading}
      />
      <div className="prompt-card-footer">
        <span>Your prompt is free-form — suggestions below only help you get started.</span>
        <button className="gradient-button" onClick={onSubmit} disabled={loading || !prompt.trim()}>
          {loading ? <LoaderCircle size={15} className="spin" /> : null}
          {loading ? "Calling model..." : "Send to model"}
          {!loading ? <ArrowRight size={15} /> : null}
        </button>
      </div>
    </div>
  );
}
