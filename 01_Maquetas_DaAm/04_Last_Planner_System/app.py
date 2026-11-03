from pathlib import Path
import base64
import re
import streamlit as st
import streamlit.components.v1 as components
from data_model import load,tasks_in_week,pending_habilitantes,week_label,week_end
from views import page,table,hide_columns
from exports import VisibleTables,excel_bytes,graph_png

root=Path(__file__).parent
st.set_page_config(page_title='DaAm · Control Last Planner System',page_icon='🔷',layout='wide',initial_sidebar_state='collapsed')
st.markdown('''<style>.block-container{padding:0!important;max-width:100%!important}header[data-testid="stHeader"]{display:none}[data-testid="stAppViewContainer"]{background:#eaf0f7}</style>''',unsafe_allow_html=True)
try:c,s,issues=load(root/'maestro_demo.xlsx')
except Exception as exc:st.error(f'No fue posible leer el maestro: {exc}');st.stop()
for issue in issues:st.warning(issue)
if c.get('Sin_Datos'):st.info('Complete el Excel maestro.');st.stop()
state=st.session_state.setdefault('demo_ui',{'page':0,'execution':'13','family':'Todas','owner':'Todos','task':'Todas','hab_scope':'Pendientes de liberación','hab_owner':'Todos','hab_state':'Todos','hab_kind':'Todos','plan_week':'12'})
names=['Resumen LPS','Programa resumen a 6 semanas','Lookahead y restricciones','Plan semanal','PPC y CNC']
n=int(state['page']);filters=[]
def select(key,label,values):
    options=[{'value':str(x[0]),'label':str(x[1])} if isinstance(x,tuple) else {'value':str(x),'label':str(x)} for x in values]
    if str(state.get(key)) not in [o['value'] for o in options]:state[key]=options[0]['value']
    filters.append({'key':key,'label':label,'options':options})
if n==2:
    select('execution','Semana de ejecución',[('Todas','Todas')]+[(w,week_label(c,w)) for w in range(c['Semana_Control'],c['Semana_Control']+6)])
    look=s['lookahead'].copy()
    if state['execution']!='Todas':look=tasks_in_week(look,c,int(state['execution']))
    select('family','Familia constructiva',['Todas']+sorted(look.Familia_Constructiva.dropna().unique().tolist()))
    if state['family']!='Todas':look=look[look.Familia_Constructiva==state['family']]
    select('owner','Responsable de tarea',['Todos']+sorted(look.Responsable_Tarea.dropna().unique().tolist()))
    if state['owner']!='Todos':look=look[look.Responsable_Tarea==state['owner']]
    select('task','Tarea Lookahead',[('Todas','Todas')]+[(r.ID_Tarea,r.Tarea_Lookahead) for r in look.itertuples()])
    if state['task']!='Todas':look=look[look.ID_Tarea==state['task']]
    hab=s['habilitantes'][s['habilitantes'].ID_Tarea.isin(look.ID_Tarea)].copy()
    select('hab_scope','Consulta de habilitantes',['Pendientes de liberación','Todos','Pendientes vencidos'])
    if state['hab_scope']!='Todos':hab=pending_habilitantes(hab)
    if state['hab_scope']=='Pendientes vencidos':hab=hab[hab.Fecha_Liberacion_Requerida<c['Fecha_Control']]
    for key,label,col in [('hab_owner','Responsable de liberación','Responsable_Liberacion'),('hab_state','Estado del habilitante','Estado_Habilitante'),('hab_kind','Tipo de habilitante','Tipo_Habilitante')]:
        select(key,label,['Todos']+sorted(hab[col].dropna().unique().tolist()))
        if state[key]!='Todos':hab=hab[hab[col]==state[key]]
    body='<section class="panel"><h2>Tareas del Lookahead</h2>'+table(hide_columns(look).drop(columns=['ID_Project','Actividad_Project'],errors='ignore'))+'</section><section class="panel"><h2>Habilitantes y restricciones vinculados</h2>'+table(hide_columns(hab).drop(columns=['ID_Tarea','ID_Project','Tipo_Habilitante','Fecha_Requerida_Liberacion_'],errors='ignore'))+'</section>'
else:
    if n==3:
        select('plan_week','Semana del plan semanal',[(w,week_label(c,w)+(' · control' if w==c['Semana_Control'] else '')) for w in range(1,c['Semana_Control']+1)])
        c={**c,'Semana_Consulta':int(state['plan_week'])}
    body=page(n,c,s,include_header=False)
# Exportar únicamente los listados visibles con los filtros aplicados.
parser=VisibleTables();parser.feed(body)
links=[]
for i,(title,df) in enumerate(parser.tables):
    data=base64.b64encode(excel_bytes(df,c,title,{'Página':names[n],**{k:v for k,v in state.items() if k!='page'}})).decode()
    links.append(f'<a class="btn" download="Listado_{i+1}_S{c["Semana_Control"]}.xlsx" href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{data}">Descargar listado {i+1} · Excel</a>')
# Mantener las descargas de gráficos del modelo.
if n==4:
    panels=re.split(r'(?=<div class="panel)',body)
    for i,chunk in enumerate(panels):
        if 'data:image/svg+xml' in chunk or 'class="bars"' in chunk:
            match=re.search(r'<h2>(.*?)</h2>',chunk)
            if match:
                image=graph_png(chunk,match.group(1),c)
                if image:links.append(f'<a class="btn" download="Grafico_{i}_S{c["Semana_Control"]}.png" href="data:image/png;base64,{base64.b64encode(image).decode()}">Descargar gráfico {i} · PNG</a>')
if links:body+='<div class="downloads">'+''.join(links)+'</div>'
payload={'names':names,'project':c['Proyecto'],'state':state,'filters':filters,'body':body,'cut':f'Programa maestro: {c["Semanas_Totales"]} semanas · Control: {week_label(c,c["Semana_Control"])} · Datos ficticios','horizon':f'Horizonte {week_label(c,c["Semana_Control"])} a {week_label(c,c["Semana_Control"]+5)} · término {week_end(c,c["Semana_Control"]+5).strftime("%d/%m/%Y")}'}
ui=components.declare_component('daam_lps',path=str(root/'interfaz'))
result=ui(payload=payload,key='daam_lps',default=state)
if isinstance(result,dict) and result!=state:
    allowed=set(state)
    updated={k:result.get(k,state[k]) for k in allowed}
    try:updated['page']=max(0,min(4,int(updated['page'])))
    except (TypeError,ValueError):updated['page']=0
    st.session_state.demo_ui=updated
    st.rerun()
