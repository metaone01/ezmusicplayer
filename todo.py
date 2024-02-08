import json
import PySide6.QtCore as Core
import PySide6.QtGui as Gui
import PySide6.QtWidgets as Widgets
import time

from settings import SKIN, STYLE, qssReader


        

class Time:
    def __init__(self) -> None:
        self.clockInit()
        self.todoInit()
        self.run()

    def clockInit(self):
        self.window = Widgets.QWidget()
        self.window.setWindowFlags(
            self.window.windowFlags()
            | Core.Qt.WindowType.FramelessWindowHint
            | Core.Qt.WindowType.Tool
            | Core.Qt.WindowType.WindowStaysOnTopHint
            | Core.Qt.WindowType.WindowDoesNotAcceptFocus
            | Core.Qt.WindowType.WindowTransparentForInput
        )
        self.window.setSizePolicy(
            Widgets.QSizePolicy.Policy.Fixed, Widgets.QSizePolicy.Policy.Fixed
        )
        self.window.setFixedSize(Core.QSize(128, 100))
        self.window.setStyle(STYLE)
        self.window.move(0, 0)
        self.time = Widgets.QLabel(self.window)
        self.time.setLayout(qssReader(SKIN, "Clock"))

    def todoInit(self):
        self.todo_window = Widgets.QListWidget()
        self.todo_window.setWindowFlags(
            self.window.windowFlags()
            | Core.Qt.WindowType.FramelessWindowHint
            | Core.Qt.WindowType.Tool
            | Core.Qt.WindowType.WindowStaysOnBottomHint
        )
        self.todo_label = Widgets.QLabel(self.todo_window)
        self.todo_label.setSizePolicy(Widgets.QSizePolicy.Policy.Fixed,Widgets.QSizePolicy.Policy.Fixed)
        self.todo_label.setFixedSize(Core.QSize(100))
        self.todo_add_btn = Widgets.QPushButton(self.todo_window)
        self.todo_window.setLayout(qssReader(SKIN, "Todo"))
        with open("./settings/todo.json",encoding='utf-8') as f:
            self.todo: dict[str,list[tuple]] = json.load(f)
            times = list(self.todo.keys())
            times.sort()
        for time in times:
            if time == "none":
                continue
            for task in self.todo[time]:
                new = Widgets.QListWidgetItem()
                new.setText(task[2])
                self.todo_window.addItem(new)
            if "none" in self.todo:
                for task in self.todo["none"]:
                    new = Widgets.QListWidgetItem()
                    new.setText(task[2])
                    self.todo_window.addItem(new)

    def run(self):
        while True:
            self.time.setText(time.strftime("%Y-%m-%d\n%H:%M:%S"))
            task_time = time.mktime(time.strptime(self.todo_window.item(0).text()[:20]))
            if task_time < time.time():
                self.todo

    def updateTodoList(self):
        with open("./settings/todo.json",'w',encoding='utf-8') as f:
            json.dump(self.todo,f,ensure_ascii=False,indent=4)