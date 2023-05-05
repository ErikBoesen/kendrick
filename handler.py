import sys
sys.path.insert(0, 'vendor')

import os
import requests
import random
import json

from PIL import Image, ImageDraw, ImageFont
from images import get_source_url, pil_from_url, resize, upload_pil_image


def transform_text(text):
    if not text:
        return "DAMN."
    # Use mention if there's something in it
    if "@" in text[:-1]:
        # Get the name after an @
        text = text.split("@")[1].split()[0]
    return text.strip(".").upper() + "."

def response(query, message):
    query = transform_text(query)
    source_url = get_source_url(message)
    if source_url is None:
        background = Image.open("resources/damn.jpg")
    else:
        background = pil_from_url(source_url)
    background_width, background_height = background.size
    draw_background = ImageDraw.Draw(background)

    font_size = background_width
    font = ImageFont.truetype("resources/times.ttf", font_size)
    words = Image.new("RGBA", draw_background.textsize(query, font=font))
    draw_words = ImageDraw.Draw(words)
    draw_words.text((0, 0), query, font=font, fill=(255, 0, 0))
    # We need to trim off the top of the image because the font has padding
    words_width, words_height = words.size
    words = words.crop((0, int(font_size * .23), words_width, words_height))
    # Resize to fit width of background
    words = resize(words, background_width)

    # Superimpose text
    background.paste(words, (0, 0), words)

    # Send finished image
    return "", upload_pil_image(background, message["token"])


def receive(event, context):
    message = json.loads(event["body"])
    print("Received message:")
    print(message)

    bot_id = message["bot_id"]
    reply = process(message)
    if reply:
        send(*reply, bot_id)

    return {
        "statusCode": 200,
        "body": "ok",
    }


def process(message):
    # Prevent self-reply
    if message["sender_type"] != "bot":
        text = message["text"]
        if text.lower().startswith("damn"):
            text = text.replace("damn", "", 1).replace("DAMN", "", 1).strip()
            return response(text, message)


def send(text, image_url, bot_id):
    url = "https://api.groupme.com/v3/bots/post"

    message = {
        "bot_id": bot_id,
        "text": text,
        "picture_url": image_url,
    }
    r = requests.post(url, json=message)
