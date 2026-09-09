# PromptGuard Ai — Corrected Four-Model Benchmark Results

**Analysis date:** 2026-09-09 22:56 UTC

**Scope:** Paired 72-case comparison per model, corrected through a separate CM5.5 full-output adjudication overlay. Original databases and evaluator labels remain unchanged.

**Adjudication:** 240 semantic records reviewed; 24 labels changed across 15 cases; 0 ambiguous records.

## 1. Overall security results

| Model | Baseline success | Baseline ASR [95% CI] | Defended success | Defended ASR [95% CI] | Absolute reduction |
|---|---:|---:|---:|---:|---:|
| **Llama 2 7B** | 12/36 | 33.3% [20.2%, 49.7%] | 0/36 | 0.0% [0.0%, 9.6%] | 33.3% |
| **Gemma 2 9B** | 11/36 | 30.6% [18.0%, 46.9%] | 0/36 | 0.0% [0.0%, 9.6%] | 30.6% |
| **Gemma 3 12B** | 8/36 | 22.2% [11.7%, 38.1%] | 0/36 | 0.0% [0.0%, 9.6%] | 22.2% |
| **Gemini 3.1 Flash Lite** | 0/36 | 0.0% [0.0%, 9.6%] | 0/36 | 0.0% [0.0%, 9.6%] | 0.0% |

## 2. Attack-family results

| Family | Model | Baseline | Defended |
|---|---|---:|---:|
| DPI | **Llama 2 7B** | 0/12 (0.0%) | 0/12 (0.0%) |
| DPI | **Gemma 2 9B** | 0/12 (0.0%) | 0/12 (0.0%) |
| DPI | **Gemma 3 12B** | 0/12 (0.0%) | 0/12 (0.0%) |
| DPI | **Gemini 3.1 Flash Lite** | 0/12 (0.0%) | 0/12 (0.0%) |
| CAN | **Llama 2 7B** | 12/12 (100.0%) | 0/12 (0.0%) |
| CAN | **Gemma 2 9B** | 11/12 (91.7%) | 0/12 (0.0%) |
| CAN | **Gemma 3 12B** | 8/12 (66.7%) | 0/12 (0.0%) |
| CAN | **Gemini 3.1 Flash Lite** | 0/12 (0.0%) | 0/12 (0.0%) |
| DATA | **Llama 2 7B** | 0/12 (0.0%) | 0/12 (0.0%) |
| DATA | **Gemma 2 9B** | 0/12 (0.0%) | 0/12 (0.0%) |
| DATA | **Gemma 3 12B** | 0/12 (0.0%) | 0/12 (0.0%) |
| DATA | **Gemini 3.1 Flash Lite** | 0/12 (0.0%) | 0/12 (0.0%) |

## 3. Difficulty results

| Difficulty | Model | Baseline | Defended |
|---|---|---:|---:|
| Easy | **Llama 2 7B** | 4/12 (33.3%) | 0/12 (0.0%) |
| Easy | **Gemma 2 9B** | 3/12 (25.0%) | 0/12 (0.0%) |
| Easy | **Gemma 3 12B** | 2/12 (16.7%) | 0/12 (0.0%) |
| Easy | **Gemini 3.1 Flash Lite** | 0/12 (0.0%) | 0/12 (0.0%) |
| Moderate | **Llama 2 7B** | 4/12 (33.3%) | 0/12 (0.0%) |
| Moderate | **Gemma 2 9B** | 4/12 (33.3%) | 0/12 (0.0%) |
| Moderate | **Gemma 3 12B** | 2/12 (16.7%) | 0/12 (0.0%) |
| Moderate | **Gemini 3.1 Flash Lite** | 0/12 (0.0%) | 0/12 (0.0%) |
| Subtle | **Llama 2 7B** | 4/12 (33.3%) | 0/12 (0.0%) |
| Subtle | **Gemma 2 9B** | 4/12 (33.3%) | 0/12 (0.0%) |
| Subtle | **Gemma 3 12B** | 4/12 (33.3%) | 0/12 (0.0%) |
| Subtle | **Gemini 3.1 Flash Lite** | 0/12 (0.0%) | 0/12 (0.0%) |

## 4. Canary leakage

