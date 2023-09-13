from __future__ import annotations

import tempfile
from typing import Dict, Final, List

import pandas as pd

from controller.utils.dataframes import columns

_VERSAO_DF_CONFIG: Final[Dict[str, columns.Column]] = {
    "receita_carteira": columns.CurrencyColumn("Receita (Carteira)"),
    "receita_estoque": columns.CurrencyColumn("Receita (Estoque)"),
    "decoracao": columns.CurrencyColumn("Decoração"),
    "tir_real": columns.RatioColumn("TIR REAL"),
    "tir_nominal": columns.RatioColumn("TIR NOMINAL"),
    "receita_vendida_pre_chaves": columns.CurrencyColumn("Receita Vendida Pré Chaves"),
    "receita_vendida_pos_chaves": columns.CurrencyColumn("Receita Vendida Pós Chaves"),
    "estoque_pre_chaves": columns.CurrencyColumn("Estoque Pré Chaves"),
    "estoque_pos_chaves": columns.CurrencyColumn("Estoque Pós Chaves"),
    "financiamento_banco": columns.CurrencyColumn("Financiamento Banco"),
    "divida_hoje": columns.CurrencyColumn("Dívida Hoje"),
    "ic": columns.CurrencyColumn("IC"),
    "ic_fp": columns.CurrencyColumn("IC FP"),
    "ltv": columns.CurrencyColumn("LTV"),
    "inadimplencia": columns.CurrencyColumn("Inadimplência"),
    "unidades_inadimplentes": columns.CurrencyColumn("Unidades Inadimplentes"),
    "razao_inadimplente_vendido": columns.Column("% inadimplente Vendido"),
    "razao_vendido": columns.RatioColumn("% Vendido"),
    "area_estoque": columns.CurrencyColumn("Area Estoque"),
    "razao_lucro_area_media_vendas": columns.RatioColumn("R$/m² Médio Vendas"),
    "razao_lucro_area_estoque": columns.CurrencyColumn("R$/m² Estoque"),
    "razao_custo_area_liquidacao_divida": columns.CurrencyColumn(
        "R$/m² para liquidar dívida"
    ),
    "distribuicao_mes": columns.CurrencyColumn("Distribuição Mes"),
    "distribuicao_acumulada": columns.CurrencyColumn("Distribuição Acumulada"),
    "projetado_a_distribuir": columns.CurrencyColumn("Projetado a Distribuir"),
    "saldo_incorporador": columns.CurrencyColumn("Saldo Incorporador"),
    "razao_custo_area_para_zerar_saldo_incorporador": columns.RatioColumn(
        "R$/m² para zerar saldo incorporador"
    ),
    "inicio_cash_sweep": columns.CurrencyColumn("Início Cash Sweep"),
    "data_base": columns.DateColumn("Data Base"),
}

fields: Final[List[str]] = [
    field for field in _VERSAO_DF_CONFIG.keys() if field != "data_base"
]


def get_label(field: str) -> str:
    if field not in _VERSAO_DF_CONFIG:
        raise ValueError("Campo inválido.")
    return _VERSAO_DF_CONFIG[field].label


def get_versoes(
    versoes_records: List[dict],
    campos_para_excluir: List[str] | None = None,
    transpose: bool = False,
) -> pd.DataFrame | None:
    if campos_para_excluir is not None and not isinstance(campos_para_excluir, list):
        raise ValueError("Indicadores inválidos.")

    if len(versoes_records) < 1:
        return None

    campos_para_excluir = ["id", "id_premissa", "id_projeto", "tir_inclui_ipca"] + (
        campos_para_excluir if campos_para_excluir is not None else []
    )

    df = pd.DataFrame.from_records(
        versoes_records,
        exclude=campos_para_excluir,
    )
    _format_columns(df)
    _set_index_as_data_base(df)
    _set_columns_names(df)

    return df if not transpose else df.T


def _set_index_as_data_base(df: pd.DataFrame) -> pd.DataFrame:
    df.set_index("data_base", inplace=True)
    return df


def _format_columns(df: pd.DataFrame) -> pd.DataFrame:
    for column in df:
        df[column] = df[column].apply(lambda x: _VERSAO_DF_CONFIG[column].format(x))
    return df


def _set_columns_names(df: pd.DataFrame) -> pd.DataFrame:
    df.rename(columns=_VERSAO_DF_CONFIG, inplace=True)
    return df


def versoes_df_to_excel(versoes_df: pd.DataFrame):
    _, nome_arquivo = tempfile.mkstemp(".xlsx")
    versoes_df.to_excel(nome_arquivo)
    return nome_arquivo
