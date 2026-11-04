import { isProposalId, normalizeOperatorStatus, normalizeProposal, type OperatorStatus, type Proposal } from './incident';
import { isScenario } from './scenarios';

/**
 * Server-only client for the loopback M4 operator API (eden.sentinel.api with
 * M4_ENABLE_LOCAL_API=1). The bearer token never reaches the browser. Operator
 * mode is off unless both variables are set, and only loopback targets are allowed.
 */
const LOOPBACK = new Set(['127.0.0.1', 'localhost', '[::1]']);

export class OperatorError extends Error {
  constructor(public status: number, public code: string) { super(code); }
}

function config(): { base: string; token: string } | null {
  const base = process.env.SENTINEL_OPERATOR_API_BASE_URL;
  const token = process.env.SENTINEL_OPERATOR_TOKEN;
  if (!base || !token) return null;
  const url = new URL(base);
  if (url.protocol !== 'http:' || !LOOPBACK.has(url.hostname) || url.username || url.password || url.search || url.hash)
    throw new OperatorError(503, 'operator_misconfigured');
  return { base: url.href.endsWith('/') ? url.href : url.href + '/', token };
}

async function call(path: string, method: 'GET' | 'POST', body?: unknown): Promise<unknown> {
  const cfg = config();
  if (!cfg) throw new OperatorError(404, 'operator_mode_disabled');
  let res: Response;
  try {
    res = await fetch(new URL(path, cfg.base), {
      method, cache: 'no-store', redirect: 'error',
      // A live advisory makes two model requests; allow for the adapter's timeouts.
      signal: AbortSignal.timeout(body && (body as { live_advisory?: boolean }).live_advisory ? 70000 : 10000),
      headers: { accept: 'application/json', authorization: `Bearer ${cfg.token}`, ...(body ? { 'content-type': 'application/json' } : {}) },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new OperatorError(503, 'operator_unavailable');
  }
  const payload: unknown = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = payload && typeof payload === 'object' ? (payload as { detail?: unknown }).detail : undefined;
    throw new OperatorError(res.status, typeof detail === 'string' ? detail : 'operator_request_failed');
  }
  return payload;
}

export async function getOperatorStatus(): Promise<OperatorStatus> {
  if (!config()) return { enabled: false };
  return normalizeOperatorStatus(await call('m4/status', 'GET'));
}

export async function createProposal(scenario: unknown, liveAdvisory: unknown): Promise<Proposal> {
  if (!isScenario(scenario)) throw new OperatorError(400, 'unknown_scenario');
  return normalizeProposal(await call('m4/proposals', 'POST', { scenario, live_advisory: liveAdvisory === true }));
}

export async function getProposal(id: string): Promise<Proposal> {
  if (!isProposalId(id)) throw new OperatorError(400, 'proposal_not_found');
  return normalizeProposal(await call(`m4/proposals/${id}`, 'GET'));
}

export async function decideProposal(id: string, decision: unknown): Promise<Proposal> {
  if (!isProposalId(id)) throw new OperatorError(400, 'proposal_not_found');
  if (decision !== 'approved' && decision !== 'rejected') throw new OperatorError(400, 'invalid_decision');
  return normalizeProposal(await call(`m4/proposals/${id}/decision`, 'POST', { decision }));
}

export async function executeProposal(id: string): Promise<Proposal> {
  if (!isProposalId(id)) throw new OperatorError(400, 'proposal_not_found');
  return normalizeProposal(await call(`m4/proposals/${id}/execute-simulation`, 'POST'));
}
