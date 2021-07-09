import sys
from itertools import islice
import time
from os.path import isfile
from pathlib import Path

import cv2

import numpy as np

from utilities import utils
from utilities.bcolors import bcolors
from utilities.pulsar_information_utility import PulsarInformationUtility

"""
Purpose of this file is to execute rough patches of code... Not to be included in final project
"""


def main(file_name, polarization):
    psr = PulsarInformationUtility(file_name[5:])  # "B0834+06_20090725_114903"
    seq_number = 0
    time_quanta_first = 0
    time_quanta_last = 0
    time_quanta_count = 0
    channel_number = int(file_name[2:4])
    n_rows = 10000  # give proper name
    root_dirname = str(Path(__file__).parent.parent.parent.absolute()) + '/'

    carry_over_flag = False

    while True:
        spec_file_path = get_spec_file_name(root_dirname, file_name, psr, seq_number, channel_number, polarization)
        if not isfile(spec_file_path):
            print(f"{bcolors.FAIL}file '{spec_file_path}' does not exist.\nExiting...{bcolors.ENDC}")
            exit()
        print(f"reading file {spec_file_path[112:]}")

        with open(spec_file_path, 'r') as f:
            while True:
                lines_from_file = []
                time_quanta_first = time_quanta_count
                for lines in f:
                    lines_from_file.append(np.fromstring(lines, dtype=float, sep=' '))
                    time_quanta_count = time_quanta_count + 1
                    if carry_over_flag and len(lines_from_file) + dyn_spec.shape[0] >= n_rows:
                        break
                    if len(lines_from_file) >= n_rows:
                        break
                if carry_over_flag:
                    dyn_spec = np.vstack([dyn_spec, np.array(lines_from_file)])
                    time_quanta_last = time_quanta_count
                    carry_over_flag = False
                else:
                    dyn_spec = np.array(lines_from_file)
                    time_quanta_last = time_quanta_count
                if dyn_spec.shape[0] < n_rows:
                    carry_over_flag = True
                    break
                else:
                    # process dynamic spectrum
                    process_dynamic_spectrum(dyn_spec, psr, time_quanta_first, time_quanta_last)
                    print(dyn_spec.shape)

            seq_number = seq_number + 1


def process_dynamic_spectrum(dynamic_spectrum, psr, time_quanta_first, time_quanta_last):
    ### Removing Bad RFI channels
    sigma_threshold = 3
    n_bins = 1000
    avg_pulse_prof_wo_robust = np.zeros((psr.n_channels, n_bins))
    dynamic_spectrum = remove_rfi(dynamic_spectrum, psr, sigma_threshold)
    interpolate2d_old(dynamic_spectrum, time_quanta_first, avg_pulse_prof_wo_robust, psr, n_bins)
    utils.plot_DS(np.transpose(avg_pulse_prof_wo_robust))


def get_robust_mean_rms_2d(arr, sigma_threshold):
    '''
    :param arr: a 2D array
    computes mean across axis 0. (mean for each row)
    :return: list of mean and rms. Each list is of dim arr.shape[1]
    '''
    mean, rms = np.zeros(arr.shape[1]), np.zeros(arr.shape[1])
    for i in range(arr.shape[1]):
        mean[i], rms[i] = get_robust_mean_rms(arr[:, i], sigma_threshold)
    return mean, rms


def interpolate2d_new(dyn_spect, time_quanta_start, avg_pulse_prof_wo_robust, psr, n_bins):
    """
    not completed. using old for now
    """
    n_channel = psr.n_channels
    P = psr.period

    n_int = psr.n_packet_integration
    replace_nan_with_mean(dyn_spect)
    time_arr = np.zeros(dyn_spect.shape[0])
    for t_count in range(time_arr.shape[0]):
        time_arr[t_count] = (time_quanta_start + t_count) * 512 * n_int / 33000

    interpolated = np.zeros((n_bins, n_channel))
    for n_ch in range(dyn_spect.shape[1]):
        interpolated[:, n_ch] = np.interp(list(range(n_bins)), time_arr, dyn_spect[:, n_ch], period=P)
    print(interpolated.shape)
    utils.plot_DS(interpolated)
    return 0


