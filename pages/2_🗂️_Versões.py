import streamlit as st

from controller import sql_functions, versoes
from pages.utils import config, forms, state
from services import dates

name = "versoes"

config.set_page_settings(st)

use_state = state.init_page_state(st, name)

get_mostrar_resultados, set_mostrar_resultados = use_state("mostrar_resultados", False)


st.header("🗂️ Versões")


projeto_form = st.form("project-form")
(
    projeto_form_col1,
    projeto_form_col2,
    projeto_form_col3,
    projeto_form_col4,
) = projeto_form.columns(4)

fundo = projeto_form_col1.selectbox(
    "fundo",
    options=forms.get_nullable_options(["Todos"]),
    help="Fundo de investimentos.",
)
incorporadora = projeto_form_col2.selectbox(
    "Incorporadora", options=forms.get_nullable_options(["Seleções múltiplas"])
)
tipo_projeto = projeto_form_col3.selectbox(
    "Tipo de projeto", options=forms.get_nullable_options(["Todos"])
)
projeto = projeto_form_col4.selectbox(
    "Projeto", options=forms.get_nullable_options([1, 2, 3])
)


def validar_projeto_form(*, tipo_projeto, incorporadora, fundo, projeto) -> str | None:
    if forms.NULL_OPTION in [tipo_projeto, incorporadora, fundo, projeto]:
        return "Preencha todos os campos para obter os resultados."
    return None


if projeto_form.form_submit_button(
    label="Aplicar",
    type="primary",
):
    resultado = validar_projeto_form(
        tipo_projeto=tipo_projeto,
        incorporadora=incorporadora,
        fundo=fundo,
        projeto=projeto,
    )
    if resultado == None:
        set_mostrar_resultados(True)
        st.experimental_rerun()
    else:
        st.error(resultado)
elif (
    validar_projeto_form(
        tipo_projeto=tipo_projeto,
        incorporadora=incorporadora,
        fundo=fundo,
        projeto=projeto,
    )
    is not None
):
    set_mostrar_resultados(False)

if get_mostrar_resultados():
    st.divider()

    st.markdown("### Resultados")

    get_mostrar_versoes, set_mostrar_versoes = use_state("mostrar_versoes", False)

    versoes_df = sql_functions.select_versoes()

    configuracao_aside, main = st.columns([1, 3])
    with configuracao_aside:
        versoes_config_form = configuracao_aside.form("version-config-form")

        def validate_versoes(
            *, versoes: list[dict], indicadores: list[str]
        ) -> str | None:
            if len(versoes) < 1:
                return "Selecione pelo menos uma versão para analisar."
            if "Todos" in indicadores and len(indicadores) > 1:
                return "Seleção de indicadores inválida."
            if len(indicadores) < 1:
                return "Selecione pelo menos um indicador."
            return None

        versoes_selecionadas = versoes_config_form.multiselect(
            "Selecionar Versões",
            options=versoes_df.to_dict("records"),
            format_func=lambda versao: dates.get_mes_ano_display(versao["data_base"]),
            max_selections=2,
            help="Selecione duas versões para comparar.",
        )

        indicadores = versoes_config_form.multiselect(
            "Escolher indicadores",
            options=["Todos"]
            + [field for field in versoes_df.keys() if field in versoes.fields],
            format_func=lambda indicador: versoes.get_label(indicador)
            if indicador in versoes_df.keys()
            else indicador,
            help="Selecione os indicadores para visualização.",
        )

        if versoes_config_form.form_submit_button(
            label="Aplicar",
            type="primary",
            kwargs={"versoes": versoes_selecionadas, "indicadores": indicadores},
        ):
            resultado = validate_versoes(
                versoes=versoes_selecionadas,
                indicadores=indicadores,
            )
            if resultado == None:
                set_mostrar_versoes(True)
                st.experimental_rerun()
            else:
                st.error(resultado)
        elif (
            validate_versoes(versoes=versoes_selecionadas, indicadores=indicadores)
            is not None
        ):
            set_mostrar_versoes(False)

    with main:
        if get_mostrar_versoes():
            try:
                resultado_versoes_df = versoes.get_versoes(
                    versoes_selecionadas,
                    None
                    if "Todos" in indicadores
                    else [key for key in versoes.fields if key not in indicadores],
                    transpose=True,
                )
            except ValueError as e:
                versoes_config_form.error(str(e))
            else:
                if resultado_versoes_df is not None:
                    main.dataframe(
                        resultado_versoes_df,
                        use_container_width=True,
                        column_config={
                            field: {"width": "auto", "alignment": "center"}
                            for field in versoes.fields
                        },
                    )
                    with open(
                        versoes.versoes_df_to_excel(resultado_versoes_df), "rb"
                    ) as versoes_excel:
                        main.download_button(
                            "Baixar análise", versoes_excel, "versoes.xlsx"
                        )
                else:
                    main.warning("Base vazia.")
