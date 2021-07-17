import argparse
import warnings
from pathlib import Path

import numpy as np

from os.path import isfile
from itertools import islice
from contextlib import ExitStack
import matplotlib.pyplot as plt

from AnalysisPackages.utilities import utils
from AnalysisPackages.utilities.bcolors import bcolors
from AnalysisPackages.utilities.pulsar_information_utility import PulsarInformationUtility

polarizations = ["XX", "YY"]


def main(file_name, ch_number, polarization, pulse_width_spec, chunk_rows=5000,
         decompression_method1=True, decompression_method2=True, plot_ds_ts_flag=False):
    global channel_number
    global psr

    polarization = polarization.upper()

    psr = PulsarInformationUtility(file_name)  # "B0834+06_20090725_114903"
    channel_number = int(ch_number[2:4])
    half_pulse_width_ch = int(round(psr.n_channels * int(pulse_width_spec) / 200))

    end_spec_file_flag = False
    root_dirname = str(Path(__file__).parent.parent.parent.absolute()) + '/'
    time_quanta_start = 0

    channel_to_frequency_array = get_channel_frequency()
    channel_to_time_delay_array = get_time_delay_array(channel_to_frequency_array)
    channel_to_column_delay = ms_time_delay_to_time_quanta(channel_to_time_delay_array, psr)
    max_dispersion_delay = int(round(channel_to_column_delay[0]))

    spec_file_paths = get_spec_file_paths(channel_number, polarization, psr, root_dirname)

    gain_correction_factor = 1
    if polarization not in polarizations:
        gain_correction_factor = get_gain_correction_factor(channel_number, psr, root_dirname)

    overflow_buffer = create_nan_array(int(round(channel_to_column_delay[0])), psr.n_channels)
    overflow_buffer_flag = False
    intensities, global_time_series = np.array([]), np.array([])

    pulse_mask = get_pulse_mask(channel_number, polarization, psr, root_dirname)

    with ExitStack() as stack:
        spec_files = [stack.enter_context(open(filename, 'r'))
                      for filename in spec_file_paths]

        while not end_spec_file_flag:
            # read spec file and get dyn spec (gain corrected dyn spectrum incase of 'Q'
            dyn_spec, end_spec_file_flag = get_dyn_spec(chunk_rows, end_spec_file_flag, gain_correction_factor,
                                                        polarization, spec_files)

            # get time series in mili seconds and update next time quanta start
            dyn_spec_time_series = get_time_array(time_quanta_start, dyn_spec.shape[0])
            if not overflow_buffer_flag:
                global_time_series = np.append(global_time_series, dyn_spec_time_series[:-max_dispersion_delay])
                print(f"read till time quanta: {time_quanta_start} -> {round(dyn_spec_time_series[-1], 2)} ms  --> "
                      f"{round(dyn_spec_time_series[-1] / psr.period, 2)} periods")
                time_quanta_start = time_quanta_start + dyn_spec.shape[0] - max_dispersion_delay
            else:
                global_time_series = np.append(global_time_series, dyn_spec_time_series)
                print(f"read till time quanta: {time_quanta_start} -> {round(dyn_spec_time_series[-1], 2)} ms  --> "
                      f"{round(dyn_spec_time_series[-1] / psr.period, 2)} periods")
                time_quanta_start = time_quanta_start + dyn_spec.shape[0]

            # remove rfi
            dyn_spec = utils.remove_rfi(dyn_spec, psr)

            # decompression
            if True:
                template_offpulse_spectrum = utils.get_robust_mean_rms_2d(dyn_spec, psr.sigma_threshold)[0]
                decompress(decompression_method1, decompression_method2, dyn_spec, template_offpulse_spectrum,
                           dyn_spec_time_series, half_pulse_width_ch, pulse_mask, psr)

            # de disperse and add buffer
            dedispersed, overflow_buffer = de_disperse(dyn_spec, channel_to_column_delay,
                                                       overflow_buffer, overflow_buffer_flag)
            # subtract robust mean
            subtract_robust_mean(dedispersed, psr.sigma_threshold)

            # freq integrate to find intensities and append to global array
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                count_nonnan = np.sum(~np.isnan(dedispersed), axis=1)
                count_filter_flag = count_nonnan > 30  # todo - name this well
                integrated = np.nanmean(dedispersed, axis=1) * count_filter_flag
                intensities = np.append(intensities, integrated)

            # plot DS and corresponding TS
            continue_flag = True
            if int(dyn_spec_time_series[-1] / psr.period) > 400:
                continue_flag = False
            if not continue_flag:
                break
            if plot_ds_ts_flag:
                if overflow_buffer_flag:
                    plot_DS_and_TS(dedispersed, intensities[-1 * chunk_rows:], dyn_spec.shape[0])
                else:
                    plot_DS_and_TS(dedispersed, intensities[-1 * chunk_rows:], dyn_spec.shape[0] - max_dispersion_delay)

            overflow_buffer_flag = True

        # plt.plot(global_time_series, intensities)
        # plt.show()

        # save data
        time_series_filename = utils.get_time_series_filename(channel_number, root_dirname, polarization, psr)

        np.savetxt(time_series_filename, np.array((global_time_series, intensities)).T)
        print("time series data saved in file: ", time_series_filename)
        # return average_pulse_profile


