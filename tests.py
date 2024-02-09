import warnings
import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import functions as func

warnings.filterwarnings('ignore')

# configuração da página
st.set_page_config(
    page_title="Web SecExec - UFS",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "#Gostou da ferramenta?\nMe siga no Linkedin: [Daniel Magalhães]("
                 "https://www.linkedin.com/in/magalhaesd/) "
    }
)

st.header('🎓 Web SecExec - UFS\n', anchor=False)

intro_text = '''O **Web SecExec – UFS** é uma ferramenta que coleta e compila dados relacionados ao curso de 
Secretariado Executivo da Universidade Federal de Sergipe, com enfoque em informações sobre graduação, 
pós-graduação, atividades de extensão e projetos de pesquisa. A aplicação é atualizada quinzenalmente, 
utilizando dados provenientes do [repositório universitário](https://dados.ufs.br/dataset/). O menu à esquerda 
fornece informações adicionais sobre a ferramenta.\n
É recomendado o acesso a partir de um desktop para melhor visualização das figuras. Caso ocorra algum erro ou bug
com a ferramenta, por gentileza, sinalizar por meio do endereço *danielmagalhaes38@hotmail.com*.\n
Autor: [Daniel Magalhães](https://www.linkedin.com/in/magalhaesd). Mais projetos podem ser encontrados 
[aqui](https://www.datascienceportfol.io/magalhaesd).
'''

st.write(intro_text)
# st.write('---')

with st.sidebar:
    st.header('Defina uma categoria de análise', anchor=False)
    category = st.selectbox('A',
                            options=['Graduação e Pós-graduação', 'Extensão e Pesquisa'],
                            label_visibility='hidden')

    st.caption(
        'A categoria de análise modifica os dados e variáveis, influenciando assim as visualizações da ferramenta.'
    )

    st.write('---')

    st.write('O menu com as opções **📈 Gráficos** e **🗃 Dados** alterna entre as janelas '
             'de análise e download dos dados.')
    st.write('Cada categoria de análise contem visualizações com informações individuais do curso de Secretariado '
             'ou comparativas com as unidade CCSA e UFS.')
    st.write('Textos gerados automaticamente resumem os dados de painéis de visualização.')

