import PySide6.QtCore as Core
import PySide6.QtGui as Gui
import PySide6.QtWidgets as Widgets
import sys
from threading import Thread
from musicplayer import MusicPlayer
# from animation import WindowAnimation, ObjectAnimation
from notification import NotificationWindow
import pylogger.pylogger as log
import atexit
import os
from settings import SysInfo, LANG,SKIN,DEBUG
from queue import Queue

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__))))


class MainWindow:
    def __init__(self, SKIN):
        self.app = Widgets.QApplication(sys.argv)
        self.window = Widgets.QWidget()
        self.geometry = SysInfo.getDisplayGeometry()



log.info("创建主窗体...")
main = MainWindow(SKIN)
log.info(f"创建通知窗口...")
# Thread(target=newNotificationWindow, args=(SKIN,), daemon=True,name="NotificationWindow").start()
queue:Queue=Queue()
Thread(target=NotificationWindow,args=(SKIN,queue),daemon=True,name="Notification Window").start()
log.info("创建音乐播放器...")
music_player = MusicPlayer(SKIN, queue)
atexit.register(music_player.source_release)
log.info("程序主循环开始")
sys.exit(main.app.exec())
