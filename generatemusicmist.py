import os, json

from settings import SETTINGS


def generate():
    MUSIC_LIST = [
        (os.path.join(music_path, filename))
        for music_path in SETTINGS["music_database"]
        for filename in os.listdir(music_path)
    ]
    with open("./settings/musiclist.json", "w", encoding="utf-8") as f:
        json.dump(MUSIC_LIST, f, indent=4, ensure_ascii=False)
