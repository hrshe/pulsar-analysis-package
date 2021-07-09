import sys
from pathlib import Path

import numpy as np

from os.path import isfile
from itertools import islice
import matplotlib.pyplot as plt

from AnalysisPackages.utilities import utils
from AnalysisPackages.utilities.bcolors import bcolors
from AnalysisPackages.utilities.pulsar_information_utility import PulsarInformationUtility


def flag_nan_from_mask(spectrum, mask):
    return spectrum*mask


def main(file_name, ch_number, polarization, pulse_width_spec):
    global channel_number
    global psr

    psr = PulsarInformationUtility(file_name)  # "B0834+06_20090725_114903"
    channel_number = int(ch_number[2:4])
    half_pulse_width_ch = int(round(psr.n_channels * int(pulse_width_spec) / 200))
    chunk_rows = 5000
    end_spec_file_flag = False
    root_dirname = str(Path(__file__).parent.parent.parent.absolute()) + '/'
    time_quanta_start = 0

    channel_to_frequency_array = get_channel_frequency()
    channel_to_time_delay_array = get_time_delay_array(channel_to_frequency_array)
    channel_to_column_delay = ms_time_delay_to_time_quanta(channel_to_time_delay_array, psr)

    spec_file_path = utils.get_spec_file_name(root_dirname, psr, channel_number, polarization)
    if not isfile(spec_file_path):
        print(f"{bcolors.FAIL}file '{spec_file_path}' does not exist.\nExiting...{bcolors.ENDC}")
        exit()
    print(f"reading file {spec_file_path[112:]}")

    overflow_buffer = create_nan_array(int(round(channel_to_column_delay[0])), psr.n_channels)
    overflow_buffer_flag = False
    intensities, global_time_series = np.array([]), np.array([])
    mask = np.loadtxt(utils.get_pulse_mask_filename(channel_number, root_dirname, polarization, psr))

    with open(spec_file_path, 'r') as spec_file:
        while not end_spec_file_flag:
            # read file
            dyn_spec, end_spec_file_flag = read_spec_file(end_spec_file_flag, chunk_rows, spec_file)

            # get time series in mili seconds and update next time quanta start
            dyn_spec_time_series = get_time_array(time_quanta_start, dyn_spec.shape[0])
            global_time_series = np.append(global_time_series, dyn_spec_time_series)
            time_quanta_start = time_quanta_start + dyn_spec.shape[0]

            # remove rfi
            dyn_spec = utils.remove_rfi(dyn_spec, psr)

            # method 1 (ignore nearest x %)
            template_offpulse_spectrum = utils.get_robust_mean_rms_2d(dyn_spec, psr.sigma_threshold)[0]
            if True:
                for index, spectrum in enumerate(dyn_spec):
                    if np.isnan(spectrum).all():  # skip missing packets spectrum
                        continue
                    index_of_max = np.nanargmax(spectrum)
                    flagged_spectrum = flag_nan_near_index(half_pulse_width_ch, index_of_max, spectrum)
                    flagged_template_offpulse_spectrum = flag_nan_near_index(half_pulse_width_ch, index_of_max,
                                                                             template_offpulse_spectrum)
                    correction_factor = np.nansum(flagged_spectrum) / np.nansum(flagged_template_offpulse_spectrum)
                    dyn_spec[index] = spectrum / correction_factor

            # todo - de compression
            # method 2 (pulse mask)
            template_offpulse_spectrum = utils.get_robust_mean_rms_2d(dyn_spec, psr.sigma_threshold)[0]
            if True:
                for index, spectrum in enumerate(dyn_spec):
                    if np.isnan(spectrum).all():  # skip missing packets spectrum
                        continue
                    t = dyn_spec_time_series[index]
                    fractional_ms_time_in_a_period = t - int(t/psr.period)*psr.period
                    mask_index = int(round(ms_time_delay_to_time_quanta(fractional_ms_time_in_a_period, psr)))
                    if mask_index >= mask.shape[0]:
                        print(f"mask_index calculated: {mask_index} is greater than mask shape: {mask.shape}")
                        mask_index = mask_index - 1

                    flagged_spectrum = flag_nan_from_mask(spectrum, mask[mask_index])
                    flagged_template_offpulse_spectrum = flag_nan_from_mask(template_offpulse_spectrum, mask[mask_index])
                    correction_factor = np.nansum(flagged_spectrum) / np.nansum(flagged_template_offpulse_spectrum)
                    dyn_spec[index] = spectrum / correction_factor

            # de disperse and add buffer
            dedispersed, overflow_buffer = de_disperse(dyn_spec, channel_to_column_delay,
                                                       overflow_buffer, overflow_buffer_flag)
            # subtract robust mean
            subtract_robust_mean(dedispersed, psr.sigma_threshold)

            # freq integrate to find intensities and append to global array
            intensities = np.append(intensities, np.nanmean(dedispersed, axis=1))

            # plot DS and corresponding TS
            if True:
                plot_DS_and_TS(dedispersed, intensities[-1 * chunk_rows:], dyn_spec.shape[0])

            overflow_buffer_flag = True
            print(time_quanta_start)

        plt.plot(global_time_series, intensities)
        plt.show()

        # todo - save data
        # output_filename = utils.get_average_pulse_file_name(root_dirname, psr, channel_number, polarization)
        # np.savetxt(output_filename, average_pulse_profile)
        # print("average pulse profile saved in file: ", output_filename)
        # return average_pulse_profile


