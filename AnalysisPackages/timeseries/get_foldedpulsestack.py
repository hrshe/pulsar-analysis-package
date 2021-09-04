import argparse
import math
from pathlib import Path
from scipy import ndimage

import numpy as np
import matplotlib.pyplot as plt

from AnalysisPackages.utilities import utils
from AnalysisPackages.utilities.pulsar_information_utility import PulsarInformationUtility


def main(file_name, ch_number, polarization, p4: int, p1bins: int, p4bins: int,
         pulse_stack=None):
    psr = PulsarInformationUtility(file_name)
    channel_number = int(ch_number[2:4])
    root_dirname = str(Path(__file__).parent.parent.parent.absolute()) + '/'
    pulse_stack_properties_filename = utils.get_pulse_stack_properties_filename(root_dirname)
    pulse_stack_properties = np.loadtxt(pulse_stack_properties_filename)
    if pulse_stack is None:
        binned_time_series_filename = \
            utils.get_binned_time_series_filename(channel_number, root_dirname, polarization, psr)

        with open(binned_time_series_filename, 'r') as binned_time_series_file:
            binned_time_series = np.loadtxt(binned_time_series_file)

        pulse_stack = binned_time_series.reshape(-1, p1bins)

        plt.imshow(pulse_stack.reshape(-1, p1bins), extent=[0, 1, 0, pulse_stack.shape[0]], origin="lower",
                   aspect="auto")
        plt.xlabel("Longitude")
        plt.ylabel("Period")
        plt.show()

        longitude_end, longitude_start, period_end, period_start = get_pulse_stack_properties(ch_number, file_name,
                                                                                              p1bins, pulse_stack,
                                                                                              pulse_stack_properties)
        pulse_stack = pulse_stack[period_start:period_end, longitude_start:longitude_end]

        plt.imshow(pulse_stack, extent=[longitude_start / p1bins, longitude_end / p1bins,
                                        period_start, period_end], origin="lower", aspect="auto")
        plt.xlabel("Longitude")
        plt.ylabel("Period")
        plt.title(f"Pulse Stack before flagged periods\n {file_name} ch {channel_number:02}")
        plt.show()

        pulse_stack[pulse_stack==0] = np.nan
        flag_periods_with_large_std(channel_number, pulse_stack)
        pulse_stack = flag_periods_with_robust_mean_rms(file_name, channel_number, pulse_stack)
        manual_flag_periods_ch01(channel_number, pulse_stack)

        if True:  # seperate plot fun
            plt.imshow(pulse_stack, extent=[longitude_start / p1bins, longitude_end / p1bins,
                                            period_start, period_end], origin="lower", aspect="auto")
            plt.xlabel("Longitude")
            plt.ylabel("Period")
            plt.title(f"Pulse Stack after flagged periods\n {file_name} ch {channel_number:02}")
            plt.show()
        if True:  # seperate plot fun
            plt.plot(np.linspace(longitude_start / p1bins, longitude_end / p1bins, longitude_end - longitude_start),
                     np.nanmean(pulse_stack, axis=0))
            plt.xlim(longitude_start / p1bins, longitude_end / p1bins)
            # plt.ylim(-32, 130)
            plt.title(f"Integrated Pulse {file_name} Band {ch_number}")
            plt.xlabel("Longitude")
            plt.show()
    else:
        longitude_start = int(float(pulse_stack_properties[0]) * p1bins)
        longitude_end = int(float(pulse_stack_properties[1]) * p1bins)
        period_start = int(pulse_stack_properties[2])
        period_end = int(pulse_stack_properties[3])
    interpolated_intermediate, interpolated_count = np.zeros((p4bins, pulse_stack.shape[1]), dtype="float"), \
                                                    np.zeros((p4bins, pulse_stack.shape[1]), dtype="float")
    for index, period in enumerate(pulse_stack):
        if np.isnan(period).any():#np.isnan(period[:167]).any():
            print(f"at least one nan value in period index: {index}")
            continue
        n_bin = np.math.modf((index / p4))[0] * p4bins
        j = int(n_bin)
        if j == p4bins - 1:
            k = 0
        else:
            k = j + 1
        delta = n_bin - j

        if 0 <= j < p4bins - 1:
            interpolated_intermediate[j, :] = interpolated_intermediate[j, :] + period * (1 - delta)
            interpolated_intermediate[k, :] = interpolated_intermediate[k, :] + period * delta
            interpolated_count[j, :] = interpolated_count[j, :] + 1 - delta
            interpolated_count[k, :] = interpolated_count[k, :] + delta
        elif j == p4bins - 1:
            k = 0
            interpolated_intermediate[j, :] = interpolated_intermediate[j, :] + period * (1 - delta)
            interpolated_intermediate[k, :] = interpolated_intermediate[k, :] + period * delta
            interpolated_count[j, :] = interpolated_count[j, :] + 1 - delta
            interpolated_count[k, :] = interpolated_count[k, :] + delta
        else:
            print("else condition of 0 <= j < bins - 1: j value is ", j)

    folded_pulse_stack = interpolated_intermediate / interpolated_count

    if True:  # separate plot fun
        plt.imshow(folded_pulse_stack,
                   extent=[longitude_start / p1bins, longitude_end / p1bins, 0, 1],
                   origin="lower", aspect="auto")
        plt.colorbar()
        plt.xlabel("Pulse Phase")
        plt.ylabel(f"Modulation Phase")
        plt.title(f"P3 folded pulse stack for {file_name} {ch_number}\nPulse Intensity flag (3-sigma)")  # \n"
        plt.show()

    # folded_pulse_stack_filename = utils.get_folded_pulse_stack_filename(channel_number, root_dirname, psr)
    # np.savetxt(folded_pulse_stack_filename, folded_pulse_stack)
    # print(f"folded pulse stack saved to : {folded_pulse_stack_filename}")

    return folded_pulse_stack


