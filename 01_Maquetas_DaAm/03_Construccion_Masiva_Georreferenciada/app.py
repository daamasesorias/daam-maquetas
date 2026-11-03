from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from data_model import load_master

ROOT = Path(__file__).parent
st.set_page_config(page_title="DaAm · Construcción Masiva Georreferenciada", page_icon="🏘️", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>.block-container{padding:0!important;max-width:100%!important}header[data-testid="stHeader"]{display:none}[data-testid="stAppViewContainer"]{background:#eaf0f7}</style>""", unsafe_allow_html=True)
component = components.declare_component("daam_masiva", path=str(ROOT / "interfaz"))
try:
    data = load_master(ROOT / "maestro_construccion_masiva.xlsx")
except Exception as error:
    st.error(f"No fue posible leer el Excel maestro: {error}")
    st.stop()
component(data=data, key="daam_masiva")
