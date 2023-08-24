import locale
from datetime import datetime
from functools import partial
from typing import Callable, Final, Generic, Optional, TypeVar, Union

from services import dates

VT = TypeVar("VT")

Formatter = Callable[[VT], str]


class Column(Generic[VT]):
    NONE_DISPLAY_VALUE: Final[str] = "-"

    label: str
    formatter: Union[Formatter, None]

    def __init__(self, label: str, formatter: Optional[Formatter] = None) -> None:
        self.label = label
        self.formatter = formatter

    def format(self, value: Union[VT, None]) -> str:
        return (
            self.formatter(value)
            if self.formatter and value is not None
            else str(value or self.NONE_DISPLAY_VALUE)
        )

    def __str__(self) -> str:
        return self.label


class DateColumn(Column[datetime]):
    def __init__(self, label: str) -> None:
        super().__init__(label, dates.get_mes_ano_display)


class CurrencyColumn(Column[float]):
    def __init__(self, label: str) -> None:
        super().__init__(label, partial(locale.currency, grouping=True))


class RatioColumn(Column[float]):
    def __init__(self, label: str) -> None:
        super().__init__(label, lambda value: f"{value:.2%}")
