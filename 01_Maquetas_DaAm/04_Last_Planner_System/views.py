from html import escape
import pandas as pd
import base64
import textwrap
import math
from data_model import pcp,cnc,CNC_MAP,management_summary,weekly_snapshot,week_start,week_end,week_label,invalid_week_records

CSS='''
*{box-sizing:border-box}body{margin:0;font-family:Arial,sans-serif;color:#173960;background:#f4f7fb;font-size:16px}h1{font-size:28px;margin:0 0 8px}h2{font-size:19px;margin:0 0 20px}p{line-height:1.5}.project-name{font-size:20px;font-weight:600;margin-bottom:12px}.banner strong{display:block;line-height:1.8}.gantt td{padding:8px 10px}.muted{color:#6780a3;font-size:14px}.banner{background:#fff2e6;padding:16px;border-radius:8px;margin:20px 0}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:20px 0}.card,.panel{background:white;border:1px solid #dbe5f2;border-radius:9px;padding:20px}.card label{font-size:13px;font-weight:700;color:#6e85a8;display:block;margin-bottom:12px}.value{font-size:26px;font-weight:bold}.panel{margin:16px 0}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;border-bottom:1px solid #e2eaf4;padding:14px 10px;vertical-align:top}th{color:#7187a7;font-weight:600}td{min-width:100px}.gantt{min-width:1050px}.gantt td:first-child{min-width:80px}.gantt td:nth-child(2){min-width:300px}.bar{background:#294e78;height:14px;border-radius:3px;display:block}.week-now{background:#fff2e6}.good{color:#294e78}.bad{color:#d23a3a}.empty{padding:20px;color:#7187a7}.bars{display:flex;align-items:flex-end;gap:22px;min-height:220px;padding-top:25px;overflow-x:auto}.barcol{min-width:100px;text-align:center;font-size:13px;flex:1}.pillar{background:#294e78;margin:10px auto;width:50px;border-radius:4px 4px 0 0}.linechart{width:100%;min-width:500px}button,select{font:inherit} @media(max-width:600px){.cards{grid-template-columns:1fr 1fr}.card{padding:14px}.value{font-size:23px}.panel{padding:14px}h1{font-size:23px}th,td{padding:10px;font-size:14px}}
'''
def e(x): return escape(str(x))
def card(title,value,sub='',color=''):
    return f'<div class="card"><label>{e(title)}</label><div class="value {color}">{e(value)}</div><p class="muted">{e(sub)}</p></div>'
def metric(plan,week,label):
    v=pcp(plan,week)
    return card(label,'Revisar semana' if invalid_week_records(plan,week) else 'En proceso' if v is None else f'{v:.1f} %',f'S{week}', '' if v is None else 'good' if v>=85 else 'bad')
def table(df,cols=None):
    if df.empty:return '<div class="empty">Sin registros disponibles.</div>'
    d=df[cols].copy() if cols else df.copy()
    for c in d:
        if pd.api.types.is_datetime64_any_dtype(d[c]):d[c]=d[c].dt.strftime('%d/%m/%Y')
    return '<div class="scroll">'+d.fillna('—').to_html(index=False,escape=True,border=0)+'</div>'
def bars(counts):
    if counts.empty:return '<p class="empty">Sin causas registradas.</p>'
    maximum=max(counts.max(),1)
    return '<div class="bars">'+''.join(f'<div class="barcol"><b>{int(n)}</b><div class="pillar" style="height:{max(8,160*n/maximum)}px"></div>{e(c)}</div>' for c,n in counts.items())+'</div>'
def heading(n,c):
    titles=['Resumen LPS','Programa resumen de 6 semanas','Lookahead, habilitantes y restricciones','Plan semanal','PPC y CNC']
    out=f'<div class="project-name">{e(c["Proyecto"])}</div><h1>{"PPC: Porcentaje de Compromisos Planificados Cumplidos<br>CNC: Causas de No Cumplimiento" if n==4 else titles[n]}</h1>'
    if n==1:
        week=c['Semana_Control']
        out+=f'<p class="muted" style="margin:4px 0 12px">Horizonte {week_label(c,week)}–{week_label(c,week+5)} · término {week_end(c,week+5).strftime("%d/%m/%Y")}</p>'
    return out

