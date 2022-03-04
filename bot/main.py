import os

from app import APIStreamHandler, App

app = App()

if not os.path.exists(".env"):
    app.log.critical("Config file wasn't found. Please fill up the .env file.")
    with open(".env", "w") as f:
        f.write("TOKEN=\nENGINE_PATH=./engine")


@app.main
async def main():
    stream_handler = APIStreamHandler(app)
    await stream_handler.begin_listening()


app.run()
