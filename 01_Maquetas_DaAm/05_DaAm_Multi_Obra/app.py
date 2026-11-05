from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from data_model import load_master
ROOT=Path(__file__).parent
st.set_page_config(page_title='DaAm · Multi Obra',page_icon='🏗️',layout='wide',initial_sidebar_state='collapsed')
st.markdown('<style>.block-container{padding:0!important;max-width:100%!important}header[data-testid="stHeader"]{display:none}[data-testid="stAppViewContainer"]{background:#eaf0f7}</style>',unsafe_allow_html=True)
component=components.declare_component('daam_multi_obra',path=str(ROOT/'interfaz'))
@st.cache_data(show_spinner=False,max_entries=3)
def read_data(path,modified,size):return load_master(path)
try:
 master=ROOT/'maestro_multi_obra.xlsx';stat=master.stat();data=read_data(str(master),stat.st_mtime_ns,stat.st_size)
except Exception as error:
 st.error('No fue posible cargar la cartera: '+str(error));st.stop()
component(data=data,key='daam_multi_obra')
