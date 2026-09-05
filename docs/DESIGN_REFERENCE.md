# Final Figma Design Reference — Frozen

Do **not** redesign the frontend. The supplied frontend source was created from the finalized PromptGuard Ai design. Antigravity should run/verify/fix it, not recreate it.

Final Figma:
`https://www.figma.com/design/kWXjddb8CeSD56D9uItKO8/PromptGuard-Ai-%E2%80%94-LLM-Guardrail-Research-Platform?node-id=0-1`

File key: `kWXjddb8CeSD56D9uItKO8`

1440×1024 reference frames:
- `1:2` — Assistant Home
- `1:5` — Response + Attack Eligibility
- `1:8` — Attack Transform + Paired Experiment
- `1:12` — Research Benchmarks
- `17:10` — Research

Navigation is exactly:
**Assistant → Experiments → Benchmarks → Research**
No Runs page.

Visual direction:
- near-black/deep navy
- dark sidebar
- thin blue/indigo borders
- cyan/violet aurora glow and primary accents
- green defense/success
- coral/red-orange attack/failure
- amber secondary research indicators
- premium developer/research tool, not gaming dashboard

Key states:
- Assistant Home: free-form prompt, six suggestions, research-flow explainer
- Response: normal live answer appears first, then four eligibility cards
- Experiment: editable transformed attack + side-by-side baseline/defended results
- Benchmarks: concise aggregate summary and four before/after rows
- Research: research question, simple aggregate visuals, key findings, benchmark-grounded answer

Initial benchmark/research values in the starter are **illustrative Figma preview data**, not research results. CX7 must replace live research states with API data while preserving the visual design.

Logo: `frontend/public/promptguard-logo.png`.
