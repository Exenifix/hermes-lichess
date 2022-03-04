import asyncio
import os
import traceback
from io import StringIO
from typing import Coroutine

import aiohttp
import chess
import chess.engine
from dotenv import load_dotenv

from colorlogs import Color, Logger
from datamodels import APIEvent, Game, GameStateEvent
from enums import Color as GameColor
from enums import EventType, GameStatus, Variant
from errors import ConnectionFailure, JSONDecodeFailure
from utils import decode_json, get_time

load_dotenv()
HEADERS = {"Authorization": "Bearer " + os.getenv("TOKEN")}


class AppMainFunction:
    def __init__(self, coro: Coroutine):
        self.coro = coro

    async def __call__(self):
        return await self.coro()


class App:
    session: aiohttp.ClientSession
    engine: chess.engine.SimpleEngine
    log: Logger
    call: AppMainFunction

    async def setup(self):
        self.session = aiohttp.ClientSession("https://lichess.org", headers=HEADERS)
        _, self.engine = await chess.engine.popen_uci(os.getenv("ENGINE_PATH"))
        self.log = Logger()
        self.games = []

    def main(self, coro: Coroutine):
        self.call = AppMainFunction(coro)
        return self.call

    def run(self):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self._run())

    async def _run(self):
        await self.setup()
        await self.call()


class StreamHandler:
    def __init__(self, app: App, endpoint: str):
        self.app = app
        self.stream = None
        self._endpoint = endpoint

    async def connect(self):
        self.app.log.info(
            "Establishing connection to %s%s",
            self.app.session._base_url,
            self._endpoint,
        )
        r = await self.app.session.get(self._endpoint)
        if r.status != 200:
            raise ConnectionFailure(r.status, await r.json())

        self.stream = r.content
        self.app.log.info(Color.colorize("CONNECTED SUCCESSFULLY", Color.GREEN))


class APIStreamHandler(StreamHandler):
    def __init__(self, app: App):
        super().__init__(app, "/api/stream/event")

    async def begin_listening(self):
        await self.connect()
        while True:
            try:
                await self._handle_events()
            except (aiohttp.ServerDisconnectedError, asyncio.TimeoutError):
                self.app.log.warning("Server disconnected, reconnecting...")
                await self.connect()
            except Exception as e:
                self.app.log.error("Unknown exception: %s", e)
                s = StringIO()
                traceback.print_exception(type(e), e, e.__traceback__, file=s)
                print(s.getvalue())
                break

    async def _handle_events(self):
        async for raw_data in self.stream.iter_any():
            decoded = raw_data.decode()
            if decoded == "\n" or decoded == "\n\n":
                continue

            try:
                data_ls = decode_json(raw_data)
            except JSONDecodeFailure:
                self.app.log.warning("Failed to decode JSON: %s", raw_data)
                continue

            for data in data_ls:
                event = APIEvent.from_json(data)
                if event is None:
                    self.app.log.warning("Received unhandled event: %s", data["type"])
                    continue

                if event.type == EventType.CHALLENGE:
                    self.app.log.info(
                        "Received a challenge, ID: %s", event.challenge.id
                    )
                    # Currently only accepting standart
                    if event.challenge.variant == Variant.STANDARD:
                        await self.accept_challenge(event.challenge.id)
                    else:
                        await self.decline_challenge(event.challenge.id)

                elif event.type == EventType.GAME_START:
                    self.app.log.info("Starting a game, ID: %s", event.game.id)
                    game_handler = GameStreamHandler(self.app, event.game)
                    asyncio.create_task(game_handler.play())

    async def accept_challenge(self, challenge_id: str):
        await self.app.session.post(f"/api/challenge/{challenge_id}/accept")

    async def decline_challenge(self, challenge_id: str):
        await self.app.session.post(f"/api/challenge/{challenge_id}/decline")


class GameStreamHandler(StreamHandler):
    def __init__(self, app, game: Game):
        super().__init__(app, f"/api/bot/game/stream/{game.id}")
        self.game = game
        self.board = chess.Board()
        self.moves = ""

    async def play(self):
        await self.connect()
        while True:
            try:
                async for raw_data in self.stream.iter_any():
                    decoded = raw_data.decode()
                    if decoded == "\n" or decoded == "\n\n":
                        continue

                    try:
                        data_ls = decode_json(raw_data)
                    except JSONDecodeFailure:
                        self.app.log.warning("Failed to decode JSON: %s", raw_data)
                        continue

                    for data in data_ls:
                        event = APIEvent.from_json(data)
                        if event is None:
                            self.app.log.warning(
                                "Received unhandled event for game %s: %s",
                                self.game.id,
                                data["type"],
                            )
                            continue

                        if event.type == EventType.GAME_STATE:
                            if event.status != GameStatus.STARTED:
                                self.app.log.info(
                                    "The game %s finished with status %s",
                                    self.game.id,
                                    str(event.status),
                                )
                                return
                            await self.on_game_state(event)

                        elif event.type == EventType.GAME_START:
                            self.app.log.info("The game %s has started", self.game.id)

            except (aiohttp.ServerDisconnectedError, asyncio.TimeoutError):
                self.app.log.warning("Server disconnected, reconnecting...")
                await self.connect()
            except Exception as e:
                self.app.log.error("Unknown exception: %s", e)
                s = StringIO()
                traceback.print_exception(type(e), e, e.__traceback__, file=s)
                print(s.getvalue())
                break

    async def take_turn(self, wtime: int, btime: int, winc: int, binc: int):
        clock, inc = (
            (wtime, winc) if self.game.color == GameColor.WHITE else (btime, binc)
        )
        move: chess.Move = (
            await self.app.engine.play(
                self.board,
                chess.engine.Limit(time=get_time(clock, inc)),
            )
        ).move
        self.push(move)

        r = await self.app.session.post(
            f"/api/bot/game/{self.game.id}/move/{move.uci()}"
        )
        if r.status != 200:
            self.app.log.warning(
                "Invalid move sent to game %s, revalidating...", self.game.id
            )
            self.revalidate()
            await self.take_turn(wtime, btime, winc, binc)

    async def on_game_state(self, event: GameStateEvent):
        self.moves = event.moves
        if self.game.color == GameColor.WHITE and not self.game.has_moved:
            self.app.log.debug("Playing as white so doing a turn")
            self.game.has_moved = True
            await self.take_turn(event.wtime, event.btime, event.winc, event.binc)
        if len(self.board.move_stack) == 0 and len(self.moves.split()) != 0:
            self.app.log.warning(
                "Received a GAME_STATE event but there were \
no moves detected on local board, revalidating..."
            )
            self.revalidate()

        try:
            server_last_move = self.moves.split()[-1]
            local_last_move = self.board.move_stack[-1].uci()
        except:
            return

        if (
            server_last_move != local_last_move
            or (self.game.color == GameColor.WHITE and len(self.moves.split()) % 2 == 0)
            or (self.game.color == GameColor.BLACK and len(self.moves.split()) % 2 != 0)
        ):
            self.push(chess.Move.from_uci(server_last_move))
            await self.take_turn(event.wtime, event.btime, event.winc, event.binc)

    def revalidate(self):
        self.app.log.info("Revalidation started")
        self.board = chess.Board()
        for move in self.moves.split():
            self.board.push_uci(move)

        self.app.log.info("Revalidation finished. Revalidated moves: %s", self.moves)

    def push(self, move: chess.Move):
        try:
            self.board.push(move)
        except AssertionError:
            self.app.log.warning(
                "Invalid move submitted to local game %s, revalidating...", self.game.id
            )
            self.revalidate()
