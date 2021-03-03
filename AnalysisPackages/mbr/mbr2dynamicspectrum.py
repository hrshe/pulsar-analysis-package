"""
Performs the following tasks:
1) Reads properties from config.txt
2) Divides single mbr file into n parts for processing
3) Computes the intensity dynamic spectra for X.Conjugate(X), Y.Conjugate(Y), real(X.Conjugate(Y)) and imaginary(X.Conjugate(Y))
    where X and Y correspond to spectrum for X polarization and Y polarization.
    More clarity can be found in section 3.3 in Drifting_Subpulse_Thesis.pdf
4) Saves this in output directory

Usage:
Run the following to view help on all optional comman line arguments
> python3 -m AnalysisPackages.mbr.mbr2dynamicspectrum -h

In most cases, we will run:
> python3 -m AnalysisPackages.mbr.mbr2dynamicspectrum ch03_B0834+06_20090725_114903

All optional parameters set to true:
> python3 -m AnalysisPackages.mbr.mbr2dynamicspectrum ch03_B0834+06_20090725_114903 -packetSynch -plotXX -plotYY -plotRealXY -plotImagXY -runPsrUtility -psrUtil
"""
import warnings
import time
import numpy as np
import argparse

from AnalysisPackages.mbr import packet
from os.path import getsize, isfile
from pathlib import Path
from AnalysisPackages.utilities.pulsar_information_utility import PulsarInformationUtility


def main(file_name, synchronization_flag=False, plot_dynamic_spectrum_flag_xx=False,
         plot_dynamic_spectrum_flag_yy=False, plot_dynamic_spectrum_flag_realxy=False,
         plot_dynamic_spectrum_flag_imagxy=False, pulsar_information_utility_flag=False, timer_flag=False):
    psr = PulsarInformationUtility(file_name[5:])  # "B0834+06_20090725_114903"

    if pulsar_information_utility_flag:
        # todo -> print config and ask to run()
        psr.run()

    # declare variables and constants
    seq_number = 0
    global_packet_count = 0
    first_packet_flag = True
    channel_number = int(file_name[2:4])
    root_dirname = str(Path(__file__).parent.parent.parent.absolute()) + '/'
    current_mbr_filename = get_mbr_filename(root_dirname, file_name, channel_number, seq_number)
    mbr_filesize = getsize(current_mbr_filename)
    packets_in_mbr_file = int(mbr_filesize / packet.packetSize)
    missing_packets_array = np.empty(psr.n_channels * 2)
    missing_packets_array.fill(np.nan)
    skip_to_n_packets = int(psr.band[channel_number].sync_first_packet) + \
                        int(psr.band[channel_number].sync_dispersion_delay_packet)
    plot_dynamic_spectra_flag = plot_dynamic_spectrum_flag_xx or plot_dynamic_spectrum_flag_yy or \
                                plot_dynamic_spectrum_flag_realxy or plot_dynamic_spectrum_flag_yy

    if timer_flag:
        time_arr = []
    while True:
        mbr_file = read_mbr_file(current_mbr_filename)

        for part_i in range(psr.n_parts):
            if timer_flag:
                start = time.perf_counter()
                print("timer started")

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

            empty_dynamic_sequence = np.empty(
                (packet_list[-1].packetNumber - zeroth_packet_number + 1, psr.n_channels * 2))
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
            # this can be an object and method
            dynamic_spectrum_cross, dynamic_spectrum_x, dynamic_spectrum_y = integrate_dynamic_spectrum_all(
                dynamic_spectrum_cross, dynamic_spectrum_x, dynamic_spectrum_y,
                missing_packets_array, psr.n_channels, psr.n_packet_integration)

            if plot_dynamic_spectra_flag:
                plot_dynamic_spectra_flag = plotting_util(dynamic_spectrum_cross, dynamic_spectrum_x,
                                                          dynamic_spectrum_y, plot_dynamic_spectra_flag,
                                                          plot_dynamic_spectrum_flag_imagxy,
                                                          plot_dynamic_spectrum_flag_realxy,
                                                          plot_dynamic_spectrum_flag_xx, plot_dynamic_spectrum_flag_yy)

            save_spec_file_all(channel_number, dynamic_spectrum_cross, dynamic_spectrum_x,
                               dynamic_spectrum_y, file_name, root_dirname, seq_number, psr)

            if timer_flag:
                timer_util(part_i, psr, start, time_arr)

        seq_number = seq_number + 1
        if not isfile(get_mbr_filename(root_dirname, file_name, channel_number, seq_number)) \
                or seq_number > psr.last_sequence_number:
            break


def timer_util(part_i, psr, start, time_arr):
    print(f"time taken for {part_i} is {str(time.perf_counter() - start)}")
    time_arr.append(time.perf_counter() - start)
    print(f"mean time for processing 1/{psr.n_parts} mbr file is: {np.mean(time_arr)}")


