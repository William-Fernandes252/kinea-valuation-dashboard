import numpy as np
import pandas as pd
import streamlit as st
from dateutil.relativedelta import relativedelta

import controller.alertas as alerta
import controller.sf_functions as sfc
import controller.sql_functions as sql
import model.fluxo as fluxo
from services import dates

sf_con = sfc.conexao_sfc()


def _status_unidades(df_status):
    df_status = df_status.groupby(["Id_Projeto", "Status"], as_index=False)[
        "Id_Unidade"
    ].count()
    return df_status


def base_vendas(data_ref, id_projeto):
    server = sql.conexao_BD()

    print("Data premissa: ", data_ref, "Id_projeto: ", id_projeto)
    df = sql.select_db_sell(server, data_ref, id_projeto)

    # ? Garantindo que está tudo com dia 1 do mês
    df[["Data_Referencia", "Data_Vencimento"]] = df[
        ["Data_Referencia", "Data_Vencimento"]
    ].applymap(lambda x: x.replace(day=1))
    data_ref = data_ref.replace(day=1)

    df_vendido = df.groupby(["Id_Projeto", "Data_Pagamento"], as_index=False)[
        "Valor_Pago"
    ].sum()
    df_saldo = df[df["Data_Vencimento"] > data_ref].reset_index(drop=True)
    df_saldo = df_saldo.groupby(["Id_Projeto", "Data_Vencimento"], as_index=False)[
        "Saldo_Pagar"
    ].sum()

    df_inad = df[df["Data_Vencimento"] <= data_ref].reset_index(drop=True)
    df_inad = df_inad.groupby(["Id_Projeto"], as_index=False)["Saldo_Pagar"].sum()

    print("df base vendas: ", df)

    return df_vendido, df_saldo, df_inad


def base_proj_vendas(data_ref, id_projeto):
    df = sql.select_db_status_unidades(data_ref, id_projeto)

    if df.empty:
        alerta._alerta_info(
            st,
            "Nenhum dado encontrato na tabela status unidades, verifique se a data da premisa está correta!",
        )
    return df


def _ajuste_lancamento(
    status_projeto, hip_vendas_lancamento, unid_total, unid_vendida, unid_estoque
):
    if status_projeto == "Lançamento":
        ajuste_lancamento = (
            (hip_vendas_lancamento * unid_total) - unid_vendida
        ) / unid_estoque
        if ajuste_lancamento < 0:
            ajuste_lancamento = 0
    else:
        ajuste_lancamento = 0
    return ajuste_lancamento


def _ajuste_periodo_obra(
    status_projeto,
    hip_vendas_lancamento,
    hip_vendas_periodo_obra,
    unid_total,
    unid_vendida,
    unid_estoque,
    ajuste_lancamento,
):
    if status_projeto == "Pós Chaves":
        ajuste_periodo_obra = 0
    elif ajuste_lancamento <= 0:
        ajuste_periodo_obra = (
            ((hip_vendas_periodo_obra + hip_vendas_lancamento) * unid_total)
            - unid_vendida
        ) / unid_estoque
        if ajuste_periodo_obra < 0:
            ajuste_periodo_obra = 0
    else:
        ajuste_periodo_obra = (hip_vendas_periodo_obra * unid_total) / unid_estoque
        if ajuste_periodo_obra < 0:
            ajuste_periodo_obra = 0

    return ajuste_periodo_obra


def _ajuste_poschave(
    ajuste_periodo_obra, hip_vendas_poschave, unid_total, unid_estoque
):
    if ajuste_periodo_obra > 0:
        ajuste_poschave = (hip_vendas_poschave * unid_total) / unid_estoque
    else:
        ajuste_poschave = 1
    return ajuste_poschave


