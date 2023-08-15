import tempfile
from typing import Literal

import pandas as pd

from controller import versoes


def _set_versoes_df_column_names(versoes_df: pd.DataFrame) -> pd.DataFrame:
    versoes_df.rename(columns=versoes.MAP_VERSAO_LABEL_FIELD, inplace=True)
    return versoes_df


def versoes_df_from_records(
    versoes_records: list[dict], indicadores: list[str] | Literal["all"]
) -> pd.DataFrame | None:
    if not isinstance(indicadores, list) and indicadores != "all":
        raise ValueError("Indicadores inválidos.")

    if len(versoes_records) < 1:
        return None

    campos_para_excluir = ["id", "id_premissa", "id_projeto", "tir_inclui_ipca"]
    if indicadores != "all":
        campos_para_excluir.extend(
            field
            for field in versoes.MAP_VERSAO_LABEL_FIELD.keys()
            if field not in indicadores
        )
    return _set_versoes_df_column_names(
        pd.DataFrame.from_records(
            versoes_records,
            exclude=campos_para_excluir,
        )
    )


def versoes_df_to_excel(versoes_df: pd.DataFrame):
    _, nome_arquivo = tempfile.mkstemp(".xlsx")
    versoes_df.to_excel(nome_arquivo, index=False)
    return nome_arquivo
