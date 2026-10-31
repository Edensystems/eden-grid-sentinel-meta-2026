import { NextRequest, NextResponse } from 'next/server';
import { getEvaluation } from '@/lib/upstream';
import { isScenario } from '@/lib/scenarios';
export const dynamic = 'force-dynamic';
export async function GET(request: NextRequest) {
  const scenario = request.nextUrl.searchParams.get('scenario');
  if (!isScenario(scenario)) return NextResponse.json({error:'Unknown synthetic scenario'}, {status:400,headers:{'Cache-Control':'no-store'}});
  try { return NextResponse.json(await getEvaluation(scenario), {headers:{'Cache-Control':'no-store'}}); }
  catch { return NextResponse.json({error:'Simulation comparison unavailable'}, {status:503,headers:{'Cache-Control':'no-store'}}); }
}
