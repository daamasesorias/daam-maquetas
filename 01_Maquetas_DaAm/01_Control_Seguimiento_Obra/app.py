from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="DaAm · Control y seguimiento de obra", page_icon="🏗️", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
.block-container {padding: 0 !important; max-width: 100% !important;}
header[data-testid="stHeader"] {display: none;}
[data-testid="stAppViewContainer"] {background: #edf2f8;}
</style>""", unsafe_allow_html=True)
interfaz = components.declare_component("daam_control", path=str(Path(__file__).parent / "interfaz"))
interfaz(key="daam_control")
