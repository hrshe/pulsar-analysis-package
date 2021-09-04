import argparse
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage

from AnalysisPackages.utilities import utils
from AnalysisPackages.utilities.pulsar_information_utility import PulsarInformationUtility


def main(pulsar_name, ch_number, rows):
    channel_number = int(ch_number[2:4])
    root_dirname = str(Path(__file__).parent.parent.parent.absolute()) + '/'
    psr = PulsarInformationUtility(pulsar_name)

    pulse_stack_filename = utils.get_folded_pulse_stack_filename(channel_number, root_dirname, psr)
    with open(pulse_stack_filename) as pulse_stack_file:
        pulse_stack = np.loadtxt(pulse_stack_file)
    # plt.imshow(pulse_stack, origin="lower", aspect="auto")
    # plt.show()

    half_row = pulse_stack.shape[0] / 2
    slope_correction_factor_range = np.linspace(0, 1, 101)
    sum_of_square = np.zeros(slope_correction_factor_range.shape)

    for index, slope_correction_factor in enumerate(slope_correction_factor_range):
        shifted_pulse_stack = np.zeros(pulse_stack.shape)
        for row in range(pulse_stack.shape[0]):
            shifted_pulse_stack[row, :] = np.roll(pulse_stack[row, :],
                                                  int(slope_correction_factor * (row - half_row)), axis=0)

        sum_of_square[index] = np.sum(np.square(np.sum(shifted_pulse_stack, axis=0)))
        print(index)
        # plt.imshow(shifted_pulse_stack, origin="lower")
        # plt.title(f"Correction factor = {slope_correction_factor}")
        # plt.show()

    # plt.plot(slope_correction_factor_range, sum_of_square)
    # plt.show()

    # slope_correction_factor = slope_correction_factor_range[np.argmax(sum_of_square)]
    slope_correction_factor = {1: 0.37, 2: 0.34, 3: 0.30, 4: 0.27}  # 100 bins
    if rows == 50:
        slope_correction_factor.update((x, y * 2) for x, y in slope_correction_factor.items())

    for row in range(pulse_stack.shape[0]):
        pulse_stack[row, :] = np.roll(pulse_stack[row, :],
                                      int(slope_correction_factor.get(channel_number) * (row - half_row)), axis=0)

    plt.imshow(pulse_stack, origin="lower")
    plt.title(f"Slope corrected P3 folded pulse stack\nfor {pulsar_name} {ch_number}")
    plt.colorbar()
    plt.show()

    # sigma = [4, 1]
    # smoothened_folded_pulse_stack = ndimage.filters.gaussian_filter(pulse_stack, sigma, mode='constant')
    plt.imshow(pulse_stack,
               origin="lower")
    plt.colorbar()
    plt.xlabel("Pulse Phase")
    plt.ylabel(f"Modulation Phase")
    plt.title(f"Smoothened P3 folded pulse stack\nfor {pulsar_name} {ch_number}")
    plt.show()

    folded_pulse_stack_filename = utils.get_smoothened_folded_pulse_stack_filename(channel_number, root_dirname, psr)
    np.savetxt(folded_pulse_stack_filename, pulse_stack)
    print(f"folded pulse stack saved to : {folded_pulse_stack_filename}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("pulsar_name", type=str,
                        help="The pulsar name or the mbr filename without the sequence number"
                             "(eg. B0834+06_20090725_114903)")
    parser.add_argument("ref_ch_number", type=str,
                        help="reference band number (eg. ch03 for band 3)")
    parser.add_argument("bins", type=int,
                        help="bins along the modulation axis (P3)")

    args = parser.parse_args()
    main(args.pulsar_name, args.ref_ch_number, args.bins)
    # B0809+74 ch03 ch02
