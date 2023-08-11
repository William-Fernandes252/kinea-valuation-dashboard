from streamlit.delta_generator import DeltaGenerator


def _alerta_info(st, frase):
    st.warning(frase, icon="⚠️")
    if not isinstance(st, DeltaGenerator):
        st.stop()
