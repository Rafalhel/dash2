import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from bs4 import BeautifulSoup
import locale


def replace_month(date_str):
    # Função para converter datas com dateutil, que é mais robusta para diferentes formatos
    month_map = {
        'jan': 'Jan', 'fev': 'Feb', 'mar': 'Mar', 'abr': 'Apr', 'mai': 'May', 'jun': 'Jun',
        'jul': 'Jul', 'ago': 'Aug', 'set': 'Sep', 'out': 'Oct', 'nov': 'Nov', 'dez': 'Dec'
    }
    for pt, en in month_map.items():
        date_str = date_str.replace(pt, en)
    return date_str



# Load the HTML file
with open('Jira (3).html', 'r', encoding='utf-8') as file:
    html_content = file.read()

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

# Extract the table headers
table = soup.find('table', {'id': 'issuetable'})
headers = [header.text.strip() for header in table.find_all('th')]

# Extract the table rows
rows = []
for row in table.find('tbody').find_all('tr'):
    cells = row.find_all('td')
    row_data = [cell.text.strip() for cell in cells]
    rows.append(row_data)

# Create a DataFrame from the extracted data
df = pd.DataFrame(rows, columns=headers)
df['Criado'] = df['Criado'].apply(replace_month)
df['Criado'] = pd.to_datetime(df['Criado'], format='%d/%b/%y %I:%M %p', errors='coerce')

# Selecionar as colunas relevantes
# Criando uma cópia do DataFrame para evitar SettingWithCopyWarning
df_selected = df[['Pai', 'Tipo de item', 'Status', 'Responsável', 'Criado']].copy()
# Aplicar a função de substituição e depois converter para datetime
df_selected['Criado'] = pd.to_datetime(df_selected['Criado'], format='%d/%b/%y %I:%M %p', errors='coerce')


# 1. Gráfico de barras: Quantidade de itens por "Tipo de Item" e "Status" para cada "Pai" sem barras de erro

item_status_count = df_selected.groupby(['Pai', 'Tipo de item', 'Status']).size().reset_index(name='Count')

plt.figure(figsize=(12, 6))
bar_plot = sns.barplot(x='Pai', y='Count', hue='Status', data=item_status_count, errorbar=None)

# Adicionando o valor total acima de cada barra
for p in bar_plot.patches:
    bar_plot.annotate(format(p.get_height(), '.1f'),
                      (p.get_x() + p.get_width() / 2., p.get_height()),
                      ha = 'center', va = 'center',
                      xytext = (0, 9),
                      textcoords = 'offset points')

plt.title('Quantidade de itens por Tipo de Item e Status para cada Pai')
plt.xlabel('Módulo')
plt.ylabel('Quantidade de Itens')
plt.legend(title='Status')
plt.xticks(rotation=90)
plt.tight_layout()
plt.savefig('BarPlot_Pai_Item_Status.png')
plt.close()

import plotly.express as px
fig1 = px.bar(item_status_count, x='Pai', y='Count', color='Status',
             title='Quantidade de itens por Tipo de Item e Status para cada Pai',
             labels={'Count': 'Quantidade de Itens', 'Pai': 'Módulo', 'Status': 'Status'})
fig1.show()

# Plot 2: Stacked bar plot
plt.figure(figsize=(12, 6))

responsible_item_count = df.groupby(['Responsável', 'Tipo de item']).size().reset_index(name='Count')
stacked_bar = sns.barplot(x='Responsável', y='Count', hue='Tipo de item', data=responsible_item_count)

# Adicionando o valor total acima de cada barra
for p in stacked_bar.patches:
    stacked_bar.annotate(format(p.get_height(), '.1f'),
                         (p.get_x() + p.get_width() / 2., p.get_height()),
                         ha = 'center', va = 'center',
                         xytext = (0, 9),
                         textcoords = 'offset points')

plt.title('Distribuição de Responsável por Tipo de Item')
plt.xlabel('Responsável')
plt.ylabel('Quantidade de Itens')
plt.legend(title='Tipo de Item')
plt.xticks(rotation=90)
plt.tight_layout()
plt.savefig('StackedBarPlot_Responsavel_Item.png')
plt.close()

# Preparando dados agregados para o gráfico empilhado
responsible_item_count = df_selected.groupby(['Responsável', 'Tipo de item']).size().reset_index(name='Count')

# Gráfico de barras empilhadas com Plotly
fig2 = px.bar(responsible_item_count, x='Responsável', y='Count', color='Tipo de item',
              title='Distribuição de Responsável por Tipo de Item',
              labels={'Count': 'Quantidade de Itens', 'Responsável': 'Responsável', 'Tipo de item': 'Tipo de Item'})
fig2.show()



# Plot 3: Timeline

# Loop through each unique item type and plot
# Plotar a linha do tempo separada por "Tipo de Item"
# Filtrar os dados válidos de criação
df_filtered = df_selected.dropna(subset=['Criado'])
locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
plt.figure(figsize=(12, 6))

for item_type in df_filtered['Tipo de item'].unique():
    series = df_filtered[df_filtered['Tipo de item'] == item_type].set_index('Criado').resample('ME').size()
    line_plot = series.plot(marker='o', label=item_type)

    # Adicionando o valor total em cada ponto da linha do tempo
    for (x, y) in series.items():
        plt.text(x, y, str(y), color='black', ha='right', va='bottom')

plt.title('Linha do Tempo de Itens Criados por Tipo de Item')
plt.xlabel('Data')
plt.ylabel('Quantidade de Itens Criados')
plt.legend(title='Tipo de Item')
plt.grid(True)
plt.tight_layout()
plt.savefig('Timeline_Creation_Items.png')

# Filtrar os dados válidos de criação e agrupar por tipo e mês
df_filtered = df_selected.dropna(subset=['Criado'])
df_timeline = df_filtered.groupby([pd.Grouper(key='Criado', freq='ME'), 'Tipo de item']).size().reset_index(name='Count')

# Gráfico de linha do tempo com Plotly
fig3 = px.line(df_timeline, x='Criado', y='Count', color='Tipo de item',
               title='Linha do Tempo de Itens Criados por Tipo de Item',
               labels={'Criado': 'Data', 'Count': 'Quantidade de Itens Criados', 'Tipo de item': 'Tipo de Item'})
fig3.update_xaxes(dtick="M1", tickformat="%b\n%Y")  # Formatação do eixo X para mostrar o mês e o ano
fig3.show()
#
# import plotly.express as px
#
# # Supondo que df_filtered já esteja preparado e configurado
# df_filtered = df_selected.dropna(subset=['Criado'])
#
# # Criar uma coluna com contagem agregada por mês e tipo de item
# df_plot = df_filtered.groupby([pd.Grouper(key='Criado', freq='ME'), 'Tipo de item']).size().reset_index(name='Count')
#
# # Criar o gráfico de linha com Plotly
# fig = px.line(df_plot, x='Criado', y='Count', color='Tipo de item',
#               title='Linha do Tempo de Itens Criados por Tipo de Item',
#               labels={'Criado': 'Data', 'Count': 'Quantidade de Itens Criados', 'Tipo de item': 'Tipo de Item'})
#
# # Mostrar o gráfico
# fig.show()
# # Supondo que df_selected já esteja preparado e configurado
# df_selected.rename(columns={'Pai': 'Módulo'}, inplace=True)
# df_selected.to_excel('dados_para_graficos.xlsx', index=False)



