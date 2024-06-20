import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from bs4 import BeautifulSoup

def extract_table_from_html(html_file):
    with open(html_file, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    table = soup.find('table', {'id': 'issuetable'})
    headers = [header.text.strip() for header in table.find_all('th')]

    rows = []
    for row in table.find('tbody').find_all('tr'):
        cells = row.find_all('td')
        row_data = [cell.text.strip() for cell in cells]
        rows.append(row_data)

    df = pd.DataFrame(rows, columns=headers)
    return df

def prepare_dataframe(df):
    df_selected = df[['Pai', 'Tipo de item']].copy()
    return df_selected

def plot_item_status_count(df_selected):
    item_status_count = df_selected.groupby(['Pai', 'Tipo de item']).size().reset_index(name='Count')

    plt.figure(figsize=(12, 6))
    sns.barplot(x='Pai', y='Count', hue='Tipo de item', data=item_status_count, ci=None)
    plt.title('Quantidade de itens por Tipo de Item e Módulos')
    plt.xlabel('Módulos')
    plt.ylabel('Quantidade de Itens')
    plt.legend(title='Tipo de Item')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig('BarPlot_Modulos_Tipo_Item.png')
    plt.close()

if __name__ == "__main__":
    df = extract_table_from_html('Jira (3).html')
    df_selected = prepare_dataframe(df)
    plot_item_status_count(df_selected)
