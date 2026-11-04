/* Structural normalization for the M4 ProposalView contract. Never substitute fake values. */
export type ProposalStatus = 'pending' | 'approved' | 'rejected' | 'applied' | 'expired';
export type AuditEventName = 'proposed' | 'approved' | 'rejected' | 'applied' | 'expired' | 'denied';
export type AuditEvent = {
  sequence: number; at: string; actor: string; event: AuditEventName;
  note: string; previousHash: string; hash: string;
};
export type PlannedInterval = {
  timestamp: string; forecastSolarKw: number; essentialKw: number;
  originalFlexibleKw: number; plannedFlexibleKw: number;
};
export type Advisory = {
  model: string; riskLevel: string; headline: string; explanation: string; nextStep: string;
};
export type Proposal = {
  mode: 'simulation';
  id: string;
  scenario: string;
  status: ProposalStatus;
  expiresAt: string;
  guardian: {
    allowed: boolean; reasons: string[]; warnings: string[];
    essentialBeforeKwh: number; essentialAfterKwh: number; reserveViolations: number;
  };
  shiftedKwh: number;
  planSha256: string;
  intervals: PlannedInterval[];
  forecast: { essentialBaselineKwh: number; essentialPlannedKwh: number; flexibleBaselineKwh: number; flexiblePlannedKwh: number };
  approvedBy: string | null;
  advisory: Advisory | null;
  realized: { essentialUnservedKwh: number; flexibleUnservedKwh: number; essentialReductionKwh: number } | null;
  auditHeadHash: string;
  audit: AuditEvent[];
};
export type OperatorStatus = { enabled: false } | { enabled: true; operatorId: string; liveAdvisory: boolean };

const STATUSES: readonly ProposalStatus[] = ['pending', 'approved', 'rejected', 'applied', 'expired'];
const EVENTS: readonly AuditEventName[] = ['proposed', 'approved', 'rejected', 'applied', 'expired', 'denied'];
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const SHA = /^[0-9a-f]{64}$/;

function obj(x: unknown, path: string): Record<string, unknown> {
  if (typeof x !== 'object' || x === null || Array.isArray(x)) throw new Error(`Invalid ${path}`);
  return x as Record<string, unknown>;
}
function num(x: unknown, path: string, min = 0): number {
  if (typeof x !== 'number' || !Number.isFinite(x) || x < min) throw new Error(`Invalid ${path}`);
  return x;
}
function str(x: unknown, path: string): string {
  if (typeof x !== 'string' || !x.length) throw new Error(`Invalid ${path}`);
  return x;
}
function bool(x: unknown, path: string): boolean {
  if (typeof x !== 'boolean') throw new Error(`Invalid ${path}`);
  return x;
}
function strList(x: unknown, path: string): string[] {
  if (!Array.isArray(x)) throw new Error(`Invalid ${path}`);
  return x.map((v, i) => str(v, `${path}[${i}]`));
}
function time(x: unknown, path: string): string {
  const s = str(x, path);
  if (Number.isNaN(Date.parse(s))) throw new Error(`Invalid ${path}`);
  return s;
}
function hash(x: unknown, path: string): string {
  const s = str(x, path);
  if (!SHA.test(s)) throw new Error(`Invalid ${path}`);
  return s;
}
function optStr(x: unknown, path: string): string | null {
  return x === null ? null : str(x, path);
}
function optNum(x: unknown, path: string, min = 0): number | null {
  return x === null ? null : num(x, path, min);
}

export function isProposalId(x: unknown): x is string {
  return typeof x === 'string' && UUID.test(x);
}

