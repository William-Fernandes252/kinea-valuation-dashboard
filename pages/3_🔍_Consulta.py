import streamlit as st

from pages.components import projeto_form
from pages.utils import config, state

name = "versoes"

config.set_page_settings(st)

use_state = state.init_page_state(st, name)

get_mostrar_comandos, set_mostrar_comandos = use_state("mostrar_comandos", False)


st.header("🔍 Consulta")

projeto_form_component = projeto_form.ProjetoForm.render(st)
if projeto_form_component.submitted:
    resultado = projeto_form_component.validator(
        tipo_projeto=projeto_form_component.tipo_projeto,
        incorporadora=projeto_form_component.incorporadora,
        fundo=projeto_form_component.fundo,
        projeto=projeto_form_component.projeto,
    )
    if resultado == None:
        set_mostrar_comandos(True)
        st.experimental_rerun()
    else:
        st.error(resultado)
elif (
    projeto_form_component.validator(
        tipo_projeto=projeto_form_component.tipo_projeto,
        incorporadora=projeto_form_component.incorporadora,
        fundo=projeto_form_component.fundo,
        projeto=projeto_form_component.projeto,
    )
    is not None
):
    set_mostrar_comandos(False)

if get_mostrar_comandos():
    st.divider()

    st.markdown("### Downloads")

    column1, column2, column3, column4 = st.columns([1, 1, 1, 1])
    with column1:
        st.download_button("Base de vendas", type="primary")
    with column2:
        st.download_button("Fluxo", type="primary")
    with column3:
        st.download_button("Curva", type="primary")
    with column4:
        st.download_button("Curva CRI", type="primary")
