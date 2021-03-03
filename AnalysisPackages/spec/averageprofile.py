import sys

import numpy as np
from os.path import isfile
from AnalysisPackages.utilities.pulsar_information_utility import PulsarInformationUtility
from pathlib import Path
import matplotlib.pyplot as plt

from mbr.mbr2dynamicspectrum import plot_DS
from utilities.bcolors import bcolors


def main(file_name, polarization):
    psr = PulsarInformationUtility(file_name[5:])  # "B0834+06_20090725_114903"
    seq_number = 0
    time_quanta_first = 0
    time_quanta_last = 0
    time_quanta_count = 0
    channel_number = int(file_name[2:4])
    n_rows = 10000  # give proper name
    root_dirname = str(Path(__file__).parent.parent.parent.absolute()) + '/'

    read_spec_and_process(channel_number, file_name, n_rows, polarization, psr, root_dirname, seq_number,
                          time_quanta_count, process_dynamic_spectrum)


def read_spec_and_process(channel_number, file_name, n_rows, polarization, psr, root_dirname, seq_number,
                          time_quanta_count, process):
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
                    process(dyn_spec, psr, time_quanta_first, time_quanta_last)
                    print(dyn_spec.shape)

            seq_number = seq_number + 1


def process_dynamic_spectrum(dynamic_spectrum, psr, time_quanta_first, time_quanta_last):
    ### Removing Bad RFI channels
    sigma_threshold = 3

    dynamic_spectrum = remove_rfi(dynamic_spectrum, psr, sigma_threshold)

    plot_DS(dynamic_spectrum)


def remove_rfi(dynamic_spectrum, psr, sigma_threshold):
    dynamic_spectrum[:, :10], dynamic_spectrum[:, psr.n_channels - 10:] = np.nan, np.nan
    mean, rms = np.nanmean(dynamic_spectrum, axis=0), np.nanstd(dynamic_spectrum, axis=0)
    # option for robust mean/rms
    snr = float(np.sqrt(psr.n_packet_integration))
    efficiency_x = mean / rms * snr
    mean_x, std_x = get_robust_mean_rms(efficiency_x[10:psr.n_channels - 10], sigma_threshold)
    dynamic_spectrum = np.where(abs(mean_x - efficiency_x) > sigma_threshold * std_x, np.nan, dynamic_spectrum)
    return dynamic_spectrum


def get_robust_mean_rms_2d(arr):
    '''
    :param arr: a 2D array
    computes mean across axis 0. (mean for each row)
    :return: list of mean and rms. Each list is of dim arr.shape[1]
    '''
    mean, rms = np.zeros(arr.shape[1]), np.zeros(arr.shape[1])
    for i in range(arr.shape[1]):
        mean[i], rms[i] = get_robust_mean_rms(arr[:, i], 3)
    return mean, rms


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
