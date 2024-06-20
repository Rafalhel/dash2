import pandas as pd
from bs4 import BeautifulSoup

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
csv_path_utf8 = 'Jira_Issues_Export_Semicolon_UTF8.csv'
df.to_csv(csv_path_utf8, index=False, sep=';', encoding='utf-8-sig')
