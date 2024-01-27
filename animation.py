from typing import NewType
import PySide6.QtCore as Core
import PySide6.QtGui as Gui
import PySide6.QtWidgets as Widgets
from threading import Thread
from time import sleep


class Mode(Core.QEasingCurve):
    LINEAR = Core.QEasingCurve.Type.Linear
    EASE_IN_OUT = Core.QEasingCurve.Type.InOutExpo
    FAST_IN_OUT = Core.QEasingCurve.Type.InOutCubic


class WindowAnimation:
    def __init__(self) -> None:
        self.animations = list()

    # def slideDown(self, mode: Mode):  # TODO
    #     animation = Core.QPropertyAnimation(self.window, b"geometry")
    #     animation.setDuration(1000)
    #     animation.setEasingCurve(mode)
    #     ax, ay, x, y = self.window.geometry()
    #     position = Core.QRect(ax, ay, x, y)
    #     animation.setStartValue(position)
    #     new_position = Core.QRect(ax, ay + 200, x, y)
    #     animation.setEndValue(new_position)
    #     animation.start()

    # def slideUp(self, mode: Mode):  # TODO
    #     animation = Core.QPropertyAnimation(self.window, b"geometry")
    #     animation.setDuration(1000)
    #     animation.setEasingCurve(mode)
    #     animation.setStartValue(Core.QRect(self.window.geometry()))
    #     animation.setEndValue(
    #         Core.QRect(self.window.geometry() - Core.QRect(0, 200, 0, 0))
    #     )
    #     animation.start()

    def fadeIn(self, window: Widgets.QWidget, mode: Mode, animation_time, slice=20):
        while id(window) in self.animations:
            sleep(0.5)
        self.animations.append(id(window))
        for i in range(0, 100, 100 // slice):
            window.setWindowOpacity(i / 100)
            sleep(animation_time / slice)
        self.animations.remove(id(window))

    def fadeOut(self, window: Widgets.QWidget, mode: Mode, animation_time, slice=20):
        while id(window) in self.animations:
            sleep(0.5)
        self.animations.append(id(window))
        for i in range(100, 0, -100 // slice):
            window.setWindowOpacity(i / 100)
            sleep(animation_time / slice)
        window.setWindowOpacity(0)
        self.animations.remove(id(window))


class ObjectAnimation:
    def __init__(self) -> None:
        self.animations = list()

    def fadeOut(self,_object:Widgets.QAbstractButton, mode: Mode, animation_time, slice=20):
        while id(_object) in self.animations:
            sleep(0.5)
        self.animations.append(id(_object))
        opacity = Widgets.QGraphicsOpacityEffect()
        _object.setGraphicsEffect(opacity)
        for i in range(100, 0, -100 // slice):
            opacity.setOpacity(i / 100)
            sleep(animation_time / slice)
        opacity.setOpacity(0)
        self.animations.remove(id(_object))

    def fadeIn(self,_object, mode: Mode, animation_time, slice=20):
        while id(_object) in self.animations:
            sleep(0.5)
        self.animations.append(id(_object))
        opacity = Widgets.QGraphicsOpacityEffect()
        opacity.setOpacity(0)
        _object.setGraphicsEffect(opacity)
        for i in range(0, 100, 100 // slice):
            opacity.setOpacity(i / 100)
            sleep(animation_time / slice)
        self.animations.remove(id(_object))
