#import pylogger.pylogger as ##--log
import PySide6.QtCore as Core
import PySide6.QtGui as Gui
import PySide6.QtWidgets as Widgets
from settings import LANG, SKIN, SysInfo, qssReader
# from animation import ObjectAnimation, WindowAnimation, Mode
from time import sleep,time
from queue import Queue
from threading import Thread
from sched import scheduler
Path = str
# win_animation = WindowAnimation()
# obj_animation = ObjectAnimation()

class NotificationWindow:
    def __init__(
        self,
        queue: Queue,
        auto_hide: bool = True,
        default_show_time: int = 5,
        *,
        fade_in: bool = True,
        fade_out: bool = True,
    ):
        return
        self.window = Widgets.QWidget()
        self.geometry = SysInfo.getDisplayGeometry()
        self.max_width, self.max_height = self.geometry
        self.width, self.height = max(600, self.max_width // 5), max(
            200, self.max_height // 5
        )
        self.layout = Widgets.QVBoxLayout()
        self.layout.setAlignment(Core.Qt.AlignmentFlag.AlignTop)
        a = Widgets.QLabel()
        a.setText("Test")
        self.window.setLayout(self.layout)
        self.default_animation_time = 0.5
        self.default_show_time: int = default_show_time
        self.remain_time: int = self.default_show_time
        self.fade_in: bool = fade_in
        self.fade_out: bool = fade_out
        self.STYLESHEET = qssReader(SKIN, "NotificationWindow")
        self.queue = queue
        self.window_init()
        self.window.setStyleSheet(self.STYLESHEET)
        self.window.show()
        self.layout.addWidget(a)
        self.showed = True
        self.run()

    def window_init(self):
        self.window.setObjectName("NotificationWindow")
        self.window.setSizePolicy(
            Widgets.QSizePolicy.Policy.Fixed, Widgets.QSizePolicy.Policy.Expanding
        )
        self.window.setGeometry(self.max_width - self.width, 0, self.width, self.height)
        self.window.setWindowFlags(
            self.window.windowFlags()
            | Core.Qt.WindowType.FramelessWindowHint
            | Core.Qt.WindowType.Tool
            | Core.Qt.WindowType.WindowStaysOnTopHint
            | Core.Qt.WindowType.WindowDoesNotAcceptFocus
            | Core.Qt.WindowType.WindowTransparentForInput
        )
        self.window.setAttribute(Core.Qt.WidgetAttribute.WA_TranslucentBackground)

    def resizeWindow(self, new_width: int, new_height: int):
        ##--log.info(
        #     f"调整了{LANG['Default Notification Window']}的大小:({self.width},{self.height}) -> ({new_width},{new_height})"
        # )
        self.width, self.height = new_width, new_height
        self.window.setGeometry(self.max_width - self.width, 0, self.width, self.height)

    def fadeIn(self):
        if self.showed:
            return
        self.showed = True
        ##--log.info(f"{LANG['Default Notification Window']}渐入")
        # self.window.setWindowOpacity(0)
        self.window.show()
        # win_animation.fadeIn(self.window,
        #     Mode.EASE_IN_OUT, self.default_animation_time
        # )

    def fadeOut(self):
        if not self.showed:
            return
        self.showed = False
        ##--log.info(f"{LANG['Default Notification Window']}渐出")
        # win_animation.fadeOut(self.window,
        #     Mode.EASE_IN_OUT, self.default_animation_time
        # )
        self.window.hide()

    def run(self):
        return #TODO
        while True:
            text, icon, noti_name, alive_time, animation_time = self.queue.get()
            ##--log.info(f"发送了新通知:{text}")
            # self.fadeIn()
            if alive_time is None:
                alive_time = self.default_show_time
            if animation_time is None:
                animation_time = self.default_animation_time
            label = Widgets.QLabel()
            label.setText(text)
            label.setWordWrap(True)
            label.setBaseSize(Core.QSize(self.width-2,100))
            label.setSizePolicy(Widgets.QSizePolicy.Policy.Expanding,Widgets.QSizePolicy.Policy.Preferred)
            if icon is not None:
                if type(icon) is bytes:
                    source_icon = Gui.QImage()
                    source_icon.loadFromData(icon)
                elif type(icon) is str:
                    source_icon = Gui.QImage(icon)
                new_size = Core.QSize(128,128)
                icon = Widgets.QLabel()
                icon.resize(new_size)
                icon.setPixmap(
                    Gui.QPixmap.fromImage(
                        source_icon.scaled(
                            new_size, Core.Qt.AspectRatioMode.KeepAspectRatio
                        )
                    )
                )
                opacity = Widgets.QGraphicsOpacityEffect()
                opacity.setOpacity(0.5)
                icon.setGraphicsEffect(opacity)
                sub_layout = Widgets.QHBoxLayout()
                frame = Widgets.QFrame()
                frame.setBaseSize(Core.QSize(400,300))
                frame.setObjectName("Notification")
                frame.setSizePolicy(
                    Widgets.QSizePolicy.Policy.Expanding,
                    Widgets.QSizePolicy.Policy.Maximum,
                )
                icon.setSizePolicy(
                    Widgets.QSizePolicy.Policy.Fixed, Widgets.QSizePolicy.Policy.Fixed
                )
                frame.setLayout(sub_layout)
                if noti_name is not None:
                    sub_layout.setObjectName(noti_name)
                sub_layout.addWidget(icon)
                sub_layout.addWidget(label)
                frame.setLayout(sub_layout)
                self.layout.addWidget(frame)
                frame.show()
                self.window.repaint()
                ##--log.info("通知渐入")
                # obj_animation.fadeIn(frame,Mode.LINEAR, animation_time)
                # sleep(alive_time - 2 * animation_time)
                # obj_animation.fadeOut(frame,Mode.LINEAR, animation_time)
                def delayFunc(self,frame,alive_time,animation_time):
                    sleep(alive_time-2*animation_time)
                    ##--log.info("通知渐出")
                    frame.hide()
                    self.layout.removeWidget(frame)
                    self.window.repaint()
                Thread(target=delayFunc,args=(self,frame,alive_time,animation_time),daemon=True).start()
            else:
                if noti_name is not None:
                    label.setObjectName(noti_name)
                def delayFunc(self,label,alive_time,animation_time):
                    ##--log.info("通知渐出")
                    sleep(alive_time - 2 * animation_time)
                    self.layout.addWidget(label)
                    label.show()
                    self.window.repaint()
                Thread(target=delayFunc,args=(self,label,alive_time,animation_time),daemon=True).start()
                # self.schedule.enter(2,0,delayFunc)
                # ObjectAnimation(label).fadeIn(Mode.LINEAR, animation_time)
                # ObjectAnimation(label).fadeOut(Mode.LINEAR, animation_time)
            self.queue.task_done()
            # if self.items_count == 0:
            #     self.fadeOut()


def append(
    queue: Queue,
    text: str,
    icon: bytes | Path | None = None,
    noti_name: str | None = None,
    alive_time: int | None = None,
    animation_time: int | None = None,
):
    return
    queue.put((text, icon, noti_name, alive_time, animation_time))
