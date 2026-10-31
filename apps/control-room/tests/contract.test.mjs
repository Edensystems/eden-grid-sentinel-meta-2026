// Node standard library tests compile the pure TS contract separately; no network.
import assert from 'node:assert/strict';
import test from 'node:test';
import { normalizeEvaluation } from './contract-built/contract.js';

const stamp = '2026-10-28T07:00:00Z';
const row = {timestamp:stamp,duration_minutes:60,solar_generation_kwh:2,
 essential_demand_kwh:1,flexible_demand_kwh:.5,soc_end_fraction:.5};
const output = {mode:'simulation',summary:{generated_solar_kwh:2,
 unserved_essential_kwh:0,unserved_flexible_kwh:0,final_soc_fraction:.5},intervals:[row]};
const fixture = {mode:'simulation',scenario:'cloudy_school_day',
 forecast:{method:'previous_day_analogue',metrics:{solar_mae_kw:.2},forecasts:[{timestamp:stamp,solar_kw:1.9}]},
 scheduling:{status:'feasible',summary:{energy_shifted_kwh:0},moves:[]},
 realized:{baseline:output,scheduled:output,battery_reserve_violations:0,max_abs_bus_residual_kwh:0}};

test('normalizes authoritative M3 data only',()=>{
 const value=normalizeEvaluation(fixture);
 assert.equal(value.mode,'simulation');assert.equal(value.points[0].solarKw,2);
 assert.equal(value.points[0].demandKw,1.5);
});
test('rejects missing simulation label',()=>assert.throws(()=>normalizeEvaluation({...fixture,mode:'measured'})));
test('rejects nonfinite data',()=>assert.throws(()=>normalizeEvaluation({...fixture,realized:{...fixture.realized,baseline:{...output,summary:{...output.summary,generated_solar_kwh:Infinity}}}})));
test('rejects mixed timestamps',()=>assert.throws(()=>normalizeEvaluation({...fixture,forecast:{...fixture.forecast,forecasts:[{timestamp:'2026-10-29T07:00:00Z',solar_kw:1.9}]}})));
test('rejects violations from upstream',()=>assert.throws(()=>normalizeEvaluation({...fixture,realized:{...fixture.realized,battery_reserve_violations:1}})));
test('rejects missing data rather than inventing defaults',()=>assert.throws(()=>normalizeEvaluation({...fixture,forecast:{...fixture.forecast,metrics:{}}})));
