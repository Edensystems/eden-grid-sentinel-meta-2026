'use client';
import { useCallback, useEffect, useState } from 'react';
import { describeError, type OperatorStatus, type Proposal } from '@/lib/incident';

const kwh = (n: number, dp = 3) => n.toLocaleString('en-US', { minimumFractionDigits: dp, maximumFractionDigits: dp });
const clock = (iso: string) => new Date(iso).toLocaleTimeString('en-US', { hour12: false });
const short = (h: string) => `${h.slice(0, 8)}…${h.slice(-4)}`;

async function post(path: string, body: unknown = {}): Promise<Proposal> {
  const res = await fetch(path, { method: 'POST', cache: 'no-store', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
  const payload = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(describeError(payload.error));
  return payload as Proposal;
}

function Step({ n, title, state, children }: { n: number; title: string; state: 'done' | 'active' | 'idle' | 'blocked'; children: React.ReactNode }) {
  return <div className={`incident-step ${state}`}>
    <div className="step-head"><span className="step-number">{String(n).padStart(2, '0')}</span><h4>{title}</h4></div>
    <div className="step-body">{children}</div>
  </div>;
}

export function IncidentPanel({ scenario, scenarioTitle }: { scenario: string; scenarioTitle: string }) {
  const [status, setStatus] = useState<OperatorStatus | null>(null);
  const [statusError, setStatusError] = useState('');
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [liveAdvisory, setLiveAdvisory] = useState(false);
  const [busy, setBusy] = useState('');
  const [notice, setNotice] = useState<{ kind: 'error' | 'denied'; text: string } | null>(null);
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    fetch('/api/operator/status', { cache: 'no-store' })
      .then(async r => { const p = await r.json(); if (!r.ok) throw new Error(describeError(p.error)); setStatus(p); })
      .catch(e => setStatusError(e instanceof Error ? e.message : 'Operator status unavailable'));
  }, []);
  useEffect(() => { setProposal(null); setNotice(null); }, [scenario]);
  useEffect(() => {
    if (proposal?.status !== 'pending' && proposal?.status !== 'approved') return;
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, [proposal?.status]);

  const run = useCallback(async (label: string, action: () => Promise<Proposal>, expectDenial = false) => {
    setBusy(label); setNotice(null);
    try { setProposal(await action()); }
    catch (e) {
      const text = e instanceof Error ? e.message : 'The operator request failed.';
      setNotice({ kind: expectDenial ? 'denied' : 'error', text });
      // A refused attempt is itself audited; reload to show the 'denied' event.
      if (proposal) {
        const r = await fetch(`/api/operator/proposals/${proposal.id}`, { cache: 'no-store' });
        if (r.ok) setProposal(await r.json());
      }
    } finally { setBusy(''); }
  }, [proposal]);

  const op = status && status.enabled ? status : null;
  const enabled = op !== null;
  const p = proposal;
  const secondsLeft = p ? Math.max(0, Math.floor((Date.parse(p.expiresAt) - now) / 1000)) : 0;

  return <section className="panel incident-panel" id="incident">
    <div className="panel-heading">
      <div><span className="section-kicker">07 / INCIDENT RESPONSE</span><h3>AI-assisted incident loop</h3>
        <p>Detect → advise → Guardian check → human decision → simulated apply → hash-chained audit</p></div>
      <span className={`metric-chip ${enabled ? 'positive-chip' : ''}`}>{enabled ? 'OPERATOR MODE · LOOPBACK' : 'READ-ONLY PREVIEW'}</span>
    </div>

    {!status && !statusError ? <p className="muted-note">Checking operator mode…</p> : null}
    {statusError ? <div className="incident-notice error">{statusError}</div> : null}
    {status && !enabled ? <div className="incident-disabled">
      <strong>Operator mode is off.</strong>
      <p>This deployment is the read-only preview: it cannot create, approve, or execute proposals. To run the incident loop locally, start the M4 operator API on loopback and set <code>SENTINEL_OPERATOR_API_BASE_URL</code> and <code>SENTINEL_OPERATOR_TOKEN</code> for the dashboard server (see <code>docs/hackathon/INCIDENT_PANEL.md</code>).</p>
    </div> : null}

    {op ? <>
      <div className="incident-toolbar">
        <div><span className="muted-label">Scenario</span><strong>{scenarioTitle}</strong></div>
        <div><span className="muted-label">Operator</span><strong>{op.operatorId}</strong><small>server-configured local identity</small></div>
        <label className={`advisory-toggle ${op.liveAdvisory ? '' : 'disabled'}`}>
          <input type="checkbox" checked={liveAdvisory} disabled={!op.liveAdvisory || !!busy || (p !== null && !['rejected', 'applied', 'expired'].includes(p.status))} onChange={e => setLiveAdvisory(e.target.checked)} />
          <span>Ask Meta Muse Spark for a live advisory<small>{op.liveAdvisory ? 'Billable: two model requests per proposal' : 'Disabled on the operator API (no billable calls)'}</small></span>
        </label>
        <button className="primary-button" disabled={!!busy || (p !== null && !['rejected', 'applied', 'expired'].includes(p.status))}
          onClick={() => run('create', () => post('/api/operator/proposals', { scenario, liveAdvisory: liveAdvisory && op.liveAdvisory }))}>
          {busy === 'create' ? (liveAdvisory ? 'Consulting Muse Spark…' : 'Planning…') : p ? 'Open a fresh proposal' : 'Open incident'}
        </button>
      </div>

      {notice ? <div className={`incident-notice ${notice.kind}`} role="status">{notice.kind === 'denied' ? '⛔ ' : ''}{notice.text}</div> : null}

      {p ? <div className="incident-steps">
        <Step n={1} title="Detect" state="done">
          <p>Forecast essential shortfall without action: <b>{kwh(p.forecast.essentialBaselineKwh)} kWh</b>.</p>
          <p className="muted-note">Forecast-time data only (prior-day solar); held-out actuals are not used for planning.</p>
        </Step>

        <Step n={2} title="Advise" state="done">
          {p.advisory ? <>
            <div className="advisory-head"><span className={`risk risk-${p.advisory.riskLevel}`}>{p.advisory.riskLevel.toUpperCase()} RISK</span><small>{p.advisory.model} · live model output</small></div>
            <strong className="advisory-headline">{p.advisory.headline}</strong>
            <p>{p.advisory.explanation}</p>
            <p className="advisory-next"><b>Suggested next step:</b> {p.advisory.nextStep}</p>
            <p className="muted-note">Advisory only. It cannot approve, execute, or change the plan.</p>
          </> : <p className="muted-note">No model advisory attached. The plan below comes from the deterministic forecast and scheduler; the Guardian and a human still decide.</p>}
        </Step>

        <Step n={3} title="Guardian check" state={p.guardian.allowed ? 'done' : 'blocked'}>
          <p className={p.guardian.allowed ? 'verdict ok' : 'verdict bad'}>{p.guardian.allowed ? '✓ Plan independently re-computed and allowed' : '✗ Plan rejected'}</p>
          <p>Essential shortfall (forecast): <b>{kwh(p.guardian.essentialBeforeKwh)} → {kwh(p.guardian.essentialAfterKwh)} kWh</b> · reserve violations: <b>{p.guardian.reserveViolations}</b> · shifted: <b>{kwh(p.shiftedKwh, 2)} kWh</b></p>
          <p>Flexible shortfall (forecast): <b>{kwh(p.forecast.flexibleBaselineKwh)} → {kwh(p.forecast.flexiblePlannedKwh)} kWh</b></p>
          {[...p.guardian.reasons, ...p.guardian.warnings].map(w => <p key={w} className="muted-note">• {w}</p>)}
          <table className="plan-table"><thead><tr><th>Interval</th><th>Solar fc kW</th><th>Essential kW</th><th>Flexible kW</th></tr></thead>
            <tbody>{p.intervals.map(r => <tr key={r.timestamp}><td>{clock(r.timestamp)}</td><td>{kwh(r.forecastSolarKw, 2)}</td><td>{kwh(r.essentialKw, 2)}</td>
              <td className={r.plannedFlexibleKw !== r.originalFlexibleKw ? 'changed' : ''}>{kwh(r.originalFlexibleKw, 2)} → {kwh(r.plannedFlexibleKw, 2)}</td></tr>)}</tbody></table>
          <p className="hash-line">plan_sha256 <code>{short(p.planSha256)}</code></p>
        </Step>

        <Step n={4} title="Human decision" state={p.status === 'pending' ? 'active' : p.status === 'rejected' || p.status === 'expired' ? 'blocked' : 'done'}>
          {p.status === 'pending' ? <>
            <p>Approve or reject this exact plan. Expires in <b>{Math.floor(secondsLeft / 60)}:{String(secondsLeft % 60).padStart(2, '0')}</b>.</p>
            <div className="decision-buttons">
              <button className="primary-button" disabled={!!busy} onClick={() => run('approve', () => post(`/api/operator/proposals/${p.id}/decision`, { decision: 'approved' }))}>Approve plan</button>
              <button className="danger-button" disabled={!!busy} onClick={() => run('reject', () => post(`/api/operator/proposals/${p.id}/decision`, { decision: 'rejected' }))}>Reject plan</button>
            </div>
          </> : p.status === 'rejected' ? <p className="verdict bad">Rejected by the operator. This proposal can never execute.</p>
            : p.status === 'expired' ? <p className="verdict bad">Expired without a decision. Open a fresh proposal.</p>
            : <p className="verdict ok">Approved by <b>{p.approvedBy}</b>.</p>}
        </Step>

        <Step n={5} title="Apply to digital twin" state={p.status === 'applied' ? 'done' : p.status === 'approved' ? 'active' : 'idle'}>
          {p.status === 'approved' ? <button className="primary-button" disabled={!!busy} onClick={() => run('apply', () => post(`/api/operator/proposals/${p.id}/execute`))}>Apply to simulation</button> : null}
          {p.realized ? <>
            <p className="verdict ok">Applied once to the synthetic twin. No physical equipment is connected.</p>
            <p>Essential unserved (held-out synthetic actuals): <b>{kwh(p.realized.essentialUnservedKwh)} kWh</b>, a reduction of <b>{kwh(p.realized.essentialReductionKwh)} kWh</b> against no action.</p>
            <p>Trade-off: flexible demand unserved <b>{kwh(p.realized.flexibleUnservedKwh)} kWh</b>.</p>
          </> : null}
          {p.status === 'pending' || p.status === 'approved' ? null : <p className="muted-note">{p.status === 'applied' ? 'Try to run it again:' : 'Try to execute anyway:'}</p>}
          {p.status !== 'pending' && p.status !== 'approved'
            ? <button className="outline-text-button" disabled={!!busy} onClick={() => run('retry', () => post(`/api/operator/proposals/${p.id}/execute`), true)}>
                {p.status === 'applied' ? 'Attempt repeat execution' : 'Attempt execution'}</button> : null}
        </Step>

        <Step n={6} title="Audit trail" state="done">
          <ol className="audit-list">{p.audit.map(e => <li key={e.sequence} className={`audit-${e.event}`}>
            <span className="audit-event">{e.event}</span><span className="audit-actor">{e.actor}</span><span className="audit-time">{clock(e.at)}</span>
            <code title={e.hash}>{short(e.previousHash)} → {short(e.hash)}</code>
            {e.event === 'denied' ? <small>{e.note}</small> : null}
          </li>)}</ol>
          <p className="muted-note">Each event hashes the previous one. Chain links are validated by the dashboard server; records live in memory only (demo, not production audit).</p>
        </Step>
      </div> : <p className="muted-note incident-empty">No open incident. Opening one runs the deterministic forecast and scheduler, then the Guardian, before anything reaches you for a decision.</p>}
    </> : null}
  </section>;
}
