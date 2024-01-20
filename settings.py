import json
import PySide6.QtCore as Core
import PySide6.QtGui as Gui
import PySide6.QtWidgets as Widgets


class SysInfo:
    @staticmethod
    def getDisplayGeometry():
        geometry = Gui.QGuiApplication.primaryScreen().size().toTuple()
        return geometry


with open("./settings/settings.json", encoding="utf-8") as f:
    SETTINGS = json.load(f)
with open(f"./languages/{SETTINGS['language']}.json", encoding="utf-8") as f:
    LANG: dict[str, str] = json.load(f)


def qssReader(skin: str, name: str):
    with open(f"./skin/{skin}/{name}.qss", encoding="utf-8") as f:
        return f.read()
