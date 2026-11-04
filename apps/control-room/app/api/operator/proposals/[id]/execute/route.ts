import { NextRequest } from 'next/server';
import { executeProposal } from '@/lib/operator';
import { fail, forbidden, ok, sameOrigin } from '@/lib/operator-http';
export const dynamic = 'force-dynamic';
export async function POST(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  if (!sameOrigin(request)) return forbidden();
  const { id } = await params;
  try { return ok(await executeProposal(id)); } catch (e) { return fail(e); }
}
