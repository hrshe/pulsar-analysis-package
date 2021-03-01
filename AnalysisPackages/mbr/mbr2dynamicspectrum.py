import sys
import warnings

import matplotlib.pyplot as plt
import numpy as np

from mbr import packet
from os.path import getsize, isfile
from pathlib import Path
from utilities.pulsar_information_utility import PulsarInformationUtility


def main(file_name, pulsar_information_utility_flag=False):
    psr = PulsarInformationUtility(file_name[5:])  # "B0834+06_20090725_114903"

    if pulsar_information_utility_flag:
        # todo -> print config and ask to run()
        psr.run()

    # declare variables and constants
    seq_number = 0
    global_packet_count = 0
    first_packet_flag = True
    synchronization_flag = False
    channel_number = int(file_name[2:4])
    root_dirname = str(Path(__file__).parent.parent.parent.absolute()) + '/'
    current_mbr_filename = get_mbr_filename(root_dirname, file_name, channel_number, seq_number)
    mbr_filesize = getsize(current_mbr_filename)
    packets_in_mbr_file = int(mbr_filesize / packet.packetSize)
    missing_packets_array = np.empty(psr.n_channels * 2)
    missing_packets_array.fill(np.nan)
    skip_to_n_packets = int(psr.band[channel_number].sync_first_packet) + \
                        int(psr.band[channel_number].sync_dispersion_delay_packet)

    while True:
        mbr_file = read_mbr_file(current_mbr_filename)

        for part_i in range(psr.n_parts):
            print_count = 0  # todo just for printing status of completion(can add a status bar)

            packet_list = packet.mbr2packetList(mbr_file.read(int(mbr_filesize / psr.n_parts)))
            print("packets read")

            zeroth_packet_number = packet_list[0].packetNumber

            if synchronization_flag:
                # skip whole part if skip_n_packets > last_packet_number
                # todo check this logic
                if skip_to_n_packets > packet_list[-1].packetNumber:
                    continue
                else:
                    if skip_to_n_packets >= packet_list[0].packetNumber:
                        zeroth_packet_number = skip_to_n_packets
                    else:
                        zeroth_packet_number = packet_list[0].packetNumber

            empty_dynamic_sequence = np.empty((packet_list[-1].packetNumber - zeroth_packet_number + 1, psr.n_channels * 2))
            empty_dynamic_sequence.fill(np.nan)
            x_polarization_dynamic_seq = np.array(empty_dynamic_sequence, copy=True)
            y_polarization_dynamic_seq = np.array(empty_dynamic_sequence, copy=True)

            dynamic_sequence_packet_count = 0

            for pkt in packet_list:
                current_pkt_number = pkt.packetNumber
                if synchronization_flag:
                    if current_pkt_number < skip_to_n_packets:
                        continue

                if print_count % 25000 == 1:  # todo add status bar
                    print("Ch:" + str(channel_number) + "	Seq Number:" + str(seq_number) + "		" +
                          "{:.2f}".format(((packets_in_mbr_file / psr.n_parts) * part_i + dynamic_sequence_packet_count)
                                          * 100 / packets_in_mbr_file)
                          + "% complete")
                print_count = print_count + 1

                if not first_packet_flag:
                    if global_packet_count != current_pkt_number:
                        # if missing packet, increase global count and col count, ie dynamic_sequence_packet_count
                        dynamic_sequence_packet_count = current_pkt_number - zeroth_packet_number
                        global_packet_count = current_pkt_number

                        # add read packet data to dynamic seq array
                        dynamic_sequence_packet_count, global_packet_count = write_packet_data_to_dynamic_sequence(
                            dynamic_sequence_packet_count, global_packet_count, pkt, x_polarization_dynamic_seq,
                            y_polarization_dynamic_seq)

                        # todo handle edge condition where missing packets between two mbr files

                    else:
                        dynamic_sequence_packet_count, global_packet_count = write_packet_data_to_dynamic_sequence(
                            dynamic_sequence_packet_count, global_packet_count, pkt, x_polarization_dynamic_seq,
                            y_polarization_dynamic_seq)

                elif first_packet_flag:
                    first_packet_number = current_pkt_number
                    global_packet_count = current_pkt_number
                    first_packet_flag = False

                    # add read packet data to dynamic seq array
                    dynamic_sequence_packet_count, global_packet_count = write_packet_data_to_dynamic_sequence(
                        dynamic_sequence_packet_count, global_packet_count, pkt, x_polarization_dynamic_seq,
                        y_polarization_dynamic_seq)

            # do fft for dyn seq to get dynamic spectra
            dynamic_spectrum_cross, dynamic_spectrum_x, dynamic_spectrum_y = compute_dynamic_spectrum_all(
                x_polarization_dynamic_seq, y_polarization_dynamic_seq)

            # remove first and last 5 columns
            clean_dynamic_spectrum_all(dynamic_spectrum_cross, dynamic_spectrum_x, dynamic_spectrum_y)

            # integrate this dynamic spectrum
            dynamic_spectrum_cross, dynamic_spectrum_x, dynamic_spectrum_y = integrate_dynamic_spectrum_all(
                    dynamic_spectrum_cross, dynamic_spectrum_x, dynamic_spectrum_y,
                    missing_packets_array, psr.n_channels, psr.n_packet_integration)

            # uncomment to plot dynamic spectrum
            # plot_DS(integrated_dynamic_spectrum)

            save_spec_file_all(channel_number, dynamic_spectrum_cross, dynamic_spectrum_x, dynamic_spectrum_y,
                               file_name, root_dirname, seq_number)

        seq_number = seq_number + 1
        if not isfile(get_mbr_filename(root_dirname, file_name, channel_number, seq_number)) \
                or seq_number > psr.last_sequence_number:
            break


