import functools
from queue import Queue
from typing import Any, Callable
import PySide6.QtCore as Core
import PySide6.QtGui as Gui
import PySide6.QtWidgets as Widgets
import os
from threading import Thread
from time import sleep
import json
import keyboard
from pyaudio import PyAudio
from pydub import AudioSegment  # type:ignore
from pydub.playback import make_chunks  # type:ignore
from mutagen import File
import random

# from animation import WindowAnimation, Mode,ObjectAnimation
import pylogger.pylogger as log
from settings import HOTKEYS, LANG, SKIN, SysInfo, qssReader
from notification import append

TITLE = "TIT2"
ARTIST = "TPE1"
ALBUM = "TALB"
TRACK = "TRCK"
LYRIC = "USLT::XXX"
COVER = "APIC:"
with open("./settings/musiclist.json", encoding="utf-8") as f:
    MUSIC_LIST: list = json.load(f)

with open("./settings/musicplayer.json", encoding="utf-8") as f:
    _SETTINGS: dict = json.load(f)

def changeSetting(key: str, value: Any):
    global _SETTINGS
    _SETTINGS[key] = value
    with open("./settings/musicplayer.json", "w", encoding="utf-8") as f:
        json.dump(_SETTINGS, f)


class PlayMode:
    repeat = "repeat"
    sequential = "sequential"
    loop = "loop"
    random = "random"

    def get(self):
        mode = _SETTINGS["mode"]
        if hasattr(self, mode):
            return self.__getattribute__(mode)
        else:
            log.fatal("意外的播放模式,请检查设置<MusicPlayer_PlayMode>是否正确配置")
            os.abort()


class Unknown:
    text: list[str] = [LANG["Unknown"]]
    data: str = LANG["Unknown"]


MUSICS = dict()
for audio in MUSIC_LIST:
    info = File(audio)
    tags: dict = info.__dict__["tags"]
    title = tags.get(TITLE, Unknown).text[0]
    artist = tags.get(ARTIST, Unknown).text[0]
    MUSICS[audio] = f"{title} - {artist}"
# win_animation = WindowAnimation()
# obj_animation = ObjectAnimation()


