import json
from typing import Any
from darkdetect import isDark  # type:ignore[import-untyped]
import PySide6.QtGui as Gui
import PySide6.QtWidgets as Widgets
import keyboard
from debuglogger import Logger


class SysInfo:
    @staticmethod
    def getDisplayGeometry():
        geometry = Gui.QGuiApplication.primaryScreen().size().toTuple()
        return geometry


with open("./settings/settings.json", encoding="utf-8") as f:
    SETTINGS: dict[str, Any] = json.load(f)
with open(f"./languages/{SETTINGS['language']}.json", encoding="utf-8") as f:
    LANG: dict[str, str] = json.load(f)
STYLE = Widgets.QStyleFactory.create("Windows") 
_DEBUG: bool = SETTINGS["debug"]


def changeSkin():
    global SKIN
    if type(SETTINGS["skin"]) is dict:
        if(SETTINGS["theme"] == "auto"):
            SKIN = SETTINGS["skin"]["dark" if isDark() else "light"]
        else:
            SKIN = SETTINGS["skin"][SETTINGS["theme"]]
    else:
        SKIN = SETTINGS["skin"]


def qssReader(skin: str, name: str):
    try:
        with open(f"./skin/{skin}/{name}.qss", encoding="utf-8") as f:
            return f.read()
    except:
        log.error(f"无法找到文件./skin/{skin}/{name}.qss")
        return ""


def changeSetting(key: str, value: Any):
    global SETTINGS
    SETTINGS[key] = value
    with open("./settings/settings.json", "w", encoding="utf-8") as f:
        json.dump(SETTINGS, f)


#HOTKEY
with open("./settings/hotkeys.json") as f:
    HOTKEYS = json.load(f)
def setHotkey(hotkey: str, callback: Any, args: Any):
    keyboard.add_hotkey(hotkey, callback, args, suppress=True)


def setHotkeyWithoutSuppress(hotkey: str, callback: Any, args: Any):
    keyboard.add_hotkey(hotkey, callback, args)


def setHotkeyOnRelease(hotkey: str, callback: Any, args: Any):
    keyboard.add_hotkey(hotkey, callback, args, trigger_on_release=True)

def register(hotkey, func, args=None):
    keyboard.add_hotkey(hotkey, func, args)
    log.info(f"注册了快捷键{hotkey} -> {func.__name__}")
#INIT
SKIN: str
changeSkin()
log = Logger(thread=True)
