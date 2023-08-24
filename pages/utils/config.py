import locale


def header(st, page_name: str):
    st.header(page_name)


def set_page_settings(st, layout: str = "wide") -> None:
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")
    st.set_page_config(
        page_title="Valuation Projetos",
        page_icon="📋",
        layout=layout,
    )