def calculo_ajuste_vendas(
    df_unidades,
    hip_vendas_lancamento,
    hip_vendas_periodo_obra,
    hip_vendas_poschave,
    status_projeto,
):
    hip_vendas_lancamento = hip_vendas_lancamento / 100
    hip_vendas_periodo_obra = hip_vendas_periodo_obra / 100
    hip_vendas_poschave = hip_vendas_poschave / 100

    quadro_unid = df_unidades.groupby(["Id_Projeto", "Status"], as_index=False)[
        "Id_Unidade"
    ].count()
    unid_total = quadro_unid["Id_Unidade"].sum()

    unid_vendida = quadro_unid[
        (quadro_unid["Status"] == "Vendida")
        | (quadro_unid["Status"] == "Quitado")
        | (quadro_unid["Status"] == "Permuta")
    ]
    unid_vendida = unid_vendida["Id_Unidade"].sum()
    unid_estoque = unid_total - unid_vendida

    # unid_vend_premissa_lancamento = hip_vendas_lancamento*unid_total
    # unid_vend_premissa_obra = hip_vendas_periodo_obra*unid_total
    # uni_vend_premissa_poschave = hip_vendas_poschave*unid_total

    if status_projeto == "Aprovação":
        hip_vendas = 0
    elif status_projeto == "Lançamento":
        hip_vendas = hip_vendas_lancamento
    elif status_projeto == "Obra":
        hip_vendas = hip_vendas_periodo_obra
    elif status_projeto == "Pós Chaves":
        hip_vendas = hip_vendas_poschave
    else:
        raise Exception("Status do projeto não definido!")

    unid_vendida_premissa = hip_vendas * unid_total
    ajuste = unid_vendida_premissa - unid_vendida
    ajuste_poschave = unid_vendida_premissa - ajuste

    ajuste_lancamento = _ajuste_lancamento(
        status_projeto, hip_vendas_lancamento, unid_total, unid_vendida, unid_estoque
    )
    ajuste_periodo_obra = _ajuste_periodo_obra(
        status_projeto,
        hip_vendas_lancamento,
        hip_vendas_periodo_obra,
        unid_total,
        unid_vendida,
        unid_estoque,
        ajuste_lancamento,
    )
    ajuste_poschave = _ajuste_poschave(
        ajuste_periodo_obra, hip_vendas_poschave, unid_total, unid_estoque
    )

    df_ajuste = pd.DataFrame(
        {
            "Fases": ["Lançamento", "Obra", "Pós Chaves"],
            "Premissa": [
                hip_vendas_lancamento,
                hip_vendas_periodo_obra,
                hip_vendas_poschave,
            ],
            "Ajuste": [ajuste_lancamento, ajuste_periodo_obra, ajuste_poschave],
        }
    )

    return df_ajuste, quadro_unid


def _diferencaEmMeses(data1, data2):
    meses = (data2.year - data1.year) * 12 + (data2.month - data1.month)
    meses += 1
    return meses


def _status_projeto(
    data_ref,
    data_lancamento,
    data_ini_obra,
    data_entrega,
    data_termino,
    pos_ch_periodo_repasse,
):
    if data_ref < data_lancamento:
        status_projeto = "Aprovação"
        data_termino_status = data_lancamento
        status_chave = "Pre"
    elif data_ref < data_ini_obra:
        status_projeto = "Lançamento"
        data_termino_status = data_ini_obra
        status_chave = "Pre"
    elif data_ref <= data_entrega:
        status_projeto = "Obra"
        data_termino_status = data_entrega
        status_chave = "Pre"
    elif data_ref > data_entrega:
        status_projeto = "Pós Chaves"
        data_termino_status = data_termino - relativedelta(
            months=pos_ch_periodo_repasse + 1
        )
        status_chave = "Pos"

    return status_projeto, data_termino_status, status_chave


