import numpy as np
import configparser
from pathlib import Path

"""
Purpose of this file is to execute rough patches of code... Not to be included in final project
"""

from AnalysisPackages.utilities.bcolors import bcolors
from AnalysisPackages.utilities.pulsar_information_utility import PulsarInformationUtility, BandSpecificConfig

config = configparser.ConfigParser()


def read_config(filename):
    config.read(filename)
    print("\n\n" + filename + " config file read into configparser")


def time_delay_2_col_delay(t):
    return t * (32150 / 512)


def calculate_time_delay(dm, band, reference_band):
    return 4.15 * 1000000 * dm * ((1 / get_band_upper_freq(band)) ** 2 - (1 / get_band_upper_freq(reference_band)) ** 2)


def get_band_upper_freq(band):  # in MHz
    try:
        bw = float(config.get('channel-' + str(band) + '-specific', 'sampling_frequency')) / 2
        cf = float(config.get('channel-' + str(band) + '-specific', 'central_frequency'))
    except configparser.NoSectionError:
        print('section ' + '[channel-' + str(band) + '-specific] does not exist... skipping')
    return cf + (bw / 2)


def config_write(filename):
    with open(filename, 'w') as configfile:
        config.write(configfile)


def config_set_sync_dispersion_delay_packet_frequency(channel_number, sync_dispersion_delay_packet):
    try:
        config.set('channel-' + str(channel_number) + '-specific', 'sync_dispersion_delay_packet',
                   str(sync_dispersion_delay_packet))
    except configparser.NoSectionError:
        print('[channel-' + str(channel_number) + '-specific] section not found. Creating new section')
        config['channel-' + str(channel_number) + '-specific'] = {
            'sync_dispersion_delay_packet': str(sync_dispersion_delay_packet)}


def populate_all_channels_sync_dispersion_delay_packet():
    root_dirname = str(Path(__file__).parent.parent.parent.absolute())
    config_filename = root_dirname + '/AnalysisPackages/resources/config.txt'
    read_config(config_filename)
    ref_band = 9
    n_channels = int(config.get('pulsar-config', 'n_channels'))
    dm = float(config.get('pulsar-config', 'dm'))
    time_delay = np.zeros(n_channels)

    # for i in range(9):
    #     time_delay[0, i] = calculate_time_delay(dm, i + 1, ref_band)  # other dm is 5.7

    print("Skip packets for dispersion delay compensation:")
    for i in range(n_channels):
        time_delay[i] = time_delay_2_col_delay(calculate_time_delay(dm, i + 1, ref_band))
        print("ch:" + str(i + 1) + "	" + str(time_delay[i]))

    for i in range(1, n_channels + 1):
        config_set_sync_dispersion_delay_packet_frequency(i, int(time_delay[i - 1]))
    config_write(config_filename)


# config_filename = root_dirname + '/AnalysisPackages/resources/config.txt'
# read_config(config_filename)
#
# band_specific = {f'band_{n}': dict(config.items(f'channel-{n}-specific')) for n in range(1, 10)}
# print(band_specific)
#
psr = PulsarInformationUtility("B0834+06_20090725_114903")
band_data: BandSpecificConfig = psr.band[2]

band_data.sampling_frequency
print(band_data.sampling_frequency)
print(psr.dm)
print(psr.psr_name)

# print(f"{bcolors.HEADER}\nconfig file path: {config_filename}")
# print(f"current config file contents: \n{bcolors.ENDC}")
# with open(config_filename, "r") as config_file:
#     print(config_file.read())
# while (True):
#     valid_option = True
#     print(f"{bcolors.HEADER}Verify contents and select options to populate missing contents")
#     print(f"1. Populate central frequency for all bands in config.txt")
#     print(f"2. Populate sampling frequency and first packet for all bands in config.txt")
#     print(f"3. Populate packets to skip for dispersion delay synchronization across bands in config.txt")
#     print(f"4. Do all{bcolors.ENDC}")
#     print(f"{bcolors.OKGREEN}5. Exit(enter Q or 5){bcolors.ENDC}")
#     print(
#         f"{bcolors.OKBLUE}NOTE: sampling frequency and central frequency are required in config.txt for dispersion delay "
#         f"synchronization(Option 3){bcolors.ENDC}")
#
#     print("Enter your option: ")
#     option = input()
#
#     if option.lower() == 'q' or (option.isnumeric() and int(option) == 5):
#         print("Bye!")
#         break
#     elif option.isnumeric():
#         if int(option) == 1:
#             print(f"executing option {option}\n")
#         elif int(option) == 2:
#             print(f"executing option {option}\n")
#         elif int(option) == 3:
#             print(f"executing option {option}\n")
#         elif int(option) == 4:
#             print(f"executing option {option}\n")
#         else:
#             valid_option = False
#     else:
#         valid_option = False
#
#     if not valid_option:
#         print(f"Invalid input: \"{option}\"\nEnter valid input(1,2,3,4,5,Q,q)")
#
#     if valid_option:
#         print(f"Option {option} execution complete. Printing new config\n")
#         with open(config_filename, "r") as config_file:
#             print(config_file.read())
