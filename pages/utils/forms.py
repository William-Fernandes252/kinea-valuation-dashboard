from collections.abc import Sequence
from typing import Any

NULL_OPTION = "-"


def get_nullable_options(options: Sequence[Any]) -> Sequence[Any]:
    return [NULL_OPTION] + options