class LyricWindow:
    def __init__(
        self,
        sync_timer: "MusicSyncTimer",
        skin: str,
        animation_time: float = 0.5,
        *,
        name: str = "",
    ):
        self.sync_timer = sync_timer
        self.window = Widgets.QWidget()
        self.label = Widgets.QLabel(self.window)
        self.geometry = SysInfo.getDisplayGeometry()
        self.max_width, self.max_height = self.geometry
        self.width, self.height = self.max_width, 200
        self.name = name
        self.STYLESHEET = qssReader(skin, "LyricWindow")
        self.lyric: list[tuple[int, str]] = [(0, LANG["NO LYRIC"])]
        self.lrc_index = 0
        self.showed = False
        self.lyric_ready = False
        self.animation_time = animation_time
        self.refresh = False
        self.label_hide = False
        self.__sub_init()

    def __sub_init(self):
        log.info(f"正在初始化歌词窗口...")
        self.window_init()
        self.label_init()
        self.window.setStyleSheet(self.STYLESHEET)
        log.info(f"歌词窗口初始化完毕")

    def window_init(self):
        self.window.setObjectName("LyricWindow")
        self.window.setSizePolicy(
            Widgets.QSizePolicy.Policy.Expanding, Widgets.QSizePolicy.Policy.Expanding
        )
        self.window.setGeometry(
            0, self.max_height - self.height, self.width, self.height
        )
        self.window.setWindowFlags(
            self.window.windowFlags()
            | Core.Qt.WindowType.FramelessWindowHint
            | Core.Qt.WindowType.Tool
            | Core.Qt.WindowType.WindowStaysOnTopHint
            | Core.Qt.WindowType.WindowDoesNotAcceptFocus
            | Core.Qt.WindowType.WindowTransparentForInput
        )
        self.window.setAttribute(Core.Qt.WidgetAttribute.WA_TranslucentBackground)

    def label_init(self):
        self.label.setObjectName("LyricWindow-Label")
        self.label.setGeometry(Core.QRect(0, 0, self.max_width, 150))
        self.label.setSizePolicy(
            Widgets.QSizePolicy.Policy.Fixed, Widgets.QSizePolicy.Policy.Fixed
        )
        self.label.setWordWrap(False)
        self.label.setAlignment(Core.Qt.AlignmentFlag.AlignCenter)
        self.label.setText(self.lyric[0][1])
        self.label.move(0, 0)

    def __timeConverter(self, time: str) -> int:
        minute, second = (float(x) for x in time.split(":"))
        return int((minute * 60 + second) * 1000)

    def __lyricAnalyzer(self, lyric: str, save_to: dict):
        count = lyric.count("[")
        if count == 0:
            return
        _lyric = [y.split("]") for x in lyric.split("][") for y in x.split("[")][1]
        lyric_text = _lyric[-1]
        for i in range(count):
            try:
                ms = self.__timeConverter(_lyric[i])
            except:
                continue
            save_to[ms] = save_to.get(ms, "") + "\n" + lyric_text

    def setLyric(self, lyric: str):
        self.label.setText(LANG["LOADING LYRIC..."])
        lyric_dict: dict[int, str] = dict()
        [self.__lyricAnalyzer(_lyric, lyric_dict) for _lyric in lyric.splitlines()]
        self.lyric = [(k, v[1:]) for k, v in lyric_dict.items()]
        self.lyric.sort(key=lambda x: x[0])  # type:ignore[call-overload]
        if len(self.lyric) == 0:
            self.lyric.append((0, LANG["NO LYRIC"]))
        if self.lyric[-1][0] == 99 * 60 * 1000 and len(self.lyric) > 1:
            self.lyric[-1] = (self.lyric[-2][0] + 2000, self.lyric[-1][1])
        log.info(f"设定了新的歌词")
        self.lyric_ready = True

    def _syncLyric(self):
        while self.showed:
            self.refresh = False
            if not self.showed:
                return
            while not self.lyric_ready:
                sleep(0.5)
            self.label.setText(self.lyric[0][1])
            if self.label_hide:
                self.labelFadeIn()
            while self.lrc_index < len(self.lyric) and self.showed and not self.refresh:
                if self.lyric[self.lrc_index][0] + 300 <= self.sync_timer.sync_timer:
                    self.label.setText(self.lyric[self.lrc_index][1])
                    self.lrc_index += 1
                sleep(0.5)
            else:
                sleep(2)
                if not (self.label_hide or self.refresh):
                    self.labelFadeOut()
                while not self.refresh:
                    sleep(0.5)
                self.lrc_index = 0

    def labelFadeIn(self):
        log.info(f"歌词渐入")
        self.label_hide = False
        # while self.label_lock:
        #     sleep(0.5)
        # self.label_lock = True
        # obj_animation.fadeIn(self.label,Mode.LINEAR, self.animation_time)
        # self.label_lock = False
        self.label.show()

    def labelFadeOut(self):
        log.info(f"歌词渐出")
        self.label_hide = True
        # while self.label_lock:
        #     sleep(0.5)
        # self.label_lock = True
        # obj_animation.fadeOut(self.label,Mode.LINEAR, self.animation_time)
        # self.label_lock = False
        self.label.hide()

    def resizeWindow(self, new_width: int, new_height: int):
        log.info(
            f"调整了歌词窗口的大小:({self.width},{self.height}) -> ({new_width},{new_height})"
        )
        self.width, self.height = new_width, new_height

    def moveWindow(self, ax: int, ay: int):
        log.info(f"移动歌词窗口到({ax},{ay})")
        self.window.move(ax, ay)

    def changeLyric(self, lyric: str):
        log.info(f"修改歌词为{lyric}")
        self.label.setText(lyric)

    def toggle(self):
        self.close() if self.showed else self.show()

    def show(self):
        log.info("打开了歌词窗口")
        self.showed = True
        # self.window.setWindowOpacity(0)
        self.window.show()
        # win_animation.fadeIn(self.window,Mode.EASE_IN_OUT, self.animation_time)
        # ObjectAnimation(self.label).fadeIn(Mode.LINEAR,self.animation_time)

    def close(self):
        log.info("关闭了歌词窗口")
        self.showed = False
        # ObjectAnimation(self.label).fadeOut(Mode.LINEAR,self.animation_time)
        # win_animation.fadeOut(self.window,Mode.EASE_IN_OUT, self.animation_time)
        self.window.close()

    def destroy(self):
        log.info("销毁了歌词窗口")
        self.showed = False
        self.window.close()
        self.window.destroy()
        return