def _calculaCurvaAjuste(
    data_ref,
    data_lancamento,
    data_ini_obra,
    data_entrega,
    data_termino,
    pre_ch_carencia,
    pos_ch_carencia,
    df_premissa,
    pos_ch_prazo_vendas,
    pos_ch_periodo_repasse,
):
    data_ref = data_ref + relativedelta(months=1)
    data_termino = data_entrega + relativedelta(
        months=pos_ch_prazo_vendas + pos_ch_periodo_repasse
    )
    dt_ini_vendas = data_ref + relativedelta(months=pre_ch_carencia)
    status_projeto, data_termino_status, status_chave = _status_projeto(
        data_ref,
        data_lancamento,
        data_ini_obra,
        data_entrega,
        data_termino,
        pos_ch_periodo_repasse,
    )
    if status_projeto == "Aprovação":
        dt_ini_vendas = data_lancamento + relativedelta(months=pre_ch_carencia)

    df_ajuste = pd.DataFrame()
    # while data_ref <= data_termino - relativedelta(months=pos_ch_periodo_repasse):
    while data_ref < data_termino:
        status_projeto_curva, data_termino_status, status_chave = _status_projeto(
            data_ref,
            data_lancamento,
            data_ini_obra,
            data_entrega,
            data_termino,
            pos_ch_periodo_repasse,
        )
        df = df_premissa[df_premissa["Fases"] == status_projeto_curva].reset_index(
            drop=True
        )
        ajuste = df["Ajuste"][0]

        if status_projeto_curva == "Pós Chaves":
            dt_ini_vendas = data_entrega + relativedelta(months=pos_ch_carencia + 1)
        if dt_ini_vendas <= data_ref:
            meses_lanc_obra = _diferencaEmMeses(dt_ini_vendas, data_termino_status)
            perc_venda = ajuste / meses_lanc_obra
        else:
            perc_venda = 0
            meses_lanc_obra = 0
        dados = [
            [
                data_ref,
                perc_venda,
                status_projeto_curva,
                status_chave,
                data_entrega,
                ajuste,
                meses_lanc_obra,
                data_termino,
                dt_ini_vendas,
                data_termino_status,
            ]
        ]

        data_ref += relativedelta(months=1)
        df_ajuste = df_ajuste.append(
            pd.DataFrame(
                dados,
                columns=[
                    "Data Ref",
                    "Ajuste",
                    "Status Projeto",
                    "Status Chave",
                    "Data entrega",
                    "ajuste",
                    "meses_lanc_obra",
                    "data_termino",
                    "dt_ini_vendas",
                    "data_termino_status",
                ],
            ),
            ignore_index=True,
        )
    return df_ajuste


def _calculaPercRecebimentoCurva(
    df_vendas,
    data_ref,
    data_termino_fase,
    perc_ato,
    perc_mensais,
    perc_repasse,
    flag="pre",
):
    meses_status_venda = df_vendas.groupby(["status_venda"], as_index=False)[
        "Data Ref"
    ].count()
    meses_status_venda.rename(columns={"Data Ref": "count"}, inplace=True)

    meses_status_venda.loc[
        meses_status_venda["status_venda"] == "mensais", "perc"
    ] = perc_mensais
    meses_status_venda.loc[
        meses_status_venda["status_venda"] == "repasse", "perc"
    ] = perc_repasse

    if perc_ato > 0:
        meses_status_venda.loc[
            meses_status_venda["status_venda"] == "mensais", "count"
        ] = (meses_status_venda["count"] - 1)

    df_vendas = df_vendas.merge(
        meses_status_venda, how="left", on="status_venda", suffixes=("", "_count")
    )
    df_vendas["perc_vendas"] = df_vendas.apply(
        lambda x: x["perc"] / x["count"]
        if x["status_venda"] in ["mensais", "repasse"] and x["count"] != 0
        else 0,
        axis=1,
    )

    # No ultimo mes de venda o Ato passa a ser o valor do Ato+mensais (apenas prechaves)
    if (data_ref == data_termino_fase) & (flag == "pre"):
        df_vendas["perc_vendas"][0] = perc_ato + perc_mensais
    else:
        df_vendas["perc_vendas"][0] = perc_ato
        df_vendas["perc"][0] = perc_ato

    df_vendas["perc_vendas"] = df_vendas["perc_vendas"] / 100
    df_vendas["mes_venda"] = data_ref
    return df_vendas


