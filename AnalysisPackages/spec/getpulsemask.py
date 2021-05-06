"""
Old code... not refactored
todo : need to refactor this code
"""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import sys

from AnalysisPackages.utilities.pulsar_information_utility import PulsarInformationUtility
from AnalysisPackages.utilities.utils import time_delay_to_quanta, millisec2timequanta, \
    get_average_pule_profile_filename, calculate_dispersion_delay


def main(file_name, ch_number, polarization):
    psr = PulsarInformationUtility(file_name)
    root_dirname = str(Path(__file__).parent.parent.parent.absolute()) + '/'
    ch_number = int(ch_number[2:4])
    psr_name = psr.psr_name_date_time

    plt.figure("average pulse profile " + psr_name + " " + str(ch_number) + " " + polarization)
    app = np.loadtxt(get_average_pule_profile_filename(ch_number, root_dirname, polarization, psr))
    plt.imshow(app, interpolation="nearest", aspect="auto")
    plt.title("average pulse profile " + psr_name + " " + str(ch_number) + " " + polarization)
    plt.show()

    cent_freq = psr.get_central_frequency(ch_number)
    n_col = millisec2timequanta(psr.period, psr)

    ref_ch = int(input("Referance channel (Refer Figure): "))  # where center of pulse is seen
    pulse_start_bin = int(input("Pulse start col number (Refer Figure): "))
    pulse_end_bin = int(input("Pulse end col number (Refer Figure): "))  # where center of pulse is seen

    pulse_width = int((pulse_end_bin - pulse_start_bin) / 2) + 1
    print(pulse_width)
    ref_col = int((pulse_end_bin + pulse_start_bin) / 2)
    print(ref_col)
    mask = np.ones((psr.n_channels, n_col), dtype=float)
    print(app.shape)
    print(mask.shape)
    if ref_col - pulse_width < 0:
        mask[:, :ref_col + pulse_width] = np.nan
        mask[:, n_col - (pulse_width - ref_col):] = np.nan

    elif ref_col - pulse_width >= 0 and ref_col + pulse_width <= n_col:
        mask[:, ref_col - pulse_width: ref_col + pulse_width] = np.nan

    elif ref_col + pulse_width > n_col:
        mask[:, ref_col - pulse_width:] = np.nan
        mask[:, :ref_col + pulse_width - n_col] = np.nan

    for ch in range(psr.n_channels):
        col_delay = int(time_delay_to_quanta(calculate_dispersion_delay(ch, psr, ref_ch), psr.n_packet_integration))
        temp = np.array(np.roll(mask[ch, :], col_delay))
        mask[ch, :] = temp

    np.savetxt(get_pulse_mask_filename(ch_number, root_dirname, polarization, psr), np.transpose(mask), fmt='%1.1f')

    plt.figure("average pulse profile " + psr_name + " " + str(ch_number) + " " + polarization)
    plt.imshow(app, interpolation="nearest")
    plt.title("average pulse profile " + psr_name + " " + str(ch_number) + " " + polarization)

    plt.figure("Profile Mask " + psr_name + " " + str(ch_number) + " " + polarization)
    plt.imshow(mask, interpolation="nearest")
    plt.title("Profile Mask " + psr_name + " " + str(ch_number) + " " + polarization)
    plt.show()

    print("Now Computing Spectrum Template")

    plt.figure("average pulse profile " + psr_name + " " + str(ch_number) + " " + polarization)
    plt.imshow(app, interpolation="nearest")
    plt.title("Note start and end column " + psr_name + " " + str(ch_number) + " " + polarization)
    plt.show()

    col_start = int(input("Enter Starting Column (Refer Figure):"))
    col_end = int(input("Enter End Column (Refer Figure):"))

    spec_template = np.mean(app[:, col_start:col_end],axis=1)
    spec_template[spec_template == 0] = np.nan
    plt.plot(spec_template)
    plt.show()

    np.savetxt(get_avg_spectrum_template_filename(ch_number, root_dirname, polarization, psr), spec_template)
    quit()


def get_pulse_mask_filename(channel_number, root_dirname, polarization, psr):
    return root_dirname + f"OutputData/{psr.psr_name_date_time}/AveragePulseProfile/ch0{str(channel_number)}/" + \
           f"ch0{str(channel_number)}_{psr.psr_name_date_time}" + '_pulse_mask_' + polarization + ".prof"


def get_avg_spectrum_template_filename(channel_number, root_dirname, polarization, psr):
    return root_dirname + f"OutputData/{psr.psr_name_date_time}/AveragePulseProfile/ch0{str(channel_number)}/" + \
           f"ch0{str(channel_number)}_{psr.psr_name_date_time}" + '_avg_spectrum_' + polarization + ".prof"

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])  # B0834+06_20090725_114903 ch03 XX