def page(n,c,s,include_header=True):
    week=c['Semana_Control'];plan=s['plan'];look=s['lookahead'];hab=s['habilitantes'];prev=plan[plan.Semana==c.get('Semana_Consulta',week-1)];current=plan[plan.Semana==week]
    title=['Resumen LPS','Programa resumen de 6 semanas','Lookahead, habilitantes y restricciones','Plan semanal','PPC y CNC'][n]
    out=heading(n,c) if include_header else ''
    if n==0:
        causes=cnc(pd.concat([plan[plan.Semana.between(1,week-1)],weekly_snapshot(plan,week)],ignore_index=True)).head(3)
        out+=f'<div class="banner"><strong>Programa maestro: {c["Semanas_Totales"]} semanas</strong><strong>Semana de control: {week_label(c,week)}</strong></div><div class="cards">'
        out+=metric(plan,week-2,f'PPC Semana S{week-2}')+metric(plan,week-1,f'PPC Semana S{week-1}')+current_metric(plan,week)
        failed,missing,pending,upcoming,overdue=management_summary(c,s)
        out+=card(f'COMPROMISOS NO CUMPLIDOS S{week-1}',len(failed),'Marcados No en el control semanal')
        out+=card(f'NO CUMPLIDOS S{week-1} SIN REPROGRAMAR EN S{week}',len(missing),'Sin registro de la misma tarea en el plan vigente')
        out+=card('HABILITANTES PENDIENTES',len(pending),'Total pendiente de liberación')
        out+=card(f'HABILITANTES PENDIENTES PARA S{week+1}',len(upcoming),'Vinculados a tareas de la próxima semana')
        out+=card('HABILITANTES VENCIDOS',len(overdue),f'Al corte {c["Fecha_Control"].strftime("%d/%m/%Y")}')+'</div>'
        missing_details=missing.reindex(columns=['ID_Tarea','Tarea_Lookahead','Responsable_Tarea','Comprometido','Avance','Causa_No_Cumplimiento']).rename(columns={'Tarea_Lookahead':'Tarea no reprogramada','Responsable_Tarea':'Responsable','Comprometido':'Comprometido semanal (%)','Avance':'Ejecutado semanal (%)','Causa_No_Cumplimiento':'Causa de no cumplimiento'})
        out+=f'<div class="panel"><details><summary style="cursor:pointer;font-weight:700">Ver tareas no reprogramadas ({len(missing)})</summary><p class="muted">Tareas no cumplidas en S{week-1} cuyo ID_Tarea no aparece en el plan semanal S{week}. Cada tarea se contabiliza una vez.</p>'+table(missing_details)+'</details></div>'
        overdue_details=overdue.sort_values('Fecha_Liberacion_Requerida')[['ID_Habilitante','Tarea_Lookahead','Actividad_Habilitante','Responsable_Liberacion','Fecha_Liberacion_Requerida','Estado_Habilitante']].rename(columns={'Tarea_Lookahead':'Tarea vinculada','Actividad_Habilitante':'Habilitante','Responsable_Liberacion':'Responsable','Fecha_Liberacion_Requerida':'Fecha requerida','Estado_Habilitante':'Estado'})
        overdue_details['Días vencidos']=(c['Fecha_Control']-overdue.sort_values('Fecha_Liberacion_Requerida')['Fecha_Liberacion_Requerida']).dt.days
        out+='<div class="panel"><details><summary style="cursor:pointer;font-weight:700">Ver habilitantes vencidos ('+str(len(overdue))+')</summary><p class="muted">Fecha requerida anterior al corte y pendiente de liberación.</p>'+table(overdue_details)+'</details></div>'
        upcoming=upcoming.sort_values('Fecha_Liberacion_Requerida',na_position='last')
        details=upcoming[['ID_Habilitante','Tarea_Lookahead','Actividad_Habilitante','Responsable_Liberacion','Fecha_Liberacion_Requerida','Estado_Habilitante']].rename(columns={'Tarea_Lookahead':'Tarea vinculada','Actividad_Habilitante':'Habilitante','Responsable_Liberacion':'Responsable','Fecha_Liberacion_Requerida':'Fecha de liberación','Estado_Habilitante':'Estado'})
        out+=f'<div class="panel"><h2>Habilitantes pendientes para S{week+1}</h2>'+table(details)+'</div>'
        out+=f'<div class="panel"><h2>Las 3 Causas de no cumplimiento más frecuentes</h2><p class="muted">Acumulado S1–S{week}, incluyendo el último corte de S{week} como preliminar.</p>'+table(causes.rename_axis('Causa').reset_index(name='Cantidad'))+'</div>'
    elif n==1:
        out+=lookahead_gantt(c,s['lookahead'])
    elif n==2:
        out+='<div class="panel"><h2>Tareas Lookahead</h2>'+table(hide_columns(look).drop(columns=['ID_Project','Actividad_Project'],errors='ignore'))+'</div><div class="panel"><h2>Habilitantes y restricciones vinculados</h2>'+table(hide_columns(hab).drop(columns=['ID_Tarea','ID_Project','Tipo_Habilitante','Fecha_Requerida_Liberacion_'],errors='ignore'))+'</div>'
    elif n==3:
        selected_week=c.get('Semana_Consulta',week)
        selected_plan=plan[plan.Semana.eq(selected_week)]
        label='Semana de control' if selected_week==week else 'Semana consultada'
        out+=f'<div class="panel"><h2>{label} · S{selected_week}</h2>'+table(selected_plan.drop(columns=['Semana','Avance','Comprometido','Semana_Compromiso','Observaciones','Observacion','Origen','ID_Tarea','ID_Project'],errors='ignore'))+'</div>'
    else:
        out+='<div class="cards">'+metric(plan,week-2,f'PPC Semana S{week-2}')+metric(plan,week-1,f'PPC Semana S{week-1}')+current_metric(plan,week)+'</div>'
        out+=f'<div class="panel"><h2>CNC por causa · S{week-2}, S{week-1} y S{week}</h2>'+comparison_cnc(plan,week,config=c)+'</div>'
        failed=plan[plan.Semana.isin([week-2,week-1]) & plan.Resultado.eq('No cumplido')].copy()
        preliminary=weekly_snapshot(plan,week)
        preliminary=preliminary[preliminary.Resultado.eq('No cumplido') & preliminary.Causa_No_Cumplimiento.fillna('').astype(str).str.strip().ne('')]
        failed=pd.concat([failed,preliminary],ignore_index=True).sort_values('Semana')
        failed['Semana']=failed.Semana.map(lambda w:f'S{int(w)} · preliminar' if w==week else f'S{int(w)}')
        failed=failed[['Semana','Tarea_Lookahead','Responsable_Tarea','Comprometido','Avance','Causa_No_Cumplimiento']].rename(columns={'Tarea_Lookahead':'Compromiso','Responsable_Tarea':'Responsable','Comprometido':'Comprometido semanal (%)','Avance':'Ejecutado semanal (%)','Causa_No_Cumplimiento':'Causa de no cumplimiento'})
        out+=f'<div class="panel scroll"><h2>Compromisos no cumplidos · S{week-2}, S{week-1} y S{week}</h2>'+table(failed)+'</div>'
        closed=[w for w in range(1,week) if pcp(plan,w) is not None]
        pcp_points=[(w,pcp(plan,w)) for w in closed]
        cnc_points=[(w,int(cnc(plan[plan.Semana==w]).sum())) for w in closed]
        snapshot=weekly_snapshot(plan,week)
        current_value=pcp(snapshot,week)
        note=''
        if current_value is not None:
            pcp_points.append((week,current_value))
            cnc_points.append((week,int(cnc(snapshot).sum())))
            note=f'<p class="muted">S{week}: preliminar al último corte registrado.</p>'
        out+='<div class="panel"><h2>Evolución del PPC</h2>'+note+line_chart(pcp_points,percent=True,config=c)+'</div>'
        out+='<div class="panel"><h2>Evolución del CNC · cantidad semanal</h2>'+note+line_chart(cnc_points,config=c)+'</div>'
        counts=cnc(plan[plan.Semana.isin(closed)])
        if current_value is not None:
            counts=counts.add(cnc(snapshot),fill_value=0).astype(int)
        counts=counts.sort_values(ascending=False)
        out+=f'<div class="panel"><h2>CNC acumuladas por causa · S1–S{week}</h2>'+note+bars(counts)+'</div>'
    return dated_week_text(out,c)


