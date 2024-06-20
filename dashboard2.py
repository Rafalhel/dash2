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
    df['[CHART] Date of First Response'] = pd.to_datetime(df['[CHART] Date of First Response'], format='%d/%b/%y %I:%M %p', errors='coerce')

    # Filtrando registros inválidos
    df = df[df['Criado'].notnull() & df['Resolvido'].notnull() & (df['Resolvido'] >= df['Criado'])]

    df['Tempo da Primeira Resposta'] = (df['[CHART] Date of First Response'] - df['Criado']).dt.total_seconds() / (3600 * 24)  # Convertendo para dias
    df['Tempo da Primeira Resposta'] = df['Tempo da Primeira Resposta'].fillna(0).astype(int)  # Substituindo NaNs por 0 e convertendo para inteiros
    df['Tempo de Solução'] = (df['Resolvido'] - df['Criado']).dt.total_seconds() / (3600 * 24)  # Convertendo para dias
    df['Tempo de Solução'] = df['Tempo de Solução'].fillna(0).astype(int)  # Substituindo NaNs por 0 e convertendo para inteiros
    return df

# Carregar e processar o arquivo backlog
def load_backlog_data(file_path):
    xls = pd.ExcelFile(file_path)
    sheets = []
    for sheet_name in xls.sheet_names:
        sheet = pd.read_excel(xls, sheet_name)
        sheets.append(sheet)
    backlog_data = pd.concat(sheets, ignore_index=True)
    return backlog_data

# Iniciar a aplicação Streamlit
st.title('Dashboard de Análise de Dados do Jira')

# Carregar os dados
jira_data = load_html_data('Jira (3).html')
backlog_data = load_backlog_data('backlog.xlsx')

# Exibir colunas do backlog para depuração
st.write('Colunas disponíveis no backlog:', backlog_data.columns.tolist())

# Combinando dados do backlog com dados do Jira
if '#JIRA\nCard' in backlog_data.columns:
    jira_data = jira_data.merge(backlog_data, left_on='Chave', right_on='#JIRA\nCard', how='left')
else:
    st.error("A coluna '#JIRA\nCard' não está presente no backlog.")
jira_data.to_csv('jira_data.csv', index=False, encoding='utf-8', sep=';')
# Filtros no sidebar
st.sidebar.title('Filtros')
tipo_selecionado_sidebar = st.sidebar.multiselect('Selecione o Tipo de Item (para gráficos)', jira_data['Tipo de item'].unique(), default=jira_data['Tipo de item'].unique())
prioridade_selecionada = st.sidebar.multiselect('Selecione a Prioridade', jira_data['Prioridade'].unique(), default=jira_data['Prioridade'].unique())

# Filtro para selecionar média ou total
metrica_selecionada = st.sidebar.radio('Selecione a Métrica', ['Média', 'Total'])

# df_filtrado = jira_data[(jira_data['Tipo de item'].isin(tipo_selecionado_sidebar)) & (jira_data['Prioridade'].isin(prioridade_selecionada))]
df_filtrado = jira_data[jira_data['Prioridade'].isin(prioridade_selecionada)]

df_filtrado = df_filtrado[df_filtrado['Tipo de item'].isin(['Bug', 'Melhoria'])]

# Gráfico de Tempo da Primeira Resposta por Mês
st.write('## Tempo da Primeira Resposta por Mês (apenas Bug e Melhoria)')

df_filtrado['Mês'] = df_filtrado['Criado'].dt.to_period('M').astype(str)

if metrica_selecionada == 'Média':
    resposta_por_mes = df_filtrado.groupby(['Mês', 'Tipo de item', 'Prioridade'])['Tempo da Primeira Resposta'].mean().reset_index()
    fig_resposta = px.line(resposta_por_mes, x='Mês', y='Tempo da Primeira Resposta', color='Tipo de item', title='Tempo da Primeira Resposta por Mês (Média em dias)',color_discrete_map={'Melhoria': 'blue', 'Bug': 'red'})
else:
    resposta_por_mes = df_filtrado.groupby(['Mês', 'Tipo de item', 'Prioridade'])['Tempo da Primeira Resposta'].sum().reset_index()
    fig_resposta = px.line(resposta_por_mes, x='Mês', y='Tempo da Primeira Resposta', color='Tipo de item', title='Tempo da Primeira Resposta por Mês (Total em dias)',color_discrete_map={'Melhoria': 'blue', 'Bug': 'red'})

st.plotly_chart(fig_resposta)

# Gráfico de Tempo de Solução por Mês
st.write('## Tempo de Solução por Mês')

