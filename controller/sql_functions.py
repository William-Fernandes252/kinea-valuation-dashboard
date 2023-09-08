from typing import Optional

import pandas as pd
from sqlalchemy import Connection, TextClause, create_engine, sql


def conexao_BD():
    server = "localhost,1433"
    database = "ValuationDashboard"
    username = "sa"
    password = "Bloodraven252"
    db_url = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
    engine = create_engine(db_url)
    return engine.connect()


def _select_sql(connection: Connection, select: TextClause):
    rows = connection.execute(select).fetchall()
    df = pd.DataFrame(rows)
    return df


def select_db_sell(data_ref, id_projeto):
    connection = conexao_BD()
    script_sql = sql.text(
        f"""
        select * 
        from Incorporacao_Unidades u
        inner join re_incorporacao_contratos c on (c.Id_Unidade = u.Id_Unidade)
        inner join re_incorporacao_contratos_parcelas p on (p.Id_Contrato = c.Id_Contrato)
        inner join re_incorporacao_fluxos_recebiveis f on (f.Id_Parcela = p.Id_Parcela)
        """,
    )
    df = _select_sql(connection, script_sql)
    return df


def select_db_status_unidades(data_ref, id_projeto):
    connection = conexao_BD()

    script_sql = sql.text(
        f"""
        select u.Id_Projeto as Id_Projeto, u.Area as Area, s.Status as Status, u.Id_Unidade as Id_Unidade
        from Incorporacao_Status_Unidades s
        inner join Incorporacao_Unidades u on (u.Id_Unidade = s.Id_Unidade)
        where u.Id_Projeto = '{id_projeto}'
        """,
    )
    df = _select_sql(connection, script_sql)
    return df


def select_indices(data_base_reajuste, data_ref):
    connection = conexao_BD()
    script_sql = sql.text(
        f"""
        select * from BD_RENDA_INDICES 
        where Codigo in ('IPCA', 'CDI')
        and Data >= '{data_base_reajuste.strftime("%Y-%m-%d")}'
        and Data <= '{data_ref.strftime("%Y-%m-%d")}'
        """,
    )
    df = _select_sql(connection, script_sql)
    return df


def select_premissa(id_projeto: Optional[str] = None):
    connection = conexao_BD()
    script_sql = sql.text(
        f"select * from incorp_val_premissa"
        + (f" where id_projeto = '{id_projeto}'" if id_projeto else "")
    )
    df = _select_sql(connection, script_sql)
    df["chave_premissa"] = df.apply(
        lambda x: str(x["versao"]) + " - " + str(x["id_premissa"]),
        axis=1,
    )
    return df


def select_juros_amortizacao(codigo, cod_oper):
    connection = conexao_BD()
    script_sql = sql.text(
        f"""
        select * from Bd_Middle_FundosCaixa where CodOper = '{cod_oper}' and Codigo = '{codigo}'
        """,
    )
    df = _select_sql(connection, script_sql)
    return df


def select_indice_proj():
    connection = conexao_BD()
    script_sql = sql.text(
        f"""
        select * from bd_renda_indices_proj
        """
    )
    df = _select_sql(connection, script_sql)
    return df


def select_versoes():
    connection = conexao_BD()
    script_sql = sql.text("SELECT * FROM versao")
    return _select_sql(connection, script_sql)


def insert_df_sql(tabela, df: pd.DataFrame):
    connection = conexao_BD()
    df.to_sql(tabela, schema="re", con=connection, if_exists="append", index=False)
    return df


def _update_sql(connection: Connection, script):
    try:
        connection.execute(script)
        return True
    except Exception as error:
        print("Erro ao executar script de update no SQL\n")
        print(error)
        return False
