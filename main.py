import PySide6.QtCore as Core
import PySide6.QtGui as Gui
import PySide6.QtWidgets as Widgets
import sys
from threading import Thread
from musicplayer import MusicPlayer

# from animation import WindowAnimation, ObjectAnimation
from notification import NotificationWindow
#import pylogger.pylogger as ##--log
import atexit
import os
from settings import HOTKEYS, SysInfo, LANG, SKIN, DEBUG
from queue import Queue
from keyboard import add_hotkey
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__))))


def themeBroadcast(*args):
    global SKIN
    from settings import changeSkin,SKIN
    changeSkin()
    music_player.changeStyle()
class MainWindow:
    def __init__(self):
        self.app = Widgets.QApplication(sys.argv)
        self.palette = Widgets.QApplication.palette()
        style = Widgets.QStyleFactory.create('fusion')
        self.app.setStyle(style)
        self.window = Widgets.QWidget()
        self.geometry = SysInfo.getDisplayGeometry()
        self.app.paletteChanged.connect(self.changeTheme)
    def changeTheme(self):
        self.app.setPalette(self.palette)
        themeBroadcast()
        


##--log.info("创建主窗体...")
window = MainWindow()
##--log.info(f"创建通知窗口...")
# Thread(target=newNotificationWindow, args=(SKIN,), daemon=True,name="NotificationWindow").start()
queue: Queue = Queue()
Thread(
    target=NotificationWindow, args=(queue,), daemon=True, name="Notification Window"
).start()
##--log.info("创建音乐播放器...")
music_player = MusicPlayer(queue)
atexit.register(music_player.source_release)
def closeApp():
    window.window.destroy()
    window.app.quit()
add_hotkey(HOTKEYS["close"],closeApp)
##--log.info("主题切换触发器已启动")

##--log.info("程序主循环开始")
sys.exit(window.app.exec())




# if __name__ == "__main__":
#     main()
