import sys
from os.path import isfile
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from AnalysisPackages.utilities import utils
from AnalysisPackages.utilities.bcolors import bcolors
from AnalysisPackages.utilities.pulsar_information_utility import PulsarInformationUtility


# repeat
def get_channel_frequency(psr, channel_number):
    central_frequency = psr.band[channel_number].central_frequency
    band_width = psr.band[channel_number].sampling_frequency / 2
    return np.array([central_frequency + (band_width / 2) - (ch * band_width / (psr.n_channels - 1)) for ch in
                     range(psr.n_channels)])


def get_time_delay_array(channel_to_frequency_array, psr, dm):
    frequency_squares = np.square(channel_to_frequency_array)
    return np.array([4.15 * ((1 / frequency_squares[psr.n_channels - 1]) - (1 / frequency_squares[ch]))
                     for ch in range(psr.n_channels)]) \
           * np.power(10, 6) * dm


def get_coloumn_delay(channel_to_time_delay_array, psr):
    return channel_to_time_delay_array


def de_disperse(average_pulse, channel_to_frequency_array, dm, bins):
    channel_to_time_delay_array = get_time_delay_array(channel_to_frequency_array, psr, dm)
    channel_to_column_delay = channel_to_time_delay_array * (bins / psr.period)
    # nan_array = np.zeros((int(channel_to_column_delay[0]), psr.n_channels)) - np.nan
    dedisperse_pulse = np.array(average_pulse)
    for ch in range(psr.n_channels):
        dedisperse_pulse[:, ch] = np.roll(dedisperse_pulse[:, ch], int(channel_to_column_delay[ch]))
    return dedisperse_pulse


def main(file_name, ch_number, polarization):
    global channel_number
    global psr

    psr = PulsarInformationUtility(file_name)  # "B0834+06_20090725_114903"
    channel_number = int(ch_number[2:4])
    root_dirname = str(Path(__file__).parent.parent.parent.absolute()) + '/'

    average_pulse_file_path = utils.get_average_pulse_file_name(root_dirname, psr, channel_number, polarization)

    if not isfile(average_pulse_file_path):
        print(f"{bcolors.FAIL}file '{average_pulse_file_path}' does not exist.\nExiting...{bcolors.ENDC}")
        exit()
    print(f"reading file {average_pulse_file_path[112:]}")
    average_pulse = np.loadtxt(average_pulse_file_path)
    bins = average_pulse.shape[0]

    # de disperse:
    channel_to_frequency_array = get_channel_frequency(psr, channel_number)

    dm_initial = psr.dm
    dm_linspace = np.linspace(dm_initial - 3, dm_initial + 3, 601)
    # dm_linspace = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12.88])
    result = np.zeros(dm_linspace.shape)

    for i in range(dm_linspace.shape[0]):
        print(i)

        dedisperse_pulse = de_disperse(average_pulse, channel_to_frequency_array, dm_linspace[i], bins)
        integrated = np.nanmean(dedisperse_pulse, axis=1)
        # isnan_count = np.count_nonzero(np.isnan(dedisperse_pulse), axis = 1)
        result[i] = np.nansum(np.square(integrated))

        if False:
            figure, axis = plt.subplots(2, 1)
            axis[0].imshow(np.transpose(dedisperse_pulse), interpolation="nearest", aspect='auto', cmap="gray",
                           extent=[0, 1, 256, 0])
            axis[0].xaxis.set_label_position('top')
            axis[0].set_xlabel('Folded Pulse Profile')
            axis[0].set_ylabel('Freq Channel')
            # axis[0].
            axis[1].plot(np.linspace(0, 1, 1000), integrated)
            axis[1].xaxis.set_label_position('bottom')
            axis[1].set_xlabel("Frequency Integrated")
            axis[1].axis(xmin=0, xmax=1, ymax=36.7, ymin=29.9)
            axis[1].text(0.9, 0.5, "DM = " + str(round(dm_linspace[i], 2)), horizontalalignment='center',
                         verticalalignment='center',
                         transform=axis[1].transAxes)
            plt.show()

    plt.plot(dm_linspace, result)
    plt.show()


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])  # B0834+06_20090725_114903 ch03 XX 1000
