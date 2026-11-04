import { getOperatorStatus } from '@/lib/operator';
import { fail, ok } from '@/lib/operator-http';
export const dynamic = 'force-dynamic';
export async function GET() {
  try { return ok(await getOperatorStatus()); } catch (e) { return fail(e); }
}