if metrica_selecionada == 'Média':
    solucao_por_mes = df_filtrado.groupby(['Mês', 'Tipo de item', 'Prioridade'])['Tempo de Solução'].mean().reset_index()
    fig_solucao = px.line(solucao_por_mes, x='Mês', y='Tempo de Solução', color='Tipo de item', title='Tempo de Solução por Mês (Média em dias)',color_discrete_map={'Melhoria': 'blue', 'Bug': 'red'})
else:
    solucao_por_mes = df_filtrado.groupby(['Mês', 'Tipo de item', 'Prioridade'])['Tempo de Solução'].sum().reset_index()
    fig_solucao = px.line(solucao_por_mes, x='Mês', y='Tempo de Solução', color='Tipo de item', title='Tempo de Solução por Mês (Total em dias)',color_discrete_map={'Melhoria': 'blue', 'Bug': 'red'})

st.plotly_chart(fig_solucao)

# Filtro de Tipo de Item para Tabela
tipo_selecionado_tabela = st.selectbox('Selecione o Tipo de Item (para tabela)', jira_data['Tipo de item'].unique())

# Verificar se as colunas estão presentes antes de exibir a tabela
colunas_tabela = ['Chave', 'Status', 'Resumo', 'Descrição', 'Análise x Documentação/Desenvolvimento/QA/Entrega', 'Responsável']
colunas_presentes = [col for col in colunas_tabela if col in jira_data.columns]

if len(colunas_presentes) < len(colunas_tabela):
    st.warning("Algumas colunas não estão presentes nos dados combinados: " + str([col for col in colunas_tabela if col not in colunas_presentes]))

# Tabela com filtro de Tipo de Item
st.write('## Tabela de Itens Filtrados')
df_tabela_filtrado = jira_data[jira_data['Tipo de item'] == tipo_selecionado_tabela]
st.dataframe(df_tabela_filtrado[colunas_presentes])

# Gráfico de Barras da Quantidade de Bugs e Melhorias por Mês
st.write('## Quantidade de Bugs e Melhorias sem Data Pré ou Data Produção (Gráfico de Barras)')

df_filtrado_sem_data = df_filtrado[(df_filtrado['Data Pré'].isnull()) & (df_filtrado['Data Produção'].isnull())]
quantidade_por_mes_sem_data = df_filtrado_sem_data.groupby(['Mês', 'Tipo de item']).size().reset_index(
    name='Quantidade')

fig_barras_sem_data = px.bar(quantidade_por_mes_sem_data, x='Mês', y='Quantidade', color='Tipo de item',
                             barmode='group',
                             title='Quantidade de Bugs e Melhorias sem Data Pré ou Data Produção por Mês',
                             color_discrete_map={'Melhoria': 'blue', 'Bug': 'red'})

st.plotly_chart(fig_barras_sem_data)

# Gráfico de Barras da Quantidade de Bugs e Melhorias com Data Pré ou Data Produção
st.write('## Quantidade de Bugs e Melhorias com Data Pré ou Data Produção (Gráfico de Barras)')

df_filtrado_data = df_filtrado[(df_filtrado['Data Pré'].notnull()) | (df_filtrado['Data Produção'].notnull())]
quantidade_por_mes_data = df_filtrado_data.groupby(['Mês', 'Tipo de item']).size().reset_index(name='Quantidade')

fig_barras_data = px.bar(quantidade_por_mes_data, x='Mês', y='Quantidade', color='Tipo de item',
                         barmode='group', title='Quantidade de Bugs e Melhorias com Data Pré ou Data Produção por Mês',
                         color_discrete_map={'Melhoria': 'blue', 'Bug': 'red'})
st.plotly_chart(fig_barras_data)

# Gráfico de Linha do Tempo de Versões
st.write('## Linha do Tempo de Versões')

# Filtrar as colunas necessárias do backlog
df_versoes = jira_data[['Versão', 'Criado', 'Data Pré']]
df_versoes = df_versoes.dropna(subset=['Versão', 'Criado', 'Data Pré'])

# Convertendo colunas para datetime
df_versoes['Criado'] = pd.to_datetime(df_versoes['Criado'], errors='coerce')
df_versoes['Data Pré'] = pd.to_datetime(df_versoes['Data Pré'], errors='coerce')

# Filtrar versões únicas
df_versoes = df_versoes.groupby('Versão').agg({'Criado': 'min', 'Data Pré': 'max'}).reset_index()

fig_versoes = px.timeline(df_versoes, x_start='Criado', x_end='Data Pré', y='Versão', title='Linha do Tempo das Versões')
st.plotly_chart(fig_versoes)