def get_pulse_mask(channel_number, polarization, psr, root_dirname):
    if polarization in polarizations:
        with open(utils.get_pulse_mask_filename(channel_number, root_dirname, polarization, psr), 'r') as mask_file:
            mask = np.loadtxt(mask_file)
    elif polarization == "I":
        with open(utils.get_pulse_mask_filename(channel_number, root_dirname, polarizations[0], psr), 'r') as mask_file:
            mask = np.loadtxt(mask_file)
    return mask


def flag_nan_from_mask(spectrum, mask):
    return spectrum * mask


def get_stokes_I(chunk_rows, spec_files, gain_correction_factor):
    dyn_spec_x, end_spec_file_flag_x = read_spec_file(chunk_rows, spec_files[0])
    dyn_spec_y, end_spec_file_flag_y = read_spec_file(chunk_rows, spec_files[1])

    dyn_spec_x = dyn_spec_x * gain_correction_factor

    return dyn_spec_x + dyn_spec_y, end_spec_file_flag_x and end_spec_file_flag_y


def get_dyn_spec(chunk_rows, end_spec_file_flag, gain_correction_factor, polarization, spec_files):
    # read file for single polarization
    if polarization in polarizations:
        dyn_spec, end_spec_file_flag = read_spec_file(chunk_rows, spec_files[0])
    # read files for XX and YY, gain correct them and return Q = XX + YY
    elif polarization == 'I':
        dyn_spec, end_spec_file_flag = get_stokes_I(chunk_rows, spec_files,
                                                    gain_correction_factor)
    return dyn_spec, end_spec_file_flag


def get_gain_correction_factor(channel_number, psr, root_dirname):
    average_spectrum_paths = [utils.get_average_spectrum_filename(channel_number, root_dirname, polarization, psr)
                              for polarization in polarizations]
    with open(average_spectrum_paths[0], 'r') as average_spectrum_file_x, \
            open(average_spectrum_paths[1], 'r') as average_spectrum_file_y:
        average_spectra = [np.loadtxt(average_spectrum_file_x), np.loadtxt(average_spectrum_file_y)]
    average_spectrum_x = average_spectra[0]
    average_spectrum_y = average_spectra[1]
    gain_correction_factor = average_spectrum_y / average_spectrum_x
    return gain_correction_factor


def get_spec_file_paths(channel_number, polarization, psr, root_dirname):
    spec_file_paths = []
    if polarization in polarizations:
        spec_file_paths.append(utils.get_spec_file_name(root_dirname, psr, channel_number, polarization))
    elif polarization == 'I':
        for polarization in polarizations:
            spec_file_paths.append(utils.get_spec_file_name(root_dirname, psr, channel_number, polarization))
    else:
        print(f"{bcolors.FAIL}polarization: '{polarization}' is not valid. \nExiting...{bcolors.ENDC}")
        exit()
    for spec_file_path in spec_file_paths:
        if not isfile(spec_file_path):
            print(f"{bcolors.FAIL}file '{spec_file_path}' does not exist.\nExiting...{bcolors.ENDC}")
            exit()
        else:
            print(f"reading file {spec_file_path}")
    return spec_file_paths


def decompress(flag_method1, flag_method2, dyn_spec, template_offpulse_spectrum, dyn_spec_time_series,
               half_pulse_width_ch, mask, psr):
    for index, spectrum in enumerate(dyn_spec):
        if np.isnan(spectrum).all():  # skip missing packets spectrum
            continue
        correction_factor_1, correction_factor_2 = 1, 1
        # method 1
        if flag_method1:
            flagged_spectrum, flagged_template_offpulse_spectrum = get_flagged_spectra_decompression_1(
                spectrum, template_offpulse_spectrum, half_pulse_width_ch)
            correction_factor_1 = np.nansum(flagged_spectrum) / np.nansum(flagged_template_offpulse_spectrum)
        if (not np.isnan(correction_factor_1)) or (correction_factor_1 == 0):
            spectrum = spectrum / correction_factor_1

        # method 2
        if flag_method2:
            t = dyn_spec_time_series[index]
            flagged_spectrum, flagged_template_offpulse_spectrum = get_flagged_spectra_decompression_2(
                spectrum, template_offpulse_spectrum, t, mask, psr)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                correction_factor_2 = np.nansum(flagged_spectrum) / np.nansum(flagged_template_offpulse_spectrum)
        if (not np.isnan(correction_factor_2)) or (correction_factor_2 == 0):
            dyn_spec[index] = spectrum / correction_factor_2


