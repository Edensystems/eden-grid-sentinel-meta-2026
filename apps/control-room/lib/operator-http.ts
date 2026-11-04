import { NextRequest, NextResponse } from 'next/server';
import { OperatorError } from './operator';

const NO_STORE = { 'Cache-Control': 'no-store' };

const LOOPBACK_HOSTS = new Set(['127.0.0.1', 'localhost', '[::1]']);

/**
 * Operator writes must come from this dashboard's own loopback origin. Origin must
 * equal the Host header (blocks cross-site posts), and the host must be loopback
 * (blocks DNS-rebinding pages, whose Origin and Host would otherwise match).
 */
export function sameOrigin(request: NextRequest): boolean {
  const origin = request.headers.get('origin');
  const host = request.headers.get('host');
  if (!origin || !host || !(request.headers.get('content-type') ?? '').startsWith('application/json')) return false;
  try {
    const url = new URL(origin);
    return url.protocol === 'http:' && url.host === host && LOOPBACK_HOSTS.has(url.hostname);
  } catch {
    return false;
  }
}

export function ok(data: unknown) {
  return NextResponse.json(data, { headers: NO_STORE });
}

export function fail(error: unknown) {
  if (error instanceof OperatorError) return NextResponse.json({ error: error.code }, { status: error.status, headers: NO_STORE });
  return NextResponse.json({ error: 'operator_response_invalid' }, { status: 502, headers: NO_STORE });
}

export function forbidden() {
  return NextResponse.json({ error: 'cross_origin_request_refused' }, { status: 403, headers: NO_STORE });
}

export async function jsonBody(request: NextRequest): Promise<Record<string, unknown>> {
  const body: unknown = await request.json().catch(() => null);
  return body && typeof body === 'object' && !Array.isArray(body) ? body as Record<string, unknown> : {};
}
