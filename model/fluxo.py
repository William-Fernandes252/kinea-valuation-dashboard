import pandas as pd
from dateutil.relativedelta import relativedelta

import controller.sf_functions as sfc
import model._vendas as v


def fluxo_proj_vendas(
    dfprojeto,
    data_ref,
    data_lancamento,
    data_ini_obra,
    data_entrega,
    data_termino,
    perc_comissao,
    venda_perc_desconto,
    precom2_bruto,
    data_base_reajuste,
    hip_vendas_lancamento,
    hip_vendas_periodo_obra,
    hip_vendas_poschave,
    pos_ch_periodo_repasse,
):
    id_projeto = dfprojeto["Id"][0]

    df = v.base_proj_vendas(data_ref, id_projeto)
    rs_m2_viabilidade = 4840.05  # ? Esse valor será substituido pelo valor da viabilidade da tabela status_unidades
    perc_reajuste = v.calculaPercentualReajuste(data_base_reajuste, data_ref)
    rs_m2_viabilidade_atualizado = rs_m2_viabilidade * (1 + perc_reajuste)

    print("perc_reajuste :", perc_reajuste)
    print("rs_m2_viabilidade_atualizado :", rs_m2_viabilidade_atualizado)

    df["perc_venda_desconto"] = 0
    rs_valuation_liquido = rs_m2_viabilidade_atualizado
    if precom2_bruto > 0:
        rs_valuation_liquido = precom2_bruto
    if perc_comissao > 0:
        rs_valuation_liquido = (
            1 - (perc_comissao / 100)
        ) * rs_valuation_liquido  # tem que considerar o desconto tbm
    if venda_perc_desconto > 0:
        rs_valuation_liquido = (
            1 - (venda_perc_desconto / 100)
        ) * rs_valuation_liquido  # tem que considerar o desconto tbm

    print("rs_valuation_liquido :", rs_valuation_liquido)

    df["rs_m2_viabilidade_atualizado"] = rs_valuation_liquido
    df["rs_m2_venda"] = df["rs_m2_viabilidade_atualizado"] * df["Area"]
    vgv_disponivel = df[df["Status"] == "Disponível"]["rs_m2_venda"].sum()

    # status_projeto = v._status_projeto(data_ref, data_lancamento, data_ini_obra, data_entrega, data_termino, pos_ch_periodo_repasse)
    # #v.calculo_ajuste_vendas(df, hip_vendas_lancamento, hip_vendas_periodo_obra, hip_vendas_poschave, status_projeto)

    return vgv_disponivel, rs_valuation_liquido


def fluxo_tot_recebiveis(
    df_proj_vendas, id_projeto, data_ref, meses_inad, pdd, outras_despesas
):
    df_vendido, df_saldo, df_inad = v.base_vendas(data_ref, id_projeto)
    df_vendido.rename(
        columns={"Data_Pagamento": "dt_mes", "Valor_Pago": "vl_vendido"}, inplace=True
    )
    df_saldo.rename(
        columns={"Data_Vencimento": "dt_mes", "Saldo_Pagar": "vl_vendido"}, inplace=True
    )

    df_fluxo = pd.concat([df_vendido, df_saldo])

    if not df_inad.empty:
        print("Meses Inadimplencia: ", meses_inad, "PDD: ", pdd)
        df_inad["Saldo"] = (df_inad["Saldo_Pagar"].iloc[0] / meses_inad) * (1 - pdd)
        datas = [data_ref + relativedelta(months=i + 1) for i in range(meses_inad)]

        # ? repetimos cada linha do DataFrame pelo número de elementos na lista datas usando o método repeat.
        # ? Isso cria uma linha para cada data na lista datas.
        df_inad = df_inad.loc[df_inad.index.repeat(len(datas))].reset_index(drop=True)
        df_inad["dt_mes"] = datas
    else:
        df_inad["dt_mes"] = None

    print("df_inad: \n", df_inad)

    df_inad.rename(columns={"Saldo": "proj_inadimplencia"}, inplace=True)
    df_inad = df_inad[["Id_Projeto", "dt_mes", "proj_inadimplencia"]]

    df_aportes = sfc.SF_select_aportes()

    df_proj_vendas.rename(
        columns={"rs_venda_estoq": "vl_a_vender", "dt_mes_curva": "dt_mes"},
        inplace=True,
    )

    df_fluxo = pd.concat([df_fluxo, df_inad, df_aportes])
    df_fluxo["dt_mes"] = pd.to_datetime(df_fluxo["dt_mes"], format="%Y-%m-%d")
    df_fluxo = df_fluxo.groupby(["Id_Projeto", "dt_mes"], as_index=False).agg(
        {"vl_vendido": "sum", "proj_inadimplencia": "sum", "sf_aportes": "sum"}
    )
    df_fluxo = df_fluxo.merge(
        df_proj_vendas[["dt_mes", "vl_a_vender"]], how="left", on=["dt_mes"]
    )
    df_fluxo.sort_values(by=["dt_mes"], inplace=True)
    df_fluxo = df_fluxo.fillna(0)
    df_fluxo["tot_recebiveis"] = df_fluxo["vl_vendido"] + df_fluxo["vl_a_vender"]

    df_fluxo["vl_outras_dispesas"] = df_fluxo["tot_recebiveis"].apply(
        lambda x: -abs(x * (outras_despesas / 100))
    )
    return df_fluxo