if category == 'Graduação e Pós-graduação':
    folder = 'datasets/discentes_graduacao.parquet'
    my_datasets = func.get_dfs(folder, 'graduacao')

    # '''
    # Aqui criei duas tabs, que são janelas a serem mostradas quando clicadas;
    # Na primeira tabs serão armazenadas as visualizações e na segunda, os dados
    # '''
    tab1, tab2 = st.tabs(['📈 Gráficos', '🗃 Dados'])
    with tab1:

        # '''
        # Bloco usado para criar a imagem em tamanho padrão (600x350);
        # Botão de download da imagem padrão;
        # E checkbox para abrir menu de alteração das proporções da imagem;
        # O parâmetro key= do checkbox é usado para criar sua identificação, para que mais tarde eu altere seu estado
        # '''

        download_fig = func.viz_to_download(my_datasets['sec'], 'geral').to_image(format='png', width=750,
                                                                                  height=500)
        st.download_button('**Baixar imagem (750x500)**', download_fig, 'img.png')
        img_check = st.checkbox('Alterar proporções para download', key='img_check')

        # '''
        # Se o checkbox for marcado é aberto o menu de alterações;
        # Nele há dois sliders que controlam as dimensões da figura;
        # A figura dinâmica é armazenada numa variável;
        # A função reset_button tem a finalidade de desmarcar o checkbox, onde uso o método session_state
        # para alterá-lo;
        # O botão de download é criado para permitir o download da imagem dinâmica. É necessário usar o parâmetro
        # on_click
        # para chamar a função de reset do checkbox;
        # Por fim há o método de criação da imagem
        # '''
        if img_check:
            with st.container(border=True):
                width_slider = st.slider('Largura', 300, 1200, 600, step=50)
                height_slider = st.slider('Altura', 175, 800, 350, step=50)
                dynamic_fig = func.viz_to_download(
                    my_datasets['sec'], 'geral', width_slider
                ).to_image(format='png', width=width_slider, height=height_slider)

                # ao passar a key de um widget para o método é possível alterar o seu estado
                def reset_button():
                    st.session_state['img_check'] = False
                    return

                # on_click para reset do checkbox
                st.download_button('**Baixar e finalizar**', dynamic_fig, 'img.png', on_click=reset_button)
                st.image(dynamic_fig)

        # '''
        # Container da visualização geral;
        # Chama uma função de criação de imagens, que retorna uma figura plotly, e passa o resutado para o exibidor
        # '''
        with st.container(border=True):
            st.subheader('Figura 1: Visão Geral das Turmas do Curso ao Longo do Tempo', anchor=False)
            st.caption('Por turma ingressante.')
            fig = func.get_viz(my_datasets['sec'], 'geral')
            st.plotly_chart(fig, use_container_width=True)

            st.info(
                'Para excluir uma variável da visualização, selecione-a no canto superior direito do gráfico.',
                icon='💡'
            )

            # '''
            # Container do resumo dos dados;
            # O texto é gerado automaticamente com base no própio dataset
            # '''
            with st.container(border=True):
                st.subheader('Resumo dos dados', anchor=False)

                data_txt = my_datasets['sec'].query('~STATUS.str.startswith("%") and STATUS != "TOTAL"')
                data_txt['COUNT'] = data_txt['COUNT'].astype(int)

                # filtragem dos dados a serem inputados no texto padrão
                max_conclussions = data_txt.query('STATUS == "CONCLUÍDO"')['COUNT'].max()
                most_conclussions = data_txt.query('STATUS == "CONCLUÍDO" and COUNT == @max_conclussions')
                max_cancellations = data_txt.query('STATUS == "CANCELADO"')['COUNT'].max()
                most_cancellations = data_txt.query('STATUS == "CANCELADO" and COUNT == @max_cancellations')
                min_active = data_txt.query('STATUS == "ATIVO" and COUNT > 0')['ANO'].min()
                least_active = data_txt.query('STATUS == "ATIVO" and ANO == @min_active')
                total_locks = data_txt.query('STATUS == "TRANCADO"')['COUNT'].sum()
                total_actives = data_txt.query('STATUS == "ATIVO"')['COUNT'].sum()

                st.write(
                    f'A turma de **{most_conclussions["ANO"].values[0]}** lidera com o maior número de graduados,'
                    f' totalizando **{most_conclussions["COUNT"].values[0]}**.'
                    f' A turma de **{most_cancellations["ANO"].values[0]}** se destaca pelos '
                    f'**{most_cancellations["COUNT"].values[0]}** cancelamentos de vínculo. Já a turma mais antiga com '
                    f'discentes ainda ativos é a de **{least_active["ANO"].values[0]}**, contando com '
                    f'**{least_active["COUNT"].values[0]}**. '
                    f'Atualmente há **{total_actives}** discentes com vínculo ativo no curso e **{total_locks}** '
                    f'solicitações de trancamento.'
                )

                # método para gerar um texto informativo singelo
                st.caption('Texto gerado automaticamente.')

        st.write('---')

        with st.container(border=True):
            st.header('Graduação', anchor=False)

            # '''
            # Próximo container da tab 1, usado para armazenar os gráficos individuais
            # '''
            st.subheader('Defina as opções de análise', anchor=False)
            def1, def2 = st.columns([.5, .5], gap='small')
            data = my_datasets['sec']

            # coluna que armazena a caixa de seleção das variáveis
            with def1:
                var_options = (
                    data.query('~STATUS.str.startswith("%") and STATUS != "TOTAL" and STATUS != "ATIVO"')['STATUS']
                    .str.capitalize().unique()
                )
                var = st.selectbox('Variável de interesse', var_options, index=1)

            # coluna que armazena a caixa de seleção das unidades de compração
            with def2:
                com_options = (
                    data.query('~STATUS.str.startswith("%") and STATUS != "TOTAL" and STATUS != "ATIVO"')['STATUS']
                    .str.capitalize().unique()
                )
                comp = st.selectbox('Unidade de comparação', ['CCSA', 'UFS'], index=0)

            # bloco que cria o slide da janela temporal
            year_options = data['ANO'].astype(int).unique()
            years = st.slider(
                'Janela temporal', np.min(year_options), np.max(year_options),
                (np.min(year_options), np.max(year_options))
            )

            # bloco para descorbir o maior valor do eixo y entre as figuras de comparação
            data1 = my_datasets['sec'].query('STATUS.isin(["TOTAL", @var])')['COUNT'].max()
            data2 = my_datasets[comp.lower()].query('STATUS.isin(["TOTAL", @var])')['COUNT'].max()
            max_yaxis = np.max([data1, data2])

        with st.container(border=True):
            # '''
            # Daqui em diante são criados os objestos que armazenarão as figuras individuais e de compração
            # '''
            upper1, upper2 = st.columns([.5, .5], gap='large')

            # condicionais para criação dos títulos das colunas upper e bottom
            if var == 'Concluído':
                header_label = 'Conclusão'
                txt_label = 'graduações'
            elif var == 'Cancelado':
                header_label = 'Cancelamento'
                txt_label = 'cancelamentos'
            elif var == 'Trancado':
                header_label = 'Trancamento'
                txt_label = 'trancamentos'

            # bloco responsável por criar a figura de barras nº 2
            with upper1:
                st.subheader(f'Figura 2: {header_label} x Total de Ingressos', anchor=False)
                st.caption('Por turma ingressante.')
                fig2 = func.get_viz(my_datasets['sec'], 'unico', var, years, max_yaxis + 1)
                st.plotly_chart(fig2, use_container_width=True)
                fig2_bttn = st.download_button(
                    '**Baixar imagem**', fig2.to_image(format='png', width=750, height=500), 'img.png', key='fig2'
                )

            # bloco responsável por criar a figura de barras nº 2
            with upper2:
                st.subheader(f'Figura 3: Mediana de {header_label} da unidade {comp}', anchor=False)
                st.caption('Por turma ingressante.')
                fig3 = func.get_viz(my_datasets[comp.lower()], 'unico', var, years, max_yaxis + 1)
                st.plotly_chart(fig3, use_container_width=True)
                fig3_bttn = st.download_button(
                    '**Baixar imagem**', fig3.to_image(format='png', width=750, height=500), 'img.png', key='fig3'
                )

            # bloco responsável por criar o texto automático
            with st.container(border=True):
                st.subheader('Resumo', anchor=False)

                sec = my_datasets['sec'].query('STATUS.isin(["TOTAL", @var.upper()])')
                sec = sec.loc[(sec['ANO'] >= str(years[0])) & (sec['ANO'] <= str(years[1]))]
                comp_unity = my_datasets[comp.lower()].query('STATUS.isin(["TOTAL", @var.upper()])')
                comp_unity = comp_unity.loc[(comp_unity['ANO'] >= str(years[0])) & (comp_unity['ANO'] <= str(years[1]))]

                # verifica em quais anos o curso superou as medianas do ccsa
                wins = {'C': [], 'T': []}
                for row in zip(sec.values, comp_unity.values):
                    if row[0][-1] > row[-1][-1]:
                        if row[0][1] == var.upper():
                            wins['C'].append(row[0])
                        else:
                            wins['T'].append(row[0])

                # texto caso uma única turma tenha superado
                if len(wins['C']) == 1:
                    txt = f'''
                    A turma de **Secretariado Executivo** do ano **{wins['C'][0][0]}** superou a mediana de 
                    **{header_label}** das turmas da unidade **{comp}** para o mesmo período, alcançando 
                    **{int(wins['C'][0][-1])}** {txt_label}, em comparação com a mediana de **{
                    int(comp_unity.query('ANO == @wins["C"][0][0] and STATUS == @var.upper()')['COUNT'].values[0])
                    }**
                    '''

                # texto caso mais de uma turma tenham superado
                if len(wins['C']) > 1:
                    years_ = [x[0] for x in wins['C']]

                    txt = f'''
                    As turmas de **Secretariado Executivo** dos anos **{', '.join(x[0] for x in wins['C'])}** 
                    superaram as medianas de **{header_label}** das turmas da unidade **{comp}** para o mesmo período, 
                    alcançando  **{', '.join(str(int(x[-1])) for x in wins['C'])}** {txt_label}, respectivamente, 
                    em comparação com as medianas de **{', '.join(str(int(x)) for x in comp_unity.query(
                        'ANO.isin(@years_) and STATUS == @var.upper()'
                    )['COUNT'].values)}**.
                    '''

                # texto caso não haja superação
                if len(wins['C']) < 1:
                    txt = f'''Nenhuma turma do curso de **Secretariado Executivo** superou as medianas de
                    **{header_label}** da unidade **{comp}**.'''

                st.write(txt)
                st.caption('Texto gerado automaticamente.')

            st.write('---')

            '''
            Segunda parte dos gráficos únicos
            '''
            bottom1, bottom2 = st.columns([.5, .5], gap='large')

            var_label = f'% {var.upper()}'
            data1 = my_datasets['sec'].query('STATUS.isin([@var_label])')['COUNT'].max()
            data2 = my_datasets[comp.lower()].query('STATUS.isin([@var_label])')['COUNT'].max()
            max_yaxis = np.max([data1, data2]) * 100

            with bottom1:
                st.subheader(f'Figura 4: Taxa de {header_label} das Turmas do Curso', anchor=False)
                st.caption('Por turma ingressante.')
                fig4 = func.get_viz(my_datasets['sec'], 'taxa', var, years, max_yaxis + 10)
                st.plotly_chart(fig4, use_container_width=True)
                fig4_bttn = st.download_button(
                    '**Baixar imagem**', fig4.to_image(format='png', width=750, height=500), 'img.png', key='fig4'
                )

            with bottom2:
                st.subheader(f'Figura 5: Taxa Mediana de {header_label} da Unidade {comp}', anchor=False)
                st.caption('Por turma ingressante.')
                fig5 = func.get_viz(my_datasets[comp.lower()], 'taxa', var, years, max_yaxis + 10)
                st.plotly_chart(fig5, use_container_width=True)
                fig5_bttn = st.download_button(
                    '**Baixar imagem**', fig5.to_image(format='png', width=750, height=500), 'img.png', key='fig5'
                )

            with st.container(border=True):
                st.subheader('Resumo', anchor=False)

                sec = my_datasets['sec'].query('STATUS == @var_label')
                sec = sec.loc[(sec['ANO'] >= str(years[0])) & (sec['ANO'] <= str(years[1]))]
                comp_unity = my_datasets[comp.lower()].query('STATUS == @var_label')
                comp_unity = comp_unity.loc[(comp_unity['ANO'] >= str(years[0])) & (comp_unity['ANO'] <= str(years[1]))]

                # verifica em quais anos o curso superou as medianas do ccsa
                wins = {'C': []}
                max_diff = 0
                year_max_diff = None
                for row in zip(sec.values, comp_unity.values):
                    if row[0][-1] > row[-1][-1]:
                        wins['C'].append(row[0])
                        diff = row[0][-1] - row[-1][-1]
                        if diff > max_diff:
                            max_diff = diff
                            year_max_diff = row[0][0]

                if len(wins['C']) > 1:
                    txt = f'''
                    A turma de **{sec.loc[sec['COUNT'] == sec['COUNT'].max(), 'ANO'].values[0]}** do Curso de 
                    **Secretariado** apresenta a maior taxa de **{header_label}**, atingindo 
                    **{sec['COUNT'].max() * 100}%**. Além disso, as turmas de **{', '.join(x[0] for x in wins['C'])}** 
                    superam as taxas medianas da unidade **{comp}**. Destaca-se que a turma de **{year_max_diff}** 
                    apresenta a maior diferença de taxa em relação à unidade de comparação, registrando um aumento 
                    de **{round(max_diff * 100, 3)}%**.
                    '''
                elif len(wins['C']) == 1:
                    txt = f'''
                    A turma de **{sec.loc[sec['COUNT'] == sec['COUNT'].max(), 'ANO'].values[0]}** do Curso de 
                    **Secretariado** apresenta a maior taxa de **{header_label}**, atingindo 
                    **{sec['COUNT'].max() * 100}%**. Além disso, a turma de **{wins['C'][0][0]}** 
                    superou a taxa mediana da unidade **{comp}**. Destaca-se que a turma de **{year_max_diff}** 
                    apresenta 
                    a maior diferença de taxa, registrando um aumento de **{round(max_diff * 100, 3)}%**.
                    '''
                elif len(wins['C']) < 1:
                    txt = f'''
                    A turma de **{sec.loc[sec['COUNT'] == sec['COUNT'].max(), 'ANO'].values[0]}** do Curso de 
                    **Secretariado** apresenta a maior taxa de **{header_label}**, atingindo 
                    **{sec['COUNT'].max() * 100}%**. Nenhuma turma superou a taxa mediana da unidade **{comp}**. 
                    Destaca-se que a turma de **{year_max_diff}** apresenta a maior diferença de taxa em relação à 
                    unidade de comparação, registrando um aumento de **{round(max_diff * 100, 3)}%**.
                    '''

                st.write(txt)
                st.caption('Texto gerado automaticamente.')

        st.write('---')

        # '''
        # Aqui se inicia as análises dos dados sobre as pós-graduação
        # '''
        with st.container(border=True):
            st.subheader('Pós-graduação', anchor=False)

        with st.container(border=True):
            folder_pos = 'datasets/discentes_pos_graduacao.parquet'
            folder_grad = 'datasets/discentes_graduacao.parquet'
            df_fig, df_pos = func.get_dfs(folder_pos, 'pos', folder_grad)
            top_area = (df_pos.query('nome_curso != "MATRÍCULA ESPECIAL"')
                        .groupby('nome_curso').size()
                        .sort_values(ascending=False))

            pie1, pie2 = st.columns(2, gap='large')
            with pie1:
                st.subheader('Figura 6: Aplicações em Pós-Graduação por Graduados', anchor=False)
                st.caption('Por discente com vínculo concluído na graduação.')
                fig6 = func.get_viz(df_fig, 'pos')
                st.plotly_chart(fig6, use_container_width=True)
                fig6_bttn = st.download_button(
                    '**Baixar imagem**', fig6.to_image(format='png', width=750, height=500), 'img.png', key='fig6'
                )

            with pie2:
                st.subheader('Figura 7: Áreas de especialização mais comuns', anchor=False)
                st.caption('Por discente com vínculo concluído na graduação.')
                fig7 = func.get_viz(pd.DataFrame({'STATUS': top_area.index, 'COUNT': top_area.values}), 'pos')
                st.plotly_chart(fig7, use_container_width=True)
                fig7_bttn = st.download_button(
                    '**Baixar imagem**', fig7.to_image(format='png', width=750, height=500), 'img.png', key='fig7'
                )

            with st.container(border=True):
                st.subheader('Resumo', anchor=False)
                txt = f'''
                Dos discentes com vínculo concluído na graduação, **{df_pos['nome_discente'].count()}** se 
                inscreveram para 
                programas de pós-graduação e **{len(df_pos.query('status_discente == "CONCLUÍDO"'))}** completaram 
                as especializações. As três áreas de especialização mais comuns são 
                **{', '.join(x.capitalize() for x in top_area.index[:3])}**.
                '''

                st.write(txt)
                st.caption('Texto gerado automaticamente.')
    # '''
    # Segunda tab, usada para armazenamento dos dados
    # '''
    with tab2:

        # '''
        # Conjunto de dados da graduação
        # '''
        with st.container(border=True):
            st.subheader('Conjunto de Dados Sobre Discentes de Graduação', anchor=False)
            st.caption('Pré-visualização')
            data1, download1 = st.columns(2, gap='large')

            with data1:
                grad_data = pd.read_parquet('datasets/discentes_graduacao.parquet')
                for col in grad_data.columns:
                    grad_data[col] = grad_data[col].astype(str)

                st.dataframe(grad_data.head(10), use_container_width=True)
                st.caption('Fonte: https://dados.ufs.br/dataset/discentes_graduacao')

            with download1:
                st.write(
                    'Para realizar o download dos dados, especifique o formato do arquivo desejado:'
                )

                ext = st.radio(
                    'Extensões',
                    ['.xlsx', '.csv', '.json', '.parquet'],
                    captions=['Planilha excel', 'Valores separados por vírgulas',
                              'Notação de objetos JavaScript', 'Dados orientados a colunas'],
                    index=None, label_visibility='hidden', key='radio1'
                )

                file_to_download = func.convert_df(grad_data, ext)

                if ext:
                    file = func.convert_df(data, ext)
                    st.download_button(
                        label=f'**Baixar como {ext}**',
                        data=file_to_download,
                        file_name=f'evolucao_secretariado{ext}',
                        key='down1'
                    )

        st.write('---')

        # '''
        # Conjunto de dados da pós-graduação
        # '''
        with st.container(border=True):
            st.subheader('Conjunto de Dados Sobre Discentes de Pós-graduação', anchor=False)
            st.caption('Pré-visualização')
            data1, download1 = st.columns(2, gap='large')

            with data1:
                grad_data = pd.read_parquet('datasets/discentes_pos_graduacao.parquet')
                for col in grad_data.columns:
                    grad_data[col] = grad_data[col].astype(str)

                st.dataframe(grad_data.head(10), use_container_width=True)
                st.caption('Fonte: https://dados.ufs.br/dataset/discentes_pos_graduacao')

            with download1:
                st.write(
                    'Para realizar o download dos dados, especifique o formato do arquivo desejado:'
                )

                ext = st.radio(
                    'Extensões',
                    ['.xlsx', '.csv', '.json', '.parquet'],
                    captions=['Planilha excel', 'Valores separados por vírgulas',
                              'Notação de objetos JavaScript', 'Dados orientados a colunas'],
                    index=None, label_visibility='hidden', key='radio2'
                )

                file_to_download = func.convert_df(grad_data, ext)

                if ext:
                    file = func.convert_df(data, ext)
                    st.download_button(
                        label=f'**Baixar como {ext}**',
                        data=file_to_download,
                        file_name=f'evolucao_secretariado{ext}',
                        key='down2'
                    )

