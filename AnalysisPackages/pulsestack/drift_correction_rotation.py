import argparse
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage

from AnalysisPackages.utilities import utils
from AnalysisPackages.utilities.pulsar_information_utility import PulsarInformationUtility


def main(pulsar_name, ch_number):
    channel_number = int(ch_number[2:4])
    root_dirname = str(Path(__file__).parent.parent.parent.absolute()) + '/'
    psr = PulsarInformationUtility(pulsar_name)

    pulse_stack_filename = utils.get_folded_pulse_stack_filename(channel_number, root_dirname, psr)
    with open(pulse_stack_filename) as pulse_stack_file:
        pulse_stack = np.loadtxt(pulse_stack_file)
    rows, cols = pulse_stack.shape
    plt.imshow(pulse_stack, origin="lower", aspect="auto")
    plt.show()

    pulse_stack = np.vstack((pulse_stack, pulse_stack, pulse_stack))
    slope_correction_factor_range = np.linspace(0, 45, 91)
    sum_of_square = np.zeros(slope_correction_factor_range.shape)

    for index, slope_correction_factor in enumerate(slope_correction_factor_range):
        shifted_pulse_stack = ndimage.rotate(pulse_stack, slope_correction_factor, reshape=False)
        sum_of_square[index] = np.sum(np.square(np.sum(shifted_pulse_stack[rows:2*rows], axis=0)))
        # plt.imshow(shifted_pulse_stack[rows:2*rows], origin="lower")
        # plt.title(f"Correction factor = {slope_correction_factor}")
        # plt.show()

    plt.plot(slope_correction_factor_range, sum_of_square)
    plt.show()

    slope_correction_factor = slope_correction_factor_range[np.argmax(sum_of_square)]
    # slope_correction_factor = np.mean([0.72, 0.68, 0.61, 0.54]) #50 bins
    # slope_correction_factor = np.mean([20.5, 19.5, 17.5, 15.5])  # 100 bins

    pulse_stack = ndimage.rotate(pulse_stack, slope_correction_factor, reshape=False)[rows:2*rows]

    plt.imshow(pulse_stack, origin="lower")
    plt.title(f"Correction factor = {slope_correction_factor}")
    plt.show()

    sigma = [3, 3]
    smoothened_folded_pulse_stack = ndimage.filters.gaussian_filter(pulse_stack, sigma, mode='constant')
    plt.imshow(smoothened_folded_pulse_stack,
               origin="lower", aspect="auto")
    plt.colorbar()
    plt.xlabel("Pulse Phase")
    plt.ylabel(f"Modulation Phase")
    plt.title(f"SmoothenedP3 folded pulse stack for {pulsar_name} {ch_number}\nAll periods")
    plt.show()

    # folded_pulse_stack_filename = utils.get_smoothened_folded_pulse_stack_filename(channel_number, root_dirname, psr)
    # np.savetxt(folded_pulse_stack_filename, smoothened_folded_pulse_stack)
    # print(f"folded pulse stack saved to : {folded_pulse_stack_filename}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("pulsar_name", type=str,
                        help="The pulsar name or the mbr filename without the sequence number"
                             "(eg. B0834+06_20090725_114903)")
    parser.add_argument("ref_ch_number", type=str,
                        help="reference band number (eg. ch03 for band 3)")

    args = parser.parse_args()
    main(args.pulsar_name, args.ref_ch_number)
    # B0809+74 ch03 ch02
