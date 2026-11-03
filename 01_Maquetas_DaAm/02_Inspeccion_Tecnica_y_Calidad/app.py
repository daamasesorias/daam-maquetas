from pathlib import Path
import base64
import io
import pandas as pd
from data_model import REQUIRED
import streamlit as st
import streamlit.components.v1 as components
from data_model import load_master,read_state,apply_action
from reports import build_pdf,build_excel
ROOT=Path(__file__).parent
st.set_page_config(page_title='DaAm · Inspección Técnica y Calidad',page_icon='🏗️',layout='wide',initial_sidebar_state='collapsed')
st.markdown('<style>.block-container{padding:0!important;max-width:100%!important}header[data-testid="stHeader"]{display:none}[data-testid="stAppViewContainer"]{background:#eaf0f7}</style>',unsafe_allow_html=True)
component=components.declare_component('daam_calidad_nueva',path=str(ROOT/'interfaz'))
try:
    seed=load_master(ROOT/'maestro_inspeccion_calidad.xlsx')
    db=ROOT/'registros_calidad.sqlite3'
    data=read_state(seed,db)
    # Respaldos integrados para las dos evidencias que no cargaban en el ejemplo.
    data['embeddedEvidence']={}
    for eid in ('F05','F07'):
        evidence=next((e for e in data['Evidencias'] if e['ID']==eid),None)
        if evidence:
            path=ROOT/'interfaz'/evidence['Archivo']
            if path.is_file():data['embeddedEvidence'][eid]='data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()

except Exception as error:
    st.error(f'No fue posible cargar la obra: {error}');st.stop()
result=st.session_state.get('result',{})
action=component(data=data,result=result,key='calidad')
if action and action.get('id')!=st.session_state.get('last_action'):
    st.session_state.last_action=action['id']
    try:
        if action.get('kind')=='template':
            buf=io.BytesIO()
            with pd.ExcelWriter(buf,engine='openpyxl') as writer:
                for sheet in REQUIRED:pd.DataFrame([r for r in data[sheet] if not (sheet=='Documentos' and r['Archivo'].startswith('DOC-'))],columns=REQUIRED[sheet]).to_excel(writer,sheet_name=sheet,index=False)
            result={'id':action['id'],'ok':True,'message':'Planilla preparada.','download':{'name':'maestro_inspeccion_calidad.xlsx','mime':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','base64':base64.b64encode(buf.getvalue()).decode()}}
        elif action.get('kind')=='report':
            fmt=action.get('format');period=action.get('period','Semanal');cut=action.get('cut')
            if fmt not in ('pdf','xlsx') or period not in ('Diario','Semanal'):raise ValueError('Formato o período inválido.')
            raw=build_pdf(data,cut,period) if fmt=='pdf' else build_excel(data,cut,period)
            result={'id':action['id'],'ok':True,'message':'Informe generado.','download':{'name':f'Informe_ITO_{period}_{cut}.{fmt}','mime':'application/pdf' if fmt=='pdf' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','base64':base64.b64encode(raw).decode()}}
        else:result={'id':action['id'],'ok':True,'message':apply_action(seed,db,action)}
    except Exception as error:result={'id':action['id'],'ok':False,'message':str(error)}
    st.session_state.result=result
    st.rerun()
