import type {
  AttackEligibilityResponse,
  AttackFamily,
  AttackGenerationResult,
  BenchmarkMetricsResponse,
  EvaluationResponse,
  ExperimentRunDetailResponse,
  ExperimentRunResponse,
  ResearchSummaryResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMsg = `Request failed with status ${response.status}`;
    try {
      const data = await response.json();
      if (data && typeof data === "object" && "detail" in data) {
        errorMsg = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      const text = await response.text().catch(() => "");
      if (text) errorMsg = text;
    }
    throw new Error(errorMsg);
  }
  return response.json();
}

export async function streamChat(
  prompt: string,
  onChunk: (chunk: string) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
    signal,
  });

  if (!response.ok) {
    let errorMsg = `Request failed with status ${response.status}`;
    try {
      const data = await response.json();
      if (data && typeof data === "object" && "detail" in data) {
        errorMsg = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      const text = await response.text().catch(() => "");
      if (text) errorMsg = text;
    }
    throw new Error(errorMsg);
  }

  if (!response.body) {
    onChunk(await response.text());
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        const remaining = decoder.decode();
        if (remaining) {
          onChunk(remaining);
        }
        break;
      }
      onChunk(decoder.decode(value, { stream: true }));
    }
  } finally {
    reader.releaseLock();
  }
}

export async function fetchAttackEligibility(
  originalTask: string,
  signal?: AbortSignal,
): Promise<AttackEligibilityResponse> {
  const response = await fetch(`${API_BASE}/api/attacks/eligibility`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ original_task: originalTask }),
    signal,
  });
  return handleResponse<AttackEligibilityResponse>(response);
}

export async function generateAttack(
  originalTask: string,
  attackFamily: AttackFamily,
  signal?: AbortSignal,
): Promise<AttackGenerationResult> {
  const response = await fetch(`${API_BASE}/api/attacks/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      original_task: originalTask,
      attack_family: attackFamily,
    }),
    signal,
  });
  return handleResponse<AttackGenerationResult>(response);
}

export async function runExperiment(
  payload: {
    original_task: string;
    attack_prompt: string;
    attack_family: AttackFamily;
    model?: string;
    temperature?: number;
    max_output_tokens?: number;
    generation_source?: "generated" | "edited_generated" | "manual";
    attack_edited?: boolean;
  },
  signal?: AbortSignal,
): Promise<ExperimentRunResponse> {
  const response = await fetch(`${API_BASE}/api/experiments/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });
  return handleResponse<ExperimentRunResponse>(response);
}

export async function evaluateExperiment(
  experimentId: string,
  signal?: AbortSignal,
): Promise<EvaluationResponse> {
  const response = await fetch(`${API_BASE}/api/experiments/${experimentId}/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    signal,
  });
  return handleResponse<EvaluationResponse>(response);
}

export async function fetchBenchmarks(signal?: AbortSignal): Promise<BenchmarkMetricsResponse> {
  const response = await fetch(`${API_BASE}/api/benchmarks`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    signal,
  });
  return handleResponse<BenchmarkMetricsResponse>(response);
}

export async function fetchResearchSummary(signal?: AbortSignal): Promise<ResearchSummaryResponse> {
  const response = await fetch(`${API_BASE}/api/research`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    signal,
  });
  return handleResponse<ResearchSummaryResponse>(response);
}

export async function fetchExperimentDetail(
  experimentId: string,
  signal?: AbortSignal,
): Promise<ExperimentRunDetailResponse> {
  const response = await fetch(`${API_BASE}/api/experiments/${experimentId}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    signal,
  });
  return handleResponse<ExperimentRunDetailResponse>(response);
}