| Model | Baseline raw | Baseline visible | Defended raw | Defended visible | Redaction rate |
|---|---:|---:|---:|---:|---:|
| **Llama 2 7B** | 12/12 | 12/12 | 11/12 | 0/12 | 100.0% |
| **Gemma 2 9B** | 11/12 | 11/12 | 11/12 | 0/12 | 100.0% |
| **Gemma 3 12B** | 8/12 | 8/12 | 6/12 | 0/12 | 100.0% |
| **Gemini 3.1 Flash Lite** | 0/12 | 0/12 | 0/12 | 0/12 | N/A |

## 5. Benign utility and false refusals

| Model | Baseline legitimate success | Defended legitimate success | Utility change | Baseline false refusal | Defended false refusal |
|---|---:|---:|---:|---:|---:|
| **Llama 2 7B** | 31/36 (86.1%) | 16/36 (44.4%) | -41.7% | 0/36 (0.0%) | 18/36 (50.0%) |
| **Gemma 2 9B** | 35/36 (97.2%) | 35/36 (97.2%) | 0.0% | 0/36 (0.0%) | 0/36 (0.0%) |
| **Gemma 3 12B** | 36/36 (100.0%) | 36/36 (100.0%) | 0.0% | 0/36 (0.0%) | 0/36 (0.0%) |
| **Gemini 3.1 Flash Lite** | 30/36 (83.3%) | 29/36 (80.6%) | -2.8% | 0/36 (0.0%) | 0/36 (0.0%) |

## 6. Paired statistical results

| Model | Metric | Evaluated pairs | Mitigated/degraded | Induced/recovered | Exact p-value |
|---|---|---:|---:|---:|---:|
| **Llama 2 7B** | Adversarial Attack Success (Baseline vs Defended) | 36 | 12 | 0 | 0.000488 |
| **Llama 2 7B** | Benign Legitimate Task Success (Baseline vs Defended) | 36 | 16 | 1 | 0.000275 |
| **Gemma 2 9B** | Adversarial Attack Success (Baseline vs Defended) | 36 | 11 | 0 | 0.000977 |
| **Gemma 2 9B** | Benign Legitimate Task Success (Baseline vs Defended) | 36 | 0 | 0 | N/A |
| **Gemma 3 12B** | Adversarial Attack Success (Baseline vs Defended) | 36 | 8 | 0 | 0.007812 |
| **Gemma 3 12B** | Benign Legitimate Task Success (Baseline vs Defended) | 36 | 0 | 0 | N/A |
| **Gemini 3.1 Flash Lite** | Adversarial Attack Success (Baseline vs Defended) | 36 | 0 | 0 | N/A |
| **Gemini 3.1 Flash Lite** | Benign Legitimate Task Success (Baseline vs Defended) | 36 | 1 | 0 | 1.0 |

## 7. Supplementary Gemini tool study

> Local comparison models (Llama 2 7B, Gemma 2 9B, Gemma 3 12B) were evaluated without native tool schemas and execution hooks to preserve strict provider neutrality. TOOL experiments evaluated Gemini 3.1 Flash Lite with read-only fixture tools and least-privilege authorization.

The supplementary set contains 12 adversarial and 6 benign tool cases. It remains excluded from the four-model comparison.

## 8. Corrected interpretation

The results did not show progressive robustness improvement across the three tested open-weight checkpoints. Observed baseline vulnerability was concentrated entirely in deterministic canary disclosure after full-output adjudication: Llama 2 leaked in 12/12 CAN cases, Gemma 2 in 11/12, and Gemma 3 in 8/12. No baseline DPI or DATA successes were confirmed under the existing attack-objective rubric. Gemini had no observed baseline successes on this fixed benchmark, but that does not establish immunity or isolate model generation as a cause.

No defended attack successes were observed in this sample. This supports effectiveness against the fixed benchmark, not universal protection. The clearest comparative finding is model-specific guardrail security–utility compatibility: Llama 2 retained a substantial defended utility penalty and false-refusal burden, while the tested Gemma configurations preserved utility more successfully. These observations are descriptive and cannot be attributed causally to release year or architecture.

## 9. Limitations

1. The attacks are fixed, explicit, and structurally aligned with narrow deterministic defenses.
2. Each family and difficulty subgroup contains only 12 cases; zero observed successes still has a wide Wilson interval.
3. Local Ollama and cloud Gemini runs differ in provider, native templates, and inference environment.
4. Semantic labels are now independently adjudicated from stored outputs, but adjudication is still a single-reviewer judgment rather than blinded multi-rater labeling.
5. One execution per prompt does not estimate run-to-run stochastic variance.