def _calculaCurvaRecebimentoParcela(
    df_ajuste,
    data_ref,
    data_entrega,
    pre_ch_ato,
    pre_ch_mensais,
    pre_ch_repasse,
    pre_ch_carencia_repasse,
    pre_ch_periodo_repasse,
    pos_ch_ato,
    pos_ch_mensais,
    pos_ch_repasse,
    pos_ch_periodo_recebimento,
    pos_ch_prazo_vendas,
):
    data_ref += relativedelta(
        months=1
    )  # ? Os calculos comecam um mês após a data da premissa valuation
    data_termino_fase = data_entrega
    dt_carencia_prechaves = data_entrega + relativedelta(months=pre_ch_carencia_repasse)
    dt_fim_carencia_repasse_pre = dt_carencia_prechaves + relativedelta(
        months=pre_ch_periodo_repasse
    )

    df_pre = pd.DataFrame()
    df_pos = pd.DataFrame()
    iteracao = 1
    iteracao_pos = 1
    while data_ref <= data_entrega:
        df_vendas = df_ajuste[df_ajuste["Data Ref"] >= data_ref].reset_index(drop=True)
        df_vendas["status_venda"] = df_vendas.apply(
            lambda x: "mensais" if x["Data Ref"] <= data_termino_fase else None, axis=1
        )
        df_vendas["status_venda"] = df_vendas.apply(
            lambda x: "carencia"
            if (x["Data Ref"] > data_termino_fase)
            & (x["Data Ref"] <= dt_carencia_prechaves)
            else x["status_venda"],
            axis=1,
        )
        df_vendas["status_venda"] = df_vendas.apply(
            lambda x: "repasse"
            if (x["Data Ref"] > dt_carencia_prechaves)
            & (x["Data Ref"] <= dt_fim_carencia_repasse_pre)
            else x["status_venda"],
            axis=1,
        )

        df_vendas = _calculaPercRecebimentoCurva(
            df_vendas,
            data_ref,
            data_termino_fase=data_entrega,
            perc_ato=pre_ch_ato,
            perc_mensais=pre_ch_mensais,
            perc_repasse=pre_ch_repasse,
        )
        df_pre = df_pre.append(df_vendas, ignore_index=True)
        data_ref += relativedelta(months=1)
        iteracao += 1

        # if iteracao == 2:
        #     break

    data_ref = df_ajuste[df_ajuste["Status Chave"] == "Pos"]["Data Ref"].min()
    dt_limite_vendas = data_entrega + relativedelta(months=pos_ch_prazo_vendas - 1)
    while data_ref <= dt_limite_vendas:
        dt_fim_recebimento = data_ref + relativedelta(months=pos_ch_periodo_recebimento)

        df_vendas = df_ajuste[df_ajuste["Data Ref"] >= data_ref].reset_index(drop=True)
        df_vendas["status_venda"] = df_vendas.apply(
            lambda x: "mensais" if x["Data Ref"] < dt_fim_recebimento else None, axis=1
        )
        df_vendas["status_venda"] = df_vendas.apply(
            lambda x: "repasse"
            if x["Data Ref"] == dt_fim_recebimento
            else x["status_venda"],
            axis=1,
        )

        df_vendas = _calculaPercRecebimentoCurva(
            df_vendas,
            data_ref,
            data_termino_fase=dt_limite_vendas,
            perc_ato=pos_ch_ato,
            perc_mensais=pos_ch_mensais,
            perc_repasse=pos_ch_repasse,
            flag="pos",
        )
        df_pos = df_pos.append(df_vendas, ignore_index=True)
        data_ref += relativedelta(months=1)
        iteracao_pos += 1

    df_fluxo_receb = pd.concat([df_pre, df_pos], ignore_index=True)
    df_fluxo_receb = df_fluxo_receb[["Data Ref", "mes_venda", "perc_vendas"]]
    df_fluxo_receb.rename(columns={"Data Ref": "mes_recebimento"}, inplace=True)

    df = pd.merge(
        df_fluxo_receb, df_ajuste, left_on="mes_venda", right_on="Data Ref", how="left"
    )
    df["perc_recebimento"] = df.apply(
        lambda x: x["perc_vendas"] * x["Ajuste"] if x["perc_vendas"] != 0 else 0, axis=1
    )
    df = df.groupby(["mes_recebimento"], as_index=False)["perc_recebimento"].sum()
    return df