def save_spec_file_all(channel_number, dynamic_spectrum_cross, dynamic_spectrum_x, dynamic_spectrum_y, file_name,
                       root_dirname, seq_number):
    save_spec_file(channel_number, dynamic_spectrum_x, file_name, root_dirname, seq_number, "XX")
    save_spec_file(channel_number, dynamic_spectrum_y, file_name, root_dirname, seq_number, "YY")
    save_spec_file(channel_number, np.real(dynamic_spectrum_cross), file_name, root_dirname, seq_number, "realXY")
    save_spec_file(channel_number, np.imag(dynamic_spectrum_cross), file_name, root_dirname, seq_number, "imagXY")


def save_spec_file(channel_number, dynamic_spectrum, file_name, root_dirname, seq_number, polarization):
    filename = open(get_output_filename(channel_number, file_name, root_dirname, seq_number, polarization), "ab")
    np.savetxt(filename, dynamic_spectrum, fmt='%1.3f')
    print(f"saved SPEC file: {file_name}")
    filename.close()


def get_output_filename(channel_number, file_name, root_dirname, seq_number, polarization):
    return root_dirname + f"OutputData/DynamicSpectrum/ch0{str(channel_number)}/" + file_name + '_'+polarization+'_' + "{0:0=3d}".format(seq_number) + ".spec"


def integrate_dynamic_spectrum_all(dynamic_spectrum_cross, dynamic_spectrum_x, dynamic_spectrum_y,
                                   missing_packets_array, n_channels, n_int):
    dynamic_spectrum_x = integrate_dynamic_spectrum(dynamic_spectrum_x, missing_packets_array, n_channels, n_int)
    dynamic_spectrum_y = integrate_dynamic_spectrum(dynamic_spectrum_y, missing_packets_array, n_channels, n_int)
    dynamic_spectrum_cross = integrate_dynamic_spectrum(dynamic_spectrum_cross, missing_packets_array, n_channels, n_int)
    return dynamic_spectrum_cross, dynamic_spectrum_x, dynamic_spectrum_y


def integrate_dynamic_spectrum(dynamic_spectrum_x, missing_packets_array, n_channels, n_int):
    remainder = len(dynamic_spectrum_x) % n_int
    dynamic_spectrum_x = np.vstack([dynamic_spectrum_x, [missing_packets_array[:n_channels]] * (n_int - remainder)])
    dynamic_spectrum_x = dynamic_spectrum_x.reshape(n_int, -1, n_channels, order="F")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        dynamic_spectrum_x = np.nanmean(dynamic_spectrum_x, axis=0)
    return dynamic_spectrum_x


def plot_DS(integrated_dynamic_spectrum):
    plt.imshow(np.transpose(integrated_dynamic_spectrum), interpolation="nearest", aspect='auto')
    plt.colorbar()
    plt.show()


def clean_dynamic_spectrum_all(dynamic_spectrum_cross, dynamic_spectrum_x, dynamic_spectrum_y):
    clean_dynamic_spectrum(dynamic_spectrum_x)
    clean_dynamic_spectrum(dynamic_spectrum_y)
    clean_dynamic_spectrum(dynamic_spectrum_cross)


def compute_dynamic_spectrum_all(x_polarization_dynamic_seq, y_polarization_dynamic_seq):
    dynamic_spectrum_x = compute_dynamic_spectrum(x_polarization_dynamic_seq)
    dynamic_spectrum_y = compute_dynamic_spectrum(y_polarization_dynamic_seq)
    dynamic_spectrum_cross = dynamic_spectrum_x * np.conj(dynamic_spectrum_y)

    return dynamic_spectrum_cross, abs(np.square(dynamic_spectrum_x)), abs(np.square(dynamic_spectrum_y))


def clean_dynamic_spectrum(dynamic_spectrum):
    dynamic_spectrum[:, 0] = 0
    dynamic_spectrum[:, 255] = 0


def compute_dynamic_spectrum(polarization_dynamic_seq):
    dynamic_spectrum = np.fft.fft2(polarization_dynamic_seq, axes=[1])[:, :256] / 512
    return dynamic_spectrum


def write_packet_data_to_dynamic_sequence(dynamic_sequence_packet_count, global_packet_count, pkt,
                                          x_polarization_dynamic_seq, y_polarization_dynamic_seq):
    x_polarization_dynamic_seq[dynamic_sequence_packet_count, :] = pkt.xpolarizationdata
    y_polarization_dynamic_seq[dynamic_sequence_packet_count, :] = pkt.ypolarizationdata
    global_packet_count = global_packet_count + 1
    dynamic_sequence_packet_count = dynamic_sequence_packet_count + 1
    return dynamic_sequence_packet_count, global_packet_count


def read_mbr_file(current_mbr_filename):
    print("Reading file	:" + current_mbr_filename)
    f1 = open(current_mbr_filename, 'rb')
    return f1


def get_mbr_filename(root_dirname, file_name, channel_number, seq_number):
    return root_dirname + f"MBRData/ch0{str(channel_number)}/" + \
           file_name + '_' + "{0:0=3d}".format(seq_number) + ".mbr"


if __name__ == '__main__':
    run_pulsar_information_utility_flag = False
    if sys.argv[2] == "True":
        run_pulsar_information_utility_flag = True
    main(sys.argv[1], run_pulsar_information_utility_flag)
