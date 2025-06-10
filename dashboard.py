import streamlit as st
import pandas as pd
import plotly.express as px

# -------- CONFIGURAÇÃO DE PAGINA --------
st.set_page_config(layout="wide")
# ----------------------------------------

# -------- CARREGAMENTO DE DADOS --------
df = pd.read_csv("smart_manufacturing_data.csv")

# ----------------------------------------
# SIDEBAR
# ----------------------------------------
st.title("DASHBOARD A2")



