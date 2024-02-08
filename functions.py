import warnings
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from io import BytesIO
import xlsxwriter


warnings.filterwarnings('ignore')


@st.cache_data
def get_dfs(data_path, cat, *args):

    # bloco responsável por coletar os dados necessários à seção de graduação
    if cat == 'graduacao':
        df = pd.read_parquet(data_path).fillna('None')  # caregamento do df e remoção de na
        df.loc[df['status_discente'].str.startswith('ATIVO'), 'status_discente'] = 'ATIVO'  # unificação da variável ATIVO
        df = df.loc[(df['status_discente'] != 'CADASTRADO') &  # remoção da var CADASTRADO
                    (df['nome_curso'].str.contains('São Cristóvão'))]  # filtro por SC

        # status agrupagos de toda a ufs

        '''
      Filtro por cursos do Campus São Cristóvão apenas;
      Agrupamento por ano e unidade (dpt) para contagem dos status;
      Pivoting para horizontalização dos status e cálculo da mediana da UFS;
      Resultado em dicionário para facilitar reseting do índex
      '''

        df_ufs = pd.DataFrame(
            df.loc[df['nome_curso'].str.contains('São Cristóvão')]
            .groupby(['ano_ingresso', 'nome_unidade'], as_index=False)['status_discente'].value_counts()
            .pivot_table(index='ano_ingresso', columns='status_discente', values='count', fill_value=0, aggfunc='median')
            .astype(int)
            .to_dict()
        ).reset_index(names='ANO')
        df_ufs['ANO'] = df_ufs['ANO'].astype('str')

        # status agrupados de t0do o ccsa
        df_ccsa = pd.DataFrame(
            df.loc[df['nome_unidade_gestora'].str.contains('SOCIAIS APLICADAS')]
            .groupby(['ano_ingresso', 'nome_curso'], as_index=False)['status_discente'].value_counts()
            .pivot_table(index='ano_ingresso', columns='status_discente', values='count', fill_value=0, aggfunc='median')
            .astype(int)
            .to_dict()
        ).reset_index(names='ANO')
        df_ccsa['ANO'] = df_ccsa['ANO'].astype('str')

        # status agrupagos do curso
        df_sec = pd.DataFrame(
            df.loc[df['nome_curso'].str.contains('Secretariado')]
            .groupby('ano_ingresso', as_index=False)['status_discente'].value_counts()
            .pivot(index='ano_ingresso', columns='status_discente', values='count')
            .fillna(0)
            .astype(int)
            .to_dict()
        ).reset_index(names='ANO')
        df_sec['ANO'] = df_sec['ANO'].astype('str')

        datasets = {
            'ufs': df_ufs,
            'ccsa': df_ccsa,
            'sec': df_sec
        }

        # cálculo do total de ingressos e das porcentagens
        for key, dataset in datasets.items():
            dataset['TOTAL'] = dataset.sum(axis='columns', numeric_only=True)  # soma de todas as colunas

            for col in dataset.columns:
                if col != 'TOTAL' and col != 'ANO':
                    dataset[f'% {col}'] = round(dataset[col] / dataset['TOTAL'], 3)  # porcentagens

            # verticalização do dataframe final (facilita a cosntrução de graphs)
            dataset = dataset.melt(
                id_vars='ANO', value_vars=dataset.columns[1:],
                var_name='STATUS', value_name='COUNT'
            )

            datasets[key] = dataset  # atualização do dataset

        return datasets

    if cat == 'pos':

        # dfs discentes de secretarido e discentes de pós, para filtragem dos discentes de pós de secretariado
        df_sec = pd.read_parquet(args[0]).query('nome_curso.str.contains("Secretariado") '
                                                'and status_discente == "CONCLUÍDO"')
        df = pd.read_parquet(data_path)

        # a filtragem foi realizada pelo nome dos discentes
        df_filter = df.merge(df_sec, on='nome_discente')
        df_semi_join = df.loc[df['nome_discente'].isin(df_filter['nome_discente'])]
        fig_data = df_semi_join.groupby('ano_ingresso', as_index=False)['status_discente'].value_counts()

        fig_data.columns = ['ANO', 'STATUS', 'COUNT']

        # retorna um df para a figura e outro para o texto
        return fig_data, df_semi_join

    if cat == 'extensao':
        df = pd.read_parquet(data_path).query('unidade.str.startswith("DEPARTAMENTO")')
        df_sec = df.query('unidade.str.contains("SECRETARIADO")')

        datasets = {'sec': df_sec}

        return datasets

    if cat == 'extensao_comp':
        df_ufs = pd.read_parquet(data_path).query('unidade.str.startswith("DEPARTAMENTO")')
        df_sec = df_ufs.query('unidade.str.contains("SECRETARIADO")')
        ccsa_centros = [
            'DEPARTAMENTO DE ADMINISTRAÇÃO', 'DEPARTAMENTO DE CIÊNCIAS CONTÁBEIS',
            'DEPARTAMENTO DE CIÊNCIA DA INFORMAÇÃO',
            'DEPARTAMENTO DE DIREITO', 'DEPARTAMENTO DE ECONOMIA', 'DEPARTAMENTO DE RELAÇÕES INTERNACIONAIS',
            'DEPARTAMENTO DE SECRETARIADO EXECUTIVO', 'DEPARTAMENTO DE SERVIÇO SOCIAL', 'DEPARTAMENTO DE TURISMO'
        ]
        df_ccsa = df_ufs.query('unidade.isin(@ccsa_centros)')

        datasets = {'sec': df_sec, 'ccsa': df_ccsa, 'ufs': df_ufs}

        var = args[0]
        min_year = args[1]
        max_year = args[2]

        # dataset secretariado
        df_sec = datasets['sec']
        for col in df_sec.columns[:-3]:
            df_sec[col] = df_sec[col].astype(str)
        sec_to_bars = (df_sec.query('@max_year >= ano >= @min_year').groupby(var, as_index=False)
                       [var].value_counts())
        sec_to_bars['unidade'] = 'DEPARTAMENTO DE SECRETARIADO'
        sec_to_bars = sec_to_bars[['unidade', var, 'count']]
        sec_to_bars['count'] = round(sec_to_bars['count'])

        # dataset ccsa
        df_ccsa = datasets['ccsa']
        for col in df_ccsa.columns[:-3]:
            df_ccsa[col] = df_ccsa[col].astype(str)
        ccsa_to_bars = (df_ccsa.query('@max_year >= ano >= @min_year')
                        .groupby(['unidade', var], as_index=False)[var].value_counts()
                        .groupby(var, as_index=False)['count'].median())
        ccsa_to_bars['unidade'] = 'CCSA'
        ccsa_to_bars = ccsa_to_bars[['unidade', var, 'count']]
        ccsa_to_bars['count'] = round(ccsa_to_bars['count'])

        # dataset ufs
        df_ufs = datasets['ufs']
        for col in df_ufs.columns[:-3]:
            df_ufs[col] = df_ufs[col].astype(str)
        ufs_to_bars = (df_ufs.query('@max_year >= ano >= @min_year')
                       .groupby(['unidade', var], as_index=False)[var].value_counts()
                       .groupby(var, as_index=False)['count'].median())
        ufs_to_bars['unidade'] = 'UFS'
        ufs_to_bars = ufs_to_bars[['unidade', var, 'count']]
        ufs_to_bars['count'] = round(ufs_to_bars['count'])

        df_united = pd.concat([sec_to_bars, ccsa_to_bars, ufs_to_bars], ignore_index=True)

        return df_united

    if cat == 'extensao_comp_financiamento':
        df_ufs = pd.read_parquet(data_path).query('unidade.str.startswith("DEPARTAMENTO")')
        df_sec = df_ufs.query('unidade.str.contains("SECRETARIADO")')
        ccsa_centros = [
            'DEPARTAMENTO DE ADMINISTRAÇÃO', 'DEPARTAMENTO DE CIÊNCIAS CONTÁBEIS',
            'DEPARTAMENTO DE CIÊNCIA DA INFORMAÇÃO',
            'DEPARTAMENTO DE DIREITO', 'DEPARTAMENTO DE ECONOMIA', 'DEPARTAMENTO DE RELAÇÕES INTERNACIONAIS',
            'DEPARTAMENTO DE SECRETARIADO EXECUTIVO', 'DEPARTAMENTO DE SERVIÇO SOCIAL', 'DEPARTAMENTO DE TURISMO'
        ]
        df_ccsa = df_ufs.query('unidade.isin(@ccsa_centros)')

        datasets = {'sec': df_sec, 'ccsa': df_ccsa, 'ufs': df_ufs}

        min_year = args[0]
        max_year = args[1]
        dfs = []
        for k, df in datasets.items():
            c1 = df['financiamento_externo'] == 'SIM'
            c2 = df['financiamento_interno'] == 'SIM'
            df['financiado'] = np.where(c1 | c2, 'SIM', 'NÃO')
            df['tipo'] = None

            # para encontrar quais atividades foram financiadas e a origem do financiamento
            for i, row in enumerate(df[['financiado', 'financiamento_externo', 'financiamento_interno']].values):
                if row[0] == 'SIM' and row[1] == 'SIM':
                    df.iloc[i, -1] = 'Externo'
                elif row[0] == 'SIM' and row[-1] == 'SIM':
                    df.iloc[i, -1] = 'Interno'
                else:
                    df.iloc[i, -1] = 'Sem financiamento'

            # para filtrar pelo ano
            df['ano'] = df['ano'].astype(str)
            df = df.query('@max_year >= ano >= @min_year')

            if k == 'sec':
                df = df.groupby('tipo', as_index=False)['tipo'].value_counts()
                df['unidade'] = 'DEPARTAMENTO DE SECRETARIADO'
                df = df[['unidade', 'tipo', 'count']]
            elif k == 'ccsa':
                df = (df.groupby('unidade', as_index=False)['tipo'].value_counts()
                      .groupby('tipo', as_index=False)['count'].median())
                df['unidade'] = 'CCSA'
                df['count'] = round(df['count'])
                df = df[['unidade', 'tipo', 'count']]
            else:
                df = (df.groupby('unidade', as_index=False)['tipo'].value_counts()
                      .groupby('tipo', as_index=False)['count'].median())
                df['unidade'] = 'UFS'
                df['count'] = round(df['count'])
                df = df[['unidade', 'tipo', 'count']]

            dfs.append(df)

        df_united = pd.concat(dfs, ignore_index=True)

        return df_united

    if cat == 'pesquisa':
        df = pd.read_parquet(data_path)
        df_sec = df.loc[df['centro/unidade'] == "DEPARTAMENTO DE SECRETARIADO EXECUTIVO"].copy()
        df_sec['ano_projeto'] = pd.to_datetime(df_sec['data_inicio']).dt.year.astype(str)

        return df_sec

    if cat == 'pesq_comp':
        min_year = args[0]
        max_year = args[1]
        var = args[2]
        df = pd.read_parquet(data_path)

        ccsa_centros = [
            'DEPARTAMENTO DE ADMINISTRAÇÃO', 'DEPARTAMENTO DE CIÊNCIAS CONTÁBEIS',
            'DEPARTAMENTO DE CIÊNCIA DA INFORMAÇÃO',
            'DEPARTAMENTO DE DIREITO', 'DEPARTAMENTO DE ECONOMIA', 'DEPARTAMENTO DE RELAÇÕES INTERNACIONAIS',
            'DEPARTAMENTO DE SECRETARIADO EXECUTIVO', 'DEPARTAMENTO DE SERVIÇO SOCIAL', 'DEPARTAMENTO DE TURISMO'
        ]

        df_ccsa = df.loc[df['centro/unidade'].isin(ccsa_centros)].copy()
        df_ccsa['ano_projeto'] = pd.to_datetime(df_ccsa['data_inicio']).dt.year.astype(str)
        df_ccsa = (df_ccsa.query('@max_year >= ano_projeto >= @min_year')
                   .groupby('centro/unidade', as_index=False)[var].value_counts()
                   .groupby(var, as_index=False)['count'].median())
        df_ccsa['unidade'] = 'CCSA'

        df_ufs = df.loc[(df['centro/unidade'].str.startswith('DEPARTAMENTO')) |
                        (df['centro/unidade'].str.startswith('CENTRO'))]
        df_ufs['ano_projeto'] = pd.to_datetime(df_ufs['data_inicio']).dt.year.astype(str)
        df_ufs = (df_ufs.query('@max_year >= ano_projeto >= @min_year')
                  .groupby('centro/unidade', as_index=False)[var].value_counts()
                  .groupby(var, as_index=False)['count'].median())
        df_ufs['unidade'] = 'UFS'

        df_sec = df.loc[df['centro/unidade'] == 'DEPARTAMENTO DE SECRETARIADO EXECUTIVO'].copy()
        df_sec['ano_projeto'] = pd.to_datetime(df_sec['data_inicio']).dt.year.astype(str)
        df_sec = (df_sec.query('@max_year >= ano_projeto >= @min_year')
                  .groupby(var, as_index=False)[var].value_counts())
        df_sec['unidade'] = 'SEC'

        df_united = pd.concat([df_sec, df_ccsa, df_ufs], ignore_index=True)

        return df_united


