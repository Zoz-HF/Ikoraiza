from scipy.fft import rfft, rfftfreq, irfft
import random
from scipy.signal.windows import boxcar, hann, hamming, gaussian
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from scipy.signal import spectrogram


def disable_enable_buttons(ui_components_dictionary, enable_or_disable):
    if enable_or_disable:
        for i in ui_components_dictionary:
            ui_components_dictionary[i].setEnabled(True)
    else:
        for i in ui_components_dictionary:
            ui_components_dictionary[i].setEnabled(False)


def handle_graph_buttons(ui_components_dictionary, graph):
    ui_components_dictionary["reset"].clicked.connect(graph.reset_graph)
    ui_components_dictionary["clear"].clicked.connect(graph.clear_graph)
    ui_components_dictionary["zoom_in"].clicked.connect(graph.zoom_in)
    ui_components_dictionary["reset"].clicked.connect(graph.reset_graph)
    ui_components_dictionary["zoom_out"].clicked.connect(graph.zoom_out)
    ui_components_dictionary["speed_up"].clicked.connect(graph.speed_up)
    ui_components_dictionary["slow_down"].clicked.connect(graph.speed_down)


def get_fourier_transform(input_data, number_of_samples, sampling_time):
    amplitudes = 2 * rfft(input_data)
    frequencies = rfftfreq(number_of_samples, sampling_time)

    return frequencies, amplitudes


def get_inverse_fourier_transform(amplitudes):
    sg_reconstructed = irfft(amplitudes / 2)
    return sg_reconstructed


def random_color_generator():
    r = random.randint(0, 255)
    g = random.randint(0, 100)
    b = random.randint(0, 100)
    return r, g, b


def window_function(std, amplitude, name, n=500):
    match name:
        case "Rectangular window":
            return amplitude * boxcar(n)
        case "Hamming window":
            return amplitude * hamming(n)
        case "Hann window":
            return amplitude * hann(n)
        case "Gaussian window":
            return amplitude * gaussian(n, float(std))


def create_figure(layout):
    figure = Figure()
    canvas = FigureCanvas(figure)
    layout.addWidget(canvas)
    return figure, canvas


def spectro_gram(data, sample_rate, figure, canvas, name):
    # Compute the spectrogram using np.fft.fft
    frequencies, times, power_spectral_density = spectrogram(data, fs=sample_rate, nperseg=1000, noverlap=500)

    # Clear previous plot and plot the new spectrogram
    figure.clear()
    subplot_to_draw_in = figure.add_subplot(111)

    # Use pcolor mesh to plot the spectrogram
    subplot_to_draw_in.pcolormesh(times, frequencies, 10 * np.log10(np.abs(power_spectral_density)), shading='auto',
                                  cmap='magma')

    subplot_to_draw_in.set_ylabel('Frequency (Hz)')
    subplot_to_draw_in.set_xlabel('Time (s)')
    subplot_to_draw_in.set_title(f'{name} Spectrogram by dB', fontsize=20)

    # Add color bar to the plot
    color_bar = figure.colorbar(subplot_to_draw_in.pcolormesh(times, frequencies, 10 *
                                                         np.log10(np.abs(power_spectral_density)),
                                                         shading='auto', cmap='magma'),
                           ax=subplot_to_draw_in, format='%+2.0f dB')
    color_bar.set_label('Intensity (dB)')

    # Draw the plot
    canvas.draw()


def clear_spectro_gram(figure, canvas):
    figure.clear()
    canvas.draw()