def replace_nan_with_mean(dyn_spect):
    mean, rms = get_robust_mean_rms_2d(dyn_spect, 3)
    mean_of_mean = np.nanmean(mean)
    mean = np.where(np.isnan(mean), mean_of_mean, mean)
    nan_indices = np.where(np.isnan(dyn_spect))
    dyn_spect[nan_indices] = np.take(mean, nan_indices[1])


def interpolate2d_old(a, time_quanta_start, avg_pulse_prof_wo_robust, psr, n_bins):
    time_arr = np.zeros(a.shape[0])
    for t_count in range(time_arr.shape[0]):
        time_arr[t_count] = (time_quanta_start + t_count) * 512 * psr.n_packet_integration / 33000
    app_wo_robust = np.zeros((psr.n_channels, n_bins))
    app_count_wo_robust = np.zeros((psr.n_channels, n_bins))
    for t in range(a.shape[0]):
        f_p = (time_arr[t] / psr.period) - int(time_arr[t] / psr.period)
        n_bin = f_p * n_bins

        j = int(n_bin)
        if j == n_bins - 1:
            k = 0
        else:
            k = j + 1
        delta = n_bin - j

        if 0 <= j < n_bins - 1:
            for ch in range(a.shape[1]):
                if not np.isnan(a[t, ch]):
                    app_wo_robust[ch, j] = app_wo_robust[ch, j] + a[t, ch] * (1 - delta)
                    app_wo_robust[ch, k] = app_wo_robust[ch, k] + a[t, ch] * delta
                    app_count_wo_robust[ch, j] = app_count_wo_robust[ch, j] + 1 - delta
                    app_count_wo_robust[ch, k] = app_count_wo_robust[ch, k] + delta

    for row in range(avg_pulse_prof_wo_robust.shape[0]):
        for col in range(avg_pulse_prof_wo_robust.shape[1]):
            if app_count_wo_robust[row, col] > 0 and avg_pulse_prof_wo_robust[row, col] != 0:
                avg_pulse_prof_wo_robust[row, col] = (avg_pulse_prof_wo_robust[row, col] + app_wo_robust[row, col] /
                                                      app_count_wo_robust[row, col]) / 2
            elif avg_pulse_prof_wo_robust[row, col] == 0 and app_count_wo_robust[row, col] > 0:
                avg_pulse_prof_wo_robust[row, col] = app_wo_robust[row, col] / app_count_wo_robust[row, col]


def remove_rfi(dynamic_spectrum, psr, sigma_threshold):
    dynamic_spectrum[:, :10], dynamic_spectrum[:, psr.n_channels - 10:] = np.nan, np.nan
    mean, rms = np.nanmean(dynamic_spectrum, axis=0), np.nanstd(dynamic_spectrum, axis=0)
    # option for robust mean/rms
    snr = float(np.sqrt(psr.n_packet_integration))
    efficiency_x = mean / rms * snr
    mean_x, std_x = get_robust_mean_rms(efficiency_x[10:psr.n_channels - 10], sigma_threshold)
    dynamic_spectrum = np.where(abs(mean_x - efficiency_x) > sigma_threshold * std_x, np.nan, dynamic_spectrum)
    return dynamic_spectrum


def get_robust_mean_rms(input_arr, sigma_threshold):
    arr = np.copy(input_arr)
    ok = False
    iter_i, rms, mean = 0, 0.0, 0.0
    while not ok:
        iter_i += 1
        threshold = rms * sigma_threshold

        mean = np.nanmean(arr)
        rms0 = rms

        if iter_i > 1:
            arr = np.where(abs(arr - mean) <= threshold, arr, np.nan)
        rms = np.nanstd(arr)

        if iter_i > 1:
            if rms == 0.0:
                ok = True  # return
            elif np.isnan(rms):
                ok = True
            elif abs((rms0 / rms) - 1.0) < 0.01:
                ok = True
    return mean, rms


def get_spec_file_name(root_dirname, file_name, psr, seq_number, channel_number, polarization):
    return root_dirname + f"OutputData/{psr.psr_name_date_time}/DynamicSpectrum/ch0{str(channel_number)}/" + \
           file_name + '_' + polarization + '_' + "{0:0=3d}".format(seq_number) + ".spec"


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])  # ch03_B0834+06_20090725_114903 XX
