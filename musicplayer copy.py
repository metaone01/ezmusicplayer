import functools
from queue import Queue
from typing import Any, Callable
import PySide6.QtCore as Core
import PySide6.QtGui as Gui
import PySide6.QtWidgets as Widgets
import os
from threading import Thread,current_thread
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
from settings import HOTKEYS, LANG, SKIN, STYLE, SysInfo, qssReader
from notification import append

TITLE = "TIT2"
ARTIST = "TPE1"
ALBUM = "TALB"
TRACK = "TRCK"
LYRIC = "USLT::XXX"
COVER = "APIC:"


class Unknown:
    text: list[str] = [LANG["Unknown"]]
    data: str = LANG["Unknown"]


with open("./settings/musiclist.json", encoding="utf-8") as f:
    MUSIC_LIST: list = json.load(f)
MUSICS = dict()
for audio in MUSIC_LIST:
    info = File(audio)
    tags: dict = info.__dict__["tags"]
    title = tags.get(TITLE, Unknown).text[0]
    artist = tags.get(ARTIST, Unknown).text[0]
    MUSICS[f"{title} - {artist}"] = audio
del MUSIC_LIST
with open("./settings/musicplayer.json", encoding="utf-8") as f:
    _SETTINGS: dict = json.load(f)


def changeSetting(key: str, value: Any):
    global _SETTINGS
    _SETTINGS[key] = value
    with open("./settings/musicplayer.json", "w", encoding="utf-8") as f:
        json.dump(_SETTINGS, f, ensure_ascii=False, indent=4)


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

# win_animation = WindowAnimation()
# obj_animation = ObjectAnimation()


class LyricWindow:
    def __init__(
        self,
        sync_timer: "MusicSyncTimer",
        app: Widgets.QApplication,
        animation_time: float = 0.5,
    ):
        self.sync_timer = sync_timer
        self.app = app
        self.window = Widgets.QWidget()
        self.label = Widgets.QLabel(self.window)
        self.geometry = SysInfo.getDisplayGeometry()
        self.max_width, self.max_height = self.geometry
        self.width, self.height = self.max_width, 200
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
        log.info(f"歌词窗口初始化完毕")

    def changeStyle(self):
        self.window.setStyleSheet(qssReader(SKIN, "LyricWindow"))

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
        self.changeStyle()

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
                sleep(0.1)
            self.label.setText(self.lyric[0][1])
            if self.label_hide:
                self.labelFadeIn()
            while self.lrc_index < len(self.lyric) and self.showed and not self.refresh:
                if self.lyric[self.lrc_index][0] + 100 <= self.sync_timer.sync_timer:
                    self.label.setText(self.lyric[self.lrc_index][1])
                    self.lrc_index += 1
                sleep(0.2)
            else:
                # self.app.processEvents(Core.QEventLoop.ProcessEventsFlag.AllEvents,200)
                if not (self.label_hide or self.refresh):
                    self.labelFadeOut()
                self.lrc_index = 0
                while not self.refresh:
                    # self.app.processEvents(Core.QEventLoop.ProcessEventsFlag.AllEvents,200)
                    sleep(1)

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
        self.label.show()
        self.refresh = True
        # win_animation.fadeIn(self.window,Mode.EASE_IN_OUT, self.animation_time)
        # ObjectAnimation(self.label).fadeIn(Mode.LINEAR,self.animation_time)

    def close(self):
        log.info("关闭了歌词窗口")
        self.showed = False
        # ObjectAnimation(self.label).fadeOut(Mode.LINEAR,self.animation_time)
        # win_animation.fadeOut(self.window,Mode.EASE_IN_OUT, self.animation_time)
        self.window.hide()

    def destroy(self):
        log.info("销毁了歌词窗口")
        self.showed = False
        self.refresh = True
        self.window.destroy(True, True)
        return


