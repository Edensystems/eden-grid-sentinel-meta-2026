// Node built-in tests for the M4 proposal contract; fixtures are real workflow output.
import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { normalizeProposal, normalizeOperatorStatus, describeError, isProposalId } from './contract-built/incident.js';

const fx = JSON.parse(readFileSync(new URL('./fixtures/m4_proposals.json', import.meta.url), 'utf8'));
const clone = x => JSON.parse(JSON.stringify(x));

test('pending proposal carries advisory and no realized outcome', () => {
  const p = normalizeProposal(fx.pending_with_advisory);
  assert.equal(p.status, 'pending');
  assert.equal(p.guardian.allowed, true);
  assert.equal(p.advisory.riskLevel, 'high');
  assert.equal(p.realized, null);
  assert.equal(p.approvedBy, null);
  assert.ok(p.intervals.length > 0);
});
test('applied proposal reports the real trade-off and the denied replay', () => {
  const p = normalizeProposal(fx.applied_then_denied);
  assert.equal(p.realized.essentialUnservedKwh, 1);
  assert.ok(Math.abs(p.realized.essentialReductionKwh - 0.7175) < 1e-9);
  assert.ok(Math.abs(p.realized.flexibleUnservedKwh - 0.877) < 1e-9);
  assert.deepEqual(p.audit.map(e => e.event), ['proposed', 'approved', 'applied', 'denied']);
  assert.equal(p.approvedBy, 'panel-operator');
});
test('rejected proposal records the refused execution', () => {
  const p = normalizeProposal(fx.rejected_then_denied);
  assert.deepEqual(p.audit.map(e => e.event), ['proposed', 'rejected', 'denied']);
  assert.equal(p.realized, null);
});
test('rejects a broken audit hash link', () => {
  const bad = clone(fx.applied_then_denied); bad.audit[2].previous_hash = 'a'.repeat(64);
  assert.throws(() => normalizeProposal(bad), /chain/);
});
test('rejects a stale audit head', () => {
  const bad = clone(fx.applied_then_denied); bad.audit_head_hash = bad.audit[0].hash;
  assert.throws(() => normalizeProposal(bad), /head/);
});
test('rejects realized outcome before application', () => {
  const bad = clone(fx.pending_with_advisory);
  Object.assign(bad, { realized_essential_unserved_kwh: 1, realized_flexible_unserved_kwh: 1, realized_essential_reduction_kwh: 0 });
  assert.throws(() => normalizeProposal(bad), /before application/);
});
test('rejects non-simulation labels', () => {
  assert.throws(() => normalizeProposal({ ...fx.pending_with_advisory, mode: 'hardware' }));
  const g = clone(fx.pending_with_advisory); g.guardian.mode = 'live';
  assert.throws(() => normalizeProposal(g));
});
test('rejects partial advisories and invalid ids', () => {
  assert.throws(() => normalizeProposal({ ...fx.pending_with_advisory, advisory_explanation: null }));
  assert.throws(() => normalizeProposal({ ...fx.pending_with_advisory, proposal_id: '../m4/status' }));
  assert.equal(isProposalId('../etc'), false);
});
test('operator status and error codes', () => {
  assert.deepEqual(normalizeOperatorStatus({ mode: 'simulation', operator_id: 'op', live_advisory_enabled: false }),
    { enabled: true, operatorId: 'op', liveAdvisory: false });
  assert.match(describeError('execution_requires_approval'), /requires an approved/);
  assert.match(describeError('decision_not_allowed_in_state_rejected'), /rejected/);
  assert.equal(describeError('<script>'), 'The operator request failed.');
});
