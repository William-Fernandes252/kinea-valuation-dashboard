from time import sleep

import streamlit as st

import controller.alertas as alerta
import controller.sf_functions as sfc
from model import fluxo
from pages.utils import config

config.set_page_settings(st)

st.header("🧮 Projetos")

projeto_tab, velocidade_vendas_tab, despesas_tab, cashsweep_tab = st.tabs(
    ["Início", "Velocidade de vendas", "Despesas", "Cashsweep"]
)
with projeto_tab:
    col_projeto, col_clona_versao = st.columns(2)

    df_projeto = sfc.SFToDF_projeto()
    option_proj = col_projeto.selectbox("Projeto:", df_projeto["Name"])
    selected_id = df_projeto.loc[df_projeto["Name"] == option_proj, "Id"].iloc[0]
    df_projeto = df_projeto[df_projeto["Id"] == selected_id].reset_index(drop=True)

    df_premissa_sql = fluxo.v.sql.select_premissa()
    option_versao = col_clona_versao.selectbox(
        "Clonar de:", df_premissa_sql["chave_premissa"]
    )
    selected_id_premissa = df_premissa_sql.loc[
        df_premissa_sql["chave_premissa"] == option_versao, "id_premissa"
    ].iloc[0]
    df_premissa_sql = df_premissa_sql[
        df_premissa_sql["id_premissa"] == selected_id_premissa
    ].reset_index(drop=True)

    col_data_premissa, col_versao = st.columns(2)
    data_premissa = col_data_premissa.date_input(
        "Data de referência", format="DD/MM/YYYY"
    )
    versao = col_versao.text_input("Nome da versão")

    datas_expander = st.expander("Projeto", expanded=False)
    with datas_expander:
        colunas_dt = st.columns([1, 1])

        with colunas_dt[0]:
            data_lancamento = colunas_dt[0].date_input(
                "Lançamento",
                value=df_projeto["Data_de_Lancamento__c"][0],
                format="DD/MM/YYYY",
            )
            data_ini_obra = colunas_dt[0].date_input(
                "Inicio das obras",
                value=df_projeto["Inicio_das_obras__c"][0],
                format="DD/MM/YYYY",
            )
            data_base_reajuste = colunas_dt[0].date_input(
                "Base reajuste",
                value=df_projeto["Data_de_referencia_viabilidade__c"][0],
                format="DD/MM/YYYY",
            )
        with colunas_dt[1]:
            data_entrega = colunas_dt[1].date_input(
                "Entrega",
                value=df_projeto["Habitese__c"][0],
                format="DD/MM/YYYY",
            )
            data_termino = colunas_dt[1].date_input(
                "Termino",
                value=df_projeto["Data_de_Termino__c"][0],
                format="DD/MM/YYYY",
            )
            perc_permuta = colunas_dt[1].number_input(
                "% Permuta", min_value=0.0, value=df_projeto["Perc_Permuta__c"][0]
            )

