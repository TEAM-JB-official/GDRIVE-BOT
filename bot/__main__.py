import os
import logging
from threading import Thread
from flask import Flask
from pyrogram import Client

from bot import (
    APP_ID,
    API_HASH,
    BOT_TOKEN,
    DOWNLOAD_DIRECTORY
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

LOGGER = logging.getLogger(__name__)

app_flask = Flask(__name__)


@app_flask.route("/")
def home():
    return "Bot is running!"


def run_web():
    port = int(os.environ.get("PORT", 5000))
    app_flask.run(host="0.0.0.0", port=port)


if __name__ == "__main__":

    if not os.path.isdir(DOWNLOAD_DIRECTORY):
        os.makedirs(DOWNLOAD_DIRECTORY)

    Thread(target=run_web).start()

    plugins = dict(root="bot/plugins")

    app = Client(
        "G-DriveBot",
        bot_token=BOT_TOKEN,
        api_id=APP_ID,
        api_hash=API_HASH,
        plugins=plugins,
        workdir=DOWNLOAD_DIRECTORY
    )

    LOGGER.info("Starting Bot!")

    app.run()
