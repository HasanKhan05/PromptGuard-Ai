type Accent = "cyan" | "purple" | "teal" | "amber";

export function SectionIntro({
  index,
  label,
  title,
  description,
  accent = "cyan",
}: {
  index: string;
  label: string;
  title: string;
  description?: string;
  accent?: Accent;
}) {
  return (
    <header className="section-intro">
      <span className={`research-pill ${accent}`}>{index} / {label}</span>
      <h2>{title}</h2>
      {description ? <p>{description}</p> : null}
    </header>
  );
}