def hide_columns(df):
    return df.drop(columns=[c for c in df if str(c).strip().lower() in ['observaciones','observacion','observación']],errors='ignore')


def line_chart(points,percent=False,config=None):
    if not points:return '<p class="empty">Sin semanas cerradas disponibles.</p>'
    maximum=100 if percent else max(1,max(v for _,v in points))
    def xy(w,v):return 70+(w-points[0][0])*660/max(1,points[-1][0]-points[0][0]),230-v/maximum*180
    svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 280" style="font-family:Arial" role="img">'
    for i in range(5):
        v=maximum*i/4;y=230-v/maximum*180
        svg+=f'<line x1="60" y1="{y}" x2="750" y2="{y}" stroke="#e2eaf4"/><text x="50" y="{y+5}" text-anchor="end" fill="#6780a3" font-size="13">{v:g}{"%" if percent else ""}</text>'
    if percent:
        y=230-85/100*180
        svg+=f'<line x1="60" y1="{y}" x2="750" y2="{y}" stroke="#d23a3a" stroke-width="2" stroke-dasharray="7 5"/><text x="745" y="{y-8}" text-anchor="end" fill="#d23a3a" font-size="11">Meta 85 %</text>'
    for (wa,va),(wb,vb) in zip(points,points[1:]):
        if wb==wa+1:
            xa,ya=xy(wa,va);xb,yb=xy(wb,vb)
            svg+=f'<line x1="{xa}" y1="{ya}" x2="{xb}" y2="{yb}" stroke="#294e78" stroke-width="3"/>'
    for w,v in points:
        x,y=xy(w,v);label=f'{v:.1f} %' if percent else str(v)
        svg+=f'<circle cx="{x}" cy="{y}" r="5" fill="#294e78"/><text x="{x}" y="{y-12}" text-anchor="middle" fill="#173960" font-size="11">{label}</text><text x="{x}" y="255" text-anchor="middle" fill="#6780a3" font-size="11">S{w}</text>'
    svg+='</svg>'
    svg=dated_week_text(svg,config) if config is not None else svg
    encoded=base64.b64encode(svg.encode()).decode()
    return f'<img style="width:100%;max-width:900px;display:block;margin:0 auto" alt="{"Evolución PPC con meta 85 por ciento" if percent else "Evolución CNC semanal"}" src="data:image/svg+xml;base64,{encoded}">'