def fluxo_distribuicao_teorica(
    indexador,
    taxa_spread,
    df_proj_vendas,
    id_projeto,
    data_ref,
    meses_inad,
    pdd,
    perc_permuta,
    outras_despesas,
):
    df_fluxo = fluxo_tot_recebiveis(
        df_proj_vendas, id_projeto, data_ref, meses_inad, pdd, outras_despesas
    )

    #! A linha atual recebe a valor da linha anterior multiplicado pelo perc_permuta
    df_fluxo["distribuicao_teorica"] = (
        df_fluxo["tot_recebiveis"] + df_fluxo["vl_outras_dispesas"]
    )
    df_fluxo["distribuicao_teorica"] = df_fluxo["distribuicao_teorica"].shift(1) * (
        perc_permuta / 100
    )
    df_fluxo["distribuicao_teorica"] = df_fluxo["distribuicao_teorica"].round(2)

    df_serie_cri = sfc.SF_select_serieCri(id_projeto)

    df_juros_amort_middle = v.sql.select_juros_amortizacao(
        df_serie_cri["Codigo_Fundo__c"][0], df_serie_cri["Name"][0]
    )
    df_juros_amort = df_juros_amort_middle
    df_juros_amort["Data"] = pd.to_datetime(df_juros_amort["Data"], format="%Y-%m-d")
    df_juros_amort["dt_mes"] = df_juros_amort["Data"].apply(lambda x: x.replace(day=1))
    df_juros_amort = df_juros_amort.groupby(["dt_mes"], as_index=False)[
        "Movimento"
    ].sum()
    df_juros_amort.rename(
        columns={"Movimento": "distribuicao_efetiva_projeto"}, inplace=True
    )
    df_juros_amort = df_juros_amort[
        df_juros_amort["dt_mes"] <= pd.to_datetime(data_ref)
    ].reset_index(drop=True)

    df_fluxo = df_fluxo.merge(df_juros_amort, how="left", on=["dt_mes"])
    df_fluxo["distribuicao_efetiva_projeto"] = df_fluxo.apply(
        lambda x: x["distribuicao_teorica"]
        if x["dt_mes"] > data_ref
        else x["distribuicao_efetiva_projeto"],
        axis=1,
    )
    df_fluxo.fillna(0, inplace=True)
    df_fluxo["saldo_cri"] = (
        df_fluxo["distribuicao_efetiva_projeto"] + df_fluxo["sf_aportes"]
    )

    print("df_fluxo: \n", df_fluxo)
    df_curva_cri = v.curvaCri(
        df_fluxo, df_juros_amort_middle, data_ref, indexador, taxa_spread
    )
