# data extraction
import requests
from bs4 import BeautifulSoup

# data manipulation
import pandas as pd
from io import BytesIO
import json

# system
import os
import time


# url de acesso aos repositórios
discentes_rep = 'https://dados.ufs.br/dataset/discentes_graduacao'
discentes_pos_rep = 'https://dados.ufs.br/dataset/discentes_pos_graduacao'
pesquisa_rep = 'https://dados.ufs.br/dataset/projetos_pesquisa/resource/pro-csv-projetos-de-pesquisa'
extensao_rep = 'https://dados.ufs.br/dataset/atividades_extensao/resource/ati-csv-atividades-de-extensao'

folder = 'datasets'


# função para extrair e compilar todos os datasets com dados sobre discentes de graduação e pós
def get_all_datasets(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # discentes de graduação e pós
    if url.endswith('discentes_graduacao') or url.endswith('discentes_pos_graduacao'):
        block = soup.find('ul', class_='resource-list').find_all('li', class_='resource-item')
        dfs = []

        # looping para extrair todos os datasets
        for tag in block:
            link = tag.find('a', class_='resource-url-analytics').get('href')
            if link.endswith('.csv'):
                resp = requests.get(link)
                data = pd.read_csv(BytesIO(resp.content), encoding='utf-8')
                dfs.append(data)
                time.sleep(10)
                print('Looping ...')

        # dataset unificado
        dataset = pd.concat(dfs, ignore_index=True)
        dataset.sort_values(by='ano_ingresso', ascending=False, inplace=True)

        return dataset


# função para extrair datasets individuais
def get_dataset(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # pesquisa e extensão
    if 'projetos-de-pesquisa' in url or 'atividades-de-extensao' in url:
        link = (soup.find('section', class_='module-resource')
                .find('a', class_='resource-url-analytics')
                .get('href'))
        resp = requests.get(link)
        data = pd.read_csv(BytesIO(resp.content), encoding='utf-8')
        data['data_inicio'] = pd.to_datetime(data['data_inicio'], dayfirst=True, errors='coerce')
        data.sort_values(by='data_inicio', ascending=False, inplace=True)

        return data

    else:
        link = (soup.find('ul', class_='resource-list')
                .find_all('li', class_='resource-item')[0]
                .find('a', class_='resource-url-analytics')
                .get('href'))
        resp = requests.get(link)
        data = pd.read_csv(BytesIO(resp.content), encoding='utf-8')

        return data


def get_metadata(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    info = (soup.find('section', class_='additional-info')
            .find('th', string='Última Atualização')
            .find_next_sibling()
            .find('span').
            get('data-datetime'))

    return info


##############
# DOWNLOAD DE TODOS OS ARQUIVOS PELA PRIMEIRA VEZ
#############

start = time.time()
report = {}
if not os.listdir(folder):

    # download de todos os datasets da graduação e pós
    for item in [
        (discentes_rep, 'discentes_graduacao.parquet'),
        (discentes_pos_rep, 'discentes_pos_graduacao.parquet')
    ]:

        print('A baixar dados do dataset: ' + item[1])
        df = get_all_datasets(item[0])  # coleta de todos os datasets

        for col in df.columns:  # conversão de tipo
            df[col] = df[col].astype('object')

        df.to_parquet(os.path.join(folder, item[1]), index=False)  # salvamento do dataset em formato parquet (faster)

        date = pd.to_datetime(get_metadata(item[0]), errors='coerce')  # atualização do metadado
        report[item[1]] = str(date)

    # download de datasets da pesquisa e extensão
    for item in [
        (pesquisa_rep, 'projetos_pesquisa.parquet'),
        (extensao_rep, 'atividades_extensao.parquet')
    ]:

        print('A baixar dados do dataset ' + item[1])
        df = get_dataset(item[0])  # coleta do dataset

        for col in df.columns:  # conversão de tipo
            df[col] = df[col].astype('object')

        df.to_parquet(os.path.join(folder, item[1]), index=False)

        if 'pesquisa' in item[1]:
            date = pd.to_datetime(get_metadata('https://dados.ufs.br/dataset/grupos_pesquisa'), errors='coerce')
            report[item[1]] = str(date)
        else:
            date = pd.to_datetime(get_metadata('https://dados.ufs.br/dataset/atividades_extensao'), errors='coerce')
            report[item[1]] = str(date)

    with open(os.path.join(folder, 'report.json'), 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4, ensure_ascii=False)


##############
# ATUALIZAÇÃO DOS ARQUIVOS
#############

if os.listdir(folder):
    with open('datasets/report.json', 'r', encoding='utf-8') as f:
        report = json.load(f)

    ''' Para evitar de usar condicionais adicionei uma tripla ao looping. Algumas categorias não não dispõe de link único
    para coletar o dataset e o metadado. '''

    for item in [
        (discentes_rep, 'discentes_graduacao.parquet', discentes_rep),
        (discentes_pos_rep, 'discentes_pos_graduacao.parquet', discentes_pos_rep),
        (pesquisa_rep, 'projetos_pesquisa.parquet', 'https://dados.ufs.br/dataset/grupos_pesquisa'),
        (extensao_rep, 'atividades_extensao.parquet', 'https://dados.ufs.br/dataset/atividades_extensao')
    ]:

        last_update = report[item[1]]  # data extraída do último download
        last_pub = str(pd.to_datetime(get_metadata(item[-1])))  # data extraída do site

        if last_pub > last_update:  # verifica se há atualização no repositório
            df = get_dataset(item[0])
            col = 'ano_ingresso' if 'graduacao' in item[1] else 'data_inicio'
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
            old_df = pd.read_parquet(os.path.join(folder, item[1]))
            new_df = pd.concat([old_df, df], ignore_index=True)
            new_df[col] = pd.to_datetime(new_df[col])
            new_df.sort_values(by=col, ascending=False, inplace=True)

            new_df.to_parquet(os.path.join(folder, item[1]), index=False)  # dataset atualizado
            report[item[1]] = last_pub  # atualiza o relatório com datas de update

        else:
            print(f'Dataset {item[1]} está em sua última versão.')

    with open('datasets/report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4, ensure_ascii=False)

end = time.time()
print(f'Tempo decorrido: {time.strftime("%H:%M:%S", time.gmtime(end - start))}')

