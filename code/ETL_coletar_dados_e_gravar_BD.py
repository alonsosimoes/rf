from datetime import date
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import create_engine
import bs4 as bs
import ftplib
import gzip
import os
import pandas as pd
import psycopg2
import re
import sys
import time
import urllib.request
import wget
import zipfile
import logging

try:
    #Config Log
    # DateTime:Level:Arquivo:Mensagem
    log_format = '%(asctime)s:%(levelname)s:%(message)s'
    '''
    Aqui definimos as configurações do modulo.

    filename = 'nome do arquivo em que vamos salvar a mensagem do log.'
    filemode = 'É a forma em que o arquivo será gravado.'
    level = 'Level em que o log atuará'
    format = 'Formatação da mensagem do log'
    '''
    logging.basicConfig(filename='exemplo.log',
                        # w -> sobrescreve o arquivo a cada log
                        # a -> não sobrescreve o arquivo
                        filemode='a',
                        level=logging.DEBUG,
                        format=log_format)

    '''
    O objeto getLogger() permite que retornemos
    varias instancias de logs.
    '''
    # Instancia do objeto getLogger()
    logger = logging.getLogger('root')

    #%%
    def getEnv(env):
        return os.getenv(env)

    load_dotenv()

    dados_rf = 'http://200.152.38.155/CNPJ/'
    output_files = Path(getEnv('OUTPUT_FILES_PATH'))
    extracted_files = Path(getEnv('EXTRACTED_FILES_PATH'))
    raw_html = urllib.request.urlopen(dados_rf)
    raw_html = raw_html.read()

    # Formatar página e converter em string
    page_items = bs.BeautifulSoup(raw_html, 'lxml')
    html_str = str(page_items)

    # Obter arquivos
    Files = []
    text = '.zip'
    for m in re.finditer(text, html_str):
        i_start = m.start()-40
        i_end = m.end()
        i_loc = html_str[i_start:i_end].find('href=')+6
        logger.info(html_str[i_start+i_loc:i_end])
        print(html_str[i_start+i_loc:i_end])
        Files.append(html_str[i_start+i_loc:i_end])

    logger.info('Arquivos que serão baixados:')
    print('Arquivos que serão baixados:')
    i_f = 0
    for f in Files:
        i_f += 1
        logger.info(str(i_f) + ' - ' + f)
        print(str(i_f) + ' - ' + f)
    #%%
    ########################################################################################################################
    ## DOWNLOAD ############################################################################################################
    ########################################################################################################################

    # Download files
    # Create this bar_progress method which is invoked automatically from wget:
    def bar_progress(current, total, width=80):
        progress_message = "Downloading: %d%% [%d / %d] bytes - " % (current / total * 100, current, total)
        # Don't use print() as it will print in new line every time.
        sys.stdout.write("\r" + progress_message)
        sys.stdout.flush()

    #%%
    # Download arquivos ################################################################################################################################
    #i_l = 0
    #for l in Files:
    #    # Download dos arquivos
    #    i_l += 1
    #    print('Baixando arquivo:')
    #    print(str(i_l) + ' - ' + l)
    #    url = dados_rf+l
    #    wget.download(url, out=output_files, bar=bar_progress)

    #%%
    # Download layout:
    #Layout = 'https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/cadastros/consultas/arquivos/NOVOLAYOUTDOSDADOSABERTOSDOCNPJ.pdf'
    #print('Baixando layout:')
    #wget.download(Layout, out=str(output_files), bar=bar_progress)

    ####################################################################################################################################################
    #%%
    # Creating directory to store the extracted files:
    if not os.path.exists(extracted_files):
        os.mkdir(extracted_files)

    # Extracting files:
    #i_l = 0
    #for l in Files:
    #    try:
    #        i_l += 1
    #        print('Descompactando arquivo:')
    #        print(str(i_l) + ' - ' + l)
    #        with zipfile.ZipFile(output_files / l, 'r') as zip_ref:
    #            zip_ref.extractall(extracted_files)
    #    except:
    #        pass

    #%%
    ########################################################################################################################
    ## LER E INSERIR DADOS #################################################################################################
    ########################################################################################################################
    insert_start = time.time()

    # Files:
    Items = [name for name in os.listdir(extracted_files) if name.endswith('')]

    # Separar arquivos:
    arquivos_empresa = []
    arquivos_estabelecimento = []
    arquivos_socios = []
    arquivos_simples = []
    arquivos_cnae = []
    arquivos_moti = []
    arquivos_munic = []
    arquivos_natju = []
    arquivos_pais = []
    arquivos_quals = []
    arquivos_tribu = []
    for i in range(len(Items)):
        if Items[i].find('EMPRE') > -1:
            arquivos_empresa.append(Items[i])
        elif Items[i].find('ESTABELE') > -1:
            arquivos_estabelecimento.append(Items[i])
        elif Items[i].find('SOCIO') > -1:
            arquivos_socios.append(Items[i])
        elif Items[i].find('SIMPLES') > -1:
            arquivos_simples.append(Items[i])
        elif Items[i].find('CNAE') > -1:
            arquivos_cnae.append(Items[i])
        elif Items[i].find('MOTI') > -1:
            arquivos_moti.append(Items[i])
        elif Items[i].find('MUNIC') > -1:
            arquivos_munic.append(Items[i])
        elif Items[i].find('NATJU') > -1:
            arquivos_natju.append(Items[i])
        elif Items[i].find('PAIS') > -1:
            arquivos_pais.append(Items[i])
        elif Items[i].find('QUALS') > -1:
            arquivos_quals.append(Items[i])
        elif Items[i].find('LUCRO') > -1:
            arquivos_tribu.append(Items[i])
        elif Items[i].find('IMUNES') > -1:
            arquivos_tribu.append(Items[i])
        else:
            pass

    #%%
    # Conectar no banco de dados:
    # Dados da conexão com o BD
    user=getEnv('DB_USER')
    passw=getEnv('DB_PASSWORD')
    host=getEnv('DB_HOST')
    port=getEnv('DB_PORT')
    database=getEnv('DB_NAME')

    # Conectar:
    engine = create_engine('postgresql://'+user+':'+passw+'@'+host+':'+port+'/'+database)
    conn = psycopg2.connect('dbname='+database+' '+'user='+user+' '+'host='+host+' '+'password='+passw)
    cur = conn.cursor()

    
    '''

    #%%
    # Arquivos de empresa:
    empresa_insert_start = time.time()

    logger.info("""
    #######################
    ## Arquivos de EMPRESA:
    #######################
    """)
    print("""
    #######################
    ## Arquivos de EMPRESA:
    #######################
    """)
    # Drop table antes do insert
    cur.execute('DROP TABLE IF EXISTS "empresa";')
    conn.commit()

    for e in range(0, len(arquivos_empresa)):
        logger.info('Trabalhando no arquivo: '+arquivos_empresa[e]+' [...]')
        print('Trabalhando no arquivo: '+arquivos_empresa[e]+' [...]')
        try:
            del empresa
        except:
            pass

        # Verificar tamanho do arquivo:
        logger.info('Lendo o arquivo ' + arquivos_empresa[e]+' [...]')
        print('Lendo o arquivo ' + arquivos_empresa[e]+' [...]')
        extracted_file_path = Path(f'{extracted_files}/{arquivos_empresa[e]}')

        empresa_lenght = sum(1 for line in open(extracted_file_path, "r", encoding='latin1'))
        logger.info('Linhas no arquivo do Empresa '+ arquivos_empresa[e] +': '+str(empresa_lenght))
        print('Linhas no arquivo do Empresa '+ arquivos_empresa[e] +': '+str(empresa_lenght))

        tamanho_das_partes = 500000 # Registros por carga
        partes = round(empresa_lenght / tamanho_das_partes)
        nrows = tamanho_das_partes
        skiprows = 0

        logger.info('Este arquivo será dividido em ' + str(partes) + ' partes para inserção no banco de dados')
        print('Este arquivo será dividido em ' + str(partes) + ' partes para inserção no banco de dados')


        for i in range(0, partes):
            logger.info('Iniciando a parte ' + str(i+1) + ' [...]')
            print('Iniciando a parte ' + str(i+1) + ' [...]')
            empresa = pd.DataFrame(columns=[0, 1, 2, 3, 4, 5, 6])

            empresa_dtypes = {0: 'object', 1: 'object', 2: 'object', 3: 'object', 4: 'object', 5: 'object', 6: 'object'}
            extracted_file_path = Path(f'{extracted_files}/{arquivos_empresa[e]}')

            empresa = pd.read_csv(filepath_or_buffer=extracted_file_path,
                            sep=';',
                            nrows=nrows,
                            skiprows=skiprows,
                            encoding='latin1',
                            header=None,
                            dtype=empresa_dtypes)

            # Tratamento do arquivo antes de inserir na base:
            empresa = empresa.reset_index()
            del empresa['index']

            # Renomear colunas
            empresa.columns = ['cnpj_basico', 'razao_social', 'natureza_juridica', 'qualificacao_responsavel', 'capital_social', 'porte_empresa', 'ente_federativo_responsavel']

            # Replace "," por "."
            empresa['capital_social'] = empresa['capital_social'].apply(lambda x: x.replace(',','.'))
            empresa['capital_social'] = empresa['capital_social'].astype(float)

            skiprows = skiprows+nrows

            # Gravar dados no banco:
            # Empresa
            empresa.to_sql(name='empresa', con=engine, if_exists='append', index=False)
            logger.info('Arquivo ' + arquivos_empresa[e] + ' inserido com sucesso no banco de dados! - Parte '+ str(i+1))
            print('Arquivo ' + arquivos_empresa[e] + ' inserido com sucesso no banco de dados! - Parte '+ str(i+1))

            try:
                del empresa
            except:
                pass
    try:
        del empresa
    except:
        pass
    logger.info('Arquivos de empresa finalizados!')
    print('Arquivos de empresa finalizados!')
    empresa_insert_end = time.time()
    empresa_Tempo_insert = round((empresa_insert_end - empresa_insert_start))
    logger.info('Tempo de execução do processo de empresa (em segundos): ' + str(empresa_Tempo_insert))
    print('Tempo de execução do processo de empresa (em segundos): ' + str(empresa_Tempo_insert))
    
    
    #%%
    # Arquivos de estabelecimento:
    estabelecimento_insert_start = time.time()

    logger.info("""
    ############################### 
    ## Arquivos de ESTABELECIMENTO:
    ###############################
    """)

    print("""
    ############################### 
    ## Arquivos de ESTABELECIMENTO:
    ###############################
    """)

    # Drop table antes do insert
    cur.execute('DROP TABLE IF EXISTS "estabelecimento";')
    conn.commit()

    for e in range(0, len(arquivos_estabelecimento)):
        logger.info('Trabalhando no arquivo: '+arquivos_estabelecimento[e]+' [...]')
        print('Trabalhando no arquivo: '+arquivos_estabelecimento[e]+' [...]')
        try:
            del estabelecimento
        except:
            pass

        # Verificar tamanho do arquivo:
        logger.info('Lendo o arquivo ' + arquivos_estabelecimento[e]+' [...]')
        print('Lendo o arquivo ' + arquivos_estabelecimento[e]+' [...]')
        extracted_file_path = Path(f'{extracted_files}/{arquivos_estabelecimento[e]}')

        estabelecimento_lenght = sum(1 for line in open(extracted_file_path, "r", encoding='latin1'))
        logger.info('Linhas no arquivo do estabelecimento '+ arquivos_estabelecimento[e] +': '+str(estabelecimento_lenght))
        print('Linhas no arquivo do estabelecimento '+ arquivos_estabelecimento[e] +': '+str(estabelecimento_lenght))

        tamanho_das_partes = 500000 # Registros por carga
        partes = round(estabelecimento_lenght / tamanho_das_partes)
        nrows = tamanho_das_partes
        skiprows = 0

        logger.info('Este arquivo será dividido em ' + str(partes) + ' partes para inserção no banco de dados')
        print('Este arquivo será dividido em ' + str(partes) + ' partes para inserção no banco de dados')


        for i in range(0, partes):
            logger.info('Iniciando a parte ' + str(i+1) + ' [...]')
            print('Iniciando a parte ' + str(i+1) + ' [...]')
            estabelecimento = pd.DataFrame(columns=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28])
        
            extracted_file_path = Path(f'{extracted_files}/{arquivos_estabelecimento[e]}')

            estabelecimento = pd.read_csv(filepath_or_buffer=extracted_file_path,
                            sep=';',
                            nrows=nrows,
                            skiprows=skiprows,
                            encoding='latin1',
                            header=None,
                            dtype='object')

            # Tratamento do arquivo antes de inserir na base:
            estabelecimento = estabelecimento.reset_index()
            del estabelecimento['index']

            # Renomear colunas
            estabelecimento.columns = ['cnpj_basico',
                                    'cnpj_ordem',
                                    'cnpj_dv',
                                    'identificador_matriz_filial',
                                    'nome_fantasia',
                                    'situacao_cadastral',
                                    'data_situacao_cadastral',
                                    'motivo_situacao_cadastral',
                                    'nome_cidade_exterior',
                                    'pais',
                                    'data_inicio_atividade',
                                    'cnae_fiscal_principal',
                                    'cnae_fiscal_secundaria',
                                    'tipo_logradouro',
                                    'logradouro',
                                    'numero',
                                    'complemento',
                                    'bairro',
                                    'cep',
                                    'uf',
                                    'municipio',
                                    'ddd_1',
                                    'telefone_1',
                                    'ddd_2',
                                    'telefone_2',
                                    'ddd_fax',
                                    'fax',
                                    'correio_eletronico',
                                    'situacao_especial',
                                    'data_situacao_especial']

            skiprows = skiprows+nrows
            # Gravar dados no banco:
            # estabelecimento
            estabelecimento.to_sql(name='estabelecimento', con=engine, if_exists='append', index=False)
            logger.info('Arquivo ' + arquivos_estabelecimento[e] + ' inserido com sucesso no banco de dados! - Parte '+ str(i+1))
            print('Arquivo ' + arquivos_estabelecimento[e] + ' inserido com sucesso no banco de dados! - Parte '+ str(i+1))
            try:
                del estabelecimento
            except:
                pass

    try:
        del estabelecimento
    except:
        pass
    logger.info('Arquivos de estabelecimento finalizados!')
    print('Arquivos de estabelecimento finalizados!')
    estabelecimento_insert_end = time.time()
    estabelecimento_Tempo_insert = round((estabelecimento_insert_end - estabelecimento_insert_start))
    logger.info('Tempo de execução do processo de estabelecimento (em segundos): ' + str(estabelecimento_Tempo_insert))
    print('Tempo de execução do processo de estabelecimento (em segundos): ' + str(estabelecimento_Tempo_insert))

    #%%
    # Arquivos de socios:
    socios_insert_start = time.time()

    logger.info("""
    ######################
    ## Arquivos de SOCIOS:
    ######################
    """)

    print("""
    ######################
    ## Arquivos de SOCIOS:
    ######################
    """)

    # Drop table antes do insert
    cur.execute('DROP TABLE IF EXISTS "socios";')
    conn.commit()

    for e in range(0, len(arquivos_socios)):
        logger.info('Trabalhando no arquivo: '+arquivos_socios[e]+' [...]')  
        print('Trabalhando no arquivo: '+arquivos_socios[e]+' [...]')  
        try:
            del socios
        except:
            pass

        # Verificar tamanho do arquivo:
        logger.info('Lendo o arquivo ' + arquivos_socios[e]+' [...]')
        print('Lendo o arquivo ' + arquivos_socios[e]+' [...]')
        
        extracted_file_path = Path(f'{extracted_files}/{arquivos_socios[e]}')

        socios_lenght = sum(1 for line in open(extracted_file_path, "r", encoding='latin1'))
        logger.info('Linhas no arquivo do socios '+ arquivos_socios[e] +': '+str(socios_lenght))
        print('Linhas no arquivo do socios '+ arquivos_socios[e] +': '+str(socios_lenght))

        tamanho_das_partes = 500000 # Registros por carga
        partes = round(socios_lenght / tamanho_das_partes)
        nrows = tamanho_das_partes
        skiprows = 0

        logger.info('Este arquivo será dividido em ' + str(partes) + ' partes para inserção no banco de dados')
        print('Este arquivo será dividido em ' + str(partes) + ' partes para inserção no banco de dados')


        for i in range(0, partes):
            logger.info('Iniciando a parte ' + str(i+1) + ' [...]')
            print('Iniciando a parte ' + str(i+1) + ' [...]')
     
            extracted_file_path = Path(f'{extracted_files}/{arquivos_socios[e]}')
            socios = pd.DataFrame(columns=[1,2,3,4,5,6,7,8,9,10,11])
            socios = pd.read_csv(filepath_or_buffer=extracted_file_path,
                                sep=';',
                                nrows=nrows,
                                skiprows=skiprows,
                                encoding='latin1',
                                header=None,
                                dtype='object')

            # Tratamento do arquivo antes de inserir na base:
            socios = socios.reset_index()
            del socios['index']

            # Renomear colunas
            socios.columns = ['cnpj_basico',
                            'identificador_socio',
                            'nome_socio_razao_social',
                            'cpf_cnpj_socio',
                            'qualificacao_socio',
                            'data_entrada_sociedade',
                            'pais',
                            'representante_legal',
                            'nome_do_representante',
                            'qualificacao_representante_legal',
                            'faixa_etaria']
            skiprows = skiprows+nrows
            # Gravar dados no banco:
            # socios
            socios.to_sql(name='socios', con=engine, if_exists='append', index=False)
            logger.info('Arquivo ' + arquivos_socios[e] + ' inserido com sucesso no banco de dados! - Parte '+ str(i+1))
            print('Arquivo ' + arquivos_socios[e] + ' inserido com sucesso no banco de dados! - Parte '+ str(i+1))
            try:
                del socios
            except:
                pass
    try:
        del socios
    except:
        pass
    logger.info('Arquivos de socios finalizados!')
    print('Arquivos de socios finalizados!')
    socios_insert_end = time.time()
    socios_Tempo_insert = round((socios_insert_end - socios_insert_start))
    logger.info('Tempo de execução do processo de sócios (em segundos): ' + str(socios_Tempo_insert))
    print('Tempo de execução do processo de sócios (em segundos): ' + str(socios_Tempo_insert))

    #%%
    # Arquivos de simples:
    simples_insert_start = time.time()

    logger.info("""
    ################################
    ## Arquivos do SIMPLES NACIONAL:
    ################################
    """)

    print("""
    ################################
    ## Arquivos do SIMPLES NACIONAL:
    ################################
    """)
    # Drop table antes do insert
    cur.execute('DROP TABLE IF EXISTS "simples";')
    conn.commit()

    for e in range(0, len(arquivos_simples)):
        logger.info('Trabalhando no arquivo: '+arquivos_simples[e]+' [...]')
        print('Trabalhando no arquivo: '+arquivos_simples[e]+' [...]')
        try:
            del simples
        except:
            pass

        # Verificar tamanho do arquivo:
        logger.info('Lendo o arquivo ' + arquivos_simples[e]+' [...]')
        print('Lendo o arquivo ' + arquivos_simples[e]+' [...]')
        extracted_file_path = Path(f'{extracted_files}/{arquivos_simples[e]}')

        simples_lenght = sum(1 for line in open(extracted_file_path, "r", encoding='latin1'))
        logger.info('Linhas no arquivo do Simples '+ arquivos_simples[e] +': '+str(simples_lenght))
        print('Linhas no arquivo do Simples '+ arquivos_simples[e] +': '+str(simples_lenght))

        tamanho_das_partes = 1000000 # Registros por carga
        partes = round(simples_lenght / tamanho_das_partes)
        nrows = tamanho_das_partes
        skiprows = 0

        logger.info('Este arquivo será dividido em ' + str(partes) + ' partes para inserção no banco de dados')
        print('Este arquivo será dividido em ' + str(partes) + ' partes para inserção no banco de dados')

        for i in range(0, partes):
            logger.info('Iniciando a parte ' + str(i+1) + ' [...]')
            print('Iniciando a parte ' + str(i+1) + ' [...]')
            simples = pd.DataFrame(columns=[1,2,3,4,5,6])

            simples = pd.read_csv(filepath_or_buffer=extracted_file_path,
                                sep=';',
                                nrows=nrows,
                                skiprows=skiprows,
                                header=None,
                                encoding='latin1',
                                dtype='object')

            # Tratamento do arquivo antes de inserir na base:
            simples = simples.reset_index()
            del simples['index']

            # Renomear colunas
            simples.columns = ['cnpj_basico',
                            'opcao_pelo_simples',
                            'data_opcao_simples',
                            'data_exclusao_simples',
                            'opcao_mei',
                            'data_opcao_mei',
                            'data_exclusao_mei']

            skiprows = skiprows+nrows

            # Gravar dados no banco:
            # simples
            simples.to_sql(name='simples', con=engine, if_exists='append', index=False)
            logger.info('Arquivo ' + arquivos_simples[e] + ' inserido com sucesso no banco de dados! - Parte '+ str(i+1))
            print('Arquivo ' + arquivos_simples[e] + ' inserido com sucesso no banco de dados! - Parte '+ str(i+1))

            try:
                del simples
            except:
                pass

    try:
        del simples
    except:
        pass

    logger.info('Arquivos do simples finalizados!')
    print('Arquivos do simples finalizados!')
    simples_insert_end = time.time()
    simples_Tempo_insert = round((simples_insert_end - simples_insert_start))
    logger.info('Tempo de execução do processo do Simples Nacional (em segundos): ' + str(simples_Tempo_insert))
    print('Tempo de execução do processo do Simples Nacional (em segundos): ' + str(simples_Tempo_insert))
    
    
    #%%
    # Arquivos de cnae:
    cnae_insert_start = time.time()
    logger.info("""
    ######################
    ## Arquivos de cnae:
    ######################
    """)

    print("""
    ######################
    ## Arquivos de cnae:
    ######################
    """)
    # Drop table antes do insert
    cur.execute('DROP TABLE IF EXISTS "cnae";')
    conn.commit()

    for e in range(0, len(arquivos_cnae)):
        logger.info('Trabalhando no arquivo: '+arquivos_cnae[e]+' [...]')
        print('Trabalhando no arquivo: '+arquivos_cnae[e]+' [...]')
        try:
            del cnae
        except:
            pass

        extracted_file_path = Path(f'{extracted_files}/{arquivos_cnae[e]}')
        cnae = pd.DataFrame(columns=[1,2])
        cnae = pd.read_csv(filepath_or_buffer=extracted_file_path, sep=';', skiprows=0, header=None, dtype='object', encoding='latin1')

        # Tratamento do arquivo antes de inserir na base:
        cnae = cnae.reset_index()
        del cnae['index']

        # Renomear colunas
        cnae.columns = ['codigo', 'descricao']

        # Gravar dados no banco:
        # cnae
        cnae.to_sql(name='cnae', con=engine, if_exists='append', index=False)
        logger.info('Arquivo ' + arquivos_cnae[e] + ' inserido com sucesso no banco de dados!')
        print('Arquivo ' + arquivos_cnae[e] + ' inserido com sucesso no banco de dados!')

    try:
        del cnae
    except:
        pass
    logger.info('Arquivos de cnae finalizados!')
    print('Arquivos de cnae finalizados!')
    cnae_insert_end = time.time()
    cnae_Tempo_insert = round((cnae_insert_end - cnae_insert_start))
    logger.info('Tempo de execução do processo de cnae (em segundos): ' + str(cnae_Tempo_insert))
    print('Tempo de execução do processo de cnae (em segundos): ' + str(cnae_Tempo_insert))

    #%%
    # Arquivos de moti:
    moti_insert_start = time.time()
    logger.info("""
    #########################################
    ## Arquivos de motivos da situação atual:
    #########################################
    """)

    print("""
    #########################################
    ## Arquivos de motivos da situação atual:
    #########################################
    """)
    # Drop table antes do insert
    cur.execute('DROP TABLE IF EXISTS "moti";')
    conn.commit()

    for e in range(0, len(arquivos_moti)):
        logger.info('Trabalhando no arquivo: '+arquivos_moti[e]+' [...]')
        print('Trabalhando no arquivo: '+arquivos_moti[e]+' [...]')
        try:
            del moti
        except:
            pass

        extracted_file_path = Path(f'{extracted_files}/{arquivos_moti[e]}')
        moti = pd.DataFrame(columns=[1,2])
        moti = pd.read_csv(filepath_or_buffer=extracted_file_path, sep=';', skiprows=0, header=None, dtype='object', encoding='latin1')

        # Tratamento do arquivo antes de inserir na base:
        moti = moti.reset_index()
        del moti['index']

        # Renomear colunas
        moti.columns = ['codigo', 'descricao']

        # Gravar dados no banco:
        # moti
        moti.to_sql(name='moti', con=engine, if_exists='append', index=False)
        logger.info('Arquivo ' + arquivos_moti[e] + ' inserido com sucesso no banco de dados!')
        print('Arquivo ' + arquivos_moti[e] + ' inserido com sucesso no banco de dados!')

    try:
        del moti
    except:
        pass
    logger.info('Arquivos de moti finalizados!')
    print('Arquivos de moti finalizados!')
    moti_insert_end = time.time()
    moti_Tempo_insert = round((moti_insert_end - moti_insert_start))
    logger.info('Tempo de execução do processo de motivos da situação atual (em segundos): ' + str(moti_Tempo_insert))
    print('Tempo de execução do processo de motivos da situação atual (em segundos): ' + str(moti_Tempo_insert))

    #%%
    # Arquivos de munic:
    munic_insert_start = time.time()
    logger.info("""
    ##########################
    ## Arquivos de municípios:
    ##########################
    """)

    print("""
    ##########################
    ## Arquivos de municípios:
    ##########################
    """)



    # Drop table antes do insert
    cur.execute('DROP TABLE IF EXISTS "munic";')
    conn.commit()

    for e in range(0, len(arquivos_munic)):
        logger.info('Trabalhando no arquivo: '+arquivos_munic[e]+' [...]')
        print('Trabalhando no arquivo: '+arquivos_munic[e]+' [...]')
        try:
            del munic
        except:
            pass

        extracted_file_path = Path(f'{extracted_files}/{arquivos_munic[e]}')
        munic = pd.DataFrame(columns=[1,2])
        munic = pd.read_csv(filepath_or_buffer=extracted_file_path, sep=';', skiprows=0, header=None, dtype='object', encoding='latin1')

        # Tratamento do arquivo antes de inserir na base:
        munic = munic.reset_index()
        del munic['index']

        # Renomear colunas
        munic.columns = ['codigo', 'descricao']

        # Gravar dados no banco:
        # munic
        munic.to_sql(name='munic', con=engine, if_exists='append', index=False)
        logger.info('Arquivo ' + arquivos_munic[e] + ' inserido com sucesso no banco de dados!')
        print('Arquivo ' + arquivos_munic[e] + ' inserido com sucesso no banco de dados!')

    try:
        del munic
    except:
        pass
    logger.info('Arquivos de munic finalizados!')
    print('Arquivos de munic finalizados!')
    munic_insert_end = time.time()
    munic_Tempo_insert = round((munic_insert_end - munic_insert_start))
    logger.info('Tempo de execução do processo de municípios (em segundos): ' + str(munic_Tempo_insert))
    print('Tempo de execução do processo de municípios (em segundos): ' + str(munic_Tempo_insert))

    #%%
    # Arquivos de natju:
    natju_insert_start = time.time()
    logger.info("""
    #################################
    ## Arquivos de natureza jurídica:
    #################################
    """)

    print("""
    #################################
    ## Arquivos de natureza jurídica:
    #################################
    """)

    # Drop table antes do insert
    cur.execute('DROP TABLE IF EXISTS "natju";')
    conn.commit()

    for e in range(0, len(arquivos_natju)):
        logger.info('Trabalhando no arquivo: '+arquivos_natju[e]+' [...]')
        print('Trabalhando no arquivo: '+arquivos_natju[e]+' [...]')
        try:
            del natju
        except:
            pass

        extracted_file_path = Path(f'{extracted_files}/{arquivos_natju[e]}')
        natju = pd.DataFrame(columns=[1,2])
        natju = pd.read_csv(filepath_or_buffer=extracted_file_path, sep=';', skiprows=0, header=None, dtype='object', encoding='latin1')

        # Tratamento do arquivo antes de inserir na base:
        natju = natju.reset_index()
        del natju['index']

        # Renomear colunas
        natju.columns = ['codigo', 'descricao']

        # Gravar dados no banco:
        # natju
        natju.to_sql(name='natju', con=engine, if_exists='append', index=False)
        logger.info('Arquivo ' + arquivos_natju[e] + ' inserido com sucesso no banco de dados!')
        print('Arquivo ' + arquivos_natju[e] + ' inserido com sucesso no banco de dados!')

    try:
        del natju
    except:
        pass
    logger.info('Arquivos de natju finalizados!')
    print('Arquivos de natju finalizados!')
    natju_insert_end = time.time()
    natju_Tempo_insert = round((natju_insert_end - natju_insert_start))
    logger.info('Tempo de execução do processo de natureza jurídica (em segundos): ' + str(natju_Tempo_insert))
    print('Tempo de execução do processo de natureza jurídica (em segundos): ' + str(natju_Tempo_insert))

    #%%
    # Arquivos de pais:
    pais_insert_start = time.time()
    logger.info("""
    ######################
    ## Arquivos de país:
    ######################
    """)
    print("""
    ######################
    ## Arquivos de país:
    ######################
    """)

    # Drop table antes do insert
    cur.execute('DROP TABLE IF EXISTS "pais";')
    conn.commit()

    for e in range(0, len(arquivos_pais)):
        logger.info('Trabalhando no arquivo: '+arquivos_pais[e]+' [...]')
        print('Trabalhando no arquivo: '+arquivos_pais[e]+' [...]')
        try:
            del pais
        except:
            pass

        extracted_file_path = Path(f'{extracted_files}/{arquivos_pais[e]}')
        pais = pd.DataFrame(columns=[1,2])
        pais = pd.read_csv(filepath_or_buffer=extracted_file_path, sep=';', skiprows=0, header=None, dtype='object', encoding='latin1')

        # Tratamento do arquivo antes de inserir na base:
        pais = pais.reset_index()
        del pais['index']

        # Renomear colunas
        pais.columns = ['codigo', 'descricao']

        # Gravar dados no banco:
        # pais
        pais.to_sql(name='pais', con=engine, if_exists='append', index=False)
        logger.info('Arquivo ' + arquivos_pais[e] + ' inserido com sucesso no banco de dados!')
        print('Arquivo ' + arquivos_pais[e] + ' inserido com sucesso no banco de dados!')

    try:
        del pais
    except:
        pass
    logger.info('Arquivos de pais finalizados!')
    print('Arquivos de pais finalizados!')
    pais_insert_end = time.time()
    pais_Tempo_insert = round((pais_insert_end - pais_insert_start))
    logger.info('Tempo de execução do processo de país (em segundos): ' + str(pais_Tempo_insert))
    print('Tempo de execução do processo de país (em segundos): ' + str(pais_Tempo_insert))

    #%%
    # Arquivos de qualificação de sócios:
    quals_insert_start = time.time()
    logger.info("""
    ######################################
    ## Arquivos de qualificação de sócios:
    ######################################
    """)

    print("""
    ######################################
    ## Arquivos de qualificação de sócios:
    ######################################
    """)
    # Drop table antes do insert
    cur.execute('DROP TABLE IF EXISTS "quals";')
    conn.commit()

    for e in range(0, len(arquivos_quals)):
        logger.info('Trabalhando no arquivo: '+arquivos_quals[e]+' [...]')
        print('Trabalhando no arquivo: '+arquivos_quals[e]+' [...]')
        try:
            del quals
        except:
            pass

        extracted_file_path = Path(f'{extracted_files}/{arquivos_quals[e]}')
        quals = pd.DataFrame(columns=[1,2])
        quals = pd.read_csv(filepath_or_buffer=extracted_file_path, sep=';', skiprows=0, header=None, dtype='object', encoding='latin1')

        # Tratamento do arquivo antes de inserir na base:
        quals = quals.reset_index()
        del quals['index']

        # Renomear colunas
        quals.columns = ['codigo', 'descricao']

        # Gravar dados no banco:
        # quals
        quals.to_sql(name='quals', con=engine, if_exists='append', index=False)
        logger.info('Arquivo ' + arquivos_quals[e] + ' inserido com sucesso no banco de dados!')
        print('Arquivo ' + arquivos_quals[e] + ' inserido com sucesso no banco de dados!')

    try:
        del quals
    except:
        pass
    logger.info('Arquivos de quals finalizados!')
    print('Arquivos de quals finalizados!')
    quals_insert_end = time.time()
    quals_Tempo_insert = round((quals_insert_end - quals_insert_start))
    logger.info('Tempo de execução do processo de qualificação de sócios (em segundos): ' + str(quals_Tempo_insert))
    print('Tempo de execução do processo de qualificação de sócios (em segundos): ' + str(quals_Tempo_insert))

    #%%
    insert_end = time.time()
    Tempo_insert = round((insert_end - insert_start))

    logger.info("""
    #############################################
    ## Processo de carga dos arquivos finalizado!
    #############################################
    """)
    print("""
    #############################################
    ## Processo de carga dos arquivos finalizado!
    #############################################
    """)

    logger.info('Tempo total de execução do processo de carga (em segundos): ' + str(Tempo_insert)) # Tempo de execução do processo (em segundos): 17.770 (4hrs e 57 min)
    print('Tempo total de execução do processo de carga (em segundos): ' + str(Tempo_insert)) # Tempo de execução do processo (em segundos): 17.770 (4hrs e 57 min)

    # ###############################
    # Tamanho dos arquivos:
    # empresa = 45.811.638
    # estabelecimento = 48.421.619
    # socios = 20.426.417
    # simples = 27.893.923
    # ###############################

    #%%
    # Criar índices na base de dados:
    
    
    #%%
    # Arquivos de tributação:
    tribu_insert_start = time.time()

    logger.info("""
    ############################### 
    ## Arquivos de TRIBUTAÇÃO:
    ###############################
    """)

    print("""
    ############################### 
    ## Arquivos de TRIBUTAÇÃO:
    ###############################
    """)

    # Drop table antes do insert
    cur.execute('DROP TABLE IF EXISTS "tributacao";')
    conn.commit()

    for e in range(0, len(arquivos_tribu)):
        logger.info('Trabalhando no arquivo: '+arquivos_tribu[e]+' [...]')
        print('Trabalhando no arquivo: '+arquivos_tribu[e]+' [...]')
        try:
            del tributacao
        except:
            pass

        # Verificar tamanho do arquivo:
        logger.info('Lendo o arquivo ' + arquivos_tribu[e]+' [...]')
        print('Lendo o arquivo ' + arquivos_tribu[e]+' [...]')
        extracted_file_path = Path(f'{extracted_files}/{arquivos_tribu[e]}')

        tribu_lenght = sum(1 for line in open(extracted_file_path, "r", encoding='latin1'))
        logger.info('Linhas no arquivo da tributação '+ arquivos_tribu[e] +': '+str(tribu_lenght))
        print('Linhas no arquivo da tributação '+ arquivos_tribu[e] +': '+str(tribu_lenght))

        tamanho_das_partes = 100000 # Registros por carga
        partes = round(tribu_lenght / tamanho_das_partes)
        nrows = tamanho_das_partes
        skiprows = 0

        logger.info('Este arquivo será dividido em ' + str(partes) + ' partes para inserção no banco de dados')
        print('Este arquivo será dividido em ' + str(partes) + ' partes para inserção no banco de dados')


        for i in range(0, partes):
            logger.info('Iniciando a parte ' + str(i+1) + ' [...]')
            print('Iniciando a parte ' + str(i+1) + ' [...]')
            tributacao = pd.DataFrame(columns=[1,2,3,4,5])
        
            extracted_file_path = Path(f'{extracted_files}/{arquivos_tribu[e]}')

            tributacao = pd.read_csv(filepath_or_buffer=extracted_file_path,
                            sep=',',
                            nrows=nrows,
                            skiprows=skiprows,
                            encoding='latin1',
                            header=None,
                            dtype='object')

            # Tratamento do arquivo antes de inserir na base:
            tributacao = tributacao.reset_index()
            del tributacao['index']

            # Renomear colunas
            tributacao.columns = ['ano', 'cnpj', 'forma_de_tributacao', 'municipio', 'uf']

            skiprows = skiprows+nrows

            # Remove "."
            tributacao['cnpj'] = tributacao['cnpj'].apply(lambda x: x.replace('.',''))
            
            # Expand cnpj_ordem
            tributacao[['cnpj_basico', 'ordem']] = tributacao['cnpj'].str.split('/', expand=True)
            tributacao[['cnpj_ordem', 'cnpj_dv']] = tributacao['ordem'].str.split('-', expand=True)
            del tributacao['ordem']
            del tributacao['cnpj']
            
            # Expand cnpj_dv
            tributacao['cnpj_basico'] = tributacao['cnpj_basico'].astype(object)
            tributacao['cnpj_ordem'] = tributacao['cnpj_ordem'].astype(object)
            tributacao['cnpj_dv'] = tributacao['cnpj_dv'].astype(object)

            # Gravar dados no banco:
            # estabelecimento
            tributacao.to_sql(name='tributacao', con=engine, if_exists='append', index=False)
            logger.info('Arquivo ' + arquivos_tribu[e] + ' inserido com sucesso no banco de dados! - Parte '+ str(i+1))
            print('Arquivo ' + arquivos_tribu[e] + ' inserido com sucesso no banco de dados! - Parte '+ str(i+1))
            try:
                del tributacao
            except:
                pass

    try:
        del tributacao
    except:
        pass
    logger.info('Arquivos de tributação finalizados!')
    print('Arquivos de tributação finalizados!')
    tribu_insert_end = time.time()
    tribu_Tempo_insert = round((tribu_insert_end - tribu_insert_start))
    logger.info('Tempo de execução do processo de tributação (em segundos): ' + str(tribu_Tempo_insert))
    print('Tempo de execução do processo de tributação (em segundos): ' + str(tribu_Tempo_insert))    

    '''
    
    index_start = time.time()
    logger.info("""
    #######################################
    ## Criar índices na base de dados [...]
    #######################################
    """)

    print("""
    #######################################
    ## Criar índices na base de dados [...]
    #######################################
    """)

    cur.execute("""
    create index empresa_cnpj on empresa(cnpj_basico);
    commit;
    create index estabelecimento_cnpj on estabelecimento(cnpj_basico);
    commit;
    create index socios_cnpj on socios(cnpj_basico);
    commit;
    create index simples_cnpj on simples(cnpj_basico);
    commit;
    create index tributacao_cnpj on tributacao(cnpj_basico);
    commit;
    """)
    conn.commit()
    logger.info("""
    ############################################################
    ## Índices criados nas tabelas, para a coluna `cnpj_basico`:
    - empresa
    - estabelecimento
    - socios
    - simples
    - tributação
    ############################################################
    """)

    print("""
    ############################################################
    ## Índices criados nas tabelas, para a coluna `cnpj_basico`:
    - empresa
    - estabelecimento
    - socios
    - simples
    - tributação
    ############################################################
    """)

    index_end = time.time()
    index_time = round(index_end - index_start)
    logger.info('Tempo para criar os índices (em segundos): ' + str(index_time))
    print('Tempo para criar os índices (em segundos): ' + str(index_time))

    #%%
    logger.info("""Processo 100% finalizado! Você já pode usar seus dados no BD!
    - Desenvolvido por: Aphonso Henrique do Amaral Rafael
    - Contribua com esse projeto aqui: https://github.com/aphonsoar/Receita_Federal_do_Brasil_-_Dados_Publicos_CNPJ
    """)

    print("""Processo 100% finalizado! Você já pode usar seus dados no BD!
    - Desenvolvido por: Aphonso Henrique do Amaral Rafael
    - Contribua com esse projeto aqui: https://github.com/aphonsoar/Receita_Federal_do_Brasil_-_Dados_Publicos_CNPJ
    """)

except Exception as Argument:
    logging.exception("Erro ocorreu!!!!")
