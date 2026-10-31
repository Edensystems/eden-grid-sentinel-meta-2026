import { NextResponse } from 'next/server';
import { getHealth } from '@/lib/upstream';
export const dynamic = 'force-dynamic';
export async function GET() {
  try { return NextResponse.json(await getHealth(), {headers:{'Cache-Control':'no-store'}}); }
  catch { return NextResponse.json({status:'unavailable',mode:'simulation'}, {status:503,headers:{'Cache-Control':'no-store'}}); }
}