class MusicSyncTimer:
    def __init__(self) -> None:
        self.sync_timer = 0
        self.volume = 0
        self.paused = False
        self.stopped = False

    def play(self, music_path) -> None:
        p = PyAudio()
        try:
            music = AudioSegment.from_file(music_path)
        except:
            log.fatal("未安装ffmpeg,无法解析音频文件")
            os.abort()
        self.dBFS = int(music.dBFS)
        log.info(f"获取到音频dBFS数值:{self.dBFS}dBFS")
        self.framerate = music.frame_rate
        log.info(f"获取到音频采样率 {self.framerate}Hz")
        stream = p.open(
            format=p.get_format_from_width(music.sample_width),
            channels=music.channels,
            rate=music.frame_rate,
            output=True,
        )
        for chunk in make_chunks(music, 500):
            self.sync_timer += 500
            chunk = chunk + self.volume
            if self.paused:
                stream.stop_stream()
                while self.paused:
                    sleep(0.5)
                    if self.stopped:
                        self.paused = False
                        self.stopped = False
                        break
                else:
                    stream.start_stream()
                    stream.write(chunk._data)
                    continue
            else:
                stream.write(chunk._data)
                continue
            break
        self.sync_timer = 0
        stream.stop_stream()
        stream.close()
        p.terminate()

    def pause(self):
        self.paused = True
        log.info("暂停播放")

    def resume(self):
        self.paused = False
        log.info("继续播放")

    def stop(self):
        self.paused = True
        self.stopped = True

    def addVolume(self, level: int = 5):
        if self.volume >= 0:
            return
        self.volume += level
        log.info(f"已升高5dBFS,目前:{self.dBFS+self.volume}dBFS")

    def reduceVolume(self, level: int = 5):
        if self.volume <= -50:
            if self.paused:
                return
            self.pause()
        self.volume -= level
        log.info(f"已降低5dBFS,目前:{self.dBFS+self.volume}dBFS")