def current_metric(plan,week):
    value=pcp(plan,week)
    return card(f'PPC Semana S{week} · preliminar','Revisar semana' if invalid_week_records(plan,week) else 'Sin datos aún' if value is None else f'{value:.1f} %','Semana en curso · corte registrado')

def current_cnc(plan,week):
    rows=weekly_snapshot(plan,week)
    if pcp(rows,week) is None:return '<p class="muted">Sin datos aún. Complete el control semanal.</p>'
    return '<p class="muted">Preliminar · semana en curso. Las causas registradas pueden cambiar hasta el cierre.</p>'+cause_chart(cnc(rows))


def cause_chart(counts):
    counts=counts.sort_values(ascending=False)
    if counts.empty:return '<p class="muted">Sin causas de no cumplimiento registradas.</p>'
    maximum=max(1,counts.max())
    out='<div role="img" aria-label="Cantidad de registros por causa de no cumplimiento">'
    for cause,count in counts.items():
        out+=f'<div style="margin:18px 0"><div style="display:flex;justify-content:space-between;gap:16px;line-height:1.5;margin-bottom:7px"><span>{e(cause)}</span><strong>{int(count)}</strong></div><div style="height:18px;background:#edf2f8;border-radius:4px"><div style="height:18px;width:{100*count/maximum:.2f}%;background:#294e78;border-radius:4px"></div></div></div>'
    return out+'</div>'


