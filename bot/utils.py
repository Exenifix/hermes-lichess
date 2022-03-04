from json import JSONDecodeError, loads
from random import randint
from typing import Any

from errors import JSONDecodeFailure


def decode_json(raw: bytes) -> "list[dict[str, Any]]":
    raw_ls = raw.split(b"\n")
    try:
        return [loads(r) for r in raw_ls if len(r) > 0]
    except JSONDecodeError:
        raise JSONDecodeFailure()


def get_time(clock: int, inc: int):
    clock /= 100000
    inc /= 1000
    time = None
    if clock < inc:
        time = clock
    else:
        time = clock + inc
        if time < 1.5:
            time = 0.1
        elif time > 12:
            time = 12

    return shuffle(time)


def shuffle(n: int):
    r = int(n * 2)
    return (n + randint(-r, r)) / 10