def plotting_util(dynamic_spectrum_cross, dynamic_spectrum_x, dynamic_spectrum_y, plot_dynamic_spectra_flag,
                  plot_dynamic_spectrum_flag_imagxy, plot_dynamic_spectrum_flag_realxy, plot_dynamic_spectrum_flag_xx,
                  plot_dynamic_spectrum_flag_yy):
    if plot_dynamic_spectrum_flag_xx:
        plot_DS(dynamic_spectrum_x)
    if plot_dynamic_spectrum_flag_yy:
        plot_DS(dynamic_spectrum_y)
    if plot_dynamic_spectrum_flag_realxy:
        plot_DS(np.real(dynamic_spectrum_cross))
    if plot_dynamic_spectrum_flag_imagxy:
        plot_DS(np.imag(dynamic_spectrum_cross))
    raw_input = input("plot dynamic spectra for next part? (Y/n)")
    if raw_input.lower() == "y":
        print("Dynamic spectra will be plotted in next part")
    elif raw_input.lower() == "n":
        plot_dynamic_spectra_flag = False
        print("Dynamic spectra will not be plotted in next part")
    else:
        plot_dynamic_spectra_flag = False
        print(f"Invalid input '{raw_input}'. Default value taken as 'n'.\n"
              f"Dynamic spectra will not be plotted in next part")
    return plot_dynamic_spectra_flag


def save_spec_file_all(channel_number, dynamic_spectrum_cross, dynamic_spectrum_x, dynamic_spectrum_y, file_name,
                       root_dirname, seq_number, psr):
    save_spec_file(channel_number, dynamic_spectrum_x, file_name, root_dirname, seq_number, "XX", psr)
    save_spec_file(channel_number, dynamic_spectrum_y, file_name, root_dirname, seq_number, "YY", psr)
    save_spec_file(channel_number, np.real(dynamic_spectrum_cross), file_name, root_dirname, seq_number, "realXY", psr)
    save_spec_file(channel_number, np.imag(dynamic_spectrum_cross), file_name, root_dirname, seq_number, "imagXY", psr)


def save_spec_file(channel_number, dynamic_spectrum, file_name, root_dirname, seq_number, polarization, psr):
    filename = open(get_output_filename(channel_number, root_dirname, seq_number, polarization, psr), "ab")
    np.savetxt(filename, dynamic_spectrum, fmt='%1.3f')
    print(f"saved SPEC file: {file_name}")
    filename.close()


def get_output_filename(channel_number, root_dirname, seq_number, polarization, psr):
    return root_dirname + f"OutputData/{psr.psr_name_date_time}/DynamicSpectrum/ch0{str(channel_number)}/" + \
           f"ch0{str(channel_number)}_{psr.psr_name_date_time}"  + '_' + polarization + '_' + "{0:0=3d}".format(seq_number) + ".spec"


def integrate_dynamic_spectrum_all(dynamic_spectrum_cross, dynamic_spectrum_x, dynamic_spectrum_y,
                                   missing_packets_array, n_channels, n_int):
    dynamic_spectrum_x = integrate_dynamic_spectrum(dynamic_spectrum_x, missing_packets_array, n_channels, n_int)
    dynamic_spectrum_y = integrate_dynamic_spectrum(dynamic_spectrum_y, missing_packets_array, n_channels, n_int)
    dynamic_spectrum_cross = integrate_dynamic_spectrum(dynamic_spectrum_cross, missing_packets_array, n_channels,
                                                        n_int)
    return dynamic_spectrum_cross, dynamic_spectrum_x, dynamic_spectrum_y


def integrate_dynamic_spectrum(dynamic_spectrum_x, missing_packets_array, n_channels, n_int):
    remainder = len(dynamic_spectrum_x) % n_int
    dynamic_spectrum_x = np.vstack([dynamic_spectrum_x, [missing_packets_array[:n_channels]] * (n_int - remainder)])
    dynamic_spectrum_x = dynamic_spectrum_x.reshape(n_int, -1, n_channels, order="F")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        dynamic_spectrum_x = np.nanmean(dynamic_spectrum_x, axis=0)
    return dynamic_spectrum_x


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
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file_name", type=str,
                        help="The mbr filename without the sequence number(eg. ch03_B0834+06_20090725_114903)")
    parser.add_argument("-s", "--packetSynch", help="Do packet level synchronization across bands", action="store_true")
    parser.add_argument("-plotXX", "--plotXX", help="plot dynamic spectrum for X polarization after processing each part "
                                                "of mbr file",
                        action="store_true")
    parser.add_argument("-plotYY", "--plotYY", help="plot dynamic spectrum for Y polarization after processing each part "
                                                "of mbr file",
                        action="store_true")
    parser.add_argument("-plotRealXY", "--plotRealXY", action="store_true",
                        help="plot dynamic spectrum for real part of cross (X.Conjugate(Y)) after processing each part of "
                             "mbr file")
    parser.add_argument("-plotImagXY", "--plotImagXY", action="store_true",
                        help="plot dynamic spectrum for imaginary part of cross (X.Conjugate(Y)) after processing each "
                             "part of mbr file")
    parser.add_argument("-psrUtil", "--psrUtil", help="run pulsar_information_utility for populating config file before "
                                                      "computing the dynamic spectra",
                        action="store_true")
    parser.add_argument("-t", "--timer", help="print time taken to process each part of mbr file",
                        action="store_true")

    args = parser.parse_args()
    main(args.input_file_name, args.packetSynch, args.plotXX, args.plotYY,
         args.plotRealXY, args.plotImagXY, args.psrUtil, args.timer)