with velocidade_vendas_tab:
    st.markdown("**Velocidade de Vendas**")

    prechaves_expander = st.expander("Pre-chaves", expanded=False)
    with prechaves_expander:
        colunas_prechaves = st.columns([1, 1, 1])
        with colunas_prechaves[0]:
            pre_ch_ato = colunas_prechaves[0].number_input(
                "% Ato", min_value=0.0, value=df_premissa_sql["pre_ch_ato"][0]
            )
            pre_ch_periodo_repasse = colunas_prechaves[0].number_input(
                "Periodo repasse",
                min_value=0,
                value=int(df_premissa_sql["pre_ch_periodo_repasse"][0]),
            )
        with colunas_prechaves[1]:
            pre_ch_mensais = colunas_prechaves[1].number_input(
                "% Mensais",
                min_value=0.0,
                value=df_premissa_sql["pre_ch_mensais"][0],
            )
            pre_ch_carencia_repasse = colunas_prechaves[1].number_input(
                "Carência repasse",
                min_value=0,
                value=(int(df_premissa_sql["pre_ch_carencia_repasse"][0])),
            )
        with colunas_prechaves[2]:
            pre_ch_repasse = colunas_prechaves[2].number_input(
                "% Repasse",
                min_value=0.0,
                value=df_premissa_sql["pre_ch_repasse"][0],
            )
            pre_ch_carencia = colunas_prechaves[2].number_input(
                "Carência",
                min_value=0,
                value=df_premissa_sql["pre_ch_carencia"][0],
            )

    poschaves_expander = st.expander("Pós-chaves", expanded=False)
    with poschaves_expander:
        colunas_poschaves = st.columns([1, 1, 1])
        with colunas_poschaves[0]:
            pos_ch_ato = st.number_input(
                "% Ato Pós",
                min_value=0.0,
                value=df_premissa_sql["pos_ch_ato"][0],
            )
            pos_ch_periodo_recebimento = st.number_input(
                "Periodo rebimento pós",
                min_value=0,
                value=df_premissa_sql["pos_ch_periodo_repasse"][0],
            )
        with colunas_poschaves[1]:
            pos_ch_mensais = st.number_input(
                "% Mensais Pós",
                min_value=0.0,
                value=df_premissa_sql["pos_ch_mensais"][0],
            )
            pos_ch_prazo_vendas = st.number_input(
                "Prazo de vendas",
                min_value=0,
                value=df_premissa_sql["pos_ch_prazo_vendas"][0],
            )
        with colunas_poschaves[2]:
            pos_ch_repasse = st.number_input(
                "% Repasse Pós",
                min_value=0.0,
                value=df_premissa_sql["pos_ch_repasse"][0],
            )
            pos_ch_carencia = st.number_input(
                "Carência Pós",
                min_value=0,
                value=df_premissa_sql["pos_ch_carencia"][0],
            )

    hip_vendas_expander = st.expander("Hipóteses de vendas", expanded=False)
    with hip_vendas_expander:
        colunas_hip_vendas = st.columns([1, 1, 1])
        with colunas_hip_vendas[0]:
            hip_vendas_lancamento = st.number_input(
                "% Vendas lançamento",
                min_value=0.0,
                value=df_premissa_sql["hip_vendas_lancamento"][0],
            )
        with colunas_hip_vendas[1]:
            hip_vendas_periodo_obra = st.number_input(
                "% Vendas obras",
                min_value=0.0,
                value=df_premissa_sql["hip_vendas_periodo_obra"][0],
            )
        with colunas_hip_vendas[2]:
            hip_vendas_poschave = st.number_input(
                "% Vendas pós chaves",
                min_value=0.0,
                value=df_premissa_sql["hip_vendas_poschave"][0],
            )

    vendas_expander = st.expander("Vendas", expanded=False)
    with vendas_expander:
        colunas_vendas = st.columns([1, 1])
        with colunas_vendas[0]:
            venda_perc_desconto = st.number_input(
                "% Desconto",
                min_value=0.0,
                max_value=100.0,
                value=df_premissa_sql["venda_perc_desconto"][0],
            )
            venda_perc_comissao = st.number_input(
                "% Comissão",
                min_value=0.0,
                max_value=100.0,
                value=df_premissa_sql["venda_perc_comissao"][0],
            )
        with colunas_vendas[1]:
            venda_preco_m2_bruto = st.number_input(
                "Preço m² Bruto",
                min_value=0.0,
                value=df_premissa_sql["venda_preco_m2_bruto"][0],
            )
            venda_preco_m2_liquido = st.number_input(
                "Preço m² Liquido",
                min_value=0.0,
                value=df_premissa_sql["venda_preco_m2_liquido"][0],
            )

        bt_curva_vendas = st.button("Visualizar Curva")
        if bt_curva_vendas:
            df = fluxo.v.base_proj_vendas(data_premissa, selected_id)
            print("selected_id :", selected_id)
            print("data_premissa :", data_premissa)
            (
                status_projeto,
                data_termino_status,
                status_chave,
            ) = fluxo.v._status_projeto(
                data_premissa,
                data_lancamento,
                data_ini_obra,
                data_entrega,
                data_termino,
                pos_ch_periodo_recebimento,
            )
            df_ajuste, quadro_unid = fluxo.v.calculo_ajuste_vendas(
                df,
                hip_vendas_lancamento,
                hip_vendas_periodo_obra,
                hip_vendas_poschave,
                status_projeto,
            )
            (
                df_curva,
                resumo_vendasAno,
                rs_valuation_liquido,
            ) = fluxo.v.curvaVendas(
                df_projeto,
                df_ajuste,
                data_premissa,
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
            )

            st.dataframe(df_ajuste)
            st.dataframe(resumo_vendasAno)

