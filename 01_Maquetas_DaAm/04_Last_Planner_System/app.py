from pathlib import Path
import os,hmac,base64
from html import escape
import streamlit as st
from data_model import load,tasks_in_week,pending_habilitantes,week_label
from views import CSS,page,heading,table,hide_columns
from exports import download_table,render_downloads

project_name='Edificio de oficinas demostrativo DaAm'
root=Path(__file__).parent
selected=root/'maestro_demo.xlsx'
st.set_page_config(page_title='DaAm · Control Last Planner System',page_icon='🔷',layout='wide')
brand_image=base64.b64encode((root/'assets'/'logo_daam_last_planner.png').read_bytes()).decode()
brand=f'<div class="brand-block"><img src="data:image/png;base64,{brand_image}" alt="DaAm Plataformas · Control Last Planner System" style="width:100%;display:block"><div style="color:white;font-size:16px;font-weight:600;margin-top:14px">{escape(project_name)}</div></div>' 
st.markdown('''<style>
@media(max-width:768px){[data-testid="stHorizontalBlock"]{flex-wrap:wrap!important}[data-testid="stHorizontalBlock"]>[data-testid="stColumn"]{width:100%!important;flex:1 1 100%!important;min-width:100%!important}}
[data-testid="stSidebar"]{background:#0e294b}
[data-testid="stSidebar"] h2{color:white;font-size:32px!important;margin-bottom:0}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:#c4d4e9;font-size:16px;line-height:1.5}
[data-testid="stSidebar"] label{color:white;font-size:16px}
[data-testid="stSidebar"] [data-baseweb="select"] *{color:#173960!important}
[data-testid="stSidebar"] button{font-size:16px;text-align:center;min-height:44px}
[data-testid="stSidebar"] button[kind="secondary"]{background:#2b5078;color:white;border:0}
[data-testid="stSidebar"] button[kind="secondary"] p{color:white}
[data-testid="stSidebar"] button[kind="primary"]{background:#436f9b;color:white;border:0}
[data-testid="stSidebar"] .brand-block{margin:0 0 22px;font-family:Arial,sans-serif}
[data-testid="stSidebar"] .brand-name{color:#ffffff;font-size:27px;font-weight:700;line-height:1.2;letter-spacing:-.5px}
[data-testid="stSidebar"] .brand-subtitle{color:#d5e1ef;font-size:15px;margin-top:7px}
[data-testid="stSidebar"] .brand-service{color:#ffffff;font-size:16px;font-weight:600;line-height:1.45;margin-top:22px;padding-top:18px;border-top:1px solid #345271}
[data-testid="stSidebar"] .brand-system{color:#d5e1ef;font-size:14px;margin-top:5px}
[data-testid="stSidebar"] .brand-client{color:#ffffff;font-size:23px;font-weight:700;letter-spacing:1px;margin-top:12px}
.stApp{background:#f4f7fb}
[data-testid="stMainBlockContainer"]{padding-top:1.5rem;max-width:none}
.st-key-mobile_navigation{display:none}
@media(max-width:768px){
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"]{display:none!important}
.st-key-mobile_navigation{display:block;background:#0e294b;border:0;border-radius:10px;padding:20px 16px;margin-bottom:20px}
.st-key-mobile_navigation .brand-block{margin-bottom:20px;font-family:Arial,sans-serif}
.st-key-mobile_navigation .brand-name{color:white;font-size:27px;font-weight:700;line-height:1.2}
.st-key-mobile_navigation .brand-subtitle{color:#d5e1ef;font-size:15px;margin-top:7px}
.st-key-mobile_navigation .brand-service{color:white;font-size:16px;font-weight:600;margin-top:18px;padding-top:16px;border-top:1px solid #345271}
.st-key-mobile_navigation .brand-client{color:white;font-size:23px;font-weight:700;letter-spacing:1px;margin-top:10px}
.st-key-mobile_navigation label p{color:white!important}
.st-key-mobile_navigation [data-baseweb="select"]{background:#ffffff;border-radius:8px}
.st-key-mobile_navigation [data-baseweb="select"] *{color:#173960!important}
.st-key-mobile_navigation [data-testid="stExpander"]{background:#0e294b!important;border:0!important;border-radius:8px;margin-top:24px!important}
.st-key-mobile_navigation [data-testid="stExpander"] details,.st-key-mobile_navigation [data-testid="stExpander"] summary{background:#2b5078!important;border-radius:8px}
.st-key-mobile_navigation [data-testid="stExpanderDetails"]{background:#0e294b!important;padding:16px 0!important}
.st-key-mobile_navigation [data-testid="stExpander"] summary{min-height:48px}
.st-key-mobile_navigation [data-testid="stExpander"] summary p,.st-key-mobile_navigation [data-testid="stExpander"] summary svg{color:white!important}
.st-key-mobile_navigation button[kind="secondary"]{background:#2b5078!important;color:white!important;border:0!important}
.st-key-mobile_navigation button[kind="primary"]{background:#436f9b!important;color:white!important;border:0!important}
.st-key-mobile_navigation button p{color:white!important}
html,body{overscroll-behavior-y:contain}
}
@media(max-width:768px){[data-testid="stMainBlockContainer"]{padding-top:3.75rem!important;padding-left:.65rem;padding-right:.65rem}}
</style>''',unsafe_allow_html=True)
st.caption('EJEMPLO DEMOSTRATIVO · Una obra ficticia · Programa maestro de 52 semanas')
if not selected.is_file():
    st.error('No se encontró el maestro de esta obra.');st.stop()
