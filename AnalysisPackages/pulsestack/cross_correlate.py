import argparse
from pathlib import Path


import numpy as np
import matplotlib.pyplot as plt

from AnalysisPackages.utilities import utils
from AnalysisPackages.utilities.pulsar_information_utility import PulsarInformationUtility


def main(pulsar_name, ref_ch_number, second_ch_number):
    ref_channel_number = int(ref_ch_number[2:4])
    second_channel_number = int(second_ch_number[2:4])
    root_dirname =  str(Path(__file__).parent.parent.parent.absolute()) + '/'
    psr = PulsarInformationUtility(pulsar_name)

    ref_pulse_stack_filename = utils.get_smoothened_folded_pulse_stack_filename(ref_channel_number, root_dirname, psr)
    with open(ref_pulse_stack_filename) as ref_pulse_stack_file:
        ref_pulse_stack = np.loadtxt(ref_pulse_stack_file)
    # plt.imshow(ref_pulse_stack, origin="lower")
    # plt.show()

    second_pulse_stack_filename = utils.get_smoothened_folded_pulse_stack_filename(second_channel_number, root_dirname, psr)
    with open(second_pulse_stack_filename) as second_pulse_stack_file:
        second_pulse_stack = np.loadtxt(second_pulse_stack_file)
    # plt.imshow(second_pulse_stack, origin="lower")
    # plt.show()
    print(second_pulse_stack.shape)

    rows, cols = second_pulse_stack.shape
    correlation_matrix = np.zeros(ref_pulse_stack.shape)
    for row_shift in range(-int(rows/2 - 1), int(rows/2 + 1)):  # range(-99, 101)
        row_shifted = np.roll(second_pulse_stack, row_shift, axis=0)
        for col_shift in range(-int((cols+1)/2), int(cols/2)):  # range(-100, 99)
            correlation_matrix[row_shift + int(rows/2 - 1), col_shift + int((cols+1)/2)] = np.sum(
                ref_pulse_stack * np.roll(row_shifted, col_shift, axis=1))

    # correlation_matrix = signal.correlate2d(ref_pulse_stack, second_pulse_stack)

    plt.tight_layout()
    plt.subplot(1,2,2)
    plt.imshow(correlation_matrix, origin="lower", extent=[-100 / 1000, 99 / 1000, -49 / 100, 50 / 100],
               cmap="coolwarm", aspect="auto")
    plt.colorbar()
    plt.xlabel("Shift in pulse phase")
    #plt.ylabel("Shift in modulation phase")
    plt.title(f"Cross correlation between\nband {ref_ch_number} and {second_ch_number}")
    # plt.text(0.5, 0.5, "sample", col)

    position_max = np.unravel_index(correlation_matrix.argmax(), correlation_matrix.shape)
    print(position_max)
    shift_pulse_phase = (position_max[1] - int((cols+1)/2)) / 1000
    shift_modulation_phase = (position_max[0] - int(rows/2 - 1)) / rows
    plt.scatter(shift_pulse_phase, shift_modulation_phase, color="y", marker="x")
    plt.annotate(f"Max: {round(correlation_matrix[position_max[0], position_max[1]], 2)} \n"
                 f"({shift_pulse_phase},{shift_modulation_phase})", (shift_pulse_phase, shift_modulation_phase),
                 xytext=(shift_pulse_phase + 0.002, shift_modulation_phase - 0.03))
    print(f"shift_pulse_phase: {shift_pulse_phase}... shift_modulation_phase: {shift_modulation_phase}")
    plt.subplot(1, 2, 1)
    plt.ylim(-0.49, 0.5)
    plt.ylabel("Shift in modulation phase")
    plt.title(f"Max at each modulation phase\nband {ref_ch_number} and {second_ch_number}")
    plt.plot(np.amax(correlation_matrix, axis=1), np.linspace(-0.49, 0.50, rows))
    plt.show()

    plt.imshow(correlation_matrix, origin="lower", extent=[-100 / 1000, 99 / 1000, -49 / 100, 50 / 100],
               cmap="coolwarm", aspect="auto")
    plt.colorbar()
    plt.xlabel("Shift in pulse phase")
    plt.ylabel("Shift in modulation phase")
    plt.title(f"Cross correlation between\nband {ref_ch_number} and {second_ch_number}")
    plt.scatter(shift_pulse_phase, shift_modulation_phase, color="y", marker="x")
    plt.annotate(f"Max: {round(correlation_matrix[position_max[0], position_max[1]], 2)} \n"
                 f"({shift_pulse_phase},{shift_modulation_phase})", (shift_pulse_phase, shift_modulation_phase),
                 xytext=(shift_pulse_phase + 0.002, shift_modulation_phase - 0.03))
    plt.show()

    plt.xlabel("Shift in modulation phase")
    plt.title(f"Cross correlation at max allignment in pulse phase\n"
              f"between bands {ref_ch_number} and {second_ch_number}")
    plt.plot(np.amax(correlation_matrix, axis=1), np.linspace(-0.5, 0.495, rows))
    plt.show()


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
