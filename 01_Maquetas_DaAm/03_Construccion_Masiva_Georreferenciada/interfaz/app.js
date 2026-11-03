'use strict';
const C=MasivaCore,$=s=>document.querySelector(s),names=['Resumen ejecutivo','Programación rítmica por vivienda','Mapa del proyecto','Detalle de vivienda','Avance por partidas por vivienda'];
const palette=['#b8976a','#527da7','#28577d','#758ba0','#b58c49','#688d90','#8a7497','#cf885f','#6c966a'];
const colors={'Sin iniciar':'#8b9bb0','En proceso':'#436f9b','Terminada':'#2b806b'};
let data=null,page=0,map=null,state={week:null,sector:'Todos',stage:'Todas',type:'Todas',unit:'Todas',status:'Todos',view:'Estado',program:'Vigente y línea base',from:'',to:''},selected='V-001';
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num=n=>Number(n).toLocaleString('es-CL',{maximumFractionDigits:1});
const pct=n=>num(n*100)+' %',money=n=>'$ '+num(n)+' MM';
const date=n=>n===null||n===undefined?'—':C.iso(n).split('-').reverse().join('/');
const button=id=>`<button class="link" data-unit="${esc(id)}">${esc(id)}</button>`;
const badge=(text,bad=false)=>`<span class="badge ${bad?'danger':''}">${esc(text)}</span>`;
const panel=(title,html)=>`<section class="panel"><h2>${title}</h2>${html}</section>`;
const card=(label,value,hint='',bad=false)=>`<div class="card"><div class="label">${label}</div><div class="value ${bad?'danger':''}">${value}</div><div class="hint">${hint}</div></div>`;
const pair=(title,plan,real,hint)=>`<div class="card"><div class="label">${title}</div><div class="pair"><div><small>Programado</small><strong>${plan}</strong></div><div><small>Real</small><strong>${real}</strong></div></div><div class="hint">${hint}</div></div>`;
function table(headers,rows,footer=''){return `<div class="tablewrap"><table><thead><tr>${headers.map(h=>`<th scope="col">${h}</th>`).join('')}</tr></thead><tbody>${rows.length?rows.map(r=>`<tr>${r.map(v=>`<td>${v}</td>`).join('')}</tr>`).join(''):`<tr><td colspan="${headers.length}" class="empty">Sin viviendas para estos filtros.</td></tr>`}</tbody>${footer}</table></div>`;}
function send(type,extra={}){window.parent.postMessage({isStreamlitMessage:true,type,...extra},'*')}
function resize(){send('streamlit:setFrameHeight',{height:Math.ceil(document.documentElement.getBoundingClientRect().height)})}
function filtered(week=state.week){return C.snapshot(data,Number(week)).filter(u=>(state.sector==='Todos'||u.Sector===state.sector)&&(state.stage==='Todas'||u.Etapa===state.stage)&&(state.type==='Todas'||u.Tipologia===state.type)&&(state.unit==='Todas'||u.ID===state.unit)&&(state.status==='Todos'||state.status===u.state||state.status==='Atrasadas'&&u.late||state.status==='Con sobrecosto'&&u.eac>u.budget+.01));}
function option(label,key,options){const el=document.createElement('label');el.textContent=label;const s=document.createElement('select');s.id=key;s.setAttribute('aria-label',label);options.forEach(([value,text])=>{const o=document.createElement('option');o.value=value;o.textContent=text;o.selected=String(value)===String(state[key]);s.appendChild(o)});s.onchange=()=>{state[key]=s.value;if(key==='sector'||key==='stage'||key==='type')state.unit='Todas';render()};el.appendChild(s);$('#filters').appendChild(el);}
function filters(){
 $('#filters').innerHTML='';option('Semana de control','week',data.weeks.map(w=>[w,'Semana '+w]));
 if(page===0)return;
 option('Sector','sector',[['Todos','Todos'],...[...new Set(data.Viviendas.map(u=>u.Sector))].map(x=>[x,x])]);
 option('Etapa','stage',[['Todas','Todas'],...[...new Set(data.Viviendas.map(u=>u.Etapa))].map(x=>[x,x])]);
 option('Tipología','type',[['Todas','Todas'],...data.Tipologias.map(t=>[t.ID,t.Nombre])]);
 if(page!==3)option('Vivienda','unit',[['Todas','Todas'],...data.Viviendas.filter(u=>(state.sector==='Todos'||u.Sector===state.sector)&&(state.stage==='Todas'||u.Etapa===state.stage)&&(state.type==='Todas'||u.Tipologia===state.type)).map(u=>[u.ID,u.ID])]);
 if(page===2){option('Estado / alerta','status',['Todos','Sin iniciar','En proceso','Terminada','Atrasadas','Con sobrecosto'].map(v=>[v,v]));option('Ver por','view',['Estado','Atraso','Sobrecosto'].map(v=>[v,v]));}
 if(page===1){option('Programación','program',['Vigente y línea base','Línea base'].map(v=>[v,v]));for(const [label,key] of [['Desde','from'],['Hasta','to']]){const l=document.createElement('label');l.textContent=label;const input=document.createElement('input');input.type='date';input.id=key;input.value=state[key];input.onchange=()=>{state[key]=input.value;render()};l.appendChild(input);$('#filters').appendChild(l)}}
}
function detailsInfo(entries){return `<div class="info">${entries.map(([k,v])=>`<div><small>${k}</small><strong>${v}</strong></div>`).join('')}</div>`;}
function summary(){
 const units=C.snapshot(data,Number(state.week)),a=C.aggregate(units),o=data.obra;
 const start=C.day(o.Inicio_programado),end=C.day(o.Fin_programado),cut=start+Number(state.week)*7-1;
 const delta=a.real-a.base,costGap=a.cost-a.costPlan,forecastGap=a.forecast-end;
 let html=panel('Datos de la obra',detailsInfo([['Nombre de la obra',esc(o.Nombre)],['Dirección',esc(o.Direccion)],['Inicio programado',date(start)],['Término programado',date(end)],['Duración',(end-start+1)+' días corridos'],['Monto contractual',money(o.Monto_contractual_MM_CLP)],['Presupuesto de costo',money(a.budget)],['Total de viviendas',units.length+' · '+data.Tipologias.map(t=>units.filter(u=>u.Tipologia===t.ID).length+' Tipo '+esc(t.ID)).join(' / ')],['Cantidad de semanas',o.Semanas_totales+' semanas'],['Semana de control','S'+state.week+' · '+date(cut)],['Sectores / etapas',new Set(units.map(u=>u.Sector)).size+' sectores · '+new Set(units.map(u=>u.Etapa)).size+' etapas'],['Tipologías',data.Tipologias.map(t=>t.Pisos+' piso(s) · '+t.Superficie_m2+' m²').join(' / ')]]));
 html+='<div class="section-label">Avance físico del conjunto</div><div class="cards three">'+pair('Avance programado vs. real',pct(a.base),pct(a.real),'Acumulado a la fecha de corte')+card('Desviación de avance',num(delta*100)+' pp','Real − programado · línea base',delta<-.0001)+card('Alerta · forecast de avance',date(a.forecast),(forecastGap>0?'+':'')+forecastGap+' días respecto del término programado',forecastGap>0)+'</div>';
 html+='<div class="section-label">Costos · CLP netos sin IVA</div><div class="cards three">'+pair('Costo programado vs. real',money(a.costPlan),money(a.cost),'Gasto acumulado al corte')+card('Desviación de costo al corte',money(costGap),'Real − programado. Diferencia de gasto al corte.')+card('Alerta · forecast de costo',money(a.eac),(a.eac>a.budget?'+':'')+money(a.eac-a.budget)+' respecto del presupuesto',a.eac>a.budget+.01)+'</div>';
 html+='<div class="section-label">Estado de las viviendas</div><div class="cards three">'+card('Viviendas terminadas',a.finished,'Avance físico de 100 %')+card('Viviendas en proceso',a.active,'Iniciadas y aún sin terminar')+card('Viviendas atrasadas',a.late,'Comparación con la programación vigente',a.late>0)+'</div>';
 const over=units.filter(u=>u.eac>u.budget+.01).sort((x,y)=>(y.eac-y.budget)-(x.eac-x.budget));
 html+='<div class="cards three">'+card('Viviendas con sobrecosto proyectado',a.over,'Costo final proyectado mayor que su presupuesto',a.over>0)+card('Mayor sobrecosto proyectado',over.length?esc(over[0].ID):'Sin alertas',over.length?money(over[0].eac-over[0].budget)+' · '+pct(over[0].eac/over[0].budget-1):'Dentro del presupuesto',over.length>0)+card('Inicios pendientes',a.pending,'Debieron iniciar al corte y aún tienen 0 %',a.pending>0)+'</div>';
 html+=panel('Alertas ejecutivas',`${a.late?`<div class="alert red">${a.late} viviendas con atraso, incluidas ${a.pending} con inicio pendiente.</div>`:'<p>Sin viviendas atrasadas al corte.</p>'}${a.over?`<div class="alert">${a.over} viviendas con costo final proyectado sobre su presupuesto.</div>`:''}<p class="note">Una vivienda en proceso puede estar atrasada y presentar sobrecosto. Las tarjetas no se suman entre sí. El atraso se evalúa contra el programa vigente; la desviación global conserva la comparación con la línea base.</p>`);
 html+=panel('Comparación de costos por vivienda',`<p class="note">Comparar viviendas de la misma tipología. El costo final proyectado considera gasto real más costo pendiente estimado; el gasto al corte por sí solo no indica ahorro ni sobrecosto.</p>`+table(['Vivienda','Tipología','Presupuesto','Costo real al corte','Costo final proyectado','Desviación final'],[...units].sort((x,y)=>x.Tipologia.localeCompare(y.Tipologia)||(y.eac/y.budget-x.eac/x.budget)).map(u=>[button(u.ID),esc(u.Tipologia),money(u.budget),money(u.cost),money(u.eac),badge(money(u.eac-u.budget)+' · '+pct(u.eac/u.budget-1),u.eac>u.budget+.01)])));
 return html;
}
function gantt(units){
 const from=state.from?C.day(state.from):C.day(data.obra.Inicio_programado),to=state.to?C.day(state.to):Math.max(C.day(data.obra.Fin_programado),...units.map(u=>Math.max(u.end,u.forecast)));
 if(!Number.isFinite(from)||!Number.isFinite(to)||to<from)return panel('Programación rítmica','<p>La fecha Hasta debe ser igual o posterior a Desde.</p>');
 const weeks=Math.ceil((to-from+1)/7),width=weeks*48,px=48/7,cut=C.day(data.obra.Inicio_programado)+state.week*7-1;
 let rows='',group='';
 for(const u of [...units].sort((a,b)=>a.Sector.localeCompare(b.Sector)||a.Tipologia.localeCompare(b.Tipologia)||a.baseStart-b.baseStart)){
  if(u.Sector+' / '+u.Tipologia!==group){group=u.Sector+' / '+u.Tipologia;rows+=`<tr class="group"><td colspan="2">${esc(group)} · ${u.Tipologia==='A'?'1 piso':'2 pisos'}</td></tr>`}
  let bars='',lanes=[];
  for(const t of [...u.tasks].sort((a,b)=>(state.program==='Línea base'?C.day(a.Inicio_base):a.start)-(state.program==='Línea base'?C.day(b.Inicio_base):b.start))){
   const s=state.program==='Línea base'?C.day(t.Inicio_base):t.start,e=state.program==='Línea base'?C.day(t.Fin_base):t.end;
   let lane=lanes.findIndex(v=>v<s);if(lane<0)lane=lanes.length;lanes[lane]=e;
   if(e<from||s>to)continue;
   const left=(Math.max(s,from)-from)*px,w=(Math.min(e,to)-Math.max(s,from)+1)*px;
   const title=`${u.ID} · ${t.Nombre}\n${date(s)}–${date(e)} · Real ${pct(t.real)}${t.replanned?' · Reprogramada':''}`;
   bars+=`<div class="segment" title="${esc(title)}" style="left:${left}px;width:${w}px;top:${6+lane*16}px;background:${palette[Number(t.Partida.slice(1))-1]}"><span style="width:${(1-t.real)*100}%"></span></div>`;
  }
  const bleft=Math.max(from,u.baseStart),bright=Math.min(to,u.baseEnd);
  if(bright>=bleft&&state.program!=='Línea base')bars+=`<div class="base" title="Línea base ${date(u.baseStart)}–${date(u.baseEnd)}" style="left:${(bleft-from)*px}px;width:${(bright-bleft+1)*px}px"></div>`;
  const cutline=cut>=from&&cut<=to?`<div class="cut" style="left:${(cut-from+1)*px}px" title="Corte ${date(cut)}"></div>`:'';
  rows+=`<tr><td class="unitcell ${u.late?'lateunit':''}">${button(u.ID)}<div class="hint">${u.state} · ${pct(u.real)}${u.late?' · Atrasada':''}</div></td><td class="timecell"><div class="rowtrack" style="width:${width}px;height:${Math.max(79,lanes.length*16+14)}px">${bars}${cutline}</div></td></tr>`;
 }
 const head=Array.from({length:weeks},(_,i)=>{const d=from+i*7;return `<span>S${Math.floor((d-C.day(data.obra.Inicio_programado))/7)+1}<br>${date(d).slice(0,5)}</span>`}).join('');
 return panel('Secuencia de construcción por vivienda',`<div class="legend">${data.Programa.slice(0,9).map((p,i)=>`<span><i class="swatch" style="background:${palette[i]}"></i>${esc(p.Nombre)}</span>`).join('')}</div><p class="note">Segmentos por partida; relleno oscuro = avance real al corte. Línea gris inferior = línea base; línea naranja vertical = corte. Pase el cursor por un segmento para consultar fechas.</p><div class="ganttwrap"><table class="rhythm"><thead><tr><th class="unitcell">Vivienda / avance</th><th class="timecell"><div class="week-head" style="width:${width}px">${head}</div></th></tr></thead><tbody>${rows||'<tr><td class="empty">Sin viviendas para estos filtros.</td></tr>'}</tbody></table></div>`);
}
function mapColor(u){return state.view==='Atraso'?(u.late?'#bb3e45':'#2b806b'):state.view==='Sobrecosto'?(u.eac>u.budget+.01?'#bb3e45':'#2b806b'):colors[u.state]}
function mapPage(units){
 const legend=state.view==='Estado'?Object.entries(colors):state.view==='Atraso'?[['Con atraso','#bb3e45'],['Sin atraso','#2b806b']]:[['Con sobrecosto','#bb3e45'],['Dentro del presupuesto','#2b806b']];
 return panel('Ubicación de las viviendas',`<div class="legend">${legend.map(([s,c])=>`<span><i class="swatch" style="background:${c}"></i>${s}</span>`).join('')}</div><div id="map"></div><p class="map-note">36 puntos originales conservados alrededor de −36,780244 / −73,0720812, Talcahuano. Viviendas ficticias alternadas: A de un piso y B de dos pisos. Seleccione una vivienda. La distribución no representa un loteo real.</p>`)+`<div id="map-selection">${panel('Seleccione una vivienda','<p class="muted">Seleccione un punto del mapa para consultar sus datos y abrir el detalle.</p>')}</div>`;
}
function mapSelection(u){return panel('Vivienda '+esc(u.ID),`<div class="statusline">${badge(u.state)}${u.late?badge('Atrasada',true):''}${u.eac>u.budget+.01?badge('Sobrecosto proyectado',true):''}</div>`+detailsInfo([['Tipología',esc(u.Tipologia)+' · '+(u.Tipologia==='A'?'1 piso':'2 pisos')],['Sector / etapa',esc(u.Sector)+' / '+esc(u.Etapa)],['Avance programado / real',pct(u.base)+' / '+pct(u.real)],['Inicio / fin programados',date(u.baseStart)+' / '+date(u.baseEnd)],['Término proyectado',date(u.forecast)],['Presupuesto',money(u.budget)],['Costo real',money(u.cost)],['Costo final proyectado',money(u.eac)]])+`<p style="margin-top:16px"><button class="link" data-unit="${esc(u.ID)}">Ver vivienda ${esc(u.ID)}</button></p>`);}
function drawMap(units){
 function select(u){$('#map-selection').innerHTML=mapSelection(u);bindUnits();resize()}
 if(!window.L){
  const minlat=-36.780244-.0005,maxlat=-36.780244+.0005,minlng=-73.0720812-.0006,maxlng=-73.0720812+.0006;
  $('#map').style.height='auto';$('#map').innerHTML=`<svg class="map-fallback" viewBox="0 0 800 500" role="img" aria-label="Distribución de viviendas por coordenadas"><text x="20" y="28" fill="#667b92" font-size="14">Vista por coordenadas · cartografía sin conexión</text>${units.map(u=>{const x=50+(u.Longitud-minlng)/(maxlng-minlng)*700,y=460-(u.Latitud-minlat)/(maxlat-minlat)*400;return `<a data-map-unit="${esc(u.ID)}" tabindex="0" role="button" aria-label="Vivienda ${esc(u.ID)}"><rect x="${x-22}" y="${y-15}" width="44" height="30" rx="5" fill="${mapColor(u)}"/><text x="${x}" y="${y+4}" text-anchor="middle" font-size="11" fill="white">${esc(u.ID.slice(2))}</text></a>`}).join('')}</svg>`;
  document.querySelectorAll('[data-map-unit]').forEach(e=>{e.onclick=()=>select(units.find(u=>u.ID===e.dataset.mapUnit));e.onkeydown=ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();e.onclick()}}});resize();return;
 }
 map=L.map('map',{scrollWheelZoom:false}).setView([-36.780244,-73.0720812],18);
 const tiles=L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:19,attribution:'Imagery © Esri, Maxar, Earthstar Geographics'}).addTo(map);let warned=false;
 tiles.on('tileerror',()=>{if(!warned){warned=true;$('#map-selection').insertAdjacentHTML('afterbegin','<p class="alert">Fondo satelital no disponible; los puntos conservan sus coordenadas y selección.</p>');resize()}});
 units.forEach(u=>{const title=`${u.ID} · Tipo ${u.Tipologia} · ${u.state}${u.late?' · Atrasada':''}`,icon=L.divIcon({className:'unit-marker',html:`<div class="house-pin ${state.view==='Estado'&&u.late?'alert-pin':''}" style="background:${mapColor(u)}">${esc(u.ID.slice(2))}</div>`,iconSize:[35,27],iconAnchor:[17,14]});const marker=L.marker([u.Latitud,u.Longitud],{icon,title}).addTo(map);marker.bindTooltip(esc(title));marker.on('click',()=>select(u))});
 if(units.length)map.fitBounds(units.map(u=>[u.Latitud,u.Longitud]),{padding:[40,40],maxZoom:19});
 setTimeout(()=>map&&map.invalidateSize(),50);
}
function detail(units){
 if(!units.length)return panel('Detalle de vivienda','<p>Sin viviendas para estos filtros.</p>');
 let u=units.find(u=>u.ID===selected)||units[0];selected=u.ID;
 const t=data.Tipologias.find(t=>t.ID===u.Tipologia);
 let html=panel('Seleccione una vivienda',`<label>Vivienda <select id="detail-unit" class="btn">${units.map(x=>`<option value="${esc(x.ID)}" ${x.ID===u.ID?'selected':''}>${esc(x.ID+' · '+x.Sector+' · Tipo '+x.Tipologia)}</option>`).join('')}</select></label>`);
 html+=panel(esc(u.ID)+' · '+esc(t.Nombre),`<div class="statusline">${badge(u.state)}${u.late?badge('Atrasada',true):''}${u.actualEnd!==null?badge(u.actualEnd>u.baseEnd?'Terminó con atraso':'Terminó dentro de plazo',u.actualEnd>u.baseEnd):''}${u.eac>u.budget+.01?badge('Sobrecosto proyectado',true):''}</div>`+detailsInfo([['Sector / etapa',esc(u.Sector)+' / '+esc(u.Etapa)],['Superficie',t.Superficie_m2+' m²'],['Distribución',t.Dormitorios+' dormitorios · '+t.Banos+' baño(s)'],['Ubicación',u.Latitud.toFixed(6)+' / '+u.Longitud.toFixed(6)],['Inicio programado',date(u.baseStart)],['Fin programado',date(u.baseEnd)],['Inicio real',date(u.actualStart)],['Fin real',date(u.actualEnd)],['Inicio vigente',date(u.start)],['Fin vigente',date(u.end)],['Término proyectado',date(u.forecast)],['Diferencia de término',(u.forecast-u.baseEnd)+' días vs. línea base']]));
 html+='<div class="cards three">'+pair('Avance programado vs. real',pct(u.base),pct(u.real),'Ponderado por las nueve partidas')+card('Desviación de avance',num((u.real-u.base)*100)+' pp','Real − línea base',u.real<u.base-.0001)+card('Costo final proyectado',money(u.eac),money(u.eac-u.budget)+' vs. presupuesto',u.eac>u.budget+.01)+'</div>';
 html+=panel('Costos de la vivienda · CLP netos',detailsInfo([['Presupuesto',money(u.budget)],['Costo programado al corte',money(u.costPlan)],['Costo real al corte',money(u.cost)],['Costo pendiente estimado',money(u.remaining)],['Costo final proyectado',money(u.eac)],['Desviación final',money(u.eac-u.budget)+' · '+pct(u.eac/u.budget-1)]]));
 html+=`<div class="visuals">${panel('Plano de planta · Tipo '+esc(t.ID),`<img data-enlarge src="${esc(t.Plano)}" alt="Plano referencial de ${esc(t.Nombre)}"><p class="note">${t.Pisos===2?'Primer y segundo piso. ':''}Esquema referencial de demostración. Pulse para ampliar.</p>`)}<div class="render">${panel('Render exterior · Tipo '+esc(t.ID),`<img data-enlarge src="${esc(t.Render)}" alt="Render referencial de ${esc(t.Nombre)}"><p class="note">Vista 3D referencial de la tipología. Pulse para ampliar.</p>`)}</div></div>`;
 html+=panel('Avance resumido de partidas',tasksTable(u));
 return html;
}
function tasksTable(u){return table(['Partida','Inicio base','Fin base','Inicio vigente','Fin vigente','Peso','Programado','Real','Aporte al total','Estado'],u.tasks.map(t=>[esc(t.Nombre),date(C.day(t.Inicio_base)),date(C.day(t.Fin_base)),date(t.start),date(t.end),pct(t.Peso),pct(t.base),pct(t.real),pct(t.Peso*t.real),badge(t.state)+(t.late?' '+badge('Atrasada',true):'')+(t.replanned?' '+badge('Reprogramada'):'')]),`<tfoot><tr><td colspan="5">Total vivienda ${esc(u.ID)}</td><td>100 %</td><td>${pct(u.base)}</td><td>${pct(u.real)}</td><td>${pct(u.real)}</td><td></td></tr></tfoot>`)}
function parts(units){
 const a=C.aggregate(units);let html='<div class="cards three">'+pair('Avance del alcance seleccionado',pct(a.base),pct(a.real),'Ponderación entre viviendas por presupuesto de costo')+card('Desviación',num((a.real-a.base)*100)+' pp','Comparación con línea base',a.real<a.base-.0001)+card('Viviendas seleccionadas',units.length,'Nueve partidas por vivienda')+'</div>';
 if(!units.length)return html+panel('Avance por partidas','<p>Sin viviendas para estos filtros.</p>');
 for(const u of units)html+=panel(button(u.ID)+' · Tipo '+esc(u.Tipologia)+' · '+esc(u.Sector),tasksTable(u));
 html+='<p class="note">Aporte al total de cada vivienda = peso de la partida × avance real. Los nueve pesos suman 100 %. El avance del conjunto pondera cada vivienda por su presupuesto, para considerar las diferentes tipologías. Las partidas reprogramadas se evalúan por sus fechas vigentes; el programado mostrado conserva la línea base.</p>';
 return html;
}
function bindUnits(){document.querySelectorAll('[data-unit]').forEach(b=>b.onclick=()=>{selected=b.dataset.unit;page=3;state.unit='Todas';state.status='Todos';render();window.scrollTo({top:0,behavior:'smooth'})})}
function exportCSV(units){const rows=[['Vivienda','Sector','Tipologia','Estado','Atrasada','Avance_programado_pct','Avance_real_pct','Presupuesto_MM_CLP','Costo_real_MM_CLP','Costo_final_proyectado_MM_CLP'],...units.map(u=>[u.ID,u.Sector,u.Tipologia,u.state,u.late?'Sí':'No',num(u.base*100),num(u.real*100),num(u.budget),num(u.cost),num(u.eac)])];const csv='\ufeff'+rows.map(r=>r.map(v=>'"'+String(v).replace(/"/g,'""')+'"').join(';')).join('\r\n');const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='viviendas_S'+state.week+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
function render(){
 if(!data)return;if(map){map.remove();map=null}
 $('#title').textContent=names[page];$('#project').textContent=data.obra.Nombre;
 const cut=C.day(data.obra.Inicio_programado)+Number(state.week)*7-1;
 $('#cut').textContent='Semana '+state.week+' · Corte: '+date(cut)+' · Datos desde maestro_construccion_masiva.xlsx';
 $('nav').innerHTML='';names.forEach((name,i)=>{const b=document.createElement('button');b.textContent=name;b.className=i===page?'active':'';b.setAttribute('aria-current',i===page?'page':'false');b.onclick=()=>{page=i;state.status='Todos';state.unit='Todas';render()};$('nav').appendChild(b)});
 filters();const units=filtered();$('#body').innerHTML=page===0?summary():page===1?gantt(units):page===2?mapPage(units):page===3?detail(units):parts(units);
 if(page===0||page===4){$('#body').insertAdjacentHTML('beforeend','<button id="export-csv" class="btn download">Descargar resumen de viviendas · CSV</button>');$('#export-csv').onclick=()=>exportCSV(page===0?C.snapshot(data,Number(state.week)):units)}
 bindUnits();if(page===2)drawMap(units);
 if(page===3&&$('#detail-unit'))$('#detail-unit').onchange=e=>{selected=e.target.value;render()};
 document.querySelectorAll('[data-enlarge]').forEach(img=>img.onclick=()=>{$('#large-image').src=img.src;$('#large-image').alt=img.alt;$('#image-caption').textContent=img.alt;$('#image-dialog').showModal()});resize();
}
$('#close-image').onclick=()=>$('#image-dialog').close();
window.addEventListener('message',event=>{if(event.source!==window.parent||event.data?.type!=='streamlit:render')return;data=event.data.args.data;if(!data)return;if(state.week===null)state.week=Number(data.obra.Semana_control);render()});
new ResizeObserver(resize).observe(document.body);send('streamlit:componentReady',{apiVersion:1});window.addEventListener('load',resize);
