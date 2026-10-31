'use client';
import type { DataPoint } from '@/lib/contract';

type Key = 'solarKw' | 'demandKw' | 'forecastKw' | 'batteryPct' | 'scheduledBatteryPct';
type Series = { key: Key; name:string; color:string; dashed?:boolean };
const OUTPUT: Series[] = [
  {key:'solarKw',name:'Actual solar',color:'#37d8b0'},
  {key:'demandKw',name:'Total demand',color:'#e6b969'},
  {key:'forecastKw',name:'Solar forecast',color:'#7992cf',dashed:true},
];
const BATTERY: Series[] = [
  {key:'batteryPct',name:'Baseline SOC',color:'#6e8bb7',dashed:true},
  {key:'scheduledBatteryPct',name:'Scheduled SOC',color:'#37d8b0'},
];

export function TrendChart({points,type}:{points:DataPoint[],type:'energy'|'battery'}) {
  const lines= type==='energy'?OUTPUT:BATTERY;
  const max = type==='battery'?100:Math.max(1, ...points.flatMap(p=>lines.map(line=>p[line.key])))*1.12;
  const width=680,height=214,left=36,right=12,top=15,bottom=28;
  const cw=width-left-right,ch=height-top-bottom;
  const xy=(point:DataPoint,index:number,key:Key):[number,number]=>[
    left+(points.length===1?cw/2:index/(points.length-1)*cw),
    top+ch-(point[key]/max)*ch,
  ];
  const path=(key:Key)=>points.map((p,i)=>{
    const [x,y]=xy(p,i,key);return `${i?'L':'M'}${x.toFixed(1)} ${y.toFixed(1)}`;
  }).join(' ');
  return <div className="trend-block">
    <div className="trend-legend">
      {lines.map(s=><span key={s.key} className="legend-item"><i style={{background:s.color}}/> {s.name}</span>)}
    </div>
    <div className="chart-scroll">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${type==='energy'?'Generation and demand in kW':'Battery state of charge in percent'} over time`} className="trend-svg">
        {[0,.25,.5,.75,1].map((fraction,i)=>{
          const y=top+ch-ch*fraction;
          return <g key={i}><line x1={left} y1={y} x2={width-right} y2={y} stroke="#334655" strokeOpacity=".63" strokeDasharray="2 6"/>
            <text x={left-8} y={y+3} fill="#84929e" fontSize="10" textAnchor="end">{(max*fraction).toFixed(type==='battery'?0:1)}</text></g>;
        })}
        {lines.map(line=><path key={line.key} d={path(line.key)} fill="none" stroke={line.color} strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round" strokeDasharray={line.dashed?'5 6':undefined}/>)}
        {lines.filter(s=>!s.dashed).map(line=>points.map((p,i)=>{
          const [x,y]=xy(p,i,line.key);
          return <circle key={`${line.key}-${i}`} cx={x} cy={y} r="3.2" fill={line.color} stroke="#0e2029" strokeWidth="1.5"><title>{`${p.timestamp} — ${line.name}: ${p[line.key].toFixed(2)}`}</title></circle>;
        }))}
        {points.map((p,i)=>{
          if (points.length>10 && i%Math.ceil(points.length/6)!==0 && i!==points.length-1)return null;
          return <text key={i} x={left+(points.length===1?cw/2:i/(points.length-1)*cw)} y={height-8} textAnchor="middle" fill="#84929e" fontSize="10">{new Date(p.timestamp).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',timeZone:'UTC'})}</text>;
        })}
      </svg>
    </div>
    <p className="chart-caption">Time in UTC · Synthetic intervals · {type==='energy'?'kW':'SOC %'}</p>
  </div>;
}
