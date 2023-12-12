import numpy as np
from pyqtgraph.Qt import QtCore
from PyQt5 import QtCore
import pygame.mixer
from pydub import AudioSegment
import pyqtgraph as pg
import scipy.io.wavfile as wav
from PyQt5.QtGui import QIcon
from PyQt5 import QtCore as qtc


def speed_change(sound, speed=1.0):
    sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
        "frame_rate": int(sound.frame_rate * speed)
    })
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)


class TimeGraph(QtCore.QObject):
    def __init__(self, graph_pointer=None, parent=None):
        super(TimeGraph, self).__init__(parent)
        self.original_file_path = None
        if graph_pointer is not None:
            self.sample_rate = 0
            self.played_file_path = ""
            self.data = [0]
            self.time = [0]
            self.time_period = 1
            self.pygame_status = None
            self.playing = False
            self.graphPointer = graph_pointer
            self.graphPointer.setLimits(xMin=0)
            self.graphPointer.setBackground("w")
            pygame.mixer.init()
            self.zoom_factor = 1.0
            self.audio_volume = 0.5
            self.speed_index = 3
            self.speeds_list = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2]
            self.whole_signal = pg.PlotCurveItem()
            self.graphPointer.addItem(self.whole_signal)
            self.played_part_of_signal = pg.PlotCurveItem()
            self.graphPointer.addItem(self.played_part_of_signal)
            self.line = pg.InfiniteLine(pos=0, movable=True)
            self.line_position = 0
            self.graphPointer.addItem(self.line)
            self.line.sigDragged.connect(self.pause)
            self.line.sigPositionChanged.connect(self.drag_line)
            self.line.sigPositionChangeFinished.connect(self.pause)

    def add_wav_file(self, file_path, name):
        self.clear_graph()
        return self.update_wave_file(file_path, name)

    def update_wave_file(self, file_path, name, old_speed=1):
        self.original_file_path = file_path
        self.played_file_path = f"played_audio/{name}.wav"
        current_speed = self.speeds_list[self.speed_index]
        self.line_position = self.line.value() * old_speed / current_speed
        if self.pygame_status:
            pygame.mixer.music.unload()
        sound = AudioSegment.from_file(self.original_file_path)

        new_file_with_new_speed = speed_change(sound, current_speed)

        new_file_with_new_speed.export(self.played_file_path, format='wav')

        self.sample_rate, self.data = wav.read(self.played_file_path)

        self.time = np.linspace(0, len(self.data) / self.sample_rate, len(self.data))

        self.time_period = self.time[1] - self.time[0]
        self.whole_signal.setData(self.time, self.data, pen="r")
        self.line.setPos(self.line_position)
        self.drag_line()
        if self.pygame_status:
            self.pygame_play_unmute()
        return self.data, self.sample_rate

    def move_line(self):
        self.line.setPos((pygame.mixer.music.get_pos() / 1000) + self.line_position)
        self.drag_line()
        if self.line.value() > self.time[-1]:
            self.line.setPos(self.time[-1])
            self.line_position = self.line.value()
            self.pause()

    def drag_line(self):
        index = int(self.line.value() // self.time_period)
        self.played_part_of_signal.setData(self.time[:index], self.data[0:index], pen="b")

    def pause(self):
        self.line_position = self.line.value()
        if self.pygame_status:
            pygame.mixer.music.pause()
        self.playing = False

    def play(self):
        self.line_position = self.line.value()
        if self.pygame_status:
            pygame.mixer.music.play(start=self.line_position)
        self.playing = True

    def speed_up(self):
        if self.speed_index < 7:
            self.speed_index += 1
            self.update_wave_file(old_speed=self.speeds_list[self.speed_index - 1])

    def speed_down(self):
        if self.speed_index > 0:
            self.speed_index -= 1
            self.update_wave_file(old_speed=self.speeds_list[self.speed_index + 1])

    def original_speed(self):
        old_speed_index = self.speed_index
        self.speed_index = 3
        self.update_wave_file(old_speed=self.speeds_list[old_speed_index])

    def reset_graph(self):
        self.line_position = 0
        self.played_part_of_signal.setData()
        self.line.setPos(0)
        self.play()

    def clear_graph(self):
        self.played_file_path = ""
        self.data = [0]
        self.time = [0]
        self.time_period = 1
        self.pygame_status = None
        self.playing = False
        self.audio_volume = 0.5
        self.whole_signal.setData()
        self.played_part_of_signal.setData()
        self.line.setPos(0)
        self.line_position = 0
        pygame.mixer.music.unload()

    def zoom_in(self):
        self.timer.stop()
        self.zoom_factor *= 2  # Increase the zoom factor
        self.graphPointer.plotItem.getViewBox().scaleBy((1 / 2, 1 / 2))

    def zoom_out(self):
        self.timer.stop()
        self.zoom_factor /= 2  # Decrease the zoom factor
        self.graphPointer.plotItem.getViewBox().scaleBy((2, 2))

    def pygame_play_unmute(self, volume=True):
        self.pygame_status = True
        pygame.mixer.music.load(self.played_file_path)
        if volume:
            pygame.mixer.music.set_volume(self.audio_volume)
        else:
            pygame.mixer.music.set_volume(volume)
        self.play()

    def pygame_play_mute(self):
        self.pause()
        pygame.mixer.music.unload()
        self.pygame_status = False
        self.play()