def comparison_cnc(plan,week,config=None):
    weeks=[w for w in [week-2,week-1,week] if w>0]
    colors=['#a9bfd7','#426b98','#0e294b'][-len(weeks):]
    counts={};notes=[]
    for w in weeks:
        rows=weekly_snapshot(plan,w) if w==week else plan[plan.Semana.eq(w)]
        if pcp(rows,w) is None:
            counts[w]=pd.Series(dtype=int);notes.append(f'S{w}: sin datos aún')
        else:counts[w]=cnc(rows)
    causes=sorted(set().union(*(set(v.index) for v in counts.values())),key=lambda cause:(-sum(v.get(cause,0)>0 for v in counts.values()),-sum(v.get(cause,0) for v in counts.values()),cause))
    out='<div style="display:flex;flex-wrap:wrap;gap:18px;margin-bottom:16px">'
    for w,color in zip(weeks,colors):
        out+=f'<span><span style="display:inline-block;width:12px;height:12px;background:{color};margin-right:6px"></span>S{w}{" · preliminar" if w==week else ""}</span>'
    out+='</div>'
    if notes:out+='<p class="muted">'+e(' · '.join(notes))+'</p>'
    if not causes:return out+'<p class="muted">Sin causas de no cumplimiento registradas para este período.</p>'
    width=max(900,240*len(causes)+80);height=340;top=30;bottom=190;left=55
    group=(width-left-25)/len(causes)
    maximum=max(1,max(int(v.max()) for v in counts.values() if not v.empty))
    step=max(1,math.ceil(maximum/5));axismax=math.ceil(maximum/step)*step
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="font-family:Arial" role="img"><title>Causas de no cumplimiento de las tres semanas</title>'
    for i,cause in enumerate(causes):
        if sum(v.get(cause,0)>0 for v in counts.values())>1:
            svg+=f'<rect x="{left+i*group+5}" y="20" width="{group-10}" height="305" rx="10" fill="#edf3fa"/>'
    for value in range(0,axismax+1,step):
        y=bottom-(bottom-top)*value/axismax
        svg+=f'<line x1="{left}" y1="{y}" x2="{width-25}" y2="{y}" stroke="#dbe5f2"/><text x="{left-12}" y="{y+5}" text-anchor="end" font-size="12" fill="#6780a3">{value}</text>'
    svg+='<text x="12" y="18" fill="#6780a3" font-size="14">Cantidad</text>'
    for i,cause in enumerate(causes):
        center=left+(i+.5)*group;barwidth=min(42,group/(len(weeks)+3));gap=7
        for j,(w,color) in enumerate(zip(weeks,colors)):
            value=int(counts[w].get(cause,0));x=center+(j-(len(weeks)-1)/2)*(barwidth+gap)-barwidth/2
            if value:
                h=(bottom-top)*value/axismax;y=bottom-h
                svg+=f'<rect x="{x}" y="{y}" width="{barwidth}" height="{h}" fill="{color}"><title>{e(cause)} · S{w}: {value}</title></rect><text x="{x+barwidth/2}" y="{y-9}" text-anchor="middle" font-size="12" font-weight="700" fill="#173960">{value}</text>'
        lines=textwrap.wrap(str(cause),width=25)
        for k,line in enumerate(lines):svg+=f'<text x="{center}" y="{bottom+24+k*17}" text-anchor="middle" font-size="12" fill="#173960">{e(line)}</text>'
        repeated=[f'S{w}' for w in weeks if counts[w].get(cause,0)>0]
        if len(repeated)>1:
            svg+=f'<text x="{center}" y="{bottom+38+len(lines)*17}" text-anchor="middle" font-size="13" font-weight="700" fill="#426b98">Se repite en {e(", ".join(repeated))}</text>'
    svg+='</svg>'
    svg=dated_week_text(svg,config) if config is not None else svg
    encoded=base64.b64encode(svg.encode()).decode()
    out+=f'<div class="scroll"><img style="width:{width}px;max-width:none;display:block;margin:0 auto" alt="Columnas por causa y semana; causas recurrentes resaltadas" src="data:image/svg+xml;base64,{encoded}"></div>'
    return out+'<p class="muted">Las causas recurrentes aparecen primero y resaltadas. En celular, deslice el gráfico horizontalmente para ver todas las causas. La semana de control refleja el último corte registrado y puede cambiar hasta el cierre.</p>'


