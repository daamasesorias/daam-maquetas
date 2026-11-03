from pathlib import Path
import io,base64
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from data_model import load_master,read_state,apply_action,download_attachment,SCHEMA
from reports import build_pdf,build_excel
ROOT=Path(__file__).parent
st.set_page_config(page_title='DaAm · Inspección Técnica y Calidad',page_icon='🏗️',layout='wide',initial_sidebar_state='collapsed')
st.markdown('<style>.block-container{padding:0!important;max-width:100%!important}header[data-testid="stHeader"]{display:none}[data-testid="stAppViewContainer"]{background:#eaf0f7}</style>',unsafe_allow_html=True)
component=components.declare_component('daam_calidad_v7',path=str(ROOT/'interfaz'))
try:
 seed=load_master(ROOT/'maestro_calidad.xlsx');db=ROOT/'registros_calidad_v7.sqlite3';data=read_state(seed,db)
 data['documentPreviews']={}
 for document in data['Documentos']:
  preview=ROOT/'interfaz/documentos/vistas'/(document['ID']+'.png')
  if preview.is_file():data['documentPreviews'][document['ID']]='data:image/png;base64,'+base64.b64encode(preview.read_bytes()).decode()
 data['embeddedEvidence']={}
 for id in ('F05','F07'):
  ev=next((e for e in data['Evidencias'] if e['ID']==id),None)
  if ev and (ROOT/'interfaz'/ev['Archivo']).is_file():data['embeddedEvidence'][id]='data:image/png;base64,'+base64.b64encode((ROOT/'interfaz'/ev['Archivo']).read_bytes()).decode()
except Exception as e:st.error('No fue posible cargar la obra: '+str(e));st.stop()
a=component(data=data,result=st.session_state.get('result',{}),key='calidad_v7')
if a and a.get('id')!=st.session_state.get('last_action'):
 st.session_state.last_action=a.get('id')
 try:
  download=None;kind=a.get('kind')
  if kind=='template':
   buf=io.BytesIO()
   with pd.ExcelWriter(buf,engine='openpyxl') as w:
    for sheet,cols in SCHEMA.items():pd.DataFrame(data[sheet],columns=cols).to_excel(w,sheet_name=sheet,index=False)
   raw=buf.getvalue();name='consolidado_calidad.xlsx';mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';msg='Consolidado preparado.'
  elif kind in ('download','preview'):
   name,mime,raw=download_attachment(db,a.get('document'));ext={'application/pdf':'.pdf','image/png':'.png','image/jpeg':'.jpg','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':'.xlsx'}[mime]
   if not name.lower().endswith(ext):name+=ext
   msg='Archivo preparado.'
  elif kind=='report':
   fmt=a.get('format')
   if fmt not in ('pdf','xlsx'):raise ValueError('Formato inválido.')
   raw=build_pdf(data) if fmt=='pdf' else build_excel(data);name='Informe_general_calidad_'+data['obra']['Fecha_corte']+'.'+fmt;mime='application/pdf' if fmt=='pdf' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';msg='Informe general generado.'
  else:msg=apply_action(seed,db,a)
  if kind in ('template','download','report'):download=dict(name=name,mime=mime,base64=base64.b64encode(raw).decode())
  result=dict(id=a['id'],ok=True,message=msg,download=download)
  if kind=='preview':result['preview']=dict(name=name,mime=mime,base64=base64.b64encode(raw).decode())
 except Exception as e:result=dict(id=a.get('id'),ok=False,message=str(e))
 st.session_state.result=result;st.rerun()
