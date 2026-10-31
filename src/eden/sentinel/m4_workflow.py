"""Local-only human approval state machine for synthetic M4 simulation.

In-memory and single-process: NOT production auth/persistence. No filesystem,
network, cloud or hardware access. Only caller-authenticated identity is accepted.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hmac
import json
from threading import RLock
from typing import TYPE_CHECKING, Callable, Literal
from uuid import uuid4

from pydantic import AwareDatetime, Field

from eden.sentinel.twin import PowerInterval, SimulationRequest, TwinModel, run_simulation
from eden.sentinel.m3_demo import available_scenarios, previous_day_fixture, target_fixture
from eden.sentinel.m3_scheduler import SchedulingPolicy, SchedulingResult, schedule_flexible_load
from eden.sentinel.m4_guardian import GuardianVerdict, guard_schedule

if TYPE_CHECKING:
    # Type-only: the M2 safeguard requires that importing the API never loads
    # the Model API adapter. Advisories are validated field by field in create().
    from eden.sentinel.muse import M3AdvisoryResult


class WorkflowError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class AuditEvent(TwinModel):
    sequence: int = Field(ge=1)
    proposal_id: str = Field(min_length=1)
    at: AwareDatetime
    actor: str = Field(min_length=1)
    event: Literal["proposed", "approved", "rejected", "applied", "expired", "denied"]
    note: str
    previous_hash: str
    hash: str


class PlannedInterval(TwinModel):
    """What the operator is approving, per interval (forecast-time values)."""
    timestamp: AwareDatetime
    duration_minutes: int
    forecast_solar_kw: float
    essential_demand_kw: float
    original_flexible_kw: float
    planned_flexible_kw: float


class ProposalView(TwinModel):
    mode: Literal["simulation"] = "simulation"
    proposal_id: str
    scenario: str
    status: Literal["pending", "approved", "rejected", "applied", "expired"]
    expires_at: AwareDatetime
    guardian: GuardianVerdict
    forecast_shifted_kwh: float
    # Informed approval: the exact Guardian-checked plan and its forecast trade-off.
    plan_sha256: str
    planned_intervals: list[PlannedInterval]
    forecast_essential_unserved_baseline_kwh: float
    forecast_essential_unserved_planned_kwh: float
    forecast_flexible_unserved_baseline_kwh: float
    forecast_flexible_unserved_planned_kwh: float
    # Retain this to detect later truncation: verify_audit(events, expected_head=...).
    audit_head_hash: str
    approved_by: str | None = None
    # Advisory-only M2 attachment (headline/risk for the human reader). It has
    # no authority: Guardian + operator decision remain the only gates.
    advisory_model: str | None = None
    advisory_risk_level: str | None = None
    advisory_headline: str | None = None
    realized_essential_unserved_kwh: float | None = None
    realized_flexible_unserved_kwh: float | None = None
    realized_essential_reduction_kwh: float | None = None
    audit: list[AuditEvent]


def _plan_digest(plan: SchedulingResult, original: SimulationRequest,
                 policy: SchedulingPolicy) -> str:
    """Bind plan, forecast input and policy together. The Guardian re-derives the
    plan from the stored input, so only this digest detects a coherent edit of all three."""
    material = {
        "scheduled_request": plan.scheduled_request.model_dump(mode="json"),
        "original": original.model_dump(mode="json"),
        "policy": policy.model_dump(mode="json"),
    }
    return sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class _Proposal:
    def __init__(self, id: str, scenario: str, planned: SchedulingResult,
                 original: SimulationRequest, policy: SchedulingPolicy,
                 verdict: GuardianVerdict, expires: datetime,
                 advisory: M3AdvisoryResult | None = None):
        self.id = id
        self.scenario = scenario
        self.advisory = advisory.model_copy(deep=True) if advisory else None
        self.plan = planned.model_copy(deep=True)
        self.original = original.model_copy(deep=True)
        self.policy = policy.model_copy(deep=True)
        self.verdict = verdict.model_copy(deep=True)
        self.plan_digest = _plan_digest(self.plan, self.original, self.policy)
        self.expires = expires
        self.status: str = "pending"
        self.approved_by: str | None = None
        self.audit: list[AuditEvent] = []
        self.realized_essential_unserved_kwh: float | None = None
        self.realized_flexible_unserved_kwh: float | None = None
        self.realized_essential_reduction_kwh: float | None = None


class LocalApprovalWorkflow:
    """In-memory transactional approval; do not run with multiple web workers."""
    def __init__(self, *, clock: Callable[[], datetime] | None = None):
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.lock = RLock()
        self.records: dict[str, _Proposal] = {}

    def _now(self) -> datetime:
        value = self.clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise WorkflowError("clock_must_be_timezone_aware")
        return value

    def _append(self, rec: _Proposal, actor: str, event: str, note: str) -> None:
        when = self._now()
        prev = rec.audit[-1].hash if rec.audit else "0" * 64
        payload = dict(sequence=len(rec.audit) + 1, proposal_id=rec.id,
                       at=when.isoformat(), actor=actor, event=event,
                       note=note, previous_hash=prev)
        digest = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        rec.audit.append(AuditEvent(**payload, hash=digest))

    def _deny(self, rec: _Proposal, actor: str, code: str) -> WorkflowError:
        """Record a refused attempt in the hash chain, then return the error to raise."""
        self._append(rec, actor, "denied", code)
        return WorkflowError(code)

    def _snapshot(self, rec: _Proposal) -> ProposalView:
        s = rec.plan.summary
        planned = [
            PlannedInterval(
                timestamp=o.timestamp, duration_minutes=o.duration_minutes,
                forecast_solar_kw=o.solar_generation_kw,
                essential_demand_kw=o.essential_demand_kw,
                original_flexible_kw=o.flexible_demand_kw,
                planned_flexible_kw=p.flexible_demand_kw,
            )
            for o, p in zip(rec.original.intervals, rec.plan.scheduled_request.intervals)
        ]
        return ProposalView(
            proposal_id=rec.id, scenario=rec.scenario, status=rec.status,
            expires_at=rec.expires, guardian=rec.verdict.model_copy(deep=True),
            forecast_shifted_kwh=s.energy_shifted_kwh,
            plan_sha256=rec.plan_digest, planned_intervals=planned,
            forecast_essential_unserved_baseline_kwh=s.essential_unserved_baseline_kwh,
            forecast_essential_unserved_planned_kwh=s.essential_unserved_scheduled_kwh,
            forecast_flexible_unserved_baseline_kwh=s.flexible_unserved_baseline_kwh,
            forecast_flexible_unserved_planned_kwh=s.flexible_unserved_scheduled_kwh,
            audit_head_hash=rec.audit[-1].hash,
            approved_by=rec.approved_by,
            advisory_model=rec.advisory.model if rec.advisory else None,
            advisory_risk_level=rec.advisory.assessment.risk_level if rec.advisory else None,
            advisory_headline=rec.advisory.assessment.headline if rec.advisory else None,
            realized_essential_unserved_kwh=rec.realized_essential_unserved_kwh,
            realized_flexible_unserved_kwh=rec.realized_flexible_unserved_kwh,
            realized_essential_reduction_kwh=rec.realized_essential_reduction_kwh,
            audit=[e.model_copy(deep=True) for e in rec.audit],
        )

    def _find(self, proposal_id: str) -> _Proposal:
        rec = self.records.get(proposal_id)
        if rec is None:
            raise WorkflowError("proposal_not_found")
        if rec.status in ("pending", "approved") and self._now() >= rec.expires:
            rec.status = "expired"
            self._append(rec, "system", "expired", "15-minute local proposal validity elapsed")
        return rec

    @staticmethod
    def _actor(actor: str) -> str:
        if not actor or not actor.strip():
            raise WorkflowError("operator_identity_required")
        return actor.strip()

    def create(self, scenario: str, *, policy: SchedulingPolicy | None = None,
               advisory: M3AdvisoryResult | None = None) -> ProposalView:
        if scenario not in available_scenarios():
            raise WorkflowError("unknown_scenario")
        if advisory is not None:
            # Advisory is untrusted prose attached for the human reader. It must
            # describe this exact scenario and can never substitute for the
            # Guardian check below or for a human decision.
            if (advisory.mode != "simulation" or advisory.kind != "advisory_only"
                    or advisory.evidence.scenario_name != scenario
                    or advisory.assessment.scenario_name != scenario
                    or advisory.assessment.requires_human_approval is not True):
                raise WorkflowError("advisory_scenario_mismatch")
        p = policy or SchedulingPolicy()
        # Crucial anti-lookahead invariant: planning uses historical solar and a
        # published (synthetic) load timetable, never the actual future solar.
        target = target_fixture(scenario)
        historic = previous_day_fixture(scenario)
        rows = []
        for observed, previous in zip(target.intervals, historic.intervals):
            data = observed.model_dump()
            data["solar_generation_kw"] = previous.solar_generation_kw
            rows.append(PowerInterval.model_validate(data))
        original = SimulationRequest(grid=target.grid, intervals=rows)
        plan = schedule_flexible_load(original, p)
        verdict = guard_schedule(plan, original, p)
        if not verdict.allowed:
            raise WorkflowError("guardian_rejected_plan")
        with self.lock:
            rec = _Proposal(str(uuid4()), scenario, plan, original, p, verdict,
                            self._now() + timedelta(minutes=15), advisory=advisory)
            self.records[rec.id] = rec
            self._append(rec, "system", "proposed",
                         f"forecast-based schedule proposed; no actuation; plan_sha256={rec.plan_digest}")
            return self._snapshot(rec)

    def inspect(self, proposal_id: str) -> ProposalView:
        with self.lock:
            return self._snapshot(self._find(proposal_id))

    def decide(self, proposal_id: str, *, operator: str,
               decision: Literal["approved", "rejected"]) -> ProposalView:
        operator = self._actor(operator)
        if decision not in ("approved", "rejected"):
            raise WorkflowError("invalid_decision")
        with self.lock:
            rec = self._find(proposal_id)
            if rec.status != "pending":
                raise self._deny(rec, operator, "decision_not_allowed_in_state_" + rec.status)
            # Recheck just before operator decision; never assume earlier guard is durable.
            if not guard_schedule(rec.plan, rec.original, rec.policy).allowed:
                raise self._deny(rec, operator, "guardian_rejected_plan")
            if not hmac.compare_digest(_plan_digest(rec.plan, rec.original, rec.policy), rec.plan_digest):
                raise self._deny(rec, operator, "plan_digest_mismatch")
            rec.status = decision
            if decision == "approved":
                rec.approved_by = operator
            self._append(rec, operator, decision, "human decision on simulation-only plan")
            return self._snapshot(rec)

    def apply_simulation(self, proposal_id: str, *, operator: str) -> ProposalView:
        operator = self._actor(operator)
        with self.lock:
            rec = self._find(proposal_id)
            if rec.status != "approved":
                raise self._deny(rec, operator, "execution_requires_approval")
            if not hmac.compare_digest(operator, rec.approved_by or ""):
                raise self._deny(rec, operator, "approval_operator_mismatch")
            if not guard_schedule(rec.plan, rec.original, rec.policy).allowed:
                raise self._deny(rec, operator, "guardian_rejected_plan")
            if not hmac.compare_digest(_plan_digest(rec.plan, rec.original, rec.policy), rec.plan_digest):
                raise self._deny(rec, operator, "plan_digest_mismatch")
            # Apply ONLY to a local M1 synthetic scenario. No physical connections.
            actual = target_fixture(rec.scenario)
            applied_rows: list[PowerInterval] = []
            for observed, scheduled in zip(actual.intervals, rec.plan.scheduled_request.intervals):
                row = observed.model_dump()
                row["flexible_demand_kw"] = scheduled.flexible_demand_kw
                applied_rows.append(PowerInterval.model_validate(row))
            scheduled_request = SimulationRequest(grid=actual.grid, intervals=applied_rows)
            baseline = run_simulation(actual)
            realized = run_simulation(scheduled_request)
            if realized.summary.reserve_violations or realized.summary.max_abs_balance_residual_kwh > 1e-8:
                raise self._deny(rec, operator, "actual_simulation_safety_failure")
            rec.realized_essential_unserved_kwh = realized.summary.unserved_essential_kwh
            rec.realized_flexible_unserved_kwh = realized.summary.unserved_flexible_kwh
            rec.realized_essential_reduction_kwh = (
                baseline.summary.unserved_essential_kwh - realized.summary.unserved_essential_kwh
            )
            rec.status = "applied"
            self._append(rec, operator, "applied", "applied to synthetic in-memory twin ONLY")
            return self._snapshot(rec)

    @staticmethod
    def verify_audit(events: list[AuditEvent], *, expected_head: str | None = None) -> bool:
        """Verify chain integrity. Without expected_head, dropping trailing events
        is undetectable; pass a previously retained audit_head_hash to catch it."""
        if expected_head is not None and (not events or not hmac.compare_digest(events[-1].hash, expected_head)):
            return False
        prev = "0" * 64
        for index, item in enumerate(events, 1):
            if item.sequence != index or item.previous_hash != prev:
                return False
            data = dict(sequence=item.sequence, proposal_id=item.proposal_id,
                        at=item.at.isoformat(), actor=item.actor,
                        event=item.event, note=item.note, previous_hash=item.previous_hash)
            digest = sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            if not hmac.compare_digest(digest, item.hash):
                return False
            prev = item.hash
        return True
