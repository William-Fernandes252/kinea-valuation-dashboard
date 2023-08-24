from typing import Callable, Tuple, TypeVar

S = TypeVar("S")

StateGetter = Callable[[], S]
StateSetter = Callable[[S], None]

UseState = Callable[[str, S], Tuple[StateGetter, StateSetter]]


def init_page_state(st, page_name: str) -> UseState:
    def use_state(key: str, initial_value: S = None) -> Tuple[StateGetter, StateSetter]:
        state_key = f"{page_name}.{key}"

        def get_state() -> S:
            return st.session_state[state_key]

        def set_state(value: S) -> None:
            st.session_state[state_key] = value

        if state_key not in st.session_state:
            set_state(initial_value)

        return (get_state, set_state)

    return use_state