class MusicSyncTimer:
    def __init__(self) -> None:
        self.sync_timer = 0
        self.volume_percent: float = _SETTINGS["volume"]
        self.minimum_volume: float = 0
        self.maximum_volume: float = 100
        log.info(
            f"设置音乐播放器音量初始值{self.volume_percent},最小值{self.minimum_volume},最大值{self.maximum_volume}"
        )
        self.paused = False
        self.stopped = False

    def play(self, music_path) -> None:
        p = PyAudio()
        music = AudioSegment.from_file(music_path)
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
        chunks = make_chunks(music, 200)
        chunk_count = 0
        while True:
            if chunk_count >= len(chunks):
                break
            chunk = chunks[chunk_count] + -40 * (1 - self.volume_percent / 100)
            self.sync_timer += 200
            if self.paused:
                stream.stop_stream()
                while self.paused:
                    sleep(0.2)
                    if self.stopped:
                        self.paused = False
                        self.stopped = False
                        break
                else:
                    stream.start_stream()
                    stream.write(chunk._data)
                    chunk_count += 1
                    continue
            else:
                stream.write(chunk._data)
                chunk_count += 1
                continue
            break
        self.sync_timer = 0
        stream.stop_stream()
        stream.close()
        p.terminate()

    def setVolume(self, volume: int):
        self.volume_percent = volume
        if volume == 0:
            self.pause()
        else:
            self.resume()

    def pause(self):
        self.paused = True
        log.info("暂停播放")

    def resume(self):
        self.paused = False
        log.info("继续播放")

    def stop(self):
        self.paused = True
        self.stopped = True


