'use client';
import { useCallback, useEffect, useState } from 'react';
import { TrendChart } from './TrendChart';
import type { DashboardData } from '@/lib/contract';
import { isScenario, SCENARIOS, SCENARIO_TITLES, type Scenario } from '@/lib/scenarios';

const icons = {
  bolt: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="m13 2-9 12h7l-1 8 10-12h-7z"/></svg>,
  shield: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M12 2 4 5v6c0 5.5 3.5 9 8 11 4.5-2 8-5.5 8-11V5z"/><path d="m9 12 2.2 2.2L16 9"/></svg>,
  activity:<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M3 12h4l3-8 4 16 3-8h4"/></svg>,
  clock:<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 2"/></svg>,
  layers:<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="m2 9 10-6 10 6-10 6zM2 14l10 6 10-6M2 19l10 6 10-6"/></svg>,
  refresh:<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M21 6v5h-5M3 18v-5h5"/><path d="M5.8 9A7 7 0 0 1 18 7l3 4M3 13l3 4A7 7 0 0 0 18.2 15"/></svg>
};
const number = (n:number,dp=2)=>n.toLocaleString('en-US',{minimumFractionDigits:dp,maximumFractionDigits:dp});
const sign = (n:number)=>n>0?'+':'';
function Stat({label,value,unit,detail,emphasis}:{label:string,value:string,unit:string,detail:string,emphasis?:boolean}) {
  return <div className={`stat-card ${emphasis?'highlight-stat':''}`}>
    <span className="stat-label">{label}</span><div className="stat-value">{value} <small>{unit}</small></div>
    <p className="stat-detail">{detail}</p>
  </div>;
}
function ProgressBars({baseline,planned,label}:{baseline:number,planned:number,label:string}){
  const max=Math.max(baseline,planned,.1);
  return <div className="progress-group"><div className="bar-heading"><strong>{label}</strong><span>Unserved kWh</span></div>
    <div className="bar-line"><span>Baseline</span><div className="bar-track"><div className="bar-fill baseline-fill" style={{width:`${Math.max(0,baseline/max*100)}%`}}/></div><b>{number(baseline,3)}</b></div>
    <div className="bar-line"><span>Scheduled</span><div className="bar-track"><div className="bar-fill planned-fill" style={{width:`${Math.max(0,planned/max*100)}%`}}/></div><b>{number(planned,3)}</b></div>
  </div>;
}
export function Dashboard(){
  const [scenario,setScenario]=useState<Scenario>('critical_priority_school');
  const [data,setData]=useState<DashboardData|null>(null);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState('');
  const [health,setHealth]=useState<'online'|'offline'|'checking'>('checking');
  const [lastUpdated,setLastUpdated]=useState<Date|null>(null);
  const [auto,setAuto]=useState(false);
  const [available,setAvailable]=useState<Scenario[]>([...SCENARIOS]);
  const load=useCallback(async (selected:Scenario,signal?:AbortSignal)=>{
    setLoading(true);setError('');
    try {
      const [status,response] = await Promise.all([
        fetch('/api/health',{cache:'no-store',signal}),
        fetch(`/api/evaluation?scenario=${encodeURIComponent(selected)}`,{cache:'no-store',signal})
      ]);
      setHealth(status.ok?'online':'offline');
      if(!status.ok || !response.ok)throw new Error('The read-only simulation service is unavailable. Start the M5 preview API.');
      const payload:DashboardData=await response.json();
      if (payload.mode !== 'simulation'||payload.scenario!==selected||!Array.isArray(payload.points))throw new Error('Unexpected server response');
      setData(payload);setLastUpdated(new Date());
    } catch(e){if(signal?.aborted)return;setData(null);setHealth('offline');setError(e instanceof Error?e.message:'Unable to load comparison');}
    finally{if(!signal?.aborted)setLoading(false);}
  },[]);
  useEffect(()=>{
    const controller=new AbortController();
    void load(scenario,controller.signal);
    return ()=>controller.abort();
  },[scenario,load]);
  useEffect(()=>{
    const controller=new AbortController();
    fetch('/api/scenarios',{signal:controller.signal}).then(r=>r.ok?r.json():[]).then((names:unknown)=>{
      if(!controller.signal.aborted && Array.isArray(names)){
        const values=names.filter(isScenario);
        if(values.length)setAvailable(values);
      }
    }).catch(()=>{});
    return ()=>controller.abort();
  },[]);
  useEffect(()=>{
    if(!auto)return;
    const timer=setInterval(()=>void load(scenario),20000);
    return ()=>clearInterval(timer);
  },[auto,scenario,load]);
  const improvement=data?data.essentialBaselineKwh-data.essentialScheduledKwh:0;
  const flexChange=data?data.flexibleScheduledKwh-data.flexibleBaselineKwh:0;
  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">E<span className="brand-dot"/></span><div><strong>EDEN</strong><small>GRID SENTINEL</small></div></div>
      <div className="nav-title">WORKSPACE</div>
      <nav className="navigation" aria-label="Main navigation">
        <a className="nav-link active" href="#overview">{icons.layers} <span>Overview</span></a>
        <a className="nav-link" href="#energy">{icons.activity}<span>Energy analytics</span></a>
        <a className="nav-link" href="#comparison">{icons.bolt}<span>Load scheduling</span></a>
        <a className="nav-link" href="#safety">{icons.shield}<span>Safety boundary</span></a>
      </nav>
      <div className="sidebar-bottom"><div className="sidebar-system"><span className="eyebrow">SYSTEM CONTEXT</span>
        <p><span className="tiny-dot"/> Synthetic demonstration</p><p>Mode <b>Read-only</b></p><p>Control <b>Disabled</b></p></div>
        <span className="sidebar-footer">RAVENSAI <span>© 2026</span></span></div>
    </aside>
    <main className="main" id="overview">
      <header className="topbar"><div className="breadcrumbs">OPERATIONS <span>/</span> SCHOOL MICROGRID <span>/</span> DASHBOARD</div>
        <div className="top-status"><span className={`connection ${health}`}><i/>{health==='online'?'API connected':health==='offline'?'API unavailable':'Connecting'}</span><span className="mini-avatar" aria-hidden="true">R</span></div></header>
      <div className="content">
        <section className="hero"><div className="hero-text"><div className="hero-eyebrow"><span className="accent-line"/> OPERATIONS CONTROL ROOM</div><h1>Energy, understood.</h1>
          <p>Predict supply constraints. Compare feasible schedules. Protect essential school loads—all inside a transparent, synthetic digital twin.</p>
          <div className="hero-tags"><span className="tag safe-tag">● SIMULATION ONLY</span><span className="tag">M5 / READ-ONLY PREVIEW</span></div></div>
          <div className="hero-art"><div className="orbit outer"/><div className="orbit middle"/><div className="orbit inner"/><div className="orbit-core">E</div><span className="orbit-label one">FORECAST</span><span className="orbit-label two">OPTIMIZE</span><span className="orbit-label three">PROTECT</span></div></section>
        <section className="toolbar"><div className="section-intro"><span className="section-kicker">01 / LIVE VIEW</span><h2>Microgrid overview</h2><p>Measured from deterministic simulations. No connected sensors.</p></div>
          <div className="controls"><label className="select-label" htmlFor="scenario">Scenario</label><select id="scenario" value={scenario} onChange={e=>{if(isScenario(e.target.value))setScenario(e.target.value)}}>{available.map(key=><option key={key} value={key}>{SCENARIO_TITLES[key]}</option>)}</select>
            <button type="button" className="outline-button" onClick={()=>void load(scenario)} disabled={loading} aria-label="Refresh scenario">{icons.refresh}</button></div></section>
        {error?<div className="error-state" role="alert"><strong>Unable to retrieve authoritative simulation data.</strong><p>{error}</p><button className="primary-button" onClick={()=>void load(scenario)}>Retry connection</button></div>:null}
        {loading && !data?<div className="loading-panel" role="status">Connecting to the read-only simulator…</div>:null}
        {data?<>
          <section className="stats-grid" aria-label="Key indicators">
            <Stat label="SOLAR ENERGY" value={number(data.generatedSolarKwh)} unit="kWh" detail="Observed synthetic generation"/>
            <Stat label="BATTERY LEVEL" value={number(data.batteryPct,1)} unit="%" detail="Final SOC after scheduling"/>
            <Stat label="ESSENTIAL SHORTFALL" value={number(data.essentialScheduledKwh,3)} unit="kWh" detail={`Baseline: ${number(data.essentialBaselineKwh,3)} kWh`} emphasis/>
            <Stat label="FLEXIBLE ENERGY SHIFTED" value={number(data.shiftedKwh,2)} unit="kWh" detail="Forecast-based local search"/>
          </section>
          <section className="panels-grid" id="energy"><div className="panel main-panel"><div className="panel-heading"><div><span className="section-kicker">02 / ENERGY FLOW</span><h3>Generation & demand</h3><p>Actual synthetic solar, total demand and prior-day forecast</p></div><span className="metric-chip">{data.points.length} intervals</span></div><TrendChart points={data.points} type="energy"/></div>
            <div className="panel"><div className="panel-heading"><div><span className="section-kicker">03 / STORAGE</span><h3>Battery trajectory</h3><p>Baseline versus retimed load schedule</p></div></div><TrendChart points={data.points} type="battery"/><div className="battery-foot"><span>FINAL SCHEDULED SOC</span><strong>{number(data.batteryPct,1)}%</strong></div><div className="battery-meter"><div style={{width:`${Math.max(0,Math.min(100,data.batteryPct))}%`}}/></div></div></section>
          <section className="panels-grid comparison-grid" id="comparison"><div className="panel"><div className="panel-heading"><div><span className="section-kicker">04 / IMPACT</span><h3>Schedule evaluation</h3><p>Held-out synthetic actuals, not forecast-only estimates</p></div><span className={`metric-chip ${improvement>0?'positive-chip':''}`}>{improvement>0?`${number(improvement,3)} kWh protected`:improvement<0?'Negative outcome':'No reduction'}</span></div>
              <ProgressBars label="Essential load" baseline={data.essentialBaselineKwh} planned={data.essentialScheduledKwh}/>
              <ProgressBars label="Flexible load" baseline={data.flexibleBaselineKwh} planned={data.flexibleScheduledKwh}/>
              <p className="insight">{improvement>0?`Essential shortfall decreased by ${number(improvement,3)} kWh.`:improvement<0?'The schedule increased essential-load shortfall.':'No essential-load reduction was observed.'} {flexChange>0?`Flexible shortfall increased by ${number(flexChange,3)} kWh: this is a real trade-off.`:flexChange<0?`Flexible shortfall decreased by ${number(-flexChange,3)} kWh.`:'Flexible shortfall was unchanged.'}</p>
            </div><div className="panel"><div className="panel-heading"><div><span className="section-kicker">05 / PLAN</span><h3>Scheduling decisions</h3><p>Bounded local search · Not a global optimum</p></div><span className="metric-chip">{data.schedulingStatus}</span></div>
              {data.moves.length?<div className="moves-list">{data.moves.slice(0,7).map((move,i)=><div className="move" key={i}><span className="move-number">{String(i+1).padStart(2,'0')}</span><div><strong>Retimed flexible load</strong><small>Interval {move.from+1} → Interval {move.to+1}</small></div><b>{number(move.energyKwh,2)} kWh</b></div>)}{data.moves.length>7?<p className="muted-note">+ {data.moves.length-7} more moves in this scenario</p>:null}</div>:<div className="empty-moves">No shift was selected for this scenario.</div>}
            </div></section>
          <section className="bottom-grid" id="safety"><div className="safety-panel"><div className="safety-icon">{icons.shield}</div><div><span className="section-kicker">06 / TRUST BOUNDARY</span><h3>Guardian & operator approval</h3><p>The M4 approval interface is intentionally not connected to this staging preview. This page cannot create, approve, or execute proposals.</p><div className="security-tags"><span>Read-only</span><span>Control disabled</span><span>No device access</span></div></div></div>
            <div className="panel provenance-panel"><span className="section-kicker">EVIDENCE & PROVENANCE</span><h3>What these numbers mean</h3><div className="evidence-row"><span>Data source</span><b>Simulated fixtures</b></div><div className="evidence-row"><span>Forecast model</span><b>Previous-day analogue</b></div><div className="evidence-row"><span>Solar MAE</span><b>{number(data.solarMaeKw,3)} kW</b></div><div className="evidence-row"><span>Reserve violations</span><b>{data.reserveViolations}</b></div><div className="evidence-row"><span>Energy residual</span><b>{data.balanceResidualKwh.toExponential(2)} kWh</b></div></div></section>
        </>:null}
        <footer className="footer"><div>EDEN GRID SENTINEL <span>·</span> SIMULATION ONLY <span>·</span> NOT FOR REAL-WORLD ELECTRICAL CONTROL</div><div className="footer-actions"><label><input type="checkbox" checked={auto} onChange={e=>setAuto(e.target.checked)}/> Auto-refresh (20s)</label><span>{lastUpdated?`Updated ${lastUpdated.toLocaleTimeString()}`:'Awaiting data'}</span></div></footer>
      </div>
    </main>
  </div>;
}
