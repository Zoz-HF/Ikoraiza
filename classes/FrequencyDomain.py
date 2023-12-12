from classes.functions import *
import pyqtgraph as pg


class FrequencyDomain:
    def __init__(self, input_spectro_pointer=None, output_spectro_pointer=None, frequency_graph=None):
        if input_spectro_pointer is not None:
            self.input_figure, self.input_canvas = create_figure(input_spectro_pointer)
            self.output_figure, self.output_canvas = create_figure(output_spectro_pointer)
            self.frequency_graph = frequency_graph
            self.frequency_graph.setBackground("w")
            self.frequency_signal = pg.PlotCurveItem()
            self.frequency_graph.addItem(self.frequency_signal)
            self.input_data = []
            self.sampling_rate = None
            self.number_of_samples = None
            self.frequencies = []
            self.amplitudes = []
            self.max_amplitudes = 0
            self.output_amplitudes = []
            self.output_data = []

    def add_new_file(self, input_data, sampling_rate):
        self.input_data = input_data
        self.sampling_rate = sampling_rate
        self.number_of_samples = len(self.input_data)
        self.frequencies, self.amplitudes = get_fourier_transform(self.input_data, self.number_of_samples,
                                                                  1 / self.sampling_rate)
        self.output_amplitudes = self.amplitudes.copy()
        frequency_graph_absolute_amplitudes = abs(self.amplitudes) / self.number_of_samples
        self.max_amplitudes = max(frequency_graph_absolute_amplitudes)
        self.frequency_signal.setData(self.frequencies, frequency_graph_absolute_amplitudes, pen="b")
        self.frequency_graph.setLimits(xMin=min(self.frequencies), xMax=max(self.frequencies),
                                       yMax=max(frequency_graph_absolute_amplitudes) * 1.1,
                                       yMin=min(frequency_graph_absolute_amplitudes) * 0.9)
        spectro_gram(self.input_data, self.sampling_rate, self.input_figure, self.input_canvas, "input")

    def update_output_spectrogram(self, data, sample_rate):
        spectro_gram(data, sample_rate, self.output_figure, self.output_canvas, "output")

    def clear(self):
        self.frequencies = None
        self.amplitudes = None
        self.frequency_signal.setData()
        self.frequency_graph.clear()
        self.frequency_graph.addItem(self.frequency_signal)
        self.input_data = []
        self.sampling_rate = None
        self.number_of_samples = None
        self.frequencies = []
        self.amplitudes = []
        self.output_data = []
        self.output_amplitudes = []
        clear_spectro_gram(self.output_figure, self.output_canvas)
        clear_spectro_gram(self.input_figure, self.input_canvas)
