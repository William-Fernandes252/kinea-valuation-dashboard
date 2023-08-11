from typing import Literal

import pandas as pd

from controller import versoes


def versoes_df_from_records(
    versoes_records: list[dict], indicadores: list[str] | Literal["all"]
) -> pd.DataFrame | None:
    if len(versoes_records) < 1:
        return None

    campos_para_excluir = ["id", "id_premissa", "id_projeto", "tir_inclui_ipca"]
    if indicadores != "all":
        campos_para_excluir.extend(
            field
            for field in versoes.MAP_VERSAO_LABEL_FIELD.keys()
            if field not in indicadores
        )
    return pd.DataFrame.from_records(
        versoes_records,
        exclude=campos_para_excluir,
    )
