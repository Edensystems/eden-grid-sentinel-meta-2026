import { NextResponse } from 'next/server';
import { getScenarios } from '@/lib/upstream';
export const dynamic = 'force-dynamic';
export async function GET() {
  try { return NextResponse.json(await getScenarios(), {headers:{'Cache-Control':'no-store'}}); }
  catch { return NextResponse.json({error:'Scenario service unavailable'}, {status:503,headers:{'Cache-Control':'no-store'}}); }
}
