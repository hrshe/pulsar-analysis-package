import argparse
from pathlib import Path


import numpy as np
import matplotlib.pyplot as plt

from AnalysisPackages.utilities import utils
from AnalysisPackages.utilities.pulsar_information_utility import PulsarInformationUtility


def main(pulsar_name, ref_ch_number, second_ch_number):
    ref_channel_number = int(ref_ch_number[2:4])
    second_channel_number = int(second_ch_number[2:4])
    root_dirname = str(Path(__file__).parent.parent.parent.absolute()) + '/'
    psr = PulsarInformationUtility(pulsar_name)

    ref_pulse_stack_filename = utils.get_folded_pulse_stack_filename(ref_channel_number, root_dirname, psr)
    with open(ref_pulse_stack_filename) as ref_pulse_stack_file:
        ref_pulse_stack = np.loadtxt(ref_pulse_stack_file)
    # plt.imshow(ref_pulse_stack, origin="lower")
    # plt.show()

    second_pulse_stack_filename = utils.get_folded_pulse_stack_filename(second_channel_number, root_dirname, psr)
    with open(second_pulse_stack_filename) as second_pulse_stack_file:
        second_pulse_stack = np.loadtxt(second_pulse_stack_file)
    # plt.imshow(second_pulse_stack, origin="lower")
    # plt.show()

    correlation_matrix = np.zeros(ref_pulse_stack.shape)
    for row_shift in range(-99, 101):  # range(-49, 51)
        row_shifted = np.roll(second_pulse_stack, row_shift, axis=0)
        for col_shift in range(-100, 99):  # range(-100, 99)
            correlation_matrix[row_shift + 99, col_shift + 100] = np.sum(
                ref_pulse_stack * np.roll(row_shifted, col_shift, axis=1))

    # correlation_matrix = signal.correlate2d(ref_pulse_stack, second_pulse_stack)

    plt.imshow(correlation_matrix, origin="lower", extent=[-100 / 1000, 99 / 1000, -99 / 100, 100 / 100],
               cmap="coolwarm", aspect="auto")
    plt.colorbar()
    plt.xlabel("Shift in pulse phase")
    plt.ylabel("Shift in modulation phase")
    plt.title(f"Cross correlation between band {ref_ch_number} and {second_ch_number}")
    # plt.text(0.5, 0.5, "sample", col)

    position_max = np.unravel_index(correlation_matrix.argmax(), correlation_matrix.shape)
    print(position_max)
    shift_pulse_phase = (position_max[1] - 100) / 1000
    shift_modulation_phase = (position_max[0] - 99) / 200
    plt.scatter(shift_pulse_phase, shift_modulation_phase, color="y", marker="x")
    plt.annotate(f"Max: {round(correlation_matrix[position_max[0], position_max[1]], 2)} \n"
                 f"({shift_pulse_phase},{shift_modulation_phase})", (shift_pulse_phase, shift_modulation_phase),
                 xytext=(shift_pulse_phase + 0.002, shift_modulation_phase - 0.03))
    plt.show()
    print(f"shift_pulse_phase: {shift_pulse_phase}... shift_modulation_phase: {shift_modulation_phase}")

    plt.xlabel("Shift in modulation phase")
    plt.title(f"Cross correlation at max allignment in pulse phase\n"
              f"between bands {ref_ch_number} and {second_ch_number}")
    plt.plot(np.linspace(-0.5, 0.495, 200), correlation_matrix[:, position_max[1]])
    plt.show()
    # rows_grid, cols_grid = np.meshgrid(np.arange(0,199), np.arange(0,100))
    # fig = plt.figure(figsize=[12,12])
    # ax = fig.gca(projection="3d")
    # ax.plot_surface(rows_grid, cols_grid, correlation_matrix, cmap=cm.coolwarm)
    # plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("pulsar_name", type=str,
                        help="The pulsar name or the mbr filename without the sequence number"
                             "(eg. B0834+06_20090725_114903)")
    parser.add_argument("ref_ch_number", type=str,
                        help="reference band number (eg. ch03 for band 3)")
    parser.add_argument("second_ch_number", type=str,
                        help="second channel number to correlate with the first (eg. ch02 for band 2)")

    args = parser.parse_args()
    main(args.pulsar_name, args.ref_ch_number, args.second_ch_number)
    # B0809+74 ch03 ch02
