import os

from app import APIStreamHandler, App

app = App()


@app.main
async def main():
    stream_handler = APIStreamHandler(app)
    await stream_handler.begin_listening()


app.run()
