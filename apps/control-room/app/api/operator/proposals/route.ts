import { NextRequest } from 'next/server';
import { createProposal } from '@/lib/operator';
import { fail, forbidden, jsonBody, ok, sameOrigin } from '@/lib/operator-http';
export const dynamic = 'force-dynamic';
export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) return forbidden();
  const body = await jsonBody(request);
  try { return ok(await createProposal(body.scenario, body.liveAdvisory)); } catch (e) { return fail(e); }
}
