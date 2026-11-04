import { getProposal } from '@/lib/operator';
import { fail, ok } from '@/lib/operator-http';
export const dynamic = 'force-dynamic';
export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  try { return ok(await getProposal(id)); } catch (e) { return fail(e); }
}