class MusicPlayer:
    def __init__(self, app: Widgets.QApplication, noti_queue: Queue) -> None:
        self.lyric_thread: Thread  # warning:only for hint
        self.app = app
        self.terminated = False
        self.noti_queue = noti_queue
        self.last_music = _SETTINGS["last_music"]
        self.hotkeys = HOTKEYS["MusicPlayer"]
        self.music_count = 0
        self.play = MusicSyncTimer()
        self.lyric = LyricWindow(self.play, self.app)
        self.init()
        self.getMusicList()
        self.hotkeyRegister()
        self.sub_thread = Thread(target=self.player, name="MusicPlayer", daemon=True)
        self.sub_thread.start()
        self.lyric.show()
        self.window.show()
        log.info("MusicPlayer初始化完成")

    @property
    def mode(self):
        return PlayMode().get()

    def init(self):
        self.window = Widgets.QWidget()
        self.icon = Widgets.QLabel()
        self.layout = Widgets.QHBoxLayout()
        self.label = Widgets.QLabel()
        self.prev_btn = Widgets.QPushButton()
        self.pause_btn = Widgets.QPushButton()
        self.next_btn = Widgets.QPushButton()
        self.volume_btn = Widgets.QPushButton()
        self.mode_btn = Widgets.QPushButton()
        self.list_btn = Widgets.QPushButton()
        self.cur_thread = hex(id(current_thread()))
        print(self.cur_thread)
        self.window.setObjectName("MusicPlayer")
        self.window.setStyle(STYLE)
        self.window.setWindowFlags(
            self.window.windowFlags()
            | Core.Qt.WindowType.FramelessWindowHint
            | Core.Qt.WindowType.Tool
            | Core.Qt.WindowType.WindowStaysOnTopHint
        )
        self.max_width, self.max_height = SysInfo.getDisplayGeometry()
        self.window.setStyleSheet(qssReader(SKIN, "MusicPlayer_Main"))
        self.window.setSizePolicy(
            Widgets.QSizePolicy.Policy.Fixed, Widgets.QSizePolicy.Policy.Fixed
        )
        self.window.setFixedSize(Core.QSize(256, 50))
        self.window.move(Core.QPoint(self.max_width // 2 - 128, 0))
        self.window.setLayout(self.layout)
        self.icon.setParent(self.window)
        self.icon.resize(50, 50)
        self.icon.move(0, 0)
        self.musicListInit()
        self.musicVolumeInit()
        self.setIcon()
        self.prev_btn.clicked.connect(self.prevMusic)
        self.pause_btn.clicked.connect(self.toggleMusic)
        self.next_btn.clicked.connect(self.nextMusic)
        self.list_btn.clicked.connect(self.toggleMusicList)
        self.mode_btn.clicked.connect(self.switchMode)
        self.volume_btn.clicked.connect(self.toggleVolumeSlider)
        self.layout.addSpacing(60)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.prev_btn)
        self.layout.addWidget(self.pause_btn)
        self.layout.addWidget(self.next_btn)
        self.layout.addWidget(self.volume_btn)
        self.layout.addWidget(self.mode_btn)
        self.layout.addWidget(self.list_btn)
        self.window.setWindowOpacity(0.9)

    def setIcon(self):
        self.prev_icon = Gui.QPixmap(f"./skin/{SKIN}/image/MusicPlayer/prev.png")
        self.pause_icon = Gui.QPixmap(f"./skin/{SKIN}/image/MusicPlayer/pause.png")
        self.resume_icon = Gui.QPixmap(f"./skin/{SKIN}/image/MusicPlayer/play.png")
        self.next_icon = Gui.QPixmap(f"./skin/{SKIN}/image/MusicPlayer/next.png")
        self.volume_icon = Gui.QPixmap(f"./skin/{SKIN}/image/MusicPlayer/volume.png")
        self.list_icon = Gui.QPixmap(f"./skin/{SKIN}/image/MusicPlayer/list.png")
        self.modes = {
            PlayMode.repeat: Gui.QPixmap(f"./skin/{SKIN}/image/MusicPlayer/repeat.png"),
            PlayMode.sequential: Gui.QPixmap(
                f"./skin/{SKIN}/image/MusicPlayer/sequential.png"
            ),
            PlayMode.loop: Gui.QPixmap(f"./skin/{SKIN}/image/MusicPlayer/loop.png"),
            PlayMode.random: Gui.QPixmap(f"./skin/{SKIN}/image/MusicPlayer/random.png"),
        }
        self.mode_order = [
            PlayMode.repeat,
            PlayMode.sequential,
            PlayMode.loop,
            PlayMode.random,
        ]
        self.prev_btn.setIcon(self.prev_icon)
        self.pause_btn.setIcon(self.pause_icon)
        self.next_btn.setIcon(self.next_icon)
        self.volume_btn.setIcon(self.volume_icon)
        self.mode_btn.setIcon(self.modes[self.mode])
        self.list_btn.setIcon(self.list_icon)

    def musicListInit(self):
        self.cur_thread = hex(id(current_thread()))
        print(self.cur_thread)
        self.list = Widgets.QListWidget()
        self.list.setParent(self.window)
        self.list.setObjectName("MusicPlayerList")
        self.list.setSizePolicy(
            Widgets.QSizePolicy.Policy.Fixed, Widgets.QSizePolicy.Policy.Fixed
        )
        self.list.setStyleSheet(qssReader(SKIN, "MusicPlayer_Musiclist"))
        self.list.setFixedSize(256, 600)
        self.list.setHorizontalScrollBarPolicy(
            Core.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.list.move(Core.QPoint(self.max_width // 2 - 128, 50))
        self.list.setWindowFlags(
            self.window.windowFlags()
            | Core.Qt.WindowType.FramelessWindowHint
            | Core.Qt.WindowType.Tool
            | Core.Qt.WindowType.WindowStaysOnTopHint
        )
        self.list.setWindowOpacity(0.9)

    def regenerateMusiclist(self):
        def _changeMusic(item: Widgets.QListWidgetItem):
            file = item.text()
            if file != self.cur_musiclist[self.music_count]:
                self.changeMusic(file)

        if self.list.isHidden():
            self.list.clear()
        else:
            self.list.hide()
            self.list.clear()
            self.list.show()
        for file in self.cur_musiclist:
            new = Widgets.QListWidgetItem(self.list)
            new.setText(file)
            self.list.addItem(new)

        self.list.itemClicked.connect(_changeMusic)
        self.list.item(self.music_count).setSelected(True)
        self.changeListFocusedItem()

    def musicVolumeInit(self):
        self.volume_slider = Widgets.QSlider(self.window)
        self.volume_slider.setObjectName("MusicPlayerVolume")
        self.volume_slider.setWindowFlags(
            self.window.windowFlags()
            | Core.Qt.WindowType.FramelessWindowHint
            | Core.Qt.WindowType.Tool
            | Core.Qt.WindowType.WindowStaysOnTopHint
        )
        self.volume_slider.setSizePolicy(
            Widgets.QSizePolicy.Policy.Fixed, Widgets.QSizePolicy.Policy.Fixed
        )
        self.volume_slider.setOrientation(Core.Qt.Orientation.Horizontal)
        self.volume_slider.setFixedSize(Core.QSize(100, 16))
        self.volume_slider.setStyleSheet(qssReader(SKIN, "MusicPlayer_Volume"))
        self.volume_slider.setTracking(True)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setSingleStep(1)
        self.volume_slider.setValue(int(self.play.volume_percent))
        self.volume_slider.move(Core.QPoint(self.max_width // 2, 50))
        self.volume_slider.valueChanged.connect(self.changeVolumePercent)
        self.volume_slider.setWindowOpacity(0.9)

    def musicListGenerator(self, num):
        self.list.hide()
        self.changeMusic(MUSICS[num])

    def getMusicList(self, file: str | None = None):
        mode = self.mode
        if not hasattr(self, "cur_musiclist"):
            self.cur_musiclist: list[str] = list()
        if file:
            self.last_music = file
            if file in self.cur_musiclist:
                self.music_count = self.cur_musiclist.index(file) - 1
                return
        else:
            self.music_count = -1
        if self.last_music == "":
            self.last_music = list(MUSICS.keys())[0]
        if mode == PlayMode.repeat:
            self.cur_musiclist = [self.last_music]
        elif mode == PlayMode.sequential:
            if file:
                self.cur_musiclist.insert(self.music_count + 1, self.last_music)
            else:
                self.cur_musiclist = list(MUSICS.keys())
                self.music_count = self.cur_musiclist.index(self.last_music)
        elif mode == PlayMode.loop:
            if file:
                self.cur_musiclist.insert(self.music_count + 1, self.last_music)
            else:
                self.cur_musiclist = list(MUSICS.keys())
                self.music_count = self.cur_musiclist.index(self.last_music)
        elif mode == PlayMode.random:
            cur_musiclist = list(MUSICS.keys())
            random.shuffle(cur_musiclist)
            self.cur_musiclist = cur_musiclist
            self.music_count = self.cur_musiclist.index(self.last_music)
        self.regenerateMusiclist()

    def toggleVolumeSlider(self):
        if self.volume_slider.isHidden():
            self.volume_slider.show()
            log.info("显示了音量调节滑块")
        else:
            self.volume_slider.hide()
            log.info("隐藏了音量调节滑块")

    def toggleMusicList(self):
        if self.list.isHidden():
            self.list.show()
            log.info("显示了播放列表")
        else:
            self.list.hide()
            log.info("隐藏了播放列表")

    def changeVolumePercent(self, volume: int):
        self.play.setVolume(volume)
        log.info(f"调整音量为{volume}%")
        changeSetting("volume", volume)

    def changeMusic(self, file):
        self.getMusicList(file)
        log.info(f"播放了{file}")
        self.nextMusic()

    def changeTheme(self):
        global SKIN
        from settings import SKIN

        self.window.setStyleSheet(qssReader(SKIN, "MusicPlayer_Main"))
        self.list.setStyleSheet(qssReader(SKIN, "MusicPlayer_Musiclist"))
        self.volume_slider.setStyleSheet(qssReader(SKIN, "MusicPlayer_Volume"))
        self.setIcon()
        self.lyric.changeStyle()
        self.window.update()
        self.lyric.window.update()
        log.info("改变了主题颜色")

    def player(self) -> None:
        while not self.terminated:
            self.changeListFocusedItem()
            self.lyric.refresh = True
            music_path = MUSICS[self.cur_musiclist[self.music_count]]
            self.audio_analyzer_thread = Thread(
                target=self.audioAnalyze,
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
            self.last_music = self.cur_musiclist[self.music_count]
            changeSetting("last_music", self.last_music)
            self.audio_analyzer_thread.join(0)
            self.play_thread.join()
            self.music_count += 1
            if self.music_count > len(self.cur_musiclist) - 1:
                self.getMusicList()
                self.music_count = 0
                self.changeListFocusedItem()
            while len(self.cur_musiclist) == 0:
                self.getMusicList()
                sleep(1)

    def exec(self):
        while not self.terminated:
            sleep(1)
            self.app.processEvents()

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

    def audioAnalyze(self, audio: str):
        class Unknown:
            text: list[str] = [LANG["Unknown"]]
            data: str = LANG["Unknown"]

        def tryLrcFile(file: str):
            class Lrc:
                text = LANG["Unknown"]

            lrc, _ = os.path.splitext(file)
            try:
                with open(f"{lrc}.lrc", encoding="utf-8") as f:
                    Lrc.text = f.read()
            except:
                Lrc.text = LANG["Unknown"]
            return Lrc

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
        lyric = tags.get(LYRIC, tryLrcFile(audio)).text
        log.info(f"获取到歌词")
        self.lyric_text = (
            f"[0:-1]{self.title} - {self.artist}\n[0:-1]{self.album}\n" + lyric
        )
        self.lyric.setLyric(self.lyric_text)
        icon = Gui.QImage()
        if self.cover_data != LANG["Unknown"]:
            icon.loadFromData(self.cover_data)
            self.icon.setPixmap(
                Gui.QPixmap.fromImage(
                    icon.scaled(
                        Core.QSize(64, 64),
                        Core.Qt.AspectRatioMode.KeepAspectRatio,
                        Core.Qt.TransformationMode.SmoothTransformation,
                    )
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
        if self.music_count < -1:
            self.music_count = -1
        self.play.stop()
        log.info("切换到上一首歌曲")

    def nextMusic(self):
        self.play.stop()
        log.info("切换到下一首歌曲")

    def switchMode(self):
        index = self.mode_order.index(self.mode) + 1
        if index >= len(self.mode_order):
            index -= len(self.mode_order)
        new_mode = self.mode_order[index]
        changeSetting("mode", new_mode)
        self.mode_btn.setIcon(self.modes[new_mode])
        self.getMusicList()
        log.info(f"修改播放模式为:{new_mode}")

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

    def changeListFocusedItem(self):
        item = self.list.item(self.music_count)
        item.setSelected(True)
        if self.list.isHidden():
            self.list.scrollToItem(
                item, Widgets.QAbstractItemView.ScrollHint.PositionAtCenter
            )

    def addVolume(self, level: float = 5):
        if self.play.volume_percent >= self.play.maximum_volume:
            return
        if self.play.volume_percent == 0:
            self.play.resume()
        self.play.volume_percent += level
        self.volume_slider.setValue(int(self.play.volume_percent))

    def reduceVolume(self, level: float = 5):
        if self.play.volume_percent <= self.play.minimum_volume:
            if self.play.paused:
                return
            self.play.pause()
        self.play.volume_percent -= level
        self.volume_slider.setValue(int(self.play.volume_percent))

    def hotkeyRegister(self):
        def register(hotkey, func, args=None):
            keyboard.add_hotkey(hotkey, func, args)
            log.info(f"注册了快捷键{hotkey} -> {func.__name__}")

        register(self.hotkeys["volume_up"], self.addVolume)
        register(self.hotkeys["volume_down"], self.reduceVolume)
        register(self.hotkeys["prev"], self.prevMusic)
        register(self.hotkeys["next"], self.nextMusic)
        register(self.hotkeys["pause"], self.toggleMusic)
        register(self.hotkeys["toggle_lyric"], self.recreateLyricThread, args=(True,))
        register(self.hotkeys["toggle_musicplayer"], self.toggleMainWindow)

    def source_release(self):
        log.info("释放资源...")
        self.play.stop()
        self.terminated = True
        self.lyric.destroy()
        self.window.destroy(True, True)
        log.info("资源释放完毕")