export function normalizeProposal(raw: unknown): Proposal {
  const root = obj(raw, 'proposal');
  if (root.mode !== 'simulation') throw new Error('Proposal is not labelled simulation');
  if (!isProposalId(root.proposal_id)) throw new Error('Invalid proposal_id');
  const status = root.status;
  if (typeof status !== 'string' || !(STATUSES as readonly string[]).includes(status)) throw new Error('Invalid status');
  const g = obj(root.guardian, 'guardian');
  if (g.mode !== 'simulation') throw new Error('Guardian verdict is not labelled simulation');
  if (!Array.isArray(root.planned_intervals) || !root.planned_intervals.length) throw new Error('Invalid planned_intervals');
  const intervals = root.planned_intervals.map((r, i) => {
    const row = obj(r, `planned_intervals[${i}]`);
    return {
      timestamp: time(row.timestamp, 'interval.timestamp'),
      forecastSolarKw: num(row.forecast_solar_kw, 'forecast_solar_kw'),
      essentialKw: num(row.essential_demand_kw, 'essential_demand_kw'),
      originalFlexibleKw: num(row.original_flexible_kw, 'original_flexible_kw'),
      plannedFlexibleKw: num(row.planned_flexible_kw, 'planned_flexible_kw'),
    };
  });
  if (!Array.isArray(root.audit) || !root.audit.length) throw new Error('Invalid audit');
  const audit = root.audit.map((e, i) => {
    const ev = obj(e, `audit[${i}]`);
    if (typeof ev.event !== 'string' || !(EVENTS as readonly string[]).includes(ev.event)) throw new Error('Invalid audit event');
    if (ev.sequence !== i + 1) throw new Error('Audit sequence gap');
    return {
      sequence: i + 1, at: time(ev.at, 'audit.at'), actor: str(ev.actor, 'audit.actor'),
      event: ev.event as AuditEventName, note: typeof ev.note === 'string' ? ev.note : '',
      previousHash: hash(ev.previous_hash, 'audit.previous_hash'), hash: hash(ev.hash, 'audit.hash'),
    };
  });
  audit.forEach((e, i) => {
    if (e.previousHash !== (i ? audit[i - 1].hash : '0'.repeat(64))) throw new Error('Audit chain link broken');
  });
  const head = hash(root.audit_head_hash, 'audit_head_hash');
  if (head !== audit[audit.length - 1].hash) throw new Error('Audit head mismatch');

  const model = optStr(root.advisory_model, 'advisory_model');
  const advisory = model === null ? null : {
    model,
    riskLevel: str(root.advisory_risk_level, 'advisory_risk_level'),
    headline: str(root.advisory_headline, 'advisory_headline'),
    explanation: str(root.advisory_explanation, 'advisory_explanation'),
    nextStep: str(root.advisory_next_step, 'advisory_next_step'),
  };
  const re = optNum(root.realized_essential_unserved_kwh, 'realized_essential_unserved_kwh');
  const rf = optNum(root.realized_flexible_unserved_kwh, 'realized_flexible_unserved_kwh');
  const rr = optNum(root.realized_essential_reduction_kwh, 'realized_essential_reduction_kwh', -Infinity);
  if ((re === null) !== (rf === null) || (re === null) !== (rr === null)) throw new Error('Partial realized outcome');
  if (status === 'applied' && re === null) throw new Error('Applied proposal without realized outcome');
  if (status !== 'applied' && re !== null) throw new Error('Realized outcome before application');

  return {
    mode: 'simulation',
    id: root.proposal_id,
    scenario: str(root.scenario, 'scenario'),
    status: status as ProposalStatus,
    expiresAt: time(root.expires_at, 'expires_at'),
    guardian: {
      allowed: bool(g.allowed, 'guardian.allowed'),
      reasons: strList(g.reasons, 'guardian.reasons'),
      warnings: strList(g.warnings, 'guardian.warnings'),
      essentialBeforeKwh: num(g.forecast_essential_unserved_before_kwh, 'guardian.before'),
      essentialAfterKwh: num(g.forecast_essential_unserved_after_kwh, 'guardian.after'),
      reserveViolations: num(g.predicted_reserve_violations, 'guardian.reserve_violations'),
    },
    shiftedKwh: num(root.forecast_shifted_kwh, 'forecast_shifted_kwh'),
    planSha256: hash(root.plan_sha256, 'plan_sha256'),
    intervals,
    forecast: {
      essentialBaselineKwh: num(root.forecast_essential_unserved_baseline_kwh, 'forecast_essential_unserved_baseline_kwh'),
      essentialPlannedKwh: num(root.forecast_essential_unserved_planned_kwh, 'forecast_essential_unserved_planned_kwh'),
      flexibleBaselineKwh: num(root.forecast_flexible_unserved_baseline_kwh, 'forecast_flexible_unserved_baseline_kwh'),
      flexiblePlannedKwh: num(root.forecast_flexible_unserved_planned_kwh, 'forecast_flexible_unserved_planned_kwh'),
    },
    approvedBy: optStr(root.approved_by, 'approved_by'),
    advisory,
    realized: re === null ? null : { essentialUnservedKwh: re, flexibleUnservedKwh: rf as number, essentialReductionKwh: rr as number },
    auditHeadHash: head,
    audit,
  };
}

export function normalizeOperatorStatus(raw: unknown): OperatorStatus {
  const root = obj(raw, 'operator status');
  if (root.mode !== 'simulation') throw new Error('Operator status is not labelled simulation');
  return { enabled: true, operatorId: str(root.operator_id, 'operator_id'), liveAdvisory: bool(root.live_advisory_enabled, 'live_advisory_enabled') };
}

/** Backend error codes the UI may show verbatim; anything else is reported generically. */
export const KNOWN_ERRORS: Record<string, string> = {
  execution_requires_approval: 'Denied: execution requires an approved proposal.',
  approval_operator_mismatch: 'Denied: only the approving operator may apply this plan.',
  guardian_rejected_plan: 'Denied: the Guardian rejected this plan.',
  plan_digest_mismatch: 'Denied: the plan no longer matches its approved hash.',
  actual_simulation_safety_failure: 'Denied: the simulated outcome failed a safety check.',
  proposal_not_found: 'Proposal not found (the local operator API keeps state in memory only).',
  live_advisory_disabled: 'Live Muse Spark advisory is disabled on the operator API.',
  advisory_not_configured: 'Live advisory requested but no model credential is configured on the server.',
  advisory_unavailable: 'The model advisory failed validation or was unavailable. No proposal was created.',
  advisory_requires_default_policy: 'Live advisory requires the default scheduling policy.',
  unknown_scenario: 'Unknown synthetic scenario.',
  invalid_decision: 'Invalid decision.',
};
export function describeError(code: unknown): string {
  if (typeof code === 'string') {
    if (code in KNOWN_ERRORS) return KNOWN_ERRORS[code];
    if (code.startsWith('decision_not_allowed_in_state_')) return `Denied: no decision allowed once a proposal is ${code.slice(30)}.`;
  }
  return 'The operator request failed.';
}
