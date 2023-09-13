from __future__ import annotations

from threading import Thread
from time import sleep
from typing import Any, Callable, List, Mapping


def set_timeout(
    seconds: int,
    fn: Callable[[*List[Any]], Any],
    args: List[Any] = None,
    kwargs: Mapping = None,
) -> None:
    def run(*args, **kwargs):
        sleep(seconds)
        fn(*args, **kwargs)

    thread = Thread(target=run, args=args or [], kwargs=kwargs or {})
    thread.run()
