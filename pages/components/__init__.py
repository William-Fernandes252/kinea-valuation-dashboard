from abc import ABC, abstractclassmethod
from collections.abc import Sequence
from functools import partial
from typing import Any, AnyStr, ClassVar, Optional, Protocol, Self

from attrs import field, frozen, validators
from streamlit.delta_generator import DeltaGenerator

Error = AnyStr


define_component = partial(frozen, slots=False, kw_only=True)


class Validator(Protocol):
    def __call__(self, *args: Any, **kwds: Any) -> Optional[Error]:
        ...


@define_component
class Component(ABC):
    root: DeltaGenerator = field(
        init=False, validator=validators.instance_of(DeltaGenerator)
    )

    @abstractclassmethod
    def render(cls, root: DeltaGenerator) -> Self:
        ...


@define_component
class Form(Component, ABC):
    NULL_OPTION: ClassVar[str] = "-"
    submitted: bool = False
    validator: Optional[Validator] = field(default=None)

    @classmethod
    def get_nullable_options(cls, options: Sequence[Any]) -> Sequence[Any]:
        return [cls.NULL_OPTION] + [*options]
