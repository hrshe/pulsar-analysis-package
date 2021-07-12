import argparse
import warnings
from pathlib import Path

import numpy as np

from os.path import isfile
from itertools import islice

from AnalysisPackages.utilities import utils
from AnalysisPackages.utilities.bcolors import bcolors
from AnalysisPackages.utilities.pulsar_information_utility import PulsarInformationUtility


# repeat
def ms_time_delay_to_time_quanta(t, psr):
    return t * ((psr.band[channel_number].sampling_frequency * 1000) / (512 * psr.n_packet_integration))


def main(file_name, ch_number, polarization, specfile_chunk_size=5000):
    global channel_number
    global psr

    psr = PulsarInformationUtility(file_name)  # "B0834+06_20090725_114903"
    channel_number = int(ch_number[2:4])
    bins = int(round(ms_time_delay_to_time_quanta(psr.period, psr)))
    average_pulse_profile = create_nan_array(bins, psr.n_channels)
    end_spec_file_flag = False
    root_dirname = str(Path(__file__).parent.parent.parent.absolute()) + '/'
    time_quanta_start = 0

    spec_file_path = utils.get_spec_file_name(root_dirname, psr, channel_number, polarization)
    print("spec file path: ", spec_file_path)
    ok_flag = input("Okay? Continue?")

    if ok_flag.lower() == 'n':
        exit()

    if not isfile(spec_file_path):
        print(f"{bcolors.FAIL}file '{spec_file_path}' does not exist.\nExiting...{bcolors.ENDC}")
        exit()
    print(f"reading file {spec_file_path[112:]}")

    # read

    with open(spec_file_path, 'r') as spec_file:
        while not end_spec_file_flag:
            # read file
            dyn_spec, end_spec_file_flag = read_spec_file(end_spec_file_flag, specfile_chunk_size, spec_file)

            # get time series in mili seconds
            time_array, time_quanta_start = get_time_array(time_quanta_start, dyn_spec.shape[0])
            print(f"read till time quanta: {time_quanta_start} -> {round(time_array[-1], 2)} ms  --> "
                  f"{round(time_array[-1] / psr.period, 2)} periods")

            # remove rfi
            dyn_spec = utils.remove_rfi(dyn_spec, psr)

            # interpolate
            interpolated = interpolate_2D(dyn_spec, time_array, bins, psr)

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                average_pulse_profile = np.nanmean(np.dstack((average_pulse_profile, interpolated)), axis=2)

            continue_flag = True if (input("continue folding?").lower() == "y") else False
            if not continue_flag:
                break
            if end_spec_file_flag:
                break

        utils.plot_DS(average_pulse_profile)
        output_filename = utils.get_average_pulse_file_name(root_dirname, psr, channel_number, polarization)
        np.savetxt(output_filename, average_pulse_profile)
        print("average pulse profile saved in file: ", output_filename)
        # return average_pulse_profile


def interpolate_2D(dyn_spec, time_array, bins, psr):
    interpolated_intermediate, interpolated_count = create_zero_array(bins, dyn_spec.shape[1]), \
                                                    create_zero_array(bins, dyn_spec.shape[1])
    for i in range(time_array.shape[0]):
        f_p = (time_array[i] / psr.period) - int(time_array[i] / psr.period)
        n_bin = f_p * bins
        j = int(n_bin)
        if j == bins - 1:
            k = 0
        else:
            k = j + 1
        delta = n_bin - j

        if 0 <= j < bins - 1:
            for ch in range(psr.n_channels):
                if not np.isnan(dyn_spec[i, ch]):
                    interpolated_intermediate[j, ch] = interpolated_intermediate[j, ch] + dyn_spec[i, ch] * (1 - delta)
                    interpolated_intermediate[k, ch] = interpolated_intermediate[k, ch] + dyn_spec[i, ch] * delta
                    interpolated_count[j, ch] = interpolated_count[j, ch] + 1 - delta
                    interpolated_count[k, ch] = interpolated_count[k, ch] + delta
        # else:
        #
        #     print("else condition of 0 <= j < bins - 1: j value is ", j)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        return interpolated_intermediate / interpolated_count


def create_zero_array(rows, cols):
    return np.zeros((rows, cols))


def create_nan_array(rows, cols):
    a = np.zeros((rows, cols))
    a[:] = np.nan
    return a


def get_time_array(time_quanta_start, n_rows):
    time_array = utils.timequanta_to_millisec(np.arange(time_quanta_start, time_quanta_start + n_rows),
                                              psr, channel_number)
    time_quanta_start = time_quanta_start + n_rows
    return time_array, time_quanta_start


def read_spec_file(end_spec_file_flag, n_rows, spec_file):
    dyn_spec = np.genfromtxt(islice(spec_file, n_rows), dtype=float)
    print("\nspec file read.")
    if dyn_spec.shape[0] < n_rows:
        print("eof for spec file reached")
        end_spec_file_flag = True

    dyn_spec[dyn_spec < 0] = np.nan

    return dyn_spec, end_spec_file_flag


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file_name", type=str,
                        help="The mbr filename without the sequence number(eg. ch03_B0834+06_20090725_114903)")
    parser.add_argument("ch_number", type=str,
                        help="band number (eg. ch03 for band 3)")
    parser.add_argument("polarization", type=str,
                        help="polarization for which average pulse profile is to be obtained ('XX' or 'YY')")
    parser.add_argument("spec_chunk_size", type=int, default=5000, nargs="?",
                        help="number of rows to be picked from .spec file at once (default value is 5000)")

    args = parser.parse_args()
    main(args.input_file_name, args.ch_number,
         args.polarization, args.spec_chunk_size)  # B0834+06_20090725_114903 ch03 XX