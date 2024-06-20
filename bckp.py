import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import plotly.express as px


# Função para converter datas
def replace_month(date_str):
    month_map = {
        'jan': 'Jan', 'fev': 'Feb', 'mar': 'Mar', 'abr': 'Apr', 'mai': 'May', 'jun': 'Jun',
        'jul': 'Jul', 'ago': 'Aug', 'set': 'Sep', 'out': 'Oct', 'nov': 'Nov', 'dez': 'Dec'
    }
    for pt, en in month_map.items():
        date_str = date_str.replace(pt, en)
    return date_str


# Carregar e processar o arquivo HTML
def load_html_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', {'id': 'issuetable'})
    headers = [header.text.strip() for header in table.find_all('th')]
    rows = [[cell.text.strip() for cell in row.find_all('td')] for row in table.find('tbody').find_all('tr')]
    df = pd.DataFrame(rows, columns=headers)
    df['Criado'] = df['Criado'].apply(replace_month)
    df['Resolvido'] = df['Resolvido'].apply(replace_month)
    df['[CHART] Date of First Response'] = df['[CHART] Date of First Response'].apply(replace_month)
    df['Criado'] = pd.to_datetime(df['Criado'], format='%d/%b/%y %I:%M %p', errors='coerce')
    df['Resolvido'] = pd.to_datetime(df['Resolvido'], format='%d/%b/%y %I:%M %p', errors='coerce')
    df['[CHART] Date of First Response'] = pd.to_datetime(df['[CHART] Date of First Response'],
                                                          format='%d/%b/%y %I:%M %p', errors='coerce')

    # Filtrando registros inválidos
    df = df[df['Criado'].notnull() & df['Resolvido'].notnull() & (df['Resolvido'] >= df['Criado'])]

    df['Tempo da Primeira Resposta'] = (df['[CHART] Date of First Response'] - df['Criado']).dt.total_seconds() / (
                3600 * 24)  # Convertendo para dias
    df['Tempo da Primeira Resposta'] = df['Tempo da Primeira Resposta'].fillna(0).astype(
        int)  # Substituindo NaNs por 0 e convertendo para inteiros
    df['Tempo de Solução'] = (df['Resolvido'] - df['Criado']).dt.total_seconds() / (3600 * 24)  # Convertendo para dias
    df['Tempo de Solução'] = df['Tempo de Solução'].fillna(0).astype(
        int)  # Substituindo NaNs por 0 e convertendo para inteiros
    return df


# Iniciar a aplicação Streamlit
st.title('Dashboard de Análise de Dados do Jira')

# Carregar os dados
jira_data = load_html_data('Jira (3).html')

# Filtros no sidebar
st.sidebar.title('Filtros')
tipo_selecionado_sidebar = st.sidebar.multiselect('Selecione o Tipo de Item (para gráficos)',
                                                  jira_data['Tipo de item'].unique(),
                                                  default=jira_data['Tipo de item'].unique())
prioridade_selecionada = st.sidebar.multiselect('Selecione a Prioridade', jira_data['Prioridade'].unique(),
                                                default=jira_data['Prioridade'].unique())

# Filtro para selecionar média ou total
metrica_selecionada = st.sidebar.radio('Selecione a Métrica', ['Média', 'Total'])

df_filtrado = jira_data[
    (jira_data['Tipo de item'].isin(tipo_selecionado_sidebar)) & (jira_data['Prioridade'].isin(prioridade_selecionada))]


# Gráfico de Tempo da Primeira Resposta por Mês
st.write('## Tempo da Primeira Resposta por Mês')

df_filtrado['Mês'] = df_filtrado['Criado'].dt.to_period('M').astype(str)

if metrica_selecionada == 'Média':
    resposta_por_mes = df_filtrado.groupby(['Mês', 'Tipo de item', 'Prioridade'])[
        'Tempo da Primeira Resposta'].mean().reset_index()
    fig_resposta = px.line(resposta_por_mes, x='Mês', y='Tempo da Primeira Resposta', color='Tipo de item',
                           title='Tempo da Primeira Resposta por Mês (Média em dias)')
else:
    resposta_por_mes = df_filtrado.groupby(['Mês', 'Tipo de item', 'Prioridade'])[
        'Tempo da Primeira Resposta'].sum().reset_index()
    fig_resposta = px.line(resposta_por_mes, x='Mês', y='Tempo da Primeira Resposta', color='Tipo de item',
                           title='Tempo da Primeira Resposta por Mês (Total em dias)')

st.plotly_chart(fig_resposta)

# Gráfico de Tempo de Solução por Mês
st.write('## Tempo de Solução por Mês')

if metrica_selecionada == 'Média':
    solucao_por_mes = df_filtrado.groupby(['Mês', 'Tipo de item', 'Prioridade'])[
        'Tempo de Solução'].mean().reset_index()
    fig_solucao = px.line(solucao_por_mes, x='Mês', y='Tempo de Solução', color='Tipo de item',
                          title='Tempo de Solução por Mês (Média em dias)')
else:
    solucao_por_mes = df_filtrado.groupby(['Mês', 'Tipo de item', 'Prioridade'])['Tempo de Solução'].sum().reset_index()
    fig_solucao = px.line(solucao_por_mes, x='Mês', y='Tempo de Solução', color='Tipo de item',
                          title='Tempo de Solução por Mês (Total em dias)')

st.plotly_chart(fig_solucao)

# Filtro de Tipo de Item para Tabela
tipo_selecionado_tabela = st.selectbox('Selecione o Tipo de Item (para tabela)', jira_data['Tipo de item'].unique())

# Tabela com filtro de Tipo de Item
st.write('## Tabela de Itens Filtrados')
df_tabela_filtrado = jira_data[jira_data['Tipo de item'] == tipo_selecionado_tabela]
st.dataframe(df_tabela_filtrado[['Chave', 'Status', 'Resumo', 'Descrição']])
