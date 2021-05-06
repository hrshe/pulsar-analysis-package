import sys
from os.path import isfile
from pathlib import Path

import numpy as np

from AnalysisPackages.utilities import utils
from AnalysisPackages.utilities.bcolors import bcolors
from AnalysisPackages.utilities.pulsar_information_utility import PulsarInformationUtility, get_central_frequency
from AnalysisPackages.utilities.utils import remove_rfi, plot_DS, time_delay_to_quanta


def main(file_name, ch_number, polarization):
    psr = PulsarInformationUtility(file_name)  # "B0834+06_20090725_114903"
    seq_number = 0
    time_quanta_count = 0
    channel_number = int(ch_number[2:4])
    n_rows = 10000  # give proper name
    root_dirname = str(Path(__file__).parent.parent.parent.absolute()) + '/'

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
                    if carry_over_flag and len(lines_from_file) + dynamic_spectrum.shape[0] >= n_rows:
                        break
                    if len(lines_from_file) >= n_rows:
                        break
                if carry_over_flag:
                    dynamic_spectrum = np.vstack([dynamic_spectrum, np.array(lines_from_file)])
                    time_quanta_last = time_quanta_count
                    carry_over_flag = False
                else:
                    dynamic_spectrum = np.array(lines_from_file)
                    time_quanta_last = time_quanta_count
                if dynamic_spectrum.shape[0] < n_rows:
                    carry_over_flag = True
                    break
                else:
                    # process dynamic spectrum
                    process(dynamic_spectrum, psr, time_quanta_first,
                            root_dirname, seq_number, channel_number, polarization)

            seq_number = seq_number + 1


def process(dynamic_spectrum, psr, time_quanta_first, root_dirname, seq_number, channel_number, polarization):
    dynamic_spectrum = remove_rfi(dynamic_spectrum, psr)
    plot_DS(dynamic_spectrum)
    add_rows = time_delay_to_quanta(, psr.n_packet_integration)
    dynamic_spectrum = np.vstack([dynamic_spectrum, np.empty(,psr.n_channels)])

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])  # B0834+06_20090725_114903 ch03 XX