class MusicPlayer:

    def __init__(self, noti_queue: Queue) -> None:
        self.modes = [
            (PlayMode.repeat,Gui.QPixmap(f'./skins/{SKIN}/image/MusicPlayer/repeat.png')),
            (PlayMode.sequential,Gui.QPixmap(f'./skins/{SKIN}/image/MusicPlayer/sequential.png')),
            (PlayMode.loop,Gui.QPixmap(f'./skins/{SKIN}/image/MusicPlayer/loop.png')),
            (PlayMode.random,Gui.QPixmap(f'./skins/{SKIN}/image/MusicPlayer/random.png'))
        ]
        self.lyric_thread: Thread  # warning:only for hint
        self.init()
        self.terminated = False
        self.last_music = _SETTINGS["last_music"]
        self.hotkeys = HOTKEYS["MusicPlayer"]
        self.getMusicList()
        self.music_count = 0
        self.noti_queue = noti_queue
        self.window.show()
        self.play = MusicSyncTimer()
        self.lyric = LyricWindow(self.play, SKIN)
        self.lyric.show()
        self.sub_thread = Thread(target=self.run, name="MusicPlayer")
        self.sub_thread.start()
        self.hotkeyRegister()

    @property
    def mode(self):
        return PlayMode().get()

    def init(self):
        self.window = Widgets.QWidget()
        self.icon = Widgets.QLabel()
        self.layout = Widgets.QHBoxLayout()
        self.label = Widgets.QLabel()
        self.prev_btn = Widgets.QPushButton()
        self.prev_icon = Gui.QPixmap(f"./skin/{SKIN}/image/MusicPlayer/prev.png")
        self.pause_btn = Widgets.QPushButton()
        self.pause_icon = Gui.QPixmap(f"./skin/{SKIN}/image/MusicPlayer/pause.png")
        self.resume_icon = Gui.QPixmap(f"./skin/{SKIN}/image/MusicPlayer/play.png")
        self.next_btn = Widgets.QPushButton()
        self.next_icon = Gui.QPixmap(f"./skin/{SKIN}/image/MusicPlayer/next.png")
        self.volume = Widgets.QWidget()
        self.volume_btn = Widgets.QPushButton()
        self.volume_icon = Gui.QPixmap(f"./skin/{SKIN}/image/MusicPlayer/volume.png")
        self.mode_btn = Widgets.QPushButton()
        self.mode_icon = Gui.QPixmap(f"./skin/{SKIN}/image/MusicPlayer/{self.mode}.png")
        self.list_btn = Widgets.QPushButton()
        self.list_icon = Gui.QPixmap(f"./skin/{SKIN}/image/MusicPlayer/list.png")
        self.list = Widgets.QWidget()
        self.list_layout = Widgets.QVBoxLayout()
        self.max_width, self.max_height = SysInfo.getDisplayGeometry()
        self.window.setGeometry(Core.QRect(self.max_width // 2 - 128, 0, 128, 50))
        self.volume.setGeometry(Core.QRect(self.max_width // 2 - 34, 0, 30, 20))
        self.list.setGeometry(Core.QRect(self.max_width // 2, 0, 50, 100))#BUG
        self.prev_btn.clicked.connect(self.prevMusic)
        self.pause_btn.clicked.connect(self.toggleMusic)
        self.next_btn.clicked.connect(self.nextMusic)
        self.list_btn.clicked.connect(self.toggleMusicList)
        self.mode_btn.clicked.connect(self.switchMode)
        self.prev_btn.setIcon(self.prev_icon)
        self.pause_btn.setIcon(self.pause_icon)
        self.next_btn.setIcon(self.next_icon)
        self.volume_btn.setIcon(self.volume_icon)
        self.mode_btn.setIcon(self.mode_icon)#BUG
        self.list_btn.setIcon(self.list_icon)
        self.window.setStyleSheet(f"./skin/{SKIN}/MusicPlayer_Main.qss")#TODO
        self.window.setWindowFlags(
            self.window.windowFlags()
            | Core.Qt.WindowType.FramelessWindowHint
            | Core.Qt.WindowType.Tool
            | Core.Qt.WindowType.WindowStaysOnTopHint
        )
        self.window.setLayout(self.layout)
        self.layout.addWidget(self.icon)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.prev_btn)
        self.layout.addWidget(self.pause_btn)
        self.layout.addWidget(self.next_btn)
        self.layout.addWidget(self.volume_btn)
        self.layout.addWidget(self.mode_btn)
        self.layout.addWidget(self.list_btn)
        self.volume.setStyleSheet(f"./skin/{SKIN}/MusicPlayer_Volume.qss")
        self.list.setStyleSheet(f"./skin/{SKIN}/MusicPlayer_Musiclist.qss")
        self.list.setWindowFlags(
            self.window.windowFlags()
            | Core.Qt.WindowType.FramelessWindowHint
            | Core.Qt.WindowType.Tool
            | Core.Qt.WindowType.WindowStaysOnTopHint
        )
        self.list.setLayout(self.list_layout)
        for file, name in MUSICS.items():
            new = Widgets.QPushButton()
            new.setObjectName("MusicListButton")
            new.setText(name)
            new.clicked.connect(lambda: self.playMusic(file))#BUG
            self.list_layout.addWidget(new)

    def getMusicList(self, file: str | None = None):
        mode = self.mode
        if file:
            self.last_music = file
        else:
            self.music_count = 0
        if self.last_music == '':
            self.last_music = MUSIC_LIST[0]
        if mode == PlayMode.repeat:
            self.cur_musiclist = [self.last_music]
        elif mode == PlayMode.sequential:
            if file:
                self.cur_musiclist = list()
            else:
                self.cur_musiclist.insert(self.music_count + 1, self.last_music)
        elif mode == PlayMode.loop:
            if file:
                self.cur_musiclist = list()
            else:
                self.cur_musiclist.insert(self.music_count + 1, self.last_music)
        elif mode == PlayMode.random:
            cur_musiclist = MUSIC_LIST
            random.shuffle(cur_musiclist)
            self.cur_musiclist = cur_musiclist

    def toggleMusicList(self):
        if self.list.isHidden():
            self.list.show()
            log.info("显示了播放列表")
        else:
            self.list.hide()
            log.info("隐藏了播放列表")

    def playMusic(self, file):
        self.getMusicList(file)
        self.nextMusic()

    def run(self) -> None:
        while not self.terminated:
            self.lyric.refresh = True
            music_path = self.cur_musiclist[self.music_count]
            self.audio_analyzer_thread = Thread(
                target=self.AudioAnalyzer,
                name="_MusicNotificationWindow",
                args=(music_path,),
                daemon=True,
            )
            self.play_thread = Thread(
                target=self.play.play,
                name="_PlayMusic",
                args=(music_path,),
                daemon=True,
            )
            self.recreateLyricThread()
            self.audio_analyzer_thread.start()
            self.play_thread.start()
            self.audio_analyzer_thread.join(0)
            self.play_thread.join()
            self.music_count += 1
            if self.music_count > len(self.cur_musiclist) - 1:
                self.getMusicList()
            while len(self.cur_musiclist) == 0:
                self.getMusicList()
                sleep(1)

    def recreateLyricThread(self, toggle: bool = False):
        if self.lyric.showed:
            if toggle:
                self.lyric.close()
                return
        else:
            self.lyric.show()
        if hasattr(self, "lyric_thread") and self.lyric_thread.is_alive():
            return
        self.lyric_thread = Thread(
            target=self.lyric._syncLyric, name="_LyricWindow", daemon=True
        )
        self.lyric_thread.start()
        self.lyric_thread.join(0)

    def AudioAnalyzer(self, audio: str):
        class Unknown:
            text: list[str] = [LANG["Unknown"]]
            data: str = LANG["Unknown"]

        class UnknownLyric:
            text: str = LANG["Unknown"]

        log.info(f"正在读取{audio}")
        info = File(audio)
        tags: dict = info.__dict__["tags"]
        self.length = info.info.length
        log.info(f"获取到时长: {self.length}s")
        self.bitrate = info.info.bitrate // 1000
        log.info(f"获取到比特率: {self.bitrate}Kbps")
        self.title = tags.get(TITLE, Unknown).text[0]
        log.info(f"获取到标题: {self.title}")
        self.artist = tags.get(ARTIST, Unknown).text[0]
        log.info(f"获取到艺术家: {self.artist}")
        self.album = tags.get(ALBUM, Unknown).text[0]
        log.info(f"获取到专辑: {self.album}")
        self.track = tags.get(TRACK, Unknown).text[0]
        log.info(f"获取到音轨数: {self.track}")
        self.cover_data = tags.get(COVER, Unknown).data
        log.info(f"获取到封面")
        lyric = tags.get(LYRIC, UnknownLyric).text
        log.info(f"获取到歌词")
        self.lyric_text = (
            f"[0:-1]{self.title} - {self.artist}\n[0:-1]{self.album}\n" + lyric
        )
        self.lyric.setLyric(self.lyric_text)
        icon = Gui.QImage()
        icon.loadFromData(self.cover_data)
        self.icon.setPixmap(
            Gui.QPixmap.fromImage(
                icon.scaled(Core.QSize(64, 64), Core.Qt.AspectRatioMode.KeepAspectRatio)
            )
        )
        append(
            self.noti_queue,
            f"{LANG['Now Playing']}:{self.title}\n{LANG['Artist']}:{self.artist}\n{LANG['Album']}:{self.album}",
            self.cover_data,
            "MusicInfoNotification",
        )

    def prevMusic(self):
        self.music_count -= 2
        self.play.stop()
        log.info("切换到上一首歌曲")

    def nextMusic(self):
        self.play.stop()
        log.info("切换到下一首歌曲")

    def switchMode(self):
        new_mode:int|None = None
        for _index,i in enumerate(self.modes):
            if i[0] == self.mode:
                new_mode=_index+1
                break
        if new_mode >= len(self.modes):
            new_mode = 0
        changeSetting("mode", self.modes[new_mode][0])
        self.mode_btn.setIcon(self.modes[new_mode][1])
        self.getMusicList()
        log.info(f"修改播放模式为:{self.mode}")

    def toggleMusic(self):
        if self.play.paused:
            self.play.resume()
            self.pause_btn.setIcon(self.pause_icon)
        else:
            self.play.pause()
            self.pause_btn.setIcon(self.resume_icon)

    def toggleMainWindow(self):
        if self.window.isHidden():
            self.window.show()
        else:
            self.window.hide()

    def hotkeyRegister(self):
        @functools.wraps(self.hotkeyRegister)
        def register(hotkey, func, args=None):
            keyboard.add_hotkey(hotkey, func, args)
            log.info(f"注册了快捷键{hotkey} -> {func}")

        register(self.hotkeys["volume_up"], self.play.addVolume)
        register(self.hotkeys["volume_down"], self.play.reduceVolume)
        register(self.hotkeys["prev"], self.prevMusic)
        register(self.hotkeys["next"], self.nextMusic)
        register(self.hotkeys["pause"], self.toggleMusic)
        register(self.hotkeys["toggle_lyric"], self.recreateLyricThread, args=(True,))
        register(self.hotkeys["toggle_musicplayer"], self.toggleMainWindow)

    def source_release(self):
        log.info("释放了所有资源")
        self.terminated = True
        self.nextMusic()
        self.lyric.destroy()
        del self.lyric


log.info("MusicPlayer初始化完成")
