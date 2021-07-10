import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from AnalysisPackages.utilities import utils
from AnalysisPackages.utilities.pulsar_information_utility import PulsarInformationUtility


def main(file_name, ch_number, polarization, bins: int):
    psr = PulsarInformationUtility(file_name)  # "B0834+06_20090725_114903"
    channel_number = int(ch_number[2:4])
    root_dirname = str(Path(__file__).parent.parent.parent.absolute()) + '/'

    with open(utils.get_time_series_filename(channel_number, root_dirname, polarization, psr), 'r') as time_series_file:
        time_series = np.loadtxt(time_series_file)
    total_periods = int(time_series[-1, 0] / psr.period) + 1

    interpolated_intermediate, interpolated_count = np.zeros(bins * total_periods, dtype="float"), \
                                                    np.zeros(bins * total_periods, dtype="float")
    for time_series_quanta in time_series:
        n_bin = (time_series_quanta[0] / psr.period) * bins
        j = int(n_bin)
        if j == bins - 1:
            k = 0
        else:
            k = j + 1
        delta = n_bin - j

        if 0 <= j < bins * total_periods - 1:
            if not np.isnan(time_series_quanta[1]):
                interpolated_intermediate[j] = interpolated_intermediate[j] + time_series_quanta[1] * (1 - delta)
                interpolated_intermediate[k] = interpolated_intermediate[k] + time_series_quanta[1] * delta
                interpolated_count[j] = interpolated_count[j] + 1 - delta
                interpolated_count[k] = interpolated_count[k] + delta
        else:
            print("else condition of 0 <= j < bins - 1: j value is ", j)

    binned_time_series = np.divide(interpolated_intermediate, interpolated_count,
                                   out=np.zeros_like(interpolated_intermediate), where= interpolated_count!=0)
    plt.plot(binned_time_series)
    plt.show()

    plt.imshow(binned_time_series.reshape(-1, bins))
    plt.show()


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])) # B0834+06_20090725_114903 ch03 XX 1000
