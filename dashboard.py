import streamlit as st
import pandas as pd
import plotly.express as px

# -------- CONFIGURAÇÃO DE PAGINA --------
st.set_page_config(layout="wide")
# ----------------------------------------

# -------- CARREGAMENTO DE DADOS --------
dados = pd.read_csv("smart_manufacturing_data.csv")


# ------------------------- FUNÇÕES -------------------
# Função para gerar relatório de qualidade dos dados
def relatorio_qualidade(df):
    relatorio = pd.DataFrame({
        'Coluna': df.columns,
        'Tipo': df.dtypes,
        'Valores Nulos': df.isnull().sum(),
        'Valores Únicos': df.nunique(),
        'Primeiros Valores': [df[col].dropna().unique()[:5] for col in df.columns]
    })
    return relatorio


# --------------- TRATAMENTO DE DADOS ---------------
# Cria colunas separadas para data e hora a partir do timestamp
dados['data'] = pd.to_datetime(dados['timestamp']).dt.date
dados['hora'] = pd.to_datetime(dados['timestamp']).dt.time
# Remove a coluna timestamp
dados = dados.drop(columns=['timestamp'])


# Remover dados cujo o nome da máquina é nulo
dados = dados[dados['machine'].notnull()]


# Remover a features downtime_risk pq tem mais de 40% de valores nulos
dados = dados.drop('downtime_risk', axis=1)

# separamos as features numéricas em uma tupla e depois colocamos um laço para substituir os valores nulos pelas medianas de cada máquina
numerical_cols = ['temperature', 'vibration',
                  'humidity', 'pressure', 'energy_consumption']
for col in numerical_cols:
    dados[col] = dados.groupby('machine')[col].transform(
        lambda x: x.fillna(x.median()))


# Substituir valores nulos da feature machine_status por 'Idle'
dados['machine_status'] = dados['machine_status'].fillna('Idle')

# Substituir valores nulos da feature maintenance_required por 'No'
dados['maintenance_required'] = dados['maintenance_required'].fillna('No')

# relatorio = relatorio_qualidade(dados)
# print(relatorio)


# ----------------------------------------
# SIDEBAR
# ----------------------------------------
st.sidebar.title("Filtros")

with st.sidebar:

# Filtro por status da máquina
    with st.sidebar.expander('Status da Máquina'):
        status = dados['machine_status'].unique()
        f_status = st.multiselect('Selecione o Status', status, default=status)

   
# Filtro por período de data
    f_datini = dados['data'].min()
    f_datfim = dados['data'].max()
    f_periodo = st.slider('Selecione o Período', f_datini, f_datfim, (f_datini, f_datfim))
    
# Filtro por máquina    
    with st.sidebar.expander('Máquinas'): 
        maquina = dados['machine'].unique()
        f_maquinas = st.multiselect('Selecione as Máquinas', maquina, default=maquina)    
    
    dados = dados[
        (dados['machine'].isin(f_maquinas)) &
        (dados['machine_status'].isin(f_status)) &
        (dados['data'] >= f_periodo[0]) &
        (dados['data'] <= f_periodo[1])
    ]

    # Exibir resumo dos filtros aplicados
   # st.sidebar.markdown("### Resumo dos Filtros")
   # st.sidebar.write(f"Máquinas selecionadas: {', '.join(f_maquinas)}")
   # st.sidebar.write(f"Status selecionados: {', '.join(f_status)}")
   # st.sidebar.write(f"Período: {f_periodo[0]} até {f_periodo[1]}")
 

# ----------------------------------------
# TABELAS
# ----------------------------------------

#------ Manutenção Requerida ------
maq_manut_requerida = dados[dados['maintenance_required']
                            == 'Yes']['machine'].unique()

#------ Temperatura Máxima e Mínima por Máquina ------
maquina_temperatura = dados.groupby('machine')['temperature'].agg([
    'max', 'min']).reset_index()
maquina_temperatura.rename(
    columns={'max': 'temperatura_maxima', 'min': 'temperatura_minima'}, inplace=True)

#------ consumo de energia por máquina ------
maquina_consumo_energia = dados.groupby('machine')['energy_consumption'].mean().reset_index()
maquina_consumo_energia.rename(columns={'energy_consumption': 'consumo_medio_energia'}, inplace=True)



# ----------------------------------------
#  GRAFICOS
# ----------------------------------------
# Gráfico de barras da contagem de máquinas por status
fig_status_count = dados['machine_status'].value_counts().reset_index()


fig_temp1 = px.bar(maquina_temperatura, x='machine', y=['temperatura_maxima', 'temperatura_minima'],
                   title='Temperatura Máxima e Mínima por Máquina')

fig_temp2 = px.pie(dados, names='machine', values='temperature',
                   title='Distribuição de Temperatura por Máquina')

fig_energy = px.area(dados, x='data', y='energy_consumption', color='machine',
                     labels={
                         'energy_consumption': 'Consumo de Energia (kWh)', 'data': 'Data'},
                     title='Consumo de Energia por Máquina')

fig_energy_bar = px.bar(
                        maquina_consumo_energia,
                        x='machine',
                        y='consumo_medio_energia',
                        title='Consumo Médio de Energia por Máquina',
                        labels={'machine': 'Máquina', 'consumo_medio_energia': 'Consumo Médio de Energia (kWh)'}
                    )

# ----------------------------------------
# DASHBOARD
# ----------------------------------------
# ---------- TITULO
st.title("DASHBOARD A2")

tab_home, tabela_Geral, temperatura, energia, status = st.tabs(
    ["Home", "Tabela", "Temperatura", "Energia", "Status"])

with tab_home:
    st.subheader("Bem-vindo ao Dashboard A2")
    st.write(
        "Este dashboard apresenta uma visão geral dos dados de manufatura inteligente.")
    st.write("Use os filtros na barra lateral para explorar os dados.")


with tabela_Geral:
    st.subheader("Tabela Geral")
    st.dataframe(dados)

with temperatura:
    st.subheader("Temperatura por Máquina")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_temp1)
    with col2:
        st.plotly_chart(fig_temp2)

with energia:
    st.subheader("Energia por Máquina")
    
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_energy)
    with col2:
        st.plotly_chart(fig_energy_bar)
        
    
    
