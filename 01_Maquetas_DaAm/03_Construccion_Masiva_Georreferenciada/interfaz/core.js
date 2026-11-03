(function(global){
'use strict';
const DAY=86400000;
const day=s=>Math.round(Date.parse(String(s).slice(0,10)+'T00:00:00Z')/DAY);
const iso=d=>new Date(d*DAY).toISOString().slice(0,10);
const sum=(a,f)=>a.reduce((s,x)=>s+f(x),0);
const clamp=n=>Math.max(0,Math.min(1,n));
const planned=(cut,start,end)=>clamp((cut-start+1)/(end-start+1));
function snapshot(data,week){
 const o=data.obra,cut=day(o.Inicio_programado)+week*7-1;
 const controls=new Map(data.Control_semanal.filter(x=>x.Semana===week).map(x=>[x.Vivienda,x]));
 return data.Viviendas.map(unit=>{
  const c=controls.get(unit.ID);if(!c)throw Error('Falta corte '+week+' / '+unit.ID);
  const tasks=data.Programa.filter(p=>p.Vivienda===unit.ID).map(p=>{
   const changes=data.Reprogramaciones.filter(r=>r.Vivienda===unit.ID&&r.Partida===p.Partida&&r.Semana_vigencia<=week).sort((a,b)=>b.Semana_vigencia-a.Semana_vigencia);
   const change=changes[0];const start=day(change?change.Nuevo_inicio:p.Inicio_base),end=day(change?change.Nuevo_fin:p.Fin_base);
   const base=planned(cut,day(p.Inicio_base),day(p.Fin_base)),current=planned(cut,start,end),real=c[p.Partida];
   return {...p,start,end,base,current,real,replanned:!!change,late:real<current-1e-6,state:real>=1-1e-6?'Terminada':real>0?'En proceso':'Sin iniciar'};
  });
  const budget=sum(tasks,p=>p.Presupuesto_MM_CLP),base=sum(tasks,p=>p.base*p.Peso),real=sum(tasks,p=>p.real*p.Peso),current=sum(tasks,p=>p.current*p.Peso);
  const start=Math.min(...tasks.map(p=>p.start)),end=Math.max(...tasks.map(p=>p.end));
  const finished=real>=1-1e-6;const state=finished?'Terminada':real>1e-6?'En proceso':'Sin iniciar';
  return {...unit,tasks,budget,base,real,current,start,end,baseStart:Math.min(...tasks.map(p=>day(p.Inicio_base))),baseEnd:Math.max(...tasks.map(p=>day(p.Fin_base))),cost:c.Costo_real_MM_CLP,remaining:c.Costo_pendiente_MM_CLP,eac:c.Costo_real_MM_CLP+c.Costo_pendiente_MM_CLP,costPlan:sum(tasks,p=>p.base*p.Presupuesto_MM_CLP),forecast:day(c.Fin_forecast),late:!finished&&real<current-1e-6,pendingStart:real<1e-6&&cut>=start,state,cut,actualStart:unit.Inicio_real&&day(unit.Inicio_real)<=cut?day(unit.Inicio_real):null,actualEnd:unit.Fin_real&&day(unit.Fin_real)<=cut?day(unit.Fin_real):null};
 });
}
function aggregate(units){
 const budget=sum(units,x=>x.budget),div=budget||1;
 return {budget,base:sum(units,x=>x.base*x.budget)/div,real:sum(units,x=>x.real*x.budget)/div,current:sum(units,x=>x.current*x.budget)/div,cost:sum(units,x=>x.cost),costPlan:sum(units,x=>x.costPlan),eac:sum(units,x=>x.eac),forecast:units.length?Math.max(...units.map(x=>x.forecast)):null,finished:units.filter(x=>x.state==='Terminada').length,active:units.filter(x=>x.state==='En proceso').length,late:units.filter(x=>x.late).length,pending:units.filter(x=>x.pendingStart).length,over:units.filter(x=>x.eac>x.budget+.01).length};
}
const api={day,iso,sum,planned,snapshot,aggregate};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else global.MasivaCore=api;
})(typeof window!=='undefined'?window:globalThis);
