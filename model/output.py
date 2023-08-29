from datetime import date


def resumoVendas(df_curva_recebimento, quadro_unid):
    # filter rows where Status is "Disponível" and then select "Unidade" column
    unid_estoque = quadro_unid[quadro_unid["Status"] == "Disponível"][
        "Id_Unidade"
    ].values[0]

    df_curva_recebimento["unid_vendas"] = (
        df_curva_recebimento["perc_recebimento"] * unid_estoque
    )