# def curvas(*args):
def curvaVendas(
    df_projeto,
    df_premissa,
    data_ref,
    quadro_unid,
    data_lancamento,
    data_ini_obra,
    data_entrega,
    data_termino,
    pre_ch_carencia,
    pos_ch_carencia,
    pos_ch_repasse,
    pos_ch_ato,
    pos_ch_mensais,
    pos_ch_prazo_vendas,
    pos_ch_periodo_recebimento,
    pre_ch_ato,
    pre_ch_mensais,
    pre_ch_repasse,
    pre_ch_carencia_repasse,
    pre_ch_periodo_repasse,
    venda_perc_comissao,
    venda_perc_desconto,
    venda_preco_m2_bruto,
    data_base_reajuste,
    hip_vendas_lancamento,
    hip_vendas_periodo_obra,
    hip_vendas_poschave,
):
    df_ajuste = _calculaCurvaAjuste(
        data_ref,
        data_lancamento,
        data_ini_obra,
        data_entrega,
        data_termino,
        pre_ch_carencia,
        pos_ch_carencia,
        df_premissa,
        pos_ch_prazo_vendas,
        pos_ch_periodo_recebimento,
    )
    df_receb_parcelas = _calculaCurvaRecebimentoParcela(
        df_ajuste,
        data_ref,
        data_entrega,
        pre_ch_ato,
        pre_ch_mensais,
        pre_ch_repasse,
        pre_ch_carencia_repasse,
        pre_ch_periodo_repasse,
        pos_ch_ato,
        pos_ch_mensais,
        pos_ch_repasse,
        pos_ch_periodo_recebimento,
        pos_ch_prazo_vendas,
    )
    vgv_disponivel, rs_valuation_liquido = fluxo.fluxo_proj_vendas(
        df_projeto,
        data_ref,
        data_lancamento,
        data_ini_obra,
        data_entrega,
        data_termino,
        venda_perc_comissao,
        venda_perc_desconto,
        venda_preco_m2_bruto,
        data_base_reajuste,
        hip_vendas_lancamento,
        hip_vendas_periodo_obra,
        hip_vendas_poschave,
        pos_ch_periodo_recebimento,
    )

    print("vgv_disponivel: ", vgv_disponivel)

    df_curva = pd.merge(
        df_ajuste[["Data Ref", "Ajuste"]],
        df_receb_parcelas,
        left_on="Data Ref",
        right_on="mes_recebimento",
        how="inner",
    )
    df_curva.rename(
        columns={
            "Ajuste": "perc_venda_estoq",
            "Data Ref": "dt_mes_curva",
            "perc_recebimento": "perc_receita",
        },
        inplace=True,
    )

    estoque = quadro_unid.loc[quadro_unid["Status"] == "Disponível"][
        "Id_Unidade"
    ].values[0]
    df_curva["qtd_venda_estoq"] = df_curva.apply(
        lambda x: x["perc_venda_estoq"] * estoque, axis=1
    )
    df_curva["rs_venda_estoq"] = df_curva.apply(
        lambda x: x["perc_venda_estoq"] * vgv_disponivel, axis=1
    )

    df_curva["dt_mes_curva"] = pd.to_datetime(df_curva["dt_mes_curva"])
    df_curva["ano_curva"] = df_curva["dt_mes_curva"].dt.year
    df_curva[["qtd_venda_estoq", "rs_venda_estoq"]] = df_curva[
        ["qtd_venda_estoq", "rs_venda_estoq"]
    ].round(0)

    # Agrupar por ano calcular quantidade de linhas por ano
    resumo_vendasAno = df_curva.groupby(["ano_curva"], as_index=False).agg(
        {"qtd_venda_estoq": "sum", "rs_venda_estoq": "sum", "dt_mes_curva": "count"}
    )
    resumo_vendasAno["Qtd Vendas por mês"] = resumo_vendasAno.apply(
        lambda x: x["qtd_venda_estoq"] / x["dt_mes_curva"], axis=1
    )
    resumo_vendasAno["R$ Vendas por mês"] = resumo_vendasAno.apply(
        lambda x: x["rs_venda_estoq"] / x["dt_mes_curva"], axis=1
    )

    resumo_vendasAno[
        ["qtd_venda_estoq", "rs_venda_estoq", "Qtd Vendas por mês", "R$ Vendas por mês"]
    ] = resumo_vendasAno[
        ["qtd_venda_estoq", "rs_venda_estoq", "Qtd Vendas por mês", "R$ Vendas por mês"]
    ].round(
        0
    )
    resumo_vendasAno["ano_curva"] = resumo_vendasAno["ano_curva"].astype(str)

    resumo_vendasAno.rename(
        columns={
            "ano_curva": "Ano",
            "qtd_venda_estoq": "Qtd Vendas ano",
            "rs_venda_estoq": "R$ Vendas ano",
        },
        inplace=True,
    )
    resumo_vendasAno = resumo_vendasAno[
        [
            "Ano",
            "Qtd Vendas ano",
            "R$ Vendas ano",
            "Qtd Vendas por mês",
            "R$ Vendas por mês",
        ]
    ]
    resumo_vendasAno_col_float = resumo_vendasAno.select_dtypes(include="float").columns
    for col in resumo_vendasAno_col_float:
        resumo_vendasAno[col] = (
            resumo_vendasAno[col].map("{:,.0f}".format).str.replace(",", ".")
        )

    # df_curva = df_curva[['dt_mes_curva','perc_venda_estoq', 'perc_receita']]
    # sql.insert_df_sql('SQNDSC005', 'incorp_val_curvas', df_curva)

    return df_curva, resumo_vendasAno, rs_valuation_liquido


