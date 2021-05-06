import sys

import numpy as np

from os.path import isfile
from AnalysisPackages.utilities.pulsar_information_utility import PulsarInformationUtility
from pathlib import Path

from AnalysisPackages.utilities import utils
from AnalysisPackages.utilities.bcolors import bcolors
from AnalysisPackages.utilities.utils import get_average_pule_profile_filename


def main(file_name, ch_number, polarization):
    psr = PulsarInformationUtility(file_name)  # "B0834+06_20090725_114903"
    seq_number = 0
    time_quanta_count = 0
    channel_number = int(ch_number[2:4])
    n_rows = 10000  # give proper name
    root_dirname = str(Path(__file__).parent.parent.parent.absolute()) + '/'

    read_spec_and_process(channel_number, file_name, n_rows, polarization, psr,
                          root_dirname, seq_number, time_quanta_count, process_dynamic_spectrum,
                          plot_average_pulse_profile_flag=True)


def read_spec_and_process(channel_number, file_name, n_rows, polarization,
                          psr, root_dirname, seq_number, time_quanta_count, process,
                          plot_average_pulse_profile_flag=False):
    n_bins = utils.millisec2timequanta(psr.period, psr)
    avg_pulse_profile = np.zeros((psr.n_channels, n_bins))
    carry_over_flag = False
    while True:
        spec_file_path = utils.get_spec_file_name(root_dirname, psr, seq_number, channel_number, polarization)
        if not isfile(spec_file_path):
            print(f"{bcolors.FAIL}file '{spec_file_path}' does not exist.\nExiting...{bcolors.ENDC}")
            exit()
        print(f"reading file {spec_file_path[112:]}")

        with open(spec_file_path, 'r') as f:
            while True:
                lines_from_file = []
                if not carry_over_flag:
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
                    process(dyn_spec, psr, time_quanta_first, plot_average_pulse_profile_flag,
                            root_dirname, seq_number, channel_number, polarization, avg_pulse_profile)

            seq_number = seq_number + 1


def process_dynamic_spectrum(dynamic_spectrum, psr, time_quanta_first, plot_average_pulse_profile_flag,
                             root_dirname, seq_number, channel_number, polarization, avg_pulse_profile):
    dynamic_spectrum = utils.remove_rfi(dynamic_spectrum, psr)
    if plot_average_pulse_profile_flag:
        utils.interpolate2d_old(dynamic_spectrum, time_quanta_first, avg_pulse_profile, psr, avg_pulse_profile.shape[1])
        output_filename = get_average_pule_profile_filename(channel_number, root_dirname,
                                                            polarization, psr)
        np.savetxt(output_filename, avg_pulse_profile)
        print(f"{bcolors.OKGREEN}average pulse profile saved to: {output_filename}{bcolors.ENDC}")
        utils.plot_DS(np.transpose(avg_pulse_profile))
        raw_input = input(f"Continue integration? (Y/n)")
        if seq_number == 1:
            exit()
        if raw_input.lower() not in ["y", "yes"]:
            exit()


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])  # B0834+06_20090725_114903 ch03 XX