def flag_nan_near_index(half_width, index_of_max, spectrum):
    flagged_spectrum = np.array(spectrum)
    if index_of_max < half_width:
        flagged_spectrum[:index_of_max + half_width] = np.nan
    if index_of_max > spectrum.shape[0] - half_width:
        flagged_spectrum[index_of_max - half_width:] = np.nan
    else:
        flagged_spectrum[index_of_max - half_width:index_of_max + half_width] = np.nan
    return flagged_spectrum


def subtract_robust_mean(dyn_spec, sigma_threshold):
    """
    Subtracts robust mean along each freq channel
    :param dyn_spec:
    :param sigma_threshold:
    :return:
    """
    for ch in range(dyn_spec.shape[1]):
        mean, rms = utils.get_robust_mean_rms(dyn_spec[:, ch], sigma_threshold)
        dyn_spec[:, ch] = dyn_spec[:, ch] - mean


def plot_DS_and_TS(DS, intensities, n_rows):
    figure, axis = plt.subplots(2, 1)
    axis[0].imshow(np.transpose(DS), interpolation="nearest", aspect='auto', cmap="gray",
                   extent=[0, n_rows, 256, 0])
    axis[0].xaxis.set_label_position('top')
    axis[0].set_xlabel('Dynamic Spectrum')
    axis[0].set_ylabel('Freq Channel')
    # axis[0].
    axis[1].plot(np.linspace(0, n_rows - 1, n_rows), intensities)
    axis[1].xaxis.set_label_position('bottom')
    axis[1].set_xlabel("Frequency Integrated")
    axis[1].axis(xmin=0, xmax=n_rows, ymax=10, ymin=-5)
    plt.show()


def create_zero_array(rows, cols):
    return np.zeros((rows, cols))


def create_nan_array(rows, cols):
    return np.zeros((rows, cols)) - np.nan


def get_time_array(time_quanta_start, n_rows):
    time_array = utils.timequanta_to_millisec(np.arange(time_quanta_start, time_quanta_start + n_rows),
                                              psr, channel_number)
    return time_array


def read_spec_file(end_spec_file_flag, n_rows, spec_file):
    dyn_spec = np.genfromtxt(islice(spec_file, n_rows), dtype=float)
    print("spec file read. dyn_spec shape:", dyn_spec.shape)
    if dyn_spec.shape[0] < n_rows:
        print("eof for spec file reached")
        end_spec_file_flag = True

    return dyn_spec, end_spec_file_flag


def get_channel_frequency():
    central_frequency = psr.band[channel_number].central_frequency
    band_width = psr.band[channel_number].sampling_frequency / 2
    return np.array([central_frequency + (band_width / 2) - (ch * band_width / (psr.n_channels - 1)) for ch in
                     range(psr.n_channels)])


def get_time_delay_array(channel_to_frequency_array):
    frequency_squares = np.square(channel_to_frequency_array)
    return np.array([4.15 * ((1 / frequency_squares[psr.n_channels - 1]) - (1 / frequency_squares[ch]))
                     for ch in range(psr.n_channels)]) * np.power(10, 6) * psr.dm


# repeat
def ms_time_delay_to_time_quanta(t, psr):
    return t * ((psr.band[channel_number].sampling_frequency * 1000) / (512 * psr.n_packet_integration))


def de_disperse(dyn_spec, channel_to_column_delay, overflow_buffer, overflow_buffer_flag):
    nan_array = create_nan_array(int(round(channel_to_column_delay[0])), psr.n_channels)
    dedispersed = np.vstack((dyn_spec, nan_array))
    for ch in range(psr.n_channels):
        dedispersed[:, ch] = np.roll(dedispersed[:, ch], int(round(channel_to_column_delay[ch])))

    if overflow_buffer_flag:
        dedispersed[:int(round(channel_to_column_delay[0])), :] = np.nanmean(
            np.dstack((dedispersed[:int(round(channel_to_column_delay[0])), :], overflow_buffer)), axis=2)
    return dedispersed[:dyn_spec.shape[0], :], dedispersed[dyn_spec.shape[0]:, :]


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])  # B0834+06_20090725_114903 ch03 XX 20
