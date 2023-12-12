import shutil
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve
import sys
from PyQt5.QtWidgets import QSlider, QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QSignalMapper
from classes.FrequencyDomain import *
from classes.TimeGraph import *
from collections import namedtuple
from Dialog import *
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QVBoxLayout, QDialog

Slider_tuple = namedtuple("Slider", ["min_frequency", "max_frequency", "slider_object", "window_curve"])

FORM_CLASS, _ = loadUiType(path.join(path.dirname(__file__), "mainWindow.ui"))


class MainApp(QMainWindow, FORM_CLASS):

    def __init__(self, parent=None):

        super(MainApp, self).__init__(parent)
        QMainWindow.__init__(self, parent=None)
        self.setupUi(self)
        self.standard_deviation = 0
        self.playing = None
        self.animation = None
        self.mode_name = None
        self.dialog_window = None
        self.setWindowTitle("Equalizer")
        self.timer = QtCore.QTimer()
        self.timer.setInterval(25)
        self.timer.timeout.connect(self.move_line)
        self.mode_mapper = QSignalMapper()
        self.mode_mapper.mapped[str].connect(self.add_signal_and_make_slider)
        self.input_signal_graph = TimeGraph(self.inputAudio)
        self.output_signal_graph = TimeGraph(self.outputAudio)
        self.outputAudio.setXLink(self.inputAudio)
        self.outputAudio.setYLink(self.inputAudio)
        self.slider_mapper = QSignalMapper()
        self.slider_mapper.mapped[str].connect(self.slider_value_change)

        self.mode_dictionary = {
            "ECG": {"RBBB": Slider_tuple(0, 17.5, None, None), "Sinus": Slider_tuple(0, 4, None, None),
                    "ventricular fibrillation": Slider_tuple(17, 150, None, None)},
            "Animal": {"Owl": Slider_tuple(0, 800, None, None), "Horse": Slider_tuple(1000, 2200, None, None),
                       "Bat": Slider_tuple(2500, 5000, None, None), "Goat": Slider_tuple(0, 7000, None, None),
                       "Dolphin": Slider_tuple(0, 14000, None, None)},
            "Musical": {"Guitar": Slider_tuple(0, 900, None, None),
                        "Piccolo": Slider_tuple(1000, 2000, None, None),
                        "Xylophone": Slider_tuple(7000, 15000, None, None),
                        "trianglemod": Slider_tuple(4000, 6000, None, None)},
            "Uniform": {}}

        self.ui_components = {"reset": self.resetGraph, "clear": self.clearGraph,
                              "zoom_in": self.zoomInBtn, "zoom_out": self.zoomOutBtn, "speed_up": self.speedUp,
                              "slow_down": self.slowDown, }

        self.frequency_domain = FrequencyDomain(input_spectro_pointer=self.spectroInputLayout,
                                                output_spectro_pointer=self.spectroOutputLayout,
                                                frequency_graph=self.frequency_graph)
        handle_graph_buttons(self.ui_components, self.input_signal_graph)
        handle_graph_buttons(self.ui_components, self.output_signal_graph)

        self.window_signal = "Rectangular window"

        self.handle_buttons()

    def handle_buttons(self):
        self.SideBar.toggled.connect(self.toggle_side_bar)
        self.windowComboBox.currentTextChanged.connect(self.window_control)
        self.Add_signal.clicked.connect(self.open_add_signal_dialog)
        self.mute_input.clicked.connect(self.unmute_input_graph)
        self.mute_output.clicked.connect(self.unmute_output_graph)
        self.muteAllSounds.clicked.connect(self.mute_all)
        self.clearGraph.clicked.connect(self.clear_all)
        self.playPauseGraph.clicked.connect(self.pause_play_graph)
        self.volumeSlider.valueChanged.connect(self.control_volume)
        disable_enable_buttons(self.ui_components, False)
        self.saveAudio.clicked.connect(self.save_output_audio_file)

    def move_line(self):
        self.input_signal_graph.move_line()
        self.output_signal_graph.move_line()

    def control_volume(self):
        volume = self.volumeSlider.value()
        pygame.mixer.music.set_volume(volume / 100.0)
        if volume == 0:
            self.muteAllSounds.setIcon(QIcon('icons/mute.png'))
        else:
            self.muteAllSounds.setIcon(QIcon('icons/sound.png'))

    def window_control(self):
        is_play = self.playing
        if is_play:
            self.pause_graphs()
        if self.windowComboBox.currentText() == 'Gaussian window':
            self.open_gaussian_window()
        self.window_signal = self.windowComboBox.currentText()
        self.create_output(False)
        if is_play:
            self.play_graphs()

    def open_gaussian_window(self):
        gaussian_window = QDialog(self)
        gaussian_window.setWindowTitle('Gaussian Window')
        layout = QVBoxLayout(gaussian_window)
        label = QLabel('standard deviation = 500', gaussian_window)
        layout.addWidget(label)
        standard_deviation_slider = QSlider(gaussian_window)
        standard_deviation_slider.setOrientation(1)
        standard_deviation_slider.setMinimum(50)
        standard_deviation_slider.setMaximum(1000)
        standard_deviation_slider.setValue(500)
        standard_deviation_slider.valueChanged.connect(
            lambda: label.setText(f'standard deviation = {standard_deviation_slider.value()}'))
        layout.addWidget(standard_deviation_slider)
        ok_button = QPushButton('OK', gaussian_window)
        ok_button.clicked.connect(gaussian_window.accept)
        layout.addWidget(ok_button)
        result = gaussian_window.exec_()
        if result == QDialog.Accepted:
            self.standard_deviation = standard_deviation_slider.value()

    def add_signal_and_make_slider(self, file_path, mode_name):
        self.clear_all()
        disable_enable_buttons(self.ui_components, True)
        self.mode_name = mode_name
        data, sample_rate = self.input_signal_graph.add_wav_file(file_path, "input")
        self.frequency_domain.add_new_file(data, sample_rate)
        if mode_name == "Uniform":
            self.add_uniform_signal(self.frequency_domain.frequencies)
        mode_slider_ranges = self.mode_dictionary[mode_name]
        position_index = 1
        for slider_name, slider_parameter in mode_slider_ranges.items():
            label = QLabel(slider_name)
            label.setFont(QFont('Helvetica [Cronyx]', 10))
            slider = QSlider()
            slider.setOrientation(0)
            slider.setMinimum(0)
            slider.setMaximum(50)
            slider.setMinimumSize(20, 250)
            slider.setValue(10)
            slider.setTickPosition(QSlider.TicksAbove)
            self.slider_mapper.setMapping(slider, slider_name)
            slider.valueChanged.connect(self.slider_mapper.map)
            self.sliderLayout.addWidget(slider)
            self.sliderLayout.addWidget(label)
            line_color = random_color_generator()
            frequency_start_line = pg.InfiniteLine(pos=slider_parameter.min_frequency, movable=False,
                                                   markers=[('>|', (1 - 0.25) / len(mode_slider_ranges.keys()), 10.0)],
                                                   pen=line_color)
            frequency_end_line = pg.InfiniteLine(pos=slider_parameter.max_frequency, movable=False,
                                                 markers=[('|<', (1 - 0.25) / len(mode_slider_ranges.keys()), 10.0)],
                                                 pen=line_color)
            pg.InfLineLabel(frequency_start_line, text=slider_name,
                            position=(1 - 0.2) * position_index / len(mode_slider_ranges.keys()))
            window_on_frequency_graph = pg.PlotCurveItem()
            self.mode_dictionary[mode_name][slider_name] = slider_parameter._replace(slider_object=slider,
                                                                                     window_curve=window_on_frequency_graph)
            self.frequency_domain.frequency_graph.addItem(window_on_frequency_graph)
            self.frequency_domain.frequency_graph.addItem(frequency_start_line)
            self.frequency_domain.frequency_graph.addItem(frequency_end_line)
            position_index += 1

        self.create_output(True)
        self.pause_play_graph()
        self.unmute_input_graph()

    def add_uniform_signal(self, frequencies):
        band_length = len(frequencies) // 10
        for i in range(10):
            self.mode_dictionary["Uniform"][f"{i + 1}"] = Slider_tuple(frequencies[i * band_length],
                                                                       frequencies[(i + 1) * band_length],
                                                                       None, None)

    def open_add_signal_dialog(self):
        self.dialog_window = Dialog()
        self.dialog_window.submitClicked.connect(self.add_signal_and_make_slider)
        self.dialog_window.show()

    def toggle_side_bar(self):
        if self.SideBar.isChecked():
            new_width = 500
        else:
            new_width = 0
        self.animation = QPropertyAnimation(self.sideBarFrame, b"minimumWidth")
        self.animation.setDuration(20)
        self.animation.setEndValue(new_width)
        self.animation.setEasingCurve(QEasingCurve.InOutQuart)
        self.animation.start()
        self.sideBarFrame.update()

    def unmute_input_graph(self):
        self.output_signal_graph.pygame_play_mute()
        self.input_signal_graph.pygame_play_unmute()
        self.mute_input.setIcon(QIcon('icons/sound.png'))
        self.mute_output.setIcon(QIcon('icons/mute.png'))

    def unmute_output_graph(self):
        self.input_signal_graph.pygame_play_mute()
        self.output_signal_graph.pygame_play_unmute()
        self.mute_output.setIcon(QIcon('icons/sound.png'))
        self.mute_input.setIcon(QIcon('icons/mute.png'))

    def mute_all(self):
        self.output_signal_graph.pygame_play_mute()
        self.input_signal_graph.pygame_play_unmute(False)
        self.mute_input.setIcon(QIcon('icons/mute.png'))
        self.mute_output.setIcon(QIcon('icons/mute.png'))
        self.muteAllSounds.setIcon(QIcon('icons/mute.png'))

    def clear_all(self):
        self.frequency_domain.clear()
        # Clear all sliders in the layout
        for widget in reversed(range(self.sliderLayout.count())):
            widget = self.sliderLayout.itemAt(widget).widget()
            if isinstance(widget, QSlider) or isinstance(widget, QLabel):
                widget.deleteLater()
        disable_enable_buttons(self.ui_components, False)

    def create_output(self, new):
        for slider in self.mode_dictionary[self.mode_name].keys():
            self.change_frequency_domain_amplitudes(slider)
            self.mode_dictionary[self.mode_name][slider].window_curve.setData(
                np.linspace(self.mode_dictionary[self.mode_name][slider].min_frequency,
                            self.mode_dictionary[self.mode_name][slider].max_frequency, 500),
                window_function(std=self.standard_deviation, name=self.window_signal,
                                amplitude=self.frequency_domain.max_amplitudes), pen="black")
        self.create_output_wav_file(new)

    def slider_value_change(self, slider_name):
        self.change_frequency_domain_amplitudes(slider_name)
        self.create_output_wav_file()

    def change_frequency_domain_amplitudes(self, slider_name):
        frequency_array = self.frequency_domain.frequencies
        modified_band = (frequency_array > self.mode_dictionary[self.mode_name][slider_name].min_frequency) & (
                frequency_array < self.mode_dictionary[self.mode_name][slider_name].max_frequency)
        window_array = window_function(n=len(frequency_array[modified_band]),
                                       amplitude=self.mode_dictionary[self.mode_name][
                                                     slider_name].slider_object.value() / 10,
                                       std=self.standard_deviation,
                                       name=self.window_signal)
        self.frequency_domain.output_amplitudes[modified_band] = self.frequency_domain.amplitudes[
                                                                     modified_band] * window_array

    def create_output_wav_file(self, new=False):
        playing_status = self.input_signal_graph.playing
        if playing_status:
            self.pause_graphs()
        reconstructed_signal = get_inverse_fourier_transform(self.frequency_domain.output_amplitudes)
        wav.write("played_audio/reconstructed.wav", self.frequency_domain.sampling_rate,
                  reconstructed_signal.astype(np.int16))
        if new:
            data, sample_rate = self.output_signal_graph.add_wav_file("played_audio/reconstructed.wav", "output")
        else:
            data, sample_rate = self.output_signal_graph.update_wave_file("played_audio/reconstructed.wav", "output")
        self.frequency_domain.update_output_spectrogram(data, sample_rate)
        if playing_status:
            self.play_graphs()

    def pause_graphs(self):
        self.timer.stop()
        self.playing = False
        self.input_signal_graph.pause()
        self.output_signal_graph.pause()

    def play_graphs(self):
        self.input_signal_graph.play()
        self.output_signal_graph.play()
        self.timer.start()
        self.playing = True

    def pause_play_graph(self):
        if self.playing:
            self.pause_graphs()
            self.playPauseGraph.setIcon(QIcon('icons/play.png'))

        else:
            self.play_graphs()
            self.playPauseGraph.setIcon(QIcon('icons/pause.png'))

    def save_output_audio_file(self):
        save_path = QFileDialog.getSaveFileName(self, 'Save File', "audio file", "wav Files (*.wav)")[0]
        shutil.copyfile("played_audio/output.wav", f"{save_path}")


def main():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