def calculaPercentualReajuste(data_base_reajuste, data_ref):
    # ? Calcula 2 meses antes
    data_ref = data_ref.replace(day=1)
    data_ref = data_ref - relativedelta(months=2)
    data_base_reajuste = data_base_reajuste.replace(day=1)
    data_base_reajuste = data_base_reajuste - relativedelta(months=2)

    df = sql.select_indices(data_base_reajuste, data_ref)
    valor_ini = df.iloc[0]["Valor"]
    valor_fim = df.iloc[-1]["Valor"]
    perc_reajuste = (valor_fim / valor_ini) - 1
    print("# Percentual de reajuste: ", perc_reajuste)
    return perc_reajuste


def _calcula_taxa_diaria(taxa, dias):
    taxa_diaria = (1 + taxa) ** (1 / dias) - 1
    return taxa_diaria


def calculaIndiceDiario(df):
    df["ult_dia_mes"] = df.apply(
        lambda x: dates.get_last_day_of_month(dates.datetime(x["DATA_REF"])).strftime(
            "%Y-%m-%d"
        ),
        axis=1,
    )
    df["dt_dia"] = df.apply(
        lambda x: pd.date_range(x["DATA_REF"], x["ult_dia_mes"], freq="D").to_list(),
        axis=1,
    )
    df_diario = df.explode("dt_dia")
    df_diario["dia_util"] = df_diario.apply(
        lambda x: dates.is_business_day(dates.datetime(x["dt_dia"])), axis=1
    )
    df_diario = df_diario[df_diario["dia_util"] == True].reset_index(drop=True)
    df_diario["qtd_dias_mes"] = df_diario.groupby(["DATA_REF"])["DATA_REF"].transform(
        "count"
    )
    df_diario["taxa_diaria"] = df_diario.apply(
        lambda x: _calcula_taxa_diaria(x["VALOR"], x["qtd_dias_mes"]), axis=1
    )
    df_diario = df_diario[["CODIGO", "DATA_REF", "VALOR", "dt_dia", "taxa_diaria"]]
    return df_diario


