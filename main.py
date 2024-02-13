from typing import Any, Callable, Mapping
import PySide6.QtCore as Core
import PySide6.QtGui as Gui
import PySide6.QtWidgets as Widgets
import sys
from threading import Thread

# from animation import WindowAnimation, ObjectAnimation
from notification import NotificationWindow
import pylogger.pylogger as log
import atexit
import os
from settings import HOTKEYS, SysInfo, LANG, SKIN, _DEBUG
from queue import Queue
from keyboard import add_hotkey
from musicplayer import MusicPlayer
from todo import Time
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__))))


def themeBroadcast(modules):
    global SKIN
    from settings import changeSkin, SKIN

    changeSkin()
    for module in modules:
        module.changeStyle()


class MainWindow:
    def __init__(self):
        self.app = Widgets.QApplication(sys.argv)
        self.window = Widgets.QWidget()
        self.geometry = SysInfo.getDisplayGeometry()
        self.queue: Queue = Queue()
        self.musicPlayerInit()
        self.todoInit()
        self.notificationWindowInit()
        self.changeThemeTriggerInit()
        add_hotkey(HOTKEYS["close"], self.closeApp)

    def changeThemeTriggerInit(self):
        self.palette = Widgets.QApplication.palette()
        style = Widgets.QStyleFactory.create("fusion")
        self.app.setPalette(self.palette)
        self.app.setStyle(style)
        self.app.paletteChanged.connect(self.changeTheme)
        log.info("主题切换触发器已启动")
        

    def changeTheme(self):
        self.app.setPalette(self.palette)
        themeBroadcast([self.music_player, self.todo.time])

    def musicPlayerInit(self):
        log.info("创建音乐播放器...")
        self.music_player = MusicPlayer(self.queue,self.app)
        log.info("完成")

    def todoInit(self):
        log.info("创建计划表...")

        class Todo(Thread):
            def __init__(
                self,
                name: str,
                app:Widgets.QApplication,
                *,
                daemon: bool | None = None,
            ) -> None:
                super().__init__(name=name,daemon=daemon)
                self.app = app

            def run(self):
                self.time = Time(self.app)
                self.time.run()

        self.todo = Todo("Todo",self.app, daemon=True)
        self.todo.start()

        log.info("完成")

    def notificationWindowInit(self):
        log.info(f"创建通知窗口...")
        Thread(
            target=NotificationWindow,
            args=(self.queue,),
            daemon=True,
            name="Notification Window",
        ).start()
        log.info("完成")

    def closeApp(self):
        log.info("正在关闭窗口...")
        self.window.destroy()
        self.music_player.source_release()
        self.todo.time.source_release()
        log.info("正在退出...")
        self.app.exit(0)
        sys.exit(0)

    def run(self):
        log.info("程序主循环开始")
        self.app.exec()
        log.info("事件循环已停止")


if __name__ == "__main__":
    log.init()
    if _DEBUG:
        log.setDebug()
    else:
        log.setOff()
    log.info("创建主窗体...")
    window = MainWindow()
    log.info("完成")
    window.run()