def flag_periods_with_robust_mean_rms(pulsar_name, channel_number, pulse_stack):
    # flag periods based on statistics on integrated pulse intensity
    plt.plot(np.nanmean(pulse_stack, axis=0))
    plt.title("Select pulse position start and end")
    plt.show()
    # start, end = list(map(int, input("input comma separated start and end position: ").split(sep=",")))
    start, end = {1: [25, 125], 2: [30, 150], 3: [60, 160], 4: [60, 160]}.get(channel_number)
    pulse_intensity = np.nansum(pulse_stack[:, start:end], axis=1)
    mean, rms = utils.get_robust_mean_rms(pulse_intensity, 3)
    plt.plot(pulse_intensity, color="blue")
    plt.text(pulse_intensity.shape[0] - 70, np.max(pulse_intensity),
             'robust mean=%5.3f,\nrobust rms =%5.3f' % tuple([mean, rms]), color="red")
    text_box_position = {1:200, 2: 22, 3: 6, 4: 2}
    plt.text(pulse_intensity.shape[0] - 70, np.max(pulse_intensity) - text_box_position.get(channel_number),
             'Blue: rejected since\nlies outside 3' + u'σ',
             color="blue")
    plt.title(f"Pulse Intensity for {pulsar_name} ch {channel_number:02}.")
    plt.xlabel("Periods")
    plt.xlabel("Intensity")
    pulse_intensity[abs(pulse_intensity - mean) > 3 * rms] = np.nan
    plt.plot(pulse_intensity, color="orange")
    plt.show()
    pulse_stack = pulse_stack * (pulse_intensity / pulse_intensity)[:, np.newaxis]
    return pulse_stack


def flag_periods_with_large_std(channel_number, pulse_stack):
    std = np.nanstd(pulse_stack, axis=1)
    std_cutoff = {1: 4, 2: 0.5, 3: 1.6, 4: 0.4}.get(channel_number)  # todo: make this configurable
    std_arr = std < std_cutoff
    std_arr = std_arr * 1.0
    std_arr[std_arr == 0] = np.nan
    for i in range(pulse_stack.shape[0]):
        pulse_stack[i] = pulse_stack[i] * std_arr[i]