def get_flagged_spectra_decompression_2(spectrum, template_offpulse_spectrum, t, mask, psr):
    fractional_ms_time_in_a_period = t - int(t / psr.period) * psr.period
    mask_index = int(round(ms_time_delay_to_time_quanta(fractional_ms_time_in_a_period, psr)))
    if mask_index >= mask.shape[0]:
        mask_index = mask_index - 1
    flagged_spectrum = flag_nan_from_mask(spectrum, mask[mask_index])
    flagged_template_offpulse_spectrum = flag_nan_from_mask(template_offpulse_spectrum, mask[mask_index])
    return flagged_spectrum, flagged_template_offpulse_spectrum


def get_flagged_spectra_decompression_1(spectrum, template_offpulse_spectrum, half_pulse_width_ch):
    index_of_max = np.nanargmax(spectrum)
    flagged_spectrum = flag_nan_near_index(half_pulse_width_ch, index_of_max, spectrum)
    flagged_template_offpulse_spectrum = flag_nan_near_index(half_pulse_width_ch, index_of_max,
                                                             template_offpulse_spectrum)
    return flagged_spectrum, flagged_template_offpulse_spectrum


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
    axis[1].axis(xmin=0, xmax=n_rows)
    plt.show()


def create_zero_array(rows, cols):
    return np.zeros((rows, cols))


def create_nan_array(rows, cols):
    return np.zeros((rows, cols)) - np.nan


def get_time_array(time_quanta_start, n_rows):
    time_array = utils.timequanta_to_millisec(np.arange(time_quanta_start, time_quanta_start + n_rows),
                                              psr, channel_number)
    return time_array


def read_spec_file(n_rows, spec_file):
    dyn_spec = np.genfromtxt(islice(spec_file, n_rows), dtype=float)
    print(f"spec file {spec_file.name[-7:-5]} read. ", end=" ")
    if dyn_spec.shape[0] < n_rows:
        print("eof for spec file reached")
        end_spec_file_flag = True
    else:
        end_spec_file_flag = False

    dyn_spec[dyn_spec <= 0] = np.nan
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
    max_delay = int(round(channel_to_column_delay[0]))
    nan_array = create_nan_array(max_delay, psr.n_channels)
    dedispersed = np.vstack((dyn_spec, nan_array))
    for ch in range(psr.n_channels):
        dedispersed[:, ch] = np.roll(dedispersed[:, ch], int(round(channel_to_column_delay[ch])))

    if overflow_buffer_flag:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            dedispersed[:max_delay, :] = np.nanmean(np.dstack((dedispersed[:max_delay, :], overflow_buffer)), axis=2)
    else:
        print("buffer overflow is false")
        return dedispersed[max_delay:dyn_spec.shape[0], :], dedispersed[dyn_spec.shape[0]:, :]
    return dedispersed[:dyn_spec.shape[0], :], dedispersed[dyn_spec.shape[0]:, :]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file_name", type=str,
                        help="The mbr filename without the sequence number(eg. ch03_B0834+06_20090725_114903)")
    parser.add_argument("ch_number", type=str,
                        help="band number (eg. ch03 for band 3)")
    parser.add_argument("polarization", type=str,
                        help="polarization for which average pulse profile is to be obtained "
                             "('XX', 'YY' or 'I' for stokes I)")
    parser.add_argument("decomp_1_width", type=int, default=40, nargs="?",
                        help="percentage of signals to be flagged around max signal for decompression by method 1. "
                             "For details, refer documentation (default value is 40)")
    parser.add_argument("-chunk", "--spec_chunk_size", type=int, default=5000, metavar="<int>",
                        help="number of rows to be picked from .spec file at once (default value is 5000)")
    parser.add_argument("-decomp1", "--decompression_method1", type=bool, default=False, metavar="<bool>",
                        help="setting this to False can disable decompression by method 1 "
                             "(usage: '-decomp1 False' default=False)")
    parser.add_argument("-decomp2", "--decompression_method2", type=bool, default=False,  metavar="<bool>",
                        help="setting this to False can disable decompression by method 2 "
                             "(usage: '-decomp2 False' default=False)")
    parser.add_argument("-plot", "--plot_ds_ts", type=bool, default=False,  metavar="<bool>",
                        help="plot dynamic spectrum and corresponding time series after "
                             "processing each chunk (usage: '-plot True' default=False)")
    args = parser.parse_args()
    main(args.input_file_name, args.ch_number, args.polarization, args.decomp_1_width, args.spec_chunk_size,
         args.decompression_method1, args.decompression_method2, args.plot_ds_ts)  # B0834+06_20090725_114903 ch03 XX 20