def curvaCri(df_fluxo, df_juros_amort_middle, data_ref, indexador, taxa_spread):
    df_fluxo = df_fluxo[["Id_Projeto", "dt_mes", "sf_aportes"]]
    min_date_fluxo = df_fluxo["dt_mes"].min()

    df_indice = sql.select_indices(min_date_fluxo.date(), data_ref)
    df_indice.rename(
        columns={"Data": "DATA_REF", "Codigo": "CODIGO", "Valor": "VALOR"}, inplace=True
    )
    df_indice = df_indice[df_indice["CODIGO"] == indexador].reset_index(drop=True)
    df_indice = calculaIndiceDiario(df_indice)
    df_indice["status"] = "Real"

    df_indice_proj = sql.select_indice_proj()
    df_indice_proj = df_indice_proj[df_indice_proj["DATA_REF"] > data_ref].reset_index(
        drop=True
    )
    df_indice_ipca = df_indice_proj[(df_indice_proj["CODIGO"] == "IPCA")].reset_index(
        drop=True
    )
    df_indice_ipca = calculaIndiceDiario(df_indice_ipca)

    if indexador == "IPCA":
        df_indice_proj_final = df_indice_ipca
        df_indice_proj_final["taxa_diferencial_proj"] = 0
    else:
        #!? Calculando a diferença entre o indexador do projeto e o IPCA
        df_indice_cdi = df_indice_proj[
            (df_indice_proj["CODIGO"] == indexador)
        ].reset_index(drop=True)
        df_indice_cdi = calculaIndiceDiario(df_indice_cdi)
        df_indice_proj_final = df_indice_ipca.merge(
            df_indice_cdi, how="left", left_on="dt_dia", right_on="dt_dia"
        )
        df_indice_proj_final["taxa_diferencial_proj"] = df_indice_proj_final.apply(
            lambda x: ((1 + x["taxa_diaria_y"]) / (1 + x["taxa_diaria_x"])) - 1, axis=1
        )
        df_indice_proj_final.rename(
            columns={
                "taxa_diaria_y": "taxa_diaria",
                "CODIGO_y": "CODIGO",
                "VALOR_y": "VALOR",
                "DATA_REF_y": "DATA_REF",
            },
            inplace=True,
        )
        df_indice_proj_final = df_indice_proj_final[
            [
                "CODIGO",
                "DATA_REF",
                "VALOR",
                "dt_dia",
                "taxa_diaria",
                "taxa_diferencial_proj",
            ]
        ]

    df_indice_proj_final["status"] = "Projeção"
    df_indice_total = pd.concat([df_indice, df_indice_proj_final])

    df_curva_cri = df_indice_total.merge(
        df_fluxo, how="left", left_on="dt_dia", right_on="dt_mes"
    )
    df_curva_cri["taxa_spread_dia"] = _calcula_taxa_diaria(taxa_spread, 252)

    df_curva_cri["atualizacao_indice"] = 0
    df_curva_cri["spread"] = 0
    df_curva_cri["saldo_final"] = 0

    df_juros_amort_middle = df_juros_amort_middle[["Data", "Movimento"]]
    df_juros_amort_middle["Data"] = pd.to_datetime(
        df_juros_amort_middle["Data"], format="%Y-%m-%d"
    )
    df_juros_amort_middle = df_juros_amort_middle.groupby(["Data"], as_index=False)[
        "Movimento"
    ].sum()

    df_curva_cri = df_curva_cri.merge(
        df_juros_amort_middle, how="left", left_on="dt_dia", right_on="Data"
    )
    df_curva_cri[
        [
            "taxa_diferencial_proj",
            "sf_aportes",
            "taxa_spread_dia",
            "atualizacao_indice",
            "spread",
            "saldo_final",
            "Movimento",
        ]
    ] = df_curva_cri[
        [
            "taxa_diferencial_proj",
            "sf_aportes",
            "taxa_spread_dia",
            "atualizacao_indice",
            "spread",
            "saldo_final",
            "Movimento",
        ]
    ].fillna(
        0
    )
    df_curva_cri["amort_integralizacao"] = (
        df_curva_cri["sf_aportes"] + df_curva_cri["Movimento"]
    )
    df_curva_cri.loc[0, "saldo_final"] = df_curva_cri.loc[0, "sf_aportes"]

    for i in range(1, len(df_curva_cri)):
        if df_curva_cri.loc[i, "status"] == "Projeção":
            df_curva_cri.loc[i, "atualizacao_indice"] = (
                df_curva_cri.loc[i - 1, "saldo_final"]
                * df_curva_cri.loc[i, "taxa_diferencial_proj"]
            )
        else:
            df_curva_cri.loc[i, "atualizacao_indice"] = (
                df_curva_cri.loc[i - 1, "saldo_final"]
                * df_curva_cri.loc[i, "taxa_diaria"]
            )

        df_curva_cri.loc[i, "spread"] = (
            df_curva_cri.loc[i - 1, "saldo_final"]
            * df_curva_cri.loc[i, "taxa_spread_dia"]
        )
        df_curva_cri.loc[i, "saldo_final"] = (
            df_curva_cri.loc[i - 1, "saldo_final"]
            + df_curva_cri.loc[i, "spread"]
            + df_curva_cri.loc[i, "atualizacao_indice"]
            + df_curva_cri.loc[i, "amort_integralizacao"]
        )

    df_curva_cri.rename(columns={"dt_dia": "data"}, inplace=True)
    df_curva_cri = df_curva_cri[
        ["data", "amort_integralizacao", "atualizacao_indice", "spread", "saldo_final"]
    ]

    df_curva_cri.to_excel("df_curva_cri.xlsx", index=False)
    print("df_curva_cri: \n", df_curva_cri)
    # sql.insert_df_sql('SQNDSC005','incorp_val_curvas_cri', df_curva_cri)

    return df_indice_total


def salvaPremissaSQL(**kwargs):
    df = pd.DataFrame([kwargs])
    sql.insert_df_sql("incorp_val_premissa", df)
