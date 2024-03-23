import json
from queue import Queue
import PySide6.QtCore as Core
import PySide6.QtGui as Gui
import PySide6.QtWidgets as Widgets
import time

from settings import SKIN, STYLE, qssReader,SysInfo


        

class Time:
    def __init__(self,app:Widgets.QApplication,noti_queue:Queue) -> None:
        self.app = app
        self.noti_queue = noti_queue
        self.clockInit()
        self.todoInit()

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
        self.window.setAttribute(Core.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.window.setSizePolicy(
            Widgets.QSizePolicy.Policy.Fixed, Widgets.QSizePolicy.Policy.Fixed
        )
        self.window.setFixedSize(Core.QSize(200, 100))
        self.window.setStyle(STYLE)
        self.window.move(0, 0)
        self.time = Widgets.QLabel(self.window)
        self.window.setStyleSheet(qssReader(SKIN, "Clock"))
        self.time.setFixedSize(Core.QSize(256,100))
        self.time.move(0,0)

    def changeTheme(self):
        global SKIN
        from settings import SKIN
        self.window.setStyleSheet(qssReader(SKIN,"Clock"))
        # self.todo_window.setStyleSheet(qssReader("SKIN","TODO")) #TODO

    def todoInit(self):
        return #TODO
        self.todo_window = Widgets.QListWidget(self.window)
        self.todo_window.setWindowFlags(
            self.window.windowFlags()
            | Core.Qt.WindowType.FramelessWindowHint
            | Core.Qt.WindowType.Tool
            | Core.Qt.WindowType.WindowStaysOnBottomHint
        )
        self.todo_window.setAttribute(Core.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.todo_window.move(Core.QPoint(0,100))
        self.todo_label = Widgets.QLabel(self.todo_window)
        self.todo_label.setSizePolicy(Widgets.QSizePolicy.Policy.Fixed,Widgets.QSizePolicy.Policy.Fixed)
        self.todo_label.setFixedSize(Core.QSize(172,28))
        self.todo_label.setText("Todo")
        self.todo_label.setObjectName("TodoLabel")
        self.todo_label.move(0,0)
        self.todo_add_btn = Widgets.QPushButton(self.todo_window)
        self.todo_add_btn.setFixedSize(Core.QSize(28,28))
        self.todo_add_btn.move(172,0)
        self.todo_add_btn.clicked.connect(self.addTodo)
        self.todo_window.setStyleSheet(qssReader(SKIN, "Todo"))
        self.todo_window.setFixedSize(200,SysInfo.getDisplayGeometry()[1])
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
        self.todo_window.show()

    def addTodo(self):
            self.add_todo_window = Widgets.QWidget()
            

    def exec(self):
        self.window.show()
        while True:
            
            self.time.setText(time.strftime("%Y-%m-%d\n%a%H:%M:%S"))
            self.time.repaint()
            # item = self.todo_window.item(0) #TODO
            # if item:
            #     task_time = time.mktime(time.strptime(item.text()[:20]))
            #     if task_time < time.time():
            #         self.todo_window.removeItemWidget(self.todo_window.item(0))
            time.sleep(1)       
            # self.app.processEvents(Core.QEventLoop.ProcessEventsFlag.EventLoopExec,1000)      

    def source_release(self):
        self.window.destroy(True,True)
        # self.todo_window.destroy(True,True)
    
    def updateTodoList(self):
        with open("./settings/todo.json",'w',encoding='utf-8') as f:
            json.dump(self.todo,f,ensure_ascii=False,indent=4)