# '''
# Início do bloco referente aos dados da extensão e pesquisa
# '''

if category == 'Extensão e Pesquisa':
    my_datasets = func.get_dfs('datasets/atividades_extensao.parquet', 'extensao')
    ext_data = my_datasets['sec']

    for col in ext_data.columns[:-3]:
        ext_data[col] = ext_data[col].astype(str)

    tab1, tab2 = st.tabs(['📈 Gráficos', '🗃 Dados'])

    # '''
    # Tab 1: Visualização dos dados
    # '''
    with tab1:

        with st.container(border=True):
            st.header('Atividades de Extensão', anchor=False)
            st.write('**Defina a janela temporal da análise**')

            # define o filtro por ano
            start_year, end_year, null_space = st.columns([.25, .25, .5])
            years = ext_data['ano'].unique()

            with start_year:
                years = np.sort(years)
                min_year = str(st.selectbox('Início', years, index=0, key='year1.1'))
            with end_year:
                max_year = str(st.selectbox('Final', years[::-1], index=0, key='year1.2'))

        # dataset filtrado
        filtered_data = ext_data.query('@max_year >= ano >= @min_year')

        # '''
        # Figura 1 extensão
        # '''
        with st.container(border=True):
            st.subheader('Figura 1: Visão Geral das Atividades de Extensão ao Longo do Tempo', anchor=False)
            fig1 = func.get_viz(filtered_data, 'ext_geral')
            st.plotly_chart(fig1, use_container_width=True)
            fig1_bttn = st.download_button(
                '**Baixar imagem**', fig1.to_image(format='png', width=750, height=500), 'img.png', key='fig1'
            )
            st.write('---')

            pie1, pie2 = st.columns([.45, .55], gap='large')

            # '''
            # Figura 2 extensão
            # '''
            with pie1:
                st.subheader('Figura 2: Áreas Temáticas', anchor=False)
                fig2 = func.get_viz(filtered_data, 'ext_pie', 'area_tematica')
                st.plotly_chart(fig2, use_container_width=True)
                fig2_bttn = st.download_button(
                    '**Baixar imagem**', fig2.to_image(format='png', width=750, height=500), 'img.png', key='fig2'
                )

            # '''
            # Figura 3 extensão
            # '''
            with pie2:
                st.subheader('Figura 3: Linhas de Extensão', anchor=False)
                fig3 = func.get_viz(
                    filtered_data[filtered_data['linha_extensao'] != 'None'].copy(), 'ext_horizontal', 'linha_extensao'
                )
                st.plotly_chart(fig3, use_container_width=True)
                fig3_bttn = st.download_button(
                    '**Baixar imagem**', fig3.to_image(format='png', width=1200, height=800), 'img.png', key='fig3'
                )

            st.write('---')
            pie3, pie4 = st.columns([.46, .54], gap='large')

            # '''
            # Figura 4 extensão
            # '''
            with pie3:
                st.subheader('Figura 4: Financiamento das Atividades', anchor=False)
                data = filtered_data

                c1 = data['financiamento_externo'] == 'SIM'
                c2 = data['financiamento_interno'] == 'SIM'
                data['financiado'] = np.where(c1 | c2, 'SIM', 'NÃO')

                data['tipo'] = None
                for i, row in enumerate(
                        data[['financiado', 'financiamento_externo', 'financiamento_interno']].values):
                    if row[0] == 'SIM' and row[1] == 'SIM':
                        data.iloc[i, -1] = 'Financiamento externo'
                    elif row[0] == 'SIM' and row[-1] == 'SIM':
                        data.iloc[i, -1] = 'Financiamento interno'
                    else:
                        data.iloc[i, -1] = 'Sem financiamento'

                fig4 = func.get_viz(data, 'ext_pie', 'tipo')
                st.plotly_chart(fig4, use_container_width=True)
                fig4_bttn = st.download_button(
                    '**Baixar imagem**', fig4.to_image(format='png', width=1200, height=800), 'img.png', key='fig4'
                )

            # '''
            # Figura 5 extensão
            # '''
            with pie4:
                st.subheader('Figura 5: Ranking de Professores por Coordenação de Atividades', anchor=False)
                top_docentes = filtered_data['coordenador'].value_counts().sort_values(ascending=True)
                ranking = len(top_docentes)
                mask = []
                for _ in range(ranking):
                    mask.append(f'Top {ranking}')
                    ranking -= 1
                top_docentes.index = mask

                fig5 = px.bar(top_docentes, top_docentes.values, top_docentes.index, text_auto=True,
                              template='plotly_white', labels={'index': '', 'x': ''})
                fig5.update_traces(textangle=0, textposition='inside')
                fig5.update_layout(
                    uniformtext_minsize=10, uniformtext_mode='hide'
                )

                st.plotly_chart(fig5, use_container_width=True)
                fig5_bttn = st.download_button(
                    '**Baixar imagem**', fig5.to_image(format='png', width=1200, height=800), 'img.png', key='fig5'
                )

            st.write('---')

            non, space, non1 = st.columns([.3, .4, .3])
            with space:
                with st.container(border=True):
                    st.header('Bolsas concedidas:', anchor=False)
                    st.subheader(ext_data["bolsas_concedidas"].astype(int).sum(), anchor=False)

            st.write('---')

            # '''
            # Texto 1 extensão
            # '''
            with st.container(border=True):
                st.subheader('Resumo', anchor=False)
                top3_temas = (filtered_data.query("area_tematica != 'None'").groupby("area_tematica").size()
                              .sort_values(ascending=False).index[:3])
                top3_linhas = (filtered_data.query("linha_extensao != 'None'").groupby("linha_extensao").size()
                               .sort_values(ascending=False).index[:3])
                atv_ano = filtered_data.groupby("ano", as_index=False).size().sort_values(by='size', ascending=False)

                if min_year != max_year:
                    txt = f'''
                    No período de **{filtered_data["ano"].min()}** a **{filtered_data["ano"].max()}** 
                    o departamento de Secretariado 
                    realizou um total de **{filtered_data["ano"].count()}** atividades de extensão, 
                    **{len(data[data['financiado'] == 'SIM'])}** destas foram com financiamento. O ano de 
                    **{atv_ano["ano"].values[0]}** se destacou pelo número significativo de atividades desenvolvidas, 
                    enquanto **{atv_ano["ano"].values[-1]}** registrou o menor número delas. As atividades concentram-se 
                    principalmente nas temáticas de **{", ".join(t.capitalize() for t in top3_temas)}**, com as 
                    principais 
                    linhas abordando **{", ".join(t.capitalize() for t in top3_linhas)}**. Três professores do 
                    departamento
                    coordenaram cerca de 
                    **{round(filtered_data['coordenador'].value_counts(normalize=True)
                             .sort_values(ascending=False)[:3].sum() * 100)}%** das atividades desenvolvidas.
                    '''
                else:
                    txt = f'''
                    No período de **{filtered_data["ano"].min()}** o departamento de Secretariado 
                    realizou um total de **{filtered_data["ano"].count()}** atividades de extensão, 
                    **{len(data[data['financiado'] == 'SIM'])}** destas foram com financiamento. As atividades 
                    concentram-se principalmente nas temáticas de **{", ".join(t.capitalize() for t in top3_temas)}**, 
                    com as principais linhas abordando **{", ".join(t.capitalize() for t in top3_linhas)}**. 
                    Três professores do departamento coordenaram cerca de 
                    **{round(filtered_data['coordenador'].value_counts(normalize=True)
                             .sort_values(ascending=False)[:3].sum() * 100)}%** das atividades desenvolvidas.
                    '''
                st.write(txt)
                st.caption('Texto gerado automaticamente')

        st.write('---')

        # '''
        # Bloco destinado à comparação entre o departamento de secretariado e o ccsa ou a ufs
        # '''
        with st.container(border=True):
            st.header('Comparação com outras unidades', anchor=False)
            st.write('**Defina a janela temporal da análise**')

            # define o filtro por ano
            star_year, end_year, null_space = st.columns([.25, .25, .5])
            years = ext_data['ano'].unique()

            with star_year:
                years = np.sort(years)
                min_year = str(st.selectbox('Início', years, index=0, key='comp_year1'))
            with end_year:
                max_year = str(st.selectbox('Final', years[::-1], index=0, key='comp_year2'))
            with null_space:
                comp = st.selectbox('Defina a unidade de comparação', ['CCSA', 'UFS'], index=0)

        # '''
        # Container com as figuras de comparação
        # '''
        with st.container(border=True):

            comp1, comp2 = st.columns(2, gap='large')

            # Figura 1
            with comp1:
                df_comp_bar = func.get_dfs('datasets/atividades_extensao.parquet',
                                           'extensao_comp', 'tipo_atividade', min_year, max_year)

                if comp == 'CCSA':
                    df_comp_bar = df_comp_bar.query('unidade.isin(["DEPARTAMENTO DE SECRETARIADO", "CCSA"])')
                else:
                    df_comp_bar = df_comp_bar.query('unidade.isin(["DEPARTAMENTO DE SECRETARIADO", "UFS"])')

                st.subheader('Figura 6: Desenvolvimento de atividades', anchor=False)
                st.caption(f'Mediana dos cursos da unidade {comp}')
                fig6 = func.get_viz(df_comp_bar, 'ext_comp')
                st.plotly_chart(fig6, use_container_width=True)
                fig6_bttn = st.download_button(
                    '**Baixar imagem**', fig6.to_image(format='png', width=1200, height=800), 'img.png', key='fig6'
                )

            # Figura 2
            with comp2:
                df_comp_pie = func.get_dfs('datasets/atividades_extensao.parquet', 'extensao_comp', 'area_tematica',
                                           min_year, max_year).query('area_tematica != "None"')

                if comp == 'CCSA':
                    df_comp_pie = df_comp_pie.query('unidade.isin(["DEPARTAMENTO DE SECRETARIADO", "CCSA"])')
                else:
                    df_comp_pie = df_comp_pie.query('unidade.isin(["DEPARTAMENTO DE SECRETARIADO", "UFS"])')

                st.subheader('Figura 7: Top 5 Áreas Temáticas', anchor=False)
                st.caption(f'Mediana dos cursos da unidade {comp}')
                fig7 = func.get_viz(df_comp_pie, 'ext_comp_pie')
                st.plotly_chart(fig7, use_container_width=True)
                fig7_bttn = st.download_button(
                    '**Baixar imagem**', fig7.to_image(format='png', width=1200, height=800), 'img.png', key='fig7'
                )

            st.write('---')

            comp3, comp4 = st.columns(2, gap='large')

            # Figura 3
            with comp3:
                df_comp_hbar = func.get_dfs('datasets/atividades_extensao.parquet', 'extensao_comp', 'linha_extensao',
                                            min_year, max_year).query('linha_extensao != "None"')

                if comp == 'CCSA':
                    df_comp_hbar = df_comp_hbar.query('unidade.isin(["DEPARTAMENTO DE SECRETARIADO", "CCSA"])')
                else:
                    df_comp_hbar = df_comp_hbar.query('unidade.isin(["DEPARTAMENTO DE SECRETARIADO", "UFS"])')

                st.subheader('Figura 8: Top 5 Linhas de Extensão', anchor=False)
                st.caption(f'Mediana dos cursos da unidade {comp}')
                fig8 = func.get_viz(df_comp_hbar, 'ext_comp_hbar')
                st.plotly_chart(fig8, use_container_width=True)
                fig8_bttn = st.download_button(
                    '**Baixar imagem**', fig8.to_image(format='png', width=1200, height=800), 'img.png', key='fig8'
                )

            with comp4:
                df_comp_pie_financ = func.get_dfs('datasets/atividades_extensao.parquet',
                                                  'extensao_comp_financiamento', min_year, max_year)

                if comp == 'CCSA':
                    df_comp_pie_financ = df_comp_pie_financ.query(
                        'unidade.isin(["DEPARTAMENTO DE SECRETARIADO", "CCSA"])')
                else:
                    df_comp_pie_financ = df_comp_pie_financ.query(
                        'unidade.isin(["DEPARTAMENTO DE SECRETARIADO", "UFS"])')

                st.subheader('Figura 9: Financiamento e Origem', anchor=False)
                st.caption(f'Mediana dos cursos da unidade {comp}')
                fig9 = func.get_viz(df_comp_pie_financ, 'ext_comp_pie')
                st.plotly_chart(fig9, use_container_width=True)
                fig9_bttn = st.download_button(
                    '**Baixar imagem**', fig9.to_image(format='png', width=1200, height=800), 'img.png', key='fig9'
                )

            st.write('---')

            none, card, none1 = st.columns([.3, .4, .3])
            with card:
                with st.container(border=True):
                    st.header('Concessão de Bolsas', anchor=False)
                    st.caption(f'Mediana dos cursos da unidade {comp}')
                    st.subheader(f'SEC: {my_datasets["sec"]["bolsas_concedidas"].astype(int).sum()}', anchor=False)
                    st.subheader(f'{comp}: {round(float(np.median(my_datasets[comp.lower()])))}', anchor=False)

        st.write('---')

        # '''
        # Bloco destinado às visualizações da Pesquisa
        # '''
        with st.container(border=True):

            pesq_data = func.get_dfs('datasets/projetos_pesquisa.parquet', 'pesquisa')

            st.header('Projetos de Pesquisa', anchor=False)
            st.write('**Defina a janela temporal da análise**')

            # define o filtro por ano
            star_year, end_year, null_space = st.columns([.25, .25, .5])
            pesq_years = pesq_data['ano_projeto'].unique()

            with star_year:
                min_year = str(st.selectbox('Início', pesq_years[::-1], index=0, key='pesq_year'))
            with end_year:
                years = np.sort(years)
                max_year = str(st.selectbox('Final', pesq_years, index=0, key='pesq_year2'))

            pesq_data = pesq_data.query('@max_year >= ano_projeto >= @min_year')

        with st.container(border=True):
            st.subheader('Figura 10: Projetos de Pesquisa ao Longo do Tempo', anchor=False)
            fig10 = func.get_viz(pesq_data, 'pesquisa')
            st.plotly_chart(fig10, use_container_width=True)
            fig10_bttn = st.download_button(
                '**Baixar imagem**', fig10.to_image(format='png', width=1200, height=800), 'img.png', key='fig10'
            )

            st.write('---')

            tb1, tb2 = st.columns([.55, .33], gap='large')
            with tb1:
                data = pesq_data.query('situacao == "EM EXECUÇÃO"')['titulo'].unique()
                projects = [title.title() for title in data]
                df_projects = pd.DataFrame({'Projetos de Pesquisa': projects})

                st.subheader('Tabela 1: Projetos de Pesquisa em Execução', anchor=False)
                st.caption('Do curso de Secretariado')
                st.dataframe(df_projects, width=820, hide_index=True,
                             column_config={'Projetos de Pesquisa': 'Projeto de Pesquisa'}, use_container_width=True)
                st.download_button('**Baixar tabela**', func.convert_df(df_projects, '.csv'),
                                   'tbProjetos.csv', key='tb1')

            with tb2:
                st.subheader('Tabela 2: Palavras-chave', anchor=False)
                st.caption('Com exceção de palavras-chave comuns como "Secretariado Executivo"')
                tb2 = func.get_viz(pesq_data, 'pesq_keywords')
                st.dataframe(tb2, width=420, hide_index=True, use_container_width=True)
                st.download_button('**Baixar tabela**', func.convert_df(tb2, '.csv'),
                                   'tbPalvrasChave.csv', key='tb2')

            st.write('---')

            tb3, tb4 = st.columns(2, gap='large')
            with tb3:
                data_gp = (pesq_data.query('situacao == "EM EXECUÇÃO"').groupby('grupo_pesquisa', as_index=False)
                           ['titulo'].count().sort_values(by='titulo', ascending=False))

                st.subheader('Tabela 3: Projetos em Execução por Grupos de Pesquisa', anchor=False)
                st.dataframe(data_gp, width=620, column_config={
                    'grupo_pesquisa': 'Grupo de Pesquisa', 'titulo': 'Projetos'},
                             hide_index=True, use_container_width=True)
                st.download_button('**Baixar tabela**', func.convert_df(data_gp, '.csv'),
                                   'tbGrupos.csv', key='tb3')

            with tb4:
                st.subheader('Tabela 4: Linhas de Pesquisa', anchor=False)
                data_lin = (pesq_data.groupby('linha_pesquisa', as_index=False)
                            .size().sort_values(by='size', ascending=False))
                st.dataframe(data_lin,
                             column_config={'linha_pesquisa': 'Linha de Pesquisa', 'size': 'Ocorrências'},
                             width=620, hide_index=True, use_container_width=True)
                st.download_button('**Baixar tabela**',
                                   func.convert_df(data_lin.sort_values(by='size', ascending=False), '.csv'),
                                   'tbLinhas.csv', key='tb4')

            st.write('---')

            empty1, tb5, empty2 = st.columns([.3, .4, .3])
            with tb5:
                st.subheader('Tabela 5: Área do Conhecimento', anchor=False)
                st.caption('Classificação CNPq')
                df_area = (pesq_data.groupby('area_conhecimento_cnpq', as_index=False)
                           .size().sort_values(by='size', ascending=False))
                st.dataframe(df_area, width=620, hide_index=True,
                             column_config={'area_conhecimento_cnpq': 'Área do Conhecimento', 'size': 'Ocorrências'},
                             use_container_width=True)
                st.download_button('**Baixar tabela**',
                                   func.convert_df(
                                       pesq_data.groupby('area_conhecimento_cnpq', as_index=False)
                                       .size().sort_values(by='size', ascending=False),
                                       '.csv'), 'tbAreas.csv', key='tb5')

            st.write('---')
            with st.container(border=True):
                data = pesq_data.groupby('ano_projeto', as_index=False)['codigo_projeto'].size()
                max_projects = data.loc[data['size'] == data['size'].max()]

                top_gp = (data_gp['grupo_pesquisa'].values[0]
                          if data_gp['grupo_pesquisa'].values[0].lower().startswith('grupo')
                          else f'Grupo de Pesquisa {data_gp["grupo_pesquisa"].values[0]}')

                txt = f'''Atualmente o Departamento de Secretariado Executivo conduz **{len(df_projects)}**
                projetos de pesquisa, focalizando principalmente nos temas 
                **{', '.join(tb2.head(3)['Palavras-chave'].values)}**, distribuídos entre **{len(data_gp)}** grupos de 
                pesquisa. O **{top_gp}** lidera com **{data_gp['titulo'].values[0]}** projetos em execução. 
                As principais linhas de pesquisa abrangem **{', '.join(data_lin.head(3)["linha_pesquisa"].values)}**, 
                e exploram áreas do conhecimento como **{', '.join(df_area.head(3)["area_conhecimento_cnpq"].values)}.**
                '''

                st.subheader('Resumo', anchor=False)
                st.write(txt)
                st.caption('Texto gerado automaticamente')

        st.write('---')

        with st.container(border=True):
            st.header('Comparação com outras unidade', anchor=False)

            # define o filtro por ano
            star_year, end_year, null_space = st.columns([.25, .25, .5])
            years = pesq_data['ano_projeto'].unique()

            with star_year:
                years = np.sort(years)
                min_year = str(st.selectbox('Início', years, index=0, key='comp_pesq'))
            with end_year:
                max_year = str(st.selectbox('Final', years[::-1], index=0, key='comp_pesq2'))
            with null_space:
                comp = st.selectbox('Defina a unidade de comparação', ['CCSA', 'UFS'], index=0, key='comp_pesq_y')

        with st.container(border=True):
            pesq_comp1, pesq_comp2 = st.columns(2, gap='large')

            with pesq_comp1:
                df_pesq_comp = func.get_dfs(
                    'datasets/projetos_pesquisa.parquet', 'pesq_comp', min_year, max_year, 'situacao'
                ).query('unidade.isin(["SEC", @comp])')

                st.subheader('Figura 11: Desenvolvimento de Projetos', anchor=False)
                st.caption(f'Mediana dos cursos da unidade {comp}')
                fig11 = func.get_viz(df_pesq_comp, 'pesq_comp_bars')
                st.plotly_chart(fig11, use_container_width=True)
                fig11_bttn = st.download_button(
                    '**Baixar imagem**', fig11.to_image(format='png', width=750, height=500), 'img.png', key='fig11'
                )

            with pesq_comp2:
                df_pesq_comp2 = func.get_dfs(
                    'datasets/projetos_pesquisa.parquet', 'pesq_comp', min_year, max_year, 'palavras_chave'
                ).query('unidade.isin(["SEC", @comp])')

                @st.cache_data
                def clean_keywords(data_inp):
                    dfs = []
                    for unity in ['SEC', comp]:
                        dataset = data_inp.query('unidade == @unity')

                        for sign in [',', '.', ':', '-']:
                            dataset['palavras_chave'] = dataset['palavras_chave'].str.replace(sign, ';', regex=False)

                        dataset['palavras_chave'] = dataset['palavras_chave'].str.lower()

                        keywords = []
                        for lin in dataset['palavras_chave'].values:
                            w = [x.strip() for x in lin.split(';') if x != '' and x != ' ']
                            keywords.extend(w)

                        keywords_size = {}
                        for w in keywords:
                            if w.title() not in keywords_size:
                                keywords_size[w.title()] = 1
                            else:
                                keywords_size[w.title()] += 1

                        stopwords = ['Secretariado', 'Secretariado Executivo', 'Universidade Federal De Sergipe',
                                     'Ufs', 'UFS', 'Sergipe', 'Turismo', 'Serviço Social']
                        df_words = pd.DataFrame(
                            {'Palavra-chave': keywords_size.keys(), 'Ocorrências': keywords_size.values()}
                        ).sort_values(by='Ocorrências', ascending=False).query('~`Palavra-chave`.isin(@stopwords)')
                        df_words['unidade'] = unity
                        dfs.append(df_words)

                    df_concat = pd.concat(dfs, ignore_index=True)

                    return df_concat

                st.subheader('Figura 12: Palvras-chave', anchor=False)
                st.caption('Com execeção de palavras comuns (UFS) e nomes de cursos (Serviço Social)')
                fig12 = func.get_viz(clean_keywords(df_pesq_comp2), 'pesq_comp_hbars')
                st.plotly_chart(fig12, use_container_width=True)
                fig12_bttn = st.download_button(
                    '**Baixar imagem**', fig12.to_image(format='png', width=750, height=500), 'img.png', key='fig12'
                )

            st.write('---')

            pesq_comp3, pesq_comp4 = st.columns(2, gap='large')
            with pesq_comp3:
                df_pesq_comp3 = func.get_dfs(
                    'datasets/projetos_pesquisa.parquet', 'pesq_comp', min_year, max_year, 'linha_pesquisa'
                ).query('unidade.isin(["SEC", @comp])')

                st.subheader('Figura 13: Linhas de Pesquisa', anchor=False)
                st.caption(f'Mediana dos cursos da unidade {comp}')
                fig13 = func.get_viz(df_pesq_comp3, 'pesq_comp_hbars')
                st.plotly_chart(fig13, use_container_width=True)
                fig13_bttn = st.download_button(
                    '**Baixar imagem**', fig13.to_image(format='png', width=750, height=500), 'img.png', key='fig13'
                )

            with pesq_comp4:
                df_pesq_comp3 = func.get_dfs(
                    'datasets/projetos_pesquisa.parquet', 'pesq_comp', min_year, max_year, 'area_conhecimento_cnpq'
                ).query('unidade.isin(["SEC", @comp])')

                st.subheader('Figura 14: Áreas do Conhecimento', anchor=False)
                st.caption(f'Mediana dos cursos da unidade {comp}')
                fig14 = func.get_viz(df_pesq_comp3, 'pesq_comp_hbars')
                st.plotly_chart(fig14, use_container_width=True)
                fig14_bttn = st.download_button(
                    '**Baixar imagem**', fig14.to_image(format='png', width=750, height=500), 'img.png', key='fig14'
                )

    with tab2:

        with st.container(border=True):
            st.subheader('Conjunto de Dados Sobre Atividades de Extensão', anchor=False)
            st.caption('Pré-visualização')
            data1, download1 = st.columns(2, gap='large')

            with data1:
                grad_data = pd.read_parquet('datasets/atividades_extensao.parquet')
                for col in grad_data.columns:
                    grad_data[col] = grad_data[col].astype(str)

                st.dataframe(grad_data.head(10), use_container_width=True)
                st.caption('Fonte: https://dados.ufs.br/dataset/atividades_extensao')

            with download1:
                st.write(
                    'Para realizar o download dos dados, especifique o formato do arquivo desejado:'
                )

                ext = st.radio(
                    'Extensões',
                    ['.xlsx', '.csv', '.json', '.parquet'],
                    captions=['Planilha excel', 'Valores separados por vírgulas',
                              'Notação de objetos JavaScript', 'Dados orientados a colunas'],
                    index=None, label_visibility='hidden', key='radio1.1'
                )

                file_to_download = func.convert_df(grad_data, ext)

                if ext:
                    file = func.convert_df(data, ext)
                    st.download_button(
                        label=f'**Baixar como {ext}**',
                        data=file_to_download,
                        file_name=f'atividades_extensao{ext}',
                        key='down1.1'
                    )

        with st.container(border=True):
            st.subheader('Conjunto de Dados Sobre Projetos de Pesquisa', anchor=False)
            st.caption('Pré-visualização')
            data1, download1 = st.columns(2, gap='large')

            with data1:
                grad_data = pd.read_parquet('datasets/projetos_pesquisa.parquet')
                for col in grad_data.columns:
                    grad_data[col] = grad_data[col].astype(str)

                st.dataframe(grad_data.head(10), use_container_width=True)
                st.caption('Fonte: https://dados.ufs.br/dataset/projetos_pesquisa')

            with download1:
                st.write(
                    'Para realizar o download dos dados, especifique o formato do arquivo desejado:'
                )

                ext = st.radio(
                    'Extensões',
                    ['.xlsx', '.csv', '.json', '.parquet'],
                    captions=['Planilha excel', 'Valores separados por vírgulas',
                              'Notação de objetos JavaScript', 'Dados orientados a colunas'],
                    index=None, label_visibility='hidden', key='radio2.1'
                )

                file_to_download = func.convert_df(grad_data, ext)

                if ext:
                    file = func.convert_df(data, ext)
                    st.download_button(
                        label=f'**Baixar como {ext}**',
                        data=file_to_download,
                        file_name=f'projetos_pesquisa{ext}',
                        key='down2.1'
                    )