def get_pulse_stack_properties(ch_number, file_name, p1bins, pulse_stack, pulse_stack_properties):
    previous_properties_flag = False
    if pulse_stack_properties.shape[0] == 4:
        print(f"previous data used: \n"
              f"Input longitude where the pulse starts: {pulse_stack_properties[0]}\n"
              f"Input longitude where the pulse ends: {pulse_stack_properties[1]}\n"
              f"Input start period number : {pulse_stack_properties[2]}\n"
              f"Input end period number : {pulse_stack_properties[3]}")
        # previous_properties_flag = True if input("use same? (y/n): ").lower() == 'y' else False
        previous_properties_flag = True
    if not previous_properties_flag:
        plot_pulse_stack(pulse_stack)
        plot_integrated_pulse_profile(ch_number, file_name, pulse_stack)
        longitude_start = int(float(input("Input longitude where the pulse starts: ")) * p1bins)
        longitude_end = int(float(input("Input longitude where the pulse ends: ")) * p1bins)
        period_start = int(input("Input start period number : "))
        period_end = int(input("Input end period number : "))
        # np.savetxt(pulse_stack_properties_filename,
        # np.array([longitude_start/1000, longitude_end/1000, period_start, period_end]))
    else:
        longitude_start = int(float(pulse_stack_properties[0]) * p1bins)
        longitude_end = int(float(pulse_stack_properties[1]) * p1bins)
        period_start = int(pulse_stack_properties[2])
        period_end = int(pulse_stack_properties[3])
    return longitude_end, longitude_start, period_end, period_start


def manual_flag_periods_ch01(channel_number, pulse_stack):
    if channel_number == 1:
        ch_1_period_flags = [27, 84, 56, 69, 111, 114, 123, 125, 128, 131, 170, 181, 195, 198, 221, 222, 219, 247,
                             273,
                             279, 291, 316, 341, 342, 361, 383, 407, 416, 438, 459, 467, 469, 485, 488, 492, 493,
                             519,
                             520, 527, 531, 560, 586, 588, 591, 596, 626, 636, 693, 703, 714, 733, 745, 774, 788]
        pulse_stack[ch_1_period_flags] = np.nan


def plot_integrated_pulse_profile(ch_number, file_name, pulse_stack):
    plt.plot(np.linspace(0, 0.999, 1000), np.mean(pulse_stack, axis=0))
    plt.xlim(0, 1)
    # plt.ylim(-32, 130)
    plt.title(f"Integrated Pulse {file_name} Band {ch_number}")
    plt.xlabel("Longitude")
    plt.show()


def plot_pulse_stack(pulse_stack):
    plt.imshow(pulse_stack, extent=[0, 1, 0, pulse_stack.shape[0]], origin="lower", aspect="auto")
    plt.xlabel("Pulse Phase")
    plt.ylabel("Period")
    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("file_name", type=str,
                        help="The mbr filename without the sequence number(eg. ch03_B0834+06_20090725_114903)")
    parser.add_argument("ch_number", type=str,
                        help="band number (eg. ch03 for band 3)")
    parser.add_argument("polarization", type=str,
                        help="polarization for which average pulse profile is to be obtained "
                             "('XX', 'YY' or 'I' for stokes I)")
    parser.add_argument("p4", type=float,
                        help="Value of P4")
    parser.add_argument("-b1", "--p1bins", type=int, default=1000, metavar="<int>",
                        help="number of bins in P1 (default value is 1000)")
    parser.add_argument("-b4", "--p4bins", type=int, default=100, metavar="<int>",
                        help="number of bins in P4 (default value is 100)")

    args = parser.parse_args()
    main(args.file_name, args.ch_number, args.polarization, args.p4, args.p1bins, args.p4bins)
    # B0809+74 ch03 I  -b1 1000 -b4 100         #todo - add p1bins in config