with despesas_tab:
    despesas = st.columns([1])
    with despesas[0]:
        st.markdown("**Despesas**")
        inad_expander = st.expander("Inadimplência", expanded=False)
        with inad_expander:
            colunas_inadimplencia = st.columns([1, 1])
            with colunas_inadimplencia[0]:
                inad_curva_projetada = st.number_input(
                    "Curva projetada",
                    min_value=1,
                    help="Em quantas parcelas mensais recebera a inadimplencia",
                    value=df_premissa_sql["inad_curva_projetada"][0],
                )
            with colunas_inadimplencia[1]:
                inad_pdd = st.number_input(
                    "% PDD",
                    min_value=0.0,
                    max_value=100.0,
                    help="Percentual de perda da inadimplência",
                    value=df_premissa_sql["inad_pdd"][0],
                )

        distratos_expander = st.expander("Distratos", expanded=False)
        with distratos_expander:
            colunas_distratos = st.columns([1, 1])
            with colunas_distratos[0]:
                dist_unidades = st.number_input(
                    "Unidades distratadas",
                    min_value=0,
                    help="Projeção de quantas unidades serão distratadas",
                    value=df_premissa_sql["dist_unidades"][0],
                )
                dist_perc_devolucao = st.number_input(
                    "% Devolução",
                    min_value=0.0,
                    help="Projeção do valor a ser devolvido por distrato",
                    value=df_premissa_sql["dist_perc_devolucao"][0],
                )
            with colunas_distratos[1]:
                dist_data_inicio = st.date_input(
                    "Inicio pagamento distrato",
                    value=df_premissa_sql["dist_data_inicio"][0],
                    format="DD/MM/YYYY",
                )
                dist_meses = st.number_input(
                    "Quantidade de parcelas",
                    min_value=0,
                    help="Quantidade de parcelas mensais a serem pagos os distratos",
                    value=df_premissa_sql["dist_meses"][0],
                )
        outras_despesas = st.number_input(
            "% Outras despesas",
            min_value=0.0,
            max_value=100.0,
            help="percentual dos recebiveis no mês que serao considerados como despesas",
            value=df_premissa_sql["outras_despesas"][0],
        )

with cashsweep_tab:
    st.markdown("**Cashsweep**")
    cashsweep_expander = st.expander("Cashsweep", expanded=False)
    with cashsweep_expander:
        colunas_cashsweep = st.columns([1, 1])
        with colunas_cashsweep[0]:
            fin_carencia = st.number_input(
                "Carência financiamento",
                min_value=0,
                help="Quantidade de meses de carencia para incorporadora pagar o banco",
                value=df_premissa_sql["fin_carencia"][0],
            )
        with colunas_cashsweep[1]:
            st.write("Cashsweep?")
            cash_sweep = st.checkbox("")

