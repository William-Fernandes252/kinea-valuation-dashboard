from typing import Self

from streamlit.delta_generator import DeltaGenerator

from pages.components import Form, define_component


@define_component
class ProjetoForm(Form):
    fundo: str
    incorporadora: str
    tipo_projeto: str
    projeto: str

    @classmethod
    def render(cls, root: DeltaGenerator) -> Self:
        def validar_projeto_form(
            *, tipo_projeto, incorporadora, fundo, projeto
        ) -> str | None:
            if cls.NULL_OPTION in [tipo_projeto, incorporadora, fundo, projeto]:
                return "Preencha todos os campos para obter os resultados."
            return None

        projeto_form = root.form("project-form")
        (
            projeto_form_col1,
            projeto_form_col2,
            projeto_form_col3,
            projeto_form_col4,
        ) = projeto_form.columns(4)

        fundo = projeto_form_col1.selectbox(
            "fundo",
            options=cls.get_nullable_options(["Todos"]),
            help="Fundo de investimentos.",
        )
        incorporadora = projeto_form_col2.selectbox(
            "Incorporadora", options=cls.get_nullable_options(["Seleções múltiplas"])
        )
        tipo_projeto = projeto_form_col3.selectbox(
            "Tipo de projeto", options=cls.get_nullable_options(["Todos"])
        )
        projeto = projeto_form_col4.selectbox(
            "Projeto", options=cls.get_nullable_options([1, 2, 3])
        )

        button = projeto_form.form_submit_button(
            label="Aplicar",
            type="primary",
        )

        return cls(
            fundo=fundo,
            incorporadora=incorporadora,
            tipo_projeto=tipo_projeto,
            projeto=projeto,
            submitted=button,
            validator=validar_projeto_form,
        )
