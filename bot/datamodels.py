from enums import *


class APIEvent:
    def __init__(self, _type: str):
        self.type = EventType(_type)

    @classmethod
    def from_json(cls, data: dict):
        try:
            event_type = EventType(data["type"])
        except ValueError:
            return None

        if event_type == EventType.GAME_START:
            return GameStartEvent(data)

        elif event_type == EventType.GAME_FINISH:
            return GameFinishEvent(data)

        elif event_type == EventType.CHALLENGE:
            return ChallengeEvent(data)

        elif event_type == EventType.GAME_STATE:
            return GameStateEvent(data)

        elif event_type == EventType.GAME_FULL:
            return GameStateEvent(data["state"])

        else:
            return None


class APIGameEvent(APIEvent):
    def __init__(self, data: dict):
        super().__init__(data["type"])
        self.game = Game.from_json(data["game"])


class GameStartEvent(APIGameEvent):
    def __init__(self, data: dict):
        super().__init__(data)


class GameFinishEvent(APIGameEvent):
    def __init__(self, data: dict):
        super().__init__(data)


class APIChallengeEvent(APIEvent):
    def __init__(self, data: dict):
        super().__init__(data["type"])
        self.challenge = Challenge.from_json(data["challenge"])


class ChallengeEvent(APIChallengeEvent):
    def __init__(self, data: dict):
        super().__init__(data)


class ChallengeCanceledEvent(APIChallengeEvent):
    def __init__(self, data: dict):
        super().__init__(data)


class ChallengeDeclinedEvent(APIChallengeEvent):
    def __init__(self, data: dict):
        super().__init__(data)


class GameStateEvent(APIEvent):
    moves: str
    wtime: int
    btime: int
    winc: int
    binc: int
    status: GameStatus

    def __init__(self, data: dict):
        super().__init__(data["type"])
        self.moves = data["moves"]
        self.wtime = data["wtime"]
        self.btime = data["btime"]
        self.winc = data["winc"]
        self.binc = data["binc"]
        self.status = GameStatus(data["status"])


class DataModel:
    pass


class Game(DataModel):
    id: str
    color: Color
    fen: str
    has_moved: bool
    is_my_turn: bool
    last_move: bool
    variant: Variant

    @classmethod
    def from_json(cls, json):
        obj = cls.__new__(cls)
        obj.id = json["gameId"]
        obj.color = Color(json["color"])
        obj.fen = json["fen"]
        obj.has_moved = json["hasMoved"]
        obj.is_my_turn = json["isMyTurn"]
        obj.last_move = json["lastMove"]
        obj.variant = Variant(json["variant"]["key"])

        return obj


class Challenge(DataModel):
    id: str
    variant: Variant
    time_control: "TimeControl"

    @classmethod
    def from_json(cls, json: dict):
        obj = cls.__new__(cls)
        obj.id = json["id"]
        obj.variant = Variant(json["variant"]["key"])
        try:
            obj.time_control = TimeControl(
                json["timeControl"]["limit"], json["timeControl"]["increment"]
            )
        except:
            obj.time_control = None

        return obj


class TimeControl:
    limit: int
    increment: int

    def __init__(self, limit, increment):
        self.limit = limit
        self.increment = increment


class BotUser(DataModel):
    id: str
    username: str

    @classmethod
    def from_json(cls, json: dict):
        obj = cls.__new__(cls)
        obj.id = json["id"]
        obj.username = json["username"]

        return obj
