from random import choice

from app import APIStreamHandler, App
from datamodels import BotUser
from utils import decode_json

app = App()


@app.main
async def main():
    stream_handler = APIStreamHandler(app)
    await stream_handler.begin_listening()


@app.loop(minutes=5)
async def challenge_sender():
    r = await app.session.get("/api/bot/online")
    users = [BotUser.from_json(d) for d in decode_json(await r.content.read())]
    user = choice(users)
    await app.challenges.send_challenge(user)


app.run()
