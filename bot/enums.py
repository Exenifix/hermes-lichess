from enum import Enum


class EventType(Enum):

    GAME_START = "gameStart"
    GAME_FINISH = "gameFinish"
    CHALLENGE = "challenge"
    CHALLENGE_CANCELED = "challengeCanceled"  # not handled
    CHALLENGE_DECLINED = "challengeDeclined"  # not handled

    GAME_FULL = "gameFull"  # handle redirected
    GAME_STATE = "gameState"


class Variant(Enum):
    STANDARD = "standard"


class Color(Enum):
    BLACK = "black"
    WHITE = "white"


class GameStatus(Enum):
    STARTED = "started"
    CREATED = "created"
    ABORTED = "aborted"
    MATE = "mate"
    RESIGN = "resign"
    STALEMATE = "stalemate"
    TIMEOUT = "timeout"
    DRAW = "draw"
    OUTOFTIME = "outoftime"
    CHEAT = "cheat"
    NO_START = "noStart"
    UNKNOWN_FINISH = "unknownFinish"
    VARIANT_END = "variantEnd"
