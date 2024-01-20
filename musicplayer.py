import functools
from queue import Queue
from typing import Callable
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
from settings import LANG, SysInfo, qssReader
from notification import append

TITLE = "TIT2"
ARTIST = "TPE1"
ALBUM = "TALB"
TRACK = "TRCK"
LYRIC = "USLT::XXX"
COVER = "APIC:"
with open("./settings/musiclist.json", encoding="utf-8") as f:
    MUSIC_LIST = json.load(f)


music_random = True
if music_random is True:
    random.shuffle(MUSIC_LIST)

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
    @property
    def styleSheetDict(self):
        return {
            k: v
            for style_sheet in self.label.styleSheet().split(";")
            for k, v in style_sheet.split(":")
        }

    def changeStyleSheet(self, style_sheet: dict):
        self.label.setStyleSheet(
            ";".join([k + ":" + v for k, v in style_sheet.items()])
        )

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
    def __init__(self, skin: str, noti_queue: Queue) -> None:
        self.lyric_thread: Thread
        self.i = 0
        self.skin = skin
        self.noti_queue = noti_queue
        self.window = Widgets.QWidget()  # TODO
        self.icon = Gui.QImage()  # TODO
        self.layout = Widgets.QHBoxLayout()  # TODO
        self.label = Widgets.QLabel()  # TODO
        self.prev_btn = Widgets.QPushButton()  # TODO
        self.prev_btn = Widgets.QPushButton()  # TODO
        self.play = MusicSyncTimer()
        self.lyric = LyricWindow(self.play, self.skin)
        self.lyric.show()
        self.thread = Thread(target=self.run, name="MusicPlayer")
        self.thread.start()
        with open("./settings/hotkeys.json") as f:
            self.hotkeys = json.load(f)["MusicPlayer"]
        self.hotkeyRegister()

    def run(self) -> None:
        while True:
            self.lyric.refresh = True
            music_path, lyric_path = MUSIC_LIST[self.i]
            self.audio_analyzer_thread = Thread(
                target=self.AudioAnalyzer,
                name="_MusicNotificationWindow",
                args=[music_path, self.lyric.setLyric],
                daemon=True,
            )
            self.play_thread = Thread(
                target=self.play.play,
                name="_PlayMusic",
                args=[music_path],
                daemon=True,
            )
            self.recreateLyricThread()
            self.audio_analyzer_thread.start()
            self.play_thread.start()
            self.audio_analyzer_thread.join(0)
            self.play_thread.join()
            self.i += 1
            if self.i > len(MUSIC_LIST) - 1:
                self.i -= len(MUSIC_LIST)

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

    def AudioAnalyzer(self, audio, lyric_callback: Callable):
        log.info(f"正在读取{audio}")
        info = File(audio)
        tags: dict = info.__dict__["tags"]

        class Unknown:
            text = [LANG["Unknown"]]
            data = LANG["Unknown"]

        class UnknownLyric:
            text = LANG["Unknown"]

        length = info.info.length
        log.info(f"获取到时长: {length}s")
        bitrate = info.info.bitrate // 1000
        log.info(f"获取到比特率: {bitrate}Kbps")
        title = tags.get(TITLE, Unknown).text[0]
        log.info(f"获取到标题: {title}")
        artist = tags.get(ARTIST, Unknown).text[0]
        log.info(f"获取到艺术家: {artist}")
        album = tags.get(ALBUM, Unknown).text[0]
        log.info(f"获取到专辑: {album}")
        track = tags.get(TRACK, Unknown).text[0]
        log.info(f"获取到音轨数: {track}")
        cover = tags.get(COVER, Unknown).data
        log.info(f"获取到封面")
        lyric = tags.get(LYRIC, UnknownLyric).text
        log.info(f"获取到歌词")
        lyric = f"[0:-1]{title} - {artist}\n[0:-1]{album}\n" + lyric
        lyric_callback(lyric)
        append(
            self.noti_queue,
            f"{LANG['Now Playing']}:{title}\n{LANG['Artist']}:{artist}\n{LANG['Album']}:{album}",
            cover,
            "MusicInfoNotification",
        )

    def prevMusic(self):
        self.i -= 2
        self.play.stop()
        log.info("切换到上一首歌曲")

    def nextMusic(self):
        self.play.stop()
        log.info("切换到下一首歌曲")

    def toggleMusic(self):
        if self.play.paused:
            self.play.resume()
        else:
            self.play.pause()

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
        register(self.hotkeys["close_main_window"], os._exit, args=(0,))

    def source_release(self):
        log.info("释放了所有资源")
        self.lyric.destroy()
        del self.music
        del self.lyric