if st.button("Calcular"):
    if versao == "" or versao == None:
        alerta._alerta_info(st, "Insira o nome da versão")

    progress_text = "Salvando dados. Aguarde..."
    my_bar = st.progress(0, text=progress_text)

    # *? Barra de Progresso
    i = 1
    percent = i
    total = 7  # * Numero de funções que serao chamadas
    my_bar.progress((percent / total), text=progress_text)
    sleep(1)

    # fluxo.fluxo_proj_vendas(df_projeto, data_premissa, data_lancamento, data_ini_obra, data_entrega, data_termino, venda_perc_comissao, venda_preco_m2_bruto, data_base_reajuste, hip_vendas_lancamento, hip_vendas_periodo_obra, hip_vendas_poschave, pos_ch_periodo_recebimento)
    # fluxo.fluxo_tot_recebiveis(con_sf=sf_con, id_projeto=selected_id, data_ref=data_premissa, meses_inad=inad_curva_projetada, pdd=inad_pdd)

    df = fluxo.v.base_proj_vendas(data_premissa, selected_id)
    percent = i + 1
    my_bar.progress((percent / total), text=progress_text)

    status_projeto, data_termino_status, status_chave = fluxo.v._status_projeto(
        data_premissa,
        data_lancamento,
        data_ini_obra,
        data_entrega,
        data_termino,
        pos_ch_periodo_recebimento,
    )
    percent = i + 1
    my_bar.progress((percent / total), text=progress_text)

    df_ajuste, quadro_unid = fluxo.v.calculo_ajuste_vendas(
        df,
        hip_vendas_lancamento,
        hip_vendas_periodo_obra,
        hip_vendas_poschave,
        status_projeto,
    )
    percent = i + 1
    my_bar.progress((percent / total), text=progress_text)

    df_curva, resumo_vendasAno, rs_valuation_liquido = fluxo.v.curvaVendas(
        df_projeto,
        df_ajuste,
        data_premissa,
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
    )
    print("df_curva\n", df)
    percent = i + 1
    my_bar.progress((percent / total), text=progress_text)

    fluxo.fluxo_distribuicao_teorica(
        indexador=df_projeto["Indexador"][0],
        taxa_spread=df_projeto["Spread"][0],
        df_proj_vendas=df_curva,
        id_projeto=selected_id,
        data_ref=data_premissa,
        meses_inad=inad_curva_projetada,
        pdd=inad_pdd,
        perc_permuta=perc_permuta,
        outras_despesas=outras_despesas,
    )
    percent = i + 1
    my_bar.progress((percent / total), text=progress_text)

    # fluxo.v.salvaPremissaSQL(id_projeto=selected_id, data_ref=data_premissa, versao=versao, data_lancamento=data_lancamento, data_ini_obra=data_ini_obra,
    #                     data_entrega=data_entrega, data_termino=data_termino, pre_ch_carencia_repasse=pre_ch_carencia_repasse, pre_ch_periodo_repasse=pre_ch_periodo_repasse,
    #                     pre_ch_ato=pre_ch_ato, pre_ch_mensais=pre_ch_mensais, pre_ch_repasse=pre_ch_repasse, pre_ch_carencia=pre_ch_carencia, pos_ch_prazo_vendas=pos_ch_prazo_vendas, pos_ch_periodo_repasse=pos_ch_periodo_recebimento,
    #                     pos_ch_ato=pos_ch_ato, pos_ch_mensais=pos_ch_mensais, pos_ch_repasse=pos_ch_repasse, pos_ch_carencia=pos_ch_carencia, hip_vendas_lancamento=hip_vendas_lancamento, hip_vendas_periodo_obra=hip_vendas_periodo_obra, hip_vendas_poschave=hip_vendas_poschave,
    #                     inad_curva_projetada=inad_curva_projetada, inad_pdd=inad_pdd, venda_perc_desconto=venda_perc_desconto, venda_perc_comissao=venda_perc_comissao, venda_preco_m2_bruto=venda_preco_m2_bruto, venda_preco_m2_liquido=rs_valuation_liquido,
    #                     fin_carencia=fin_carencia, cash_sweep=cash_sweep, dist_unidades=dist_unidades, dist_perc_devolucao=dist_perc_devolucao, dist_data_inicio=dist_data_inicio, dist_meses=dist_meses, outras_despesas=outras_despesas, data_insert=datetime.now())

    percent = i + 1
    my_bar.progress((percent / total), text=progress_text)
    sleep(1)

    my_bar.empty()
    st.success("Premissa salva com sucesso!")