@st.cache_data
def get_viz(dataset, type_, *args):
    # figura da visualização geral
    if type_ == 'geral':
        # Tratamento dos dados de entrada
        data = (dataset
                .query('~STATUS.str.startswith("%") and STATUS != "TOTAL"')
                .copy())
        data['STATUS'] = data['STATUS'].str.capitalize()

        fig = px.bar(
            data, x='ANO', y='COUNT', color='STATUS', text_auto=True,
            labels=dict(COUNT='', ANO='', STATUS=''),
            barmode='relative', template='plotly_white',
            width=1350
        )

        fig.update_traces(textfont_size=14, textangle=0, textposition='inside')
        fig.update_layout(
            uniformtext_minsize=14, uniformtext_mode='hide',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            xaxis=dict(tickmode='linear', dragmode=False)
        )

        return fig

    if type_ == 'unico':
        # Tratamento dos dados de entrada
        var = args[0].upper()
        min_y = str(args[1][0])
        max_y = str(args[1][1])
        max_yaxis = args[-1]

        data = (
            dataset.loc[
                (dataset['STATUS'].isin(['TOTAL', var])) & ((dataset['ANO'] >= min_y) & (dataset['ANO'] <= max_y))
            ]
        )
        data['STATUS'] = data['STATUS'].str.capitalize()
        data = data.sort_values(by=['STATUS', 'ANO'], ascending=[False, True])

        fig = px.bar(
            data, x='ANO', y='COUNT', color='STATUS', text_auto=True,
            labels=dict(COUNT='', ANO='', STATUS=''),
            barmode='group', template='plotly_white',
            width=620
        )

        fig.update_traces(textangle=0, textposition='inside')
        fig.update_layout(
            uniformtext_minsize=8, uniformtext_mode='hide',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            yaxis_range=[0, max_yaxis]
        )

        return fig

    if type_ == 'taxa':
        var = '% ' + args[0].upper()
        min_y = str(args[1][0])
        max_y = str(args[1][1])
        max_yaxis = args[-1]

        data = (dataset
                .query('STATUS == @var and ANO >= @min_y and ANO <= @max_y')
                .copy())
        data['COUNT'] = round(data['COUNT'] * 100, 3)
        labels = data['COUNT'].map(lambda x: f'{x}%').values

        fig = px.line(
            data, x='ANO', y='COUNT', color='STATUS', text=labels,
            labels=dict(COUNT='', ANO='', STATUS=''),
            template='plotly_white', width=620
        )

        fig.update_traces(textposition='top right', opacity=.8)
        fig.update_layout(
            uniformtext_minsize=6,
            xaxis=dict(showline=True, showgrid=False, showticklabels=True, ticks='outside'),
            yaxis=dict(showgrid=False, zeroline=False, showline=False, showticklabels=False),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            yaxis_range=[-3, max_yaxis], font_color='black'
        )

        if args[0] == 'Concluído':
            label_name = '% Conclusão'
        elif args[0] == 'Cancelado':
            label_name = '% Cancelamento'
        elif args[0] == 'Trancado':
            label_name = '% Trancamento'
        fig.for_each_trace(lambda x: x.update(name=label_name))

        return fig

    if type_ == 'pos':

        # fig = px.pie(dataset, values='COUNT', names='STATUS', hole=.5,
        #              template='plotly_white', width=620)
        #
        # fig.update_traces(textinfo='percent', marker=dict(line=dict(width=1)))

        data = dataset.groupby('STATUS', as_index=False)['COUNT'].sum()
        data.sort_values(by='COUNT', ascending=True, inplace=True)
        fig = px.bar(data, x='COUNT', y='STATUS', text='COUNT', labels={'STATUS': '', 'COUNT': ''},
                     template='plotly_white', width=620)

        fig.update_traces(textfont_size=12, textangle=0, textposition='inside')
        fig.update_layout(
            uniformtext_minsize=12, uniformtext_mode='hide',
            xaxis=dict(tickmode='linear')
        )

        return fig

    '''
    Aqui se inicia os comandos para geração dos gráficos da categoria extensão e pesquisa
    '''

    if type_ == 'ext_geral':
        data = dataset.groupby('ano', as_index=False)['tipo_atividade'].value_counts()
        fig = px.bar(data, 'ano', 'count', color='tipo_atividade', text_auto=True,
                     labels=dict(ano='', count='', tipo_atividade=''), template='plotly_white', width=1350)

        fig.update_traces(textfont_size=14, textangle=0, textposition='inside')
        fig.update_layout(
            uniformtext_minsize=14, uniformtext_mode='hide',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            xaxis=dict(tickmode='linear')
        )

        return fig

    if type_ == 'ext_pie':
        data = dataset.groupby(args[0], as_index=False).size()
        fig = px.pie(data, names=args[0], values='size', hole=.5, template='plotly_white', width=620)

        fig.update_traces(textinfo='percent', marker=dict(line=dict(width=1)), textposition='inside',
                          insidetextorientation='horizontal')
        fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide')

        return fig

    if type_ == 'ext_horizontal':
        col = args[0]
        data = dataset.groupby(col, as_index=False).size().sort_values(by='size')
        fig = px.bar(data, 'size', col, text='size', labels={col: '', 'size': ''},
                     template='plotly_white', width=750)

        fig.update_traces(textfont_size=12, textangle=0, textposition='inside')
        fig.update_layout(
            uniformtext_minsize=12, uniformtext_mode='hide'
        )

        return fig

    if type_ == 'ext_comp':
        fig = px.bar(dataset, 'unidade', 'count', dataset.columns[-2], barmode='group', template='plotly_white',
                     labels={'unidade': '', 'count': '', dataset.columns[-2]: ''}, text_auto=True, width=620)

        fig.update_traces(textfont_size=12, textangle=0, textposition='inside')
        fig.update_layout(
            uniformtext_minsize=12, uniformtext_mode='hide',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )

        return fig

    if type_ == 'ext_comp_pie':
        fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'domain'}, {'type': 'domain'}]])
        unidade = dataset['unidade'].unique()

        data = dataset.query('unidade == @unidade[0]').sort_values(by='count', ascending=False).iloc[:5, :]
        fig.add_trace(go.Pie(labels=data[data.columns[-2]], values=data[data.columns[-1]], name=unidade[0]), 1, 1)

        data2 = dataset.query('unidade == @unidade[1]').sort_values(by='count', ascending=False).iloc[:5, :]
        fig.add_trace(go.Pie(labels=data2[data2.columns[-2]], values=data2[data2.columns[-1]], name=unidade[1]), 1, 2)

        fig.update_traces(hole=.5, hoverinfo="label+value", marker=dict(line=dict(width=1)), textposition='inside',
                          insidetextorientation='horizontal')
        fig.update_layout(annotations=[dict(text='SEC', x=0.18, y=0.5, font_size=20, showarrow=False),
                          dict(text=unidade[1], x=0.82, y=0.5, font_size=20, showarrow=False)], template='plotly_white',
                          uniformtext_minsize=12, uniformtext_mode='hide', width=700,
                          margin=dict(t=50))

        return fig

    if type_ == 'ext_comp_hbar':
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True)
        unidade = dataset['unidade'].unique()

        data = dataset.query('unidade == @unidade[0]').sort_values(by='count', ascending=False).iloc[:5, :]
        data = data.sort_values(by='count')
        fig.add_trace(
            go.Bar(x=data[data.columns[-1]], y=data[data.columns[-2]], orientation='h', name='SEC'), 1, 1
        )

        data2 = dataset.query('unidade == @unidade[1]').sort_values(by='count', ascending=False).iloc[:5, :]
        data2 = data2.sort_values(by='count')
        fig.add_trace(
            go.Bar(x=data2[data2.columns[-1]], y=data2[data2.columns[-2]], orientation='h', name=unidade[1]), 2, 1
        )

        fig.update_traces()
        fig.update_layout(width=620, template='plotly_white',
                          legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

        return fig

    if type_ == 'pesquisa':
        data = dataset.groupby('ano_projeto', as_index=False)['codigo_projeto'].size()
        fig = px.bar(data, x='ano_projeto', y='size', template='plotly_white', labels={'ano_projeto': '', 'size': ''},
                     text_auto=True, width=1350)

        fig.update_traces(textfont_size=12, textangle=0, textposition='inside')
        fig.update_layout(
            uniformtext_minsize=12, uniformtext_mode='hide',
            xaxis=dict(tickmode='linear')
        )

        return fig

    if type_ == 'pesq_keywords':
        for sign in [',', '.', ':']:
            dataset['palavras_chave'] = dataset['palavras_chave'].str.replace(sign, ';', regex=False)
        dataset['palavras_chave'] = dataset['palavras_chave'].str.lower()

        keywords = []
        for row in dataset['palavras_chave'].values:
            w = [x.strip() for x in row.split(';') if x != '' and x != ' ']
            keywords.extend(w)

        keywords_size = {}
        for k in keywords:
            if k not in keywords_size:
                keywords_size[k] = 1
            else:
                keywords_size[k] += 1

        df_keywords = pd.DataFrame({'Palavras-chave': keywords_size.keys(), 'Ocorrências': keywords_size.values()})
        stopwords = ["secretariado executivo", "secretariado", "secretário executivo",
                     'universidade federal de sergipe', 'ufs', '']
        df_keywords = df_keywords.query('~`Palavras-chave`.isin(@stopwords)')
        df_keywords['Palavras-chave'] = df_keywords['Palavras-chave'].str.title()
        df_keywords = df_keywords.sort_values(by='Ocorrências', ascending=False).reset_index(drop=True)

        return df_keywords

    if type_ == 'pesq_comp_bars':
        fig = px.bar(dataset, 'unidade', 'count', color='situacao', template='plotly_white',
                     labels={'unidade': '', 'count': '', 'situacao': ''}, text_auto=True, width=620)

        fig.update_traces(textfont_size=12, textangle=0, textposition='inside')
        fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide',
                          legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

        return fig

    if type_ == 'pesq_comp_hbars':
        fig = make_subplots(rows=2, cols=1)
        unidade = dataset['unidade'].unique()
        col = dataset.columns[-2]

        data = dataset.query('unidade == @unidade[0]').sort_values(by=col, ascending=False).iloc[:5, :]
        data = data.sort_values(by=col)
        fig.add_trace(
            go.Bar(x=data[data.columns[-2]], y=data[data.columns[0]], orientation='h', name='SEC'), 1, 1
        )

        data2 = dataset.query('unidade == @unidade[1]').sort_values(by=col, ascending=False).iloc[:5, :]
        data2 = data2.sort_values(by=col)
        fig.add_trace(
            go.Bar(x=data2[data2.columns[-2]], y=data2[data2.columns[0]], orientation='h', name=unidade[1]), 2, 1
        )

        fig.update_traces()
        fig.update_layout(width=620, template='plotly_white',
                          legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                          xaxis=dict(tickmode='linear'))

        return fig


@st.cache_data
def viz_to_download(dataset, type_, *args):

    if type_ == 'geral':
        data = (dataset
                .query('~STATUS.str.startswith("%") and STATUS != "TOTAL"')
                .copy())
        data['STATUS'] = data['STATUS'].str.capitalize()

        fig = px.bar(
            data, x='ANO', y='COUNT', color='STATUS', text_auto=True,
            labels=dict(COUNT='', ANO='', STATUS=''),
            barmode='relative', template='plotly_white'
        )

        fig.update_traces(textangle=0, textposition='inside')

        if args:
            if args[0] >= (300 + 450):
                fig.update_layout(
                    uniformtext_minsize=12, uniformtext_mode='hide',
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
                )
            else:
                fig.update_layout(uniformtext_minsize=6, uniformtext_mode='hide')
            return fig

        fig.update_layout(
            uniformtext_minsize=6, uniformtext_mode='hide',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )

        return fig


@st.cache_resource
def convert_df(df, ext):

    if ext == '.xlsx':
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Dados', index=False)
            workbook = writer.book
            worksheet = writer.sheets['Dados']
            header_format = workbook.add_format({'border': False})

            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)

        buffer.seek(0)
        return buffer.getvalue()

    elif ext == '.csv':
        return df.to_csv(index=False, encoding='utf-8')

    elif ext == '.json':
        return df.to_json(force_ascii=False)

    else:
        return df.to_parquet()
