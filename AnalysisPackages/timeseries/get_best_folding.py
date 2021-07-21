import argparse
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from AnalysisPackages.utilities import utils
from AnalysisPackages.timeseries import get_foldedpulsestack
from AnalysisPackages.utilities.pulsar_information_utility import PulsarInformationUtility


def main(file_name, ch_number, polarization, p4: int, p1bins: int, p4bins: int):
    psr = PulsarInformationUtility(file_name)
    channel_number = int(ch_number[2:4])
    root_dirname = str(Path(__file__).parent.parent.parent.absolute()) + '/'

    binned_time_series_filename = utils.get_binned_time_series_filename(channel_number, root_dirname, polarization, psr)

    with open(binned_time_series_filename, 'r') as binned_time_series_file:  # todo - can be extracted to a common util
        binned_time_series = np.loadtxt(binned_time_series_file)

    pulse_stack = binned_time_series.reshape(-1, p1bins)

    pulse_stack_properties_filename = utils.get_pulse_stack_properties_filename(root_dirname)
    pulse_stack_properties = np.loadtxt(pulse_stack_properties_filename)
    previous_properties_flag = False
    if pulse_stack_properties.shape[0] == 4:
        print(f"previous data used: \n"
              f"Input longitude where the pulse starts: {pulse_stack_properties[0]}\n"
              f"Input longitude where the pulse ends: {pulse_stack_properties[1]}\n"
              f"Input start period number : {pulse_stack_properties[2]}\n"
              f"Input end period number : {pulse_stack_properties[3]}")
        previous_properties_flag = True if input("use same? (y/n): ").lower() == 'y' else False

    if not previous_properties_flag:
        plot_pulse_stack(pulse_stack)
        plot_integrated_pulse_profile(ch_number, file_name, pulse_stack)
        longitude_start = int(float(input("Input longitude where the pulse starts: ")) * 1000)
        longitude_end = int(float(input("Input longitude where the pulse ends: ")) * 1000)
        period_start = int(input("Input start period number : "))
        period_end = int(input("Input end period number : "))
        np.savetxt(pulse_stack_properties_filename,
                   np.array([longitude_start, longitude_end, period_start, period_end]))
    else:
        longitude_start = int(float(pulse_stack_properties[0])*1000)
        longitude_end = int(float(pulse_stack_properties[1])*1000)
        period_start = int(pulse_stack_properties[2])
        period_end = int(pulse_stack_properties[3])

    pulse_stack = pulse_stack[period_start:period_end, longitude_start:longitude_end]

    if False:  # seperate plot fun
        plt.imshow(pulse_stack, extent=[longitude_start / 1000, longitude_end / 1000,
                                        period_start, period_end], origin="lower", aspect="auto")
        plt.xlabel("Longitude")
        plt.ylabel("Period")
        plt.show()
    if False:  # seperate plot fun
        plt.plot(np.linspace(longitude_start / 1000, longitude_end / 1000, longitude_end - longitude_start),
                 np.mean(pulse_stack, axis=0))
        plt.xlim(longitude_start / 1000, longitude_end / 1000)
        # plt.ylim(-32, 130)
        plt.title(f"Integrated Pulse {file_name} Band {ch_number}")
        plt.xlabel("Longitude")
        plt.show()

    folding_parameter_list = np.linspace(81, 380, 3000)
    sum_of_squares_list = np.zeros(folding_parameter_list.shape)
    for i in range(folding_parameter_list.shape[0]):
        folded_pulse_stack = get_foldedpulsestack.main(file_name, ch_number, polarization, folding_parameter_list[i],
                                                       p1bins, p4bins, pulse_stack)
        sum_of_squares_list[i] = np.nansum(np.square(folded_pulse_stack))

    plt.plot(folding_parameter_list, sum_of_squares_list)
    plt.show()


def plot_integrated_pulse_profile(ch_number, file_name, pulse_stack):
    plt.plot(np.linspace(0, 0.999, 1000), np.mean(pulse_stack, axis=0))
    plt.xlim(0, 1)
    # plt.ylim(-32, 130)
    plt.title(f"Integrated Pulse {file_name} Band {ch_number}")
    plt.xlabel("Longitude")
    plt.show()


def plot_pulse_stack(pulse_stack):
    plt.imshow(pulse_stack, extent=[0, 1, 0, pulse_stack.shape[0]], origin="lower", aspect="auto")
    plt.xlabel("Longitude")
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