def dated_week_text(html, config):
    """Add dates to visible week tokens without changing identifiers or attributes."""
    import re
    from html.parser import HTMLParser
    class WeekText(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.parts=[]
        def handle_starttag(self, tag, attrs): self.parts.append(self.get_starttag_text())
        def handle_startendtag(self, tag, attrs): self.parts.append(self.get_starttag_text())
        def handle_endtag(self, tag): self.parts.append(f'</{tag}>')
        def handle_data(self, text):
            self.parts.append(re.sub(r'(?<![\w])S(\d+)(?![\d(])', lambda m: week_label(config,int(m[1])), text))
        def handle_entityref(self, name): self.parts.append('&'+name+';')
        def handle_charref(self, name): self.parts.append('&#'+name+';')
    parser=WeekText();parser.feed(html)
    return ''.join(parser.parts)


def lookahead_gantt(config,look):
    from data_model import tasks_in_week,task_weeks
    week=config['Semana_Control'];weeks=list(range(week,week+6))
    visible=look[look.index.isin(set().union(*(set(tasks_in_week(look,config,w).index) for w in weeks)))].copy()
    # Compatibilidad con maestros anteriores, que aún usan actividades Project.
    if 'ID_Familia' not in visible:visible['ID_Familia']=visible.get('ID_Project',pd.Series(index=visible.index,dtype=str))
    if 'Familia_Constructiva' not in visible:visible['Familia_Constructiva']=visible.get('Actividad_Project',pd.Series(index=visible.index,dtype=str))
    visible['ID_Familia']=visible.ID_Familia.fillna('Sin familia')
    visible['Familia_Constructiva']=visible.Familia_Constructiva.fillna('Sin familia asignada')
    out='<div class="panel scroll"><h2>Gantt del lookahead</h2><table class="gantt"><thead><tr><th>ID / Familia</th><th>Tarea Lookahead</th><th>Inicio</th><th>Término</th>'
    for w in weeks:out+=f'<th>{week_label(config,w)}<br>({week_end(config,w).strftime("%d/%m/%Y")})</th>'
    out+='</tr></thead><tbody>'
    for (code,family),group in visible.groupby(['ID_Familia','Familia_Constructiva'],sort=True):
        active={w:set(tasks_in_week(group,config,w).index) for w in weeks}
        out+=f'<tr style="background:#edf3fa;font-weight:700"><td>{e(code)}</td><td>{e(family)}</td><td></td><td></td>'
        for w in weeks:out+='<td>'+ (f'<span class="bar" title="{len(active[w])} tareas"></span>' if active[w] else '')+'</td>'
        out+='</tr>'
        for idx,row in group.iterrows():
            date=lambda value:'' if pd.isna(value) else value.strftime('%d/%m/%Y')
            out+=f'<tr><td>{e(row.ID_Tarea)}</td><td>{e(row.Tarea_Lookahead)}</td><td>{date(row.Inicio_Tarea)}</td><td>{date(row.Fin_Tarea)}</td>'
            for w in weeks:out+='<td>'+('<span class="bar"></span>' if idx in active[w] else '')+'</td>'
            out+='</tr>'
    if visible.empty:out+='<tr><td colspan="10">Sin tareas registradas para este horizonte.</td></tr>'
    return out+'</tbody></table></div>'
