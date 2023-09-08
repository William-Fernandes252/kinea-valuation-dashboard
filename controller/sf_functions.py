import pandas as pd
import requests
from simple_salesforce import Salesforce
from sqlalchemy.sql import text

from . import sql_functions


def conexao_sfc():
    session = requests.Session()
    session.verify = False
    username = "inovacaorealestate@kinea.com.br"
    password = "kinea@01"
    security_token = "P9zPqnewS1qpaudQF4IVEycV"
    session = session
    try:
        sf = Salesforce(
            username=username, password=password, security_token=security_token
        )
    except:
        sf = Salesforce(
            username=username, password=password, security_token=security_token
        )
    return sf


# Dados projetos:
# Id  Name Data_de_Lancamento_c Data_de_Terminoc Inicio_das_obrasc Habitesec Data_de_referencia_viabilidadec  Perc_Permuta_c Indexador  Spread
# 0 a153s00000W43X5AAJ Lapa            2021-09-01         2024-11-01          2022-05-01  2024-03-01 2021-07-01             9.17      IPCA  0.0825


# Série CRI
# Código Série CETIP |	Código do fundo |	Projeto Real Estate |	Percentual | 	Data inicial | Aniversário CRI
# 21G0688160	        		KSC	 	                            100,00%	 	                    20
# Código Série CETIP == Name
# Projeto Real Estate == Id_Projeto


def SFToDF_projeto():
    # ? 0123s000000nRtCAAU - Cri Permuta
    script = text(
        r"SELECT Id, Name, Data_de_Lancamento__c, Data_de_Termino__c, Inicio_das_obras__c, Habitese__c, Data_de_referencia_viabilidade__c, Perc_Permuta__c, Indexador_Alvo__c, Spreed__c FROM Projeto_Real_Estate__c"
    )
    result = sql_functions.conexao_BD().execute(script).fetchall()
    df = pd.DataFrame(result, index=None)
    df["Spread"] = df["Spreed__c"].apply(lambda x: x / 100 if (x != None) else None)
    df = df.sort_values(by="Name")
    df = df.reset_index(drop=True)
    return df


def SF_select_serieCri(id_projeto):
    script = text(
        f"SELECT Id, Name, Codigo_Fundo__c, Aniversario_CRI__c FROM Serie_CRI__c where Projeto_Real_Estate__c = '{id_projeto}'",
    )
    result = sql_functions.conexao_BD().execute(script).fetchall()
    df = pd.DataFrame(result, index=None)
    df = df.drop(columns=["attributes", "Id"])
    df.rename(columns={"Projeto_Real_Estate__c": "Id_Projeto"}, inplace=True)
    df.to_excel("Serie_CRI__c.xlsx", index=False)
    return df


def SF_select_aportes(sf):
    script = text(
        r"SELECT Id, Data__c, Valor__c, Projeto_Real_Estate__c FROM Aportes__c"
    )
    rows = sql_functions.conexao_BD().execute(script).fetchall()
    df = pd.DataFrame(rows, index=None)
    df = df.drop(columns=["attributes", "Id"])
    df.rename(
        columns={
            "Projeto_Real_Estate__c": "Id_Projeto",
            "Data__c": "dt_mes",
            "Valor__c": "sf_aportes",
        },
        inplace=True,
    )
    df["sf_aportes"] = df["sf_aportes"] * -1
    df.to_excel("Aportes__c.xlsx", index=False)
    return df
