import { ArrowRight } from "lucide-react";

export function SuggestionCard({
  title,
  description,
  onUse,
}: {
  title: string;
  description: string;
  onUse: () => void;
}) {
  return (
    <button type="button" className="suggestion-card" onClick={onUse}>
      <strong>{title}</strong>
      <span>{description}</span>
      <small>Use suggestion <ArrowRight size={12} /></small>
    </button>
  );
}
