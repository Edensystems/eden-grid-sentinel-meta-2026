import { normalizeEvaluation } from './contract';
import { isScenario } from './scenarios';

/** Server-only fixed-endpoint fetch. No generic URL forwarding and no credentials. */
async function upstream(path: string): Promise<unknown> {
  const base = process.env.SENTINEL_API_BASE_URL || 'http://127.0.0.1:8000';
  const parsed = new URL(base);
  if (!['http:', 'https:'].includes(parsed.protocol) || parsed.username || parsed.password || parsed.search || parsed.hash)
    throw new Error('Invalid backend configuration');
  const target = new URL(path, parsed.href.endsWith('/') ? parsed.href : parsed.href + '/');
  const res = await fetch(target, {cache:'no-store', signal: AbortSignal.timeout(7000), headers:{accept:'application/json'}});
  if (!res.ok) throw new Error(`Backend returned ${res.status}`);
  return res.json();
}
export async function getHealth() {
  const x = await upstream('health');
  if (typeof x !== 'object' || x === null || Array.isArray(x)) throw new Error('Invalid backend response');
  const value = x as Record<string, unknown>;
  if (value.status !== 'ok' || value.data_mode !== 'simulation' || value.control_mode !== 'read_only')
    throw new Error('Backend is not the M5 read-only preview');
  return {status:'ok', mode:'simulation', control_mode:'read_only'};
}
export async function getScenarios() {
  const raw = await upstream('m3/scenarios');
  if (!Array.isArray(raw) || raw.some(x=>!isScenario(x))) throw new Error('Unexpected backend scenarios');
  return raw;
}
export async function getEvaluation(scenario: string) {
  if (!isScenario(scenario)) throw new Error('Unsupported scenario');
  const data = normalizeEvaluation(await upstream(`m3/evaluate/${scenario}`));
  if (data.scenario !== scenario) throw new Error('Scenario mismatch');
  return data;
}