routes=['Resumen LPS','Programa resumen a 6 semanas','Lookahead y restricciones','Plan semanal','PPC y CNC']
if st.session_state.get('route')=='Programa de seis semanas':st.session_state.route='Programa resumen a 6 semanas'
st.session_state.setdefault('route',routes[0])
def navigation(prefix):
    for label in routes:
        if st.button(label,key=prefix+'_'+label,type='primary' if st.session_state.route==label else 'secondary',use_container_width=True):
            st.session_state.route=label;st.rerun()
with st.sidebar:
    st.markdown(brand,unsafe_allow_html=True)
    navigation('desktop')
with st.container(key='mobile_navigation'):
    st.markdown(brand,unsafe_allow_html=True)
    with st.expander('☰ Menú',expanded=False):navigation('mobile')
route=st.session_state.route
try:config,sheets,issues=load(selected)
except Exception as exc:st.error(f'No fue posible leer el Maestro: {exc}');st.stop()
if config.get('Sin_Datos'):
    st.title(config.get('Proyecto','Proyecto'))
    st.info('Esta obra aún no tiene información cargada.')
    st.stop()
for issue in issues:st.warning(issue)
routes=['Resumen LPS','Programa resumen a 6 semanas','Lookahead y restricciones','Plan semanal','PPC y CNC'];n=routes.index(route)
st.html(f'<style>{CSS}</style><div>{heading(n,config)}</div>')
if n==2:
    look=sheets['lookahead'];hab=sheets['habilitantes']
    control=config['Semana_Control']
    with st.container(border=True):
        st.subheader('1. Tareas del lookahead')
        filter_row=st.columns(3)
        selected_week=filter_row[0].selectbox('Semana de ejecución de la tarea',['Todas']+list(range(control,control+6)),index=2,format_func=lambda w:w if w=='Todas' else week_label(config,w),key=f'execution_week_{selected.parent.name}_{control}')
        if selected_week!='Todas':look=tasks_in_week(look,config,selected_week)
        family_col='Familia_Constructiva' if 'Familia_Constructiva' in look else 'Actividad_Project'
        activity=filter_row[1].selectbox('Familia constructiva',['Todas']+sorted(look[family_col].dropna().unique().tolist()))
        if activity!='Todas':look=look[look[family_col]==activity]
        task_owner=filter_row[2].selectbox('Responsable de la tarea',['Todos']+sorted(look.Responsable_Tarea.dropna().unique().tolist()))
        if task_owner!='Todos':look=look[look.Responsable_Tarea==task_owner]
        task=st.selectbox('Tarea Lookahead',['Todas']+look.ID_Tarea.tolist(),format_func=lambda x:x if x=='Todas' else str(look.loc[look.ID_Tarea==x,'Tarea_Lookahead'].iloc[0]))
        if task!='Todas':look=look[look.ID_Tarea==task]
        scope='Todas las semanas' if selected_week=='Todas' else f'Semana {week_label(config,selected_week)}'
        st.caption(f'{scope} · {len(look)} tareas con los filtros seleccionados')
        st.html(f'<style>{CSS}</style>'+table(hide_columns(look).drop(columns=['ID_Project','Actividad_Project'],errors='ignore')))
        task_filters={'Semana de ejecución':scope,'Actividad':activity,'Responsable de tarea':task_owner,'Tarea':task}
        download_table(hide_columns(look).drop(columns=['ID_Project','Actividad_Project'],errors='ignore'),config,'Tareas Lookahead',task_filters,'lookahead')
    hab=hab[hab.ID_Tarea.isin(look.ID_Tarea)].copy()
    with st.container(border=True):
        st.subheader('2. Habilitantes y restricciones vinculados')
        st.caption('Se muestran los habilitantes vinculados a las tareas seleccionadas arriba.')
        hab_row=st.columns(3)
        status_scope=hab_row[0].selectbox('Consulta de habilitantes',['Pendientes de liberación','Todos','Pendientes vencidos'])
        if status_scope!='Todos':hab=pending_habilitantes(hab)
        if status_scope=='Pendientes vencidos':hab=hab[hab.Fecha_Liberacion_Requerida<config['Fecha_Control']]
        owner=hab_row[1].selectbox('Responsable de liberación del habilitante',['Todos']+sorted(hab.Responsable_Liberacion.dropna().unique().tolist()))
        if owner!='Todos':hab=hab[hab.Responsable_Liberacion==owner]
        state=hab_row[2].selectbox('Estado del habilitante',['Todos']+sorted(hab.Estado_Habilitante.dropna().unique().tolist()))
        if state!='Todos':hab=hab[hab.Estado_Habilitante==state]
        hab_row2=st.columns(3)
        kind=hab_row2[0].selectbox('Tipo de habilitante',['Todos']+sorted(hab.Tipo_Habilitante.dropna().unique().tolist()))
        if kind!='Todos':hab=hab[hab.Tipo_Habilitante==kind]
        st.caption(f'{scope} · {len(hab)} habilitantes vinculados con los filtros seleccionados')
        st.html(f'<style>{CSS}</style>'+table(hide_columns(hab).drop(columns=['ID_Tarea','ID_Project','Tipo_Habilitante','Fecha_Requerida_Liberacion_'],errors='ignore')))
        download_table(hide_columns(hab).drop(columns=['ID_Tarea','ID_Project','Tipo_Habilitante','Fecha_Requerida_Liberacion_'],errors='ignore'),config,'Habilitantes y restricciones',{**task_filters,'Consulta':status_scope,'Responsable de liberación':owner,'Estado habilitante':state,'Tipo habilitante':kind},'habilitantes')
else:
    if n==3:
        available=list(range(1,config['Semana_Control']+1))
        config=dict(config)
        config['Semana_Consulta']=st.selectbox('Seleccionar semana',available,index=len(available)-1,format_func=lambda w:f'{week_label(config,w)} · semana de control' if w==config['Semana_Control'] else week_label(config,w),key=f'plan_week_{selected.parent.name}_{config["Semana_Control"]}')
    body=page(n,config,sheets,include_header=False)
    render_downloads(body,config,route,CSS)
