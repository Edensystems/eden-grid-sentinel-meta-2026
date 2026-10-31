import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { normalizeEvaluation } from './contract-built/contract.js';
const fixtures = JSON.parse(readFileSync(new URL('./fixtures/synthetic_m3_results.json', import.meta.url), 'utf8'));
for (const [name, value] of Object.entries(fixtures)) {
  test(`real synthetic M3 response normalized: ${name}`, () => {
    const normalized = normalizeEvaluation(value);
    assert.equal(normalized.scenario,name);
    assert.equal(normalized.points.length,value.forecast.forecasts.length);
    assert.ok(normalized.balanceResidualKwh < 1e-8);
    assert.equal(normalized.reserveViolations,0);
    assert.equal(normalized.essentialBaselineKwh,value.realized.baseline.summary.unserved_essential_kwh);
    assert.equal(normalized.essentialScheduledKwh,value.realized.scheduled.summary.unserved_essential_kwh);
  });
}
