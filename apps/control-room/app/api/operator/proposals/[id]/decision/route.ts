import { NextRequest } from 'next/server';
import { decideProposal } from '@/lib/operator';
import { fail, forbidden, jsonBody, ok, sameOrigin } from '@/lib/operator-http';
export const dynamic = 'force-dynamic';
export async function POST(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  if (!sameOrigin(request)) return forbidden();
  const { id } = await params;
  const body = await jsonBody(request);
  try { return ok(await decideProposal(id, body.decision)); } catch (e) { return fail(e); }
}
