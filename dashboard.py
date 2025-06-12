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

# Filtro por manutenção requerida
    with st.sidebar.expander('Manutenção Requerida'):
        manut_opcoes = dados['maintenance_required'].unique()
        f_manut = st.multiselect('Manutenção Requerida', manut_opcoes, default=manut_opcoes)

        dados = dados[dados['maintenance_required'].isin(f_manut)]
    
# Filtro por máquina    
    with st.sidebar.expander('Máquinas'): 
        maquina = dados['machine'].unique()
        f_maquinas = st.multiselect('Selecione as Máquinas', maquina, default=maquina)    
    
    dados = dados[
        (dados['machine'].isin(f_maquinas)) &
        (dados['machine_status'].isin(f_status)) &
        (dados['maintenance_required'].isin(f_manut)) &
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

#-------- TIPO DE FALHA -----
# Soma a quantidade de máquinas por failure_type
maquinas_por_failure = dados.groupby('failure_type')['machine'].nunique().reset_index()
maquinas_por_failure.rename(columns={'machine': 'quantidade_maquinas'}, inplace=True)

# Calcula o percentual de máquinas por failure_type
total_maquinas_failure = dados['machine'].nunique()
maquinas_por_failure['percentual'] = (maquinas_por_failure['quantidade_maquinas'] / total_maquinas_failure) * 100



#----- TIPO DE FALHA -----
# Quantidade de cada tipo de falha
quantidade_falhas = dados['failure_type'].value_counts().reset_index()
quantidade_falhas.columns = ['Tipo de Falha', 'Quantidade']

# Calcula o percentual de ocorrências por tipo de falha
quantidade_falhas['percentual'] = (quantidade_falhas['Quantidade'] / quantidade_falhas['Quantidade'].sum()) * 100



#----- STATUS DA MÁQUINA -----
# Soma a quantidade de máquinas por machine_status
maquinas_por_status = dados.groupby('machine_status')['machine'].nunique().reset_index()
maquinas_por_status.rename(columns={'machine': 'quantidade_maquinas'}, inplace=True)

# Calcula o percentual de máquinas por status
total_maquinas = dados['machine'].nunique()
maquinas_por_status['percentual'] = (maquinas_por_status['quantidade_maquinas'] / total_maquinas) * 100

#---- VIBRAÇÃO -----
# Agrupa os dados por máquina e calcula a média de vibração
maquina_vibracao = dados.groupby('machine')['vibration'].mean().reset_index()
maquina_vibracao.rename(columns={'vibration': 'media_vibracao'}, inplace=True)

# ----------------------------------------
#  GRAFICOS
# ----------------------------------------
# Gráfico de barras da contagem de máquinas por status
fig_status_count = dados['machine_status'].value_counts().reset_index()

#----- TEMPERATURA -----
fig_temp1 = px.bar(maquina_temperatura, x='machine', y=['temperatura_maxima', 'temperatura_minima'],
                   title='Temperatura Máxima e Mínima por Máquina')

fig_temp2 = px.pie(dados, names='machine', values='temperature',
                   title='Distribuição de Temperatura por Máquina')

# Gráficos de linha para cada máquina mostrando variação de temperatura e umidade
line_charts = []
for maquina_nome in dados['machine'].unique():
    df_maquina = dados[dados['machine'] == maquina_nome]
    fig = px.line(
        df_maquina,
        x='data',
        y=['temperature', 'humidity'],
        title=f'Variação de Temperatura e Umidade - {maquina_nome}',
        labels={'value': 'Valor', 'variable': 'Variável', 'data': 'Data'}
    )
line_charts.append((maquina_nome, fig))
    

#----- ENERGIA -----
fig_energy = px.area(dados, x='data', y='energy_consumption', color='machine',
                     labels={
                         'energy_consumption': 'Consumo de Energia (kWh)', 'data': 'Data'},
                     title='Consumo de Energia por Máquina')

fig_energy_bar = px.bar(
                        maquina_consumo_energia,
                        x='machine',
                        y='consumo_medio_energia',
                        text_auto=True,
                        title='Consumo Médio de Energia por Máquina',
                        labels={'machine': 'Máquina', 'consumo_medio_energia': 'Consumo Médio de Energia (kWh)'}
                    )


#------ STATUS DA MÁQUINA -----
fig_status_bar = px.bar(
                        maquinas_por_status,
                        x='machine_status',
                        y='quantidade_maquinas',
                        text_auto=True,
                        title='Quantidade de Máquinas por Status',
                        labels={'machine_status': 'Status da Máquina', 'quantidade_maquinas': 'Quantidade de Máquinas'}
                    )

# Gráfico de pizza da distribuição de máquinas por status
fig_status_pie = px.pie(maquinas_por_status, names='machine_status', values='percentual',
                       title='Distribuição de Máquinas por Status',
                       labels={'machine_status': 'Status da Máquina', 'percentual': 'Percentual de Máquinas'})



#---- TIPO DE FALHA -----
# Gráfico de barras para quantidade de cada tipo de falha
fig_falhas_bar = px.bar(
                        quantidade_falhas,
                        x='Tipo de Falha',
                        y='Quantidade',
                        text_auto=True,
                        title='Quantidade de Ocorrências por Tipo de Falha',
                        labels={'Tipo de Falha': 'Tipo de Falha', 'Quantidade': 'Quantidade'}
                    )

# Gráfico de pizza para percentual de ocorrências por tipo de falha
fig_falhas_pie = px.pie(
                        quantidade_falhas,
                        names='Tipo de Falha',
                        values='percentual',
                        title='Percentual de Ocorrências por Tipo de Falha',
                        labels={'Tipo de Falha': 'Tipo de Falha', 'percentual': 'Percentual'}
                    )

# Gráfico Sunburst para tipo de falha por máquina
fig_falhas_sunburst = px.sunburst(
                        dados,
                        path=['failure_type', 'machine'],
                        values=None,
                        title='Hierarquia de Tipos de Falha por Máquina',
                        color='failure_type'
                    )

#----- VIBRAÇÃO -----
# Gráfico de barras horizontais para quantidade de máquinas por status
fig_vibracao_bar = px.bar(
                        maquinas_por_status,
                        x='quantidade_maquinas',
                        y='machine_status',
                        text_auto=True,
                        title='Quantidade de Máquinas por Status',      
                        labels={'machine_status': 'Status da Máquina', 'quantidade_maquinas': 'Quantidade de Máquinas'}
                    )

                    # Gráfico de barras horizontais da média de vibração por máquina
fig_vibracao_h_bar = px.bar(
                        maquina_vibracao,
                        x='media_vibracao',
                        y='machine',
                        orientation='h',
                        text_auto=True,
                        title='Média de Vibração por Máquina',
                        labels={'machine': 'Máquina', 'media_vibracao': 'Média de Vibração'}
                    )

# ----------------------------------------
# DASHBOARD
# ----------------------------------------
# ---------- TITULO
st.title("DASHBOARD A2")
#--- Criação das abas
tab_home, tabela_Geral, temperatura, energia, tipo_falha, vibracao = st.tabs(
    ["Home", "Tabela", "Temperatura", "Consumo de Energia", "Tipo de Falha","Vibração"])


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
   
    for maquina_nome, fig in line_charts:
        st.plotly_chart(fig, use_container_width=True)
        
        
    exibir_corr = dados[['humidity', 'temperature']].corr().iloc[0, 1]
    st.sidebar.markdown(f"**Correlação entre Umidade e Temperatura:** {exibir_corr:.2f}")
        

with energia:
    st.subheader("Energia por Máquina")
    
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_energy)
    with col2:
        st.plotly_chart(fig_energy_bar)

with tipo_falha:
    st.subheader("tipo de falha")
    
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_falhas_bar)
    with col2:
        st.plotly_chart(fig_falhas_pie)    
  
        
with vibracao:
    st.subheader("Vibracao por Máquina")
    st.plotly_chart(fig_falhas_sunburst)
    st.plotly_chart(fig_vibracao_h_bar)
        
  
