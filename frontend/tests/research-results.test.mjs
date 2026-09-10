import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const dataUrl = new URL("../lib/research-results.json", import.meta.url);

async function loadResults() {
  return JSON.parse(await readFile(dataUrl, "utf8"));
}

test("publishes the frozen CM5.6 security, canary, and utility results", async () => {
  const results = await loadResults();

  assert.deepEqual(
    results.models.map(({ key, baselineAttackSuccesses, defendedAttackSuccesses }) => ({
      key,
      baselineAttackSuccesses,
      defendedAttackSuccesses,
    })),
    [
      { key: "llama2", baselineAttackSuccesses: 12, defendedAttackSuccesses: 0 },
      { key: "gemma2", baselineAttackSuccesses: 11, defendedAttackSuccesses: 0 },
      { key: "gemma3", baselineAttackSuccesses: 8, defendedAttackSuccesses: 0 },
      { key: "gemini", baselineAttackSuccesses: 0, defendedAttackSuccesses: 0 },
    ],
  );

  assert.deepEqual(
    results.models.map(({ key, defendedRawCanary, defendedVisibleCanary }) => ({
      key,
      defendedRawCanary,
      defendedVisibleCanary,
    })),
    [
      { key: "llama2", defendedRawCanary: 11, defendedVisibleCanary: 0 },
      { key: "gemma2", defendedRawCanary: 11, defendedVisibleCanary: 0 },
      { key: "gemma3", defendedRawCanary: 6, defendedVisibleCanary: 0 },
      { key: "gemini", defendedRawCanary: 0, defendedVisibleCanary: 0 },
    ],
  );

  assert.deepEqual(
    results.models.map(({ key, baselineUtility, defendedUtility, defendedFalseRefusal }) => ({
      key,
      baselineUtility,
      defendedUtility,
      defendedFalseRefusal,
    })),
    [
      { key: "llama2", baselineUtility: 86.1, defendedUtility: 44.4, defendedFalseRefusal: 50 },
      { key: "gemma2", baselineUtility: 97.2, defendedUtility: 97.2, defendedFalseRefusal: 0 },
      { key: "gemma3", baselineUtility: 100, defendedUtility: 100, defendedFalseRefusal: 0 },
      { key: "gemini", baselineUtility: 83.3, defendedUtility: 80.6, defendedFalseRefusal: 0 },
    ],
  );
});

test("keeps DPI and DATA as null findings while CAN is the only demonstrated mitigation", async () => {
  const results = await loadResults();

  assert.deepEqual(
    results.attackFamilies.map(({ key, baselineSuccesses }) => ({ key, baselineSuccesses })),
    [
      { key: "dpi", baselineSuccesses: [0, 0, 0, 0] },
      { key: "can", baselineSuccesses: [12, 11, 8, 0] },
      { key: "data", baselineSuccesses: [0, 0, 0, 0] },
    ],
  );
  assert.equal(results.defenseVerdicts.outputScreening.status, "demonstrated");
  assert.equal(results.defenseVerdicts.inputScreening.status, "null");
  assert.equal(results.defenseVerdicts.instructionData.status, "null");
});
