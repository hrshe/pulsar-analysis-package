"""
To perform the following tasks:
1) get central frequency and option to populate in resources
2) get packet number delay for dispersion and option to populate in resources

Also holds the information in resources to be used in actual code
"""
import os
import sys

import numpy as np
from pathlib import Path
import configparser

from AnalysisPackages.resources.bcolors import bcolors
from AnalysisPackages.synchronization import synchronization_all

config = configparser.ConfigParser()


def get_intermediate_frequency(channel_number):
    if channel_number in (1, 2):
        return 70
    return 140


def config_write(filename):
    with open(filename, 'w') as configfile:
        config.write(configfile)


def config_set_central_frequency(channel_number, central_freq):
    try:
        config.set('channel-' + str(channel_number) + '-specific', 'central_frequency', str(central_freq))
    except configparser.NoSectionError:
        print('[channel-' + str(channel_number) + '-specific] section not found. Creating new section')
        config['channel-' + str(channel_number) + '-specific'] = {'central_frequency': str(central_freq)}


def populate_resources(central_freq, channel_number, output_filename, populate_config,
                       populate_resources_file):
    if populate_resources_file:
        with open(output_filename, "a") as output_file:
            output_file.write(str(channel_number) + "\t" + str(central_freq) + "\n")
    if populate_config:
        config_set_central_frequency(channel_number, central_freq)


def populate_resources_setup(psr_name, config_filename, output_filename, populate_config, populate_resources_file,
                             root_dirname):
    if populate_config:
        config.read(config_filename)
        print("populate_config set to True. " + config_filename + " will be updated")
    else:
        print("populate_config set to False. " + config_filename + " will not be updated")
    if populate_resources_file:
        output_filename = str(root_dirname +
                              "/AnalysisPackages/resources/ChannelVsDispersionPacketDelay_"
                              + psr_name + ".txt")
        with open(output_filename, "w") as output_file:
            output_file.truncate(0)
        print("populate_resources_file set to True. " + output_filename + " will be updated\n\n")
    else:
        print("populate_resources_file set to False. " + output_filename + " will not be updated\n\n")


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


def config_set_sync_dispersion_delay_packet_frequency(channel_number, sync_dispersion_delay_packet):
    try:
        config.set('channel-' + str(channel_number) + '-specific', 'sync_dispersion_delay_packet',
                   str(sync_dispersion_delay_packet))
    except configparser.NoSectionError:
        print('[channel-' + str(channel_number) + '-specific] section not found. Creating new section')
        config['channel-' + str(channel_number) + '-specific'] = {
            'sync_dispersion_delay_packet': str(sync_dispersion_delay_packet)}


def print_run_options():
    print(f"{bcolors.HEADER}Verify contents and select options to populate missing contents")
    print(f"1. Populate central frequency for all bands in config.txt")
    print(f"2. Populate sampling frequency and first packet for all bands in config.txt")
    print(f"3. Populate packets to skip for dispersion delay synchronization across bands in config.txt")
    print(f"4. Do all{bcolors.ENDC}")
    print(f"{bcolors.OKGREEN}5. Exit(enter Q or 5){bcolors.ENDC}")
    print(
        f"{bcolors.OKBLUE}NOTE: sampling frequency and central frequency are required in config.txt for "
        f"dispersion delay synchronization(Option 3){bcolors.ENDC}")
    print("Enter your option: ")


class PulsarInformationUtility:
    def __init__(self, mbr_pulsar_name_date_time):
        self.root_dirname = str(Path(__file__).parent.parent.parent.absolute())
        self.config_filename = self.root_dirname + '/AnalysisPackages/resources/config.txt'
        config.read(self.config_filename)
        self.psr_name_date_tine = mbr_pulsar_name_date_time
        self.psr_name = mbr_pulsar_name_date_time[:9]

        self.period = float(config.get('pulsar-config', 'period'))
        self.dm = float(config.get('pulsar-config', 'dm'))
        self.n_bands = int(config.get('pulsar-config', 'n_bands'))

        self.n_packet_integration = int(config.get('general-config', 'n_packet_integration'))
        self.last_sequence_number = int(config.get('general-config', 'last_sequence_number'))
        self.n_channels = int(config.get('general-config', 'n_channels'))

        self.set_band_specific_from_config()

    def set_band_specific_from_config(self):
        read_config(self.config_filename)
        try:
            self.band_specific = {f'band{n}': dict(config.items(f'channel-{n}-specific')) for n in range(1, 10)}
        except configparser.NoSectionError:
            print(f"{bcolors.WARNING}\nChannel specific section missing... Check config.txt or use run() method "
                  f"of this class to repopulate config.txt{bcolors.ENDC}")

    """
    returns a dictionary of channel_number and central_frequency as key(int):value(float) pairs
    
    eg: {1: 120, 2: 172, 3: 233, 4: 330}
    cf.get(3) gives 233.0.
    """
    def populate_all_channels_central_frequency_in_config(self, populate_config_flag=True,
                                                          populate_resources_file_flag=False):
        print(f"{bcolors.HEADER}Populating central frequency...\n{bcolors.ENDC}")
        root_dirname = self.root_dirname
        config_filename = self.config_filename
        output_filename = (root_dirname + "/AnalysisPackages/resources/ChannelVsDispersionPacketDelay_"
                           + self.psr_name_date_tine + ".txt")

        populate_resources_setup(self.psr_name_date_tine, config_filename, output_filename, populate_config_flag,
                                 populate_resources_file_flag, root_dirname)

        output_array = []
        input_dirname = str(root_dirname + "/MBRData")
        print("input directory name : ", input_dirname)

        for channel_number in range(1, 10):
            if not os.path.exists(str(input_dirname) + "/ch0" + str(channel_number)):
                print("PATH NOT FOUND: " + str(input_dirname) + "/ch0" + str(channel_number))
                print("Continuing to next available channel number\n")
                continue

            mbr_filename = input_dirname + "/ch0" + str(channel_number) + "/ch0" + str(
                channel_number) + "_" + self.psr_name_date_tine + "_000.mbr"
            print("\nreading file         : ", mbr_filename)
            file = open(mbr_filename, "rb")
            file.read(22)
            lo_freq = int.from_bytes(file.read(2), byteorder='big')
            central_freq = float(lo_freq - get_intermediate_frequency(channel_number))
            print("ch:0" + str(channel_number) + "	LO: " + str(lo_freq) + "	CF: "
                  + str(central_freq))

            populate_resources(central_freq, channel_number, output_filename, populate_config_flag,
                               populate_resources_file_flag)
            output_array.append([channel_number, central_freq])

        if populate_config_flag:
            config_write(config_filename)

        return dict(output_array)

    def populate_all_channels_sampling_frequency_and_first_packet_in_config(self):
        print(f"{bcolors.HEADER}Populating sampling frequency and first packet...\n{bcolors.ENDC}")
        synchronization_all.main(self.psr_name_date_tine)

    def populate_all_channels_sync_dispersion_delay_packet(self):
        print(f"{bcolors.HEADER}Populating dispersion delay packet sync...\n{bcolors.ENDC}")
        read_config(self.config_filename)
        ref_band = 9
        n_bands = self.n_bands
        dm = self.dm
        time_delay = np.zeros(n_bands)

        print("Skip packets for dispersion delay compensation:")
        for i in range(n_bands):
            time_delay[i] = time_delay_2_col_delay(calculate_time_delay(dm, i + 1, ref_band))
            print("ch:" + str(i + 1) + "	" + str(time_delay[i]))

        for i in range(1, n_bands + 1):
            config_set_sync_dispersion_delay_packet_frequency(i, int(time_delay[i - 1]))
        config_write(self.config_filename)

    def run(self):
        config_filename = self.config_filename
        print(f"{bcolors.HEADER}\nconfig file path: {config_filename}")
        print(f"current config file contents: \n{bcolors.ENDC}")

        with open(config_filename, "r") as config_file:
            print(config_file.read())

        while True:
            valid_option = True
            print_run_options()
            option = input()
            if option.lower() == 'q' or (option.isnumeric() and int(option) == 5):
                print("\n*** Bye! ***\n")
                break
            if option.isnumeric():
                if int(option) == 1:
                    self.populate_all_channels_central_frequency_in_config()
                elif int(option) == 2:
                    self.populate_all_channels_sampling_frequency_and_first_packet_in_config()
                elif int(option) == 3:
                    self.populate_all_channels_sync_dispersion_delay_packet()
                elif int(option) == 4:
                    self.populate_all_channels_central_frequency_in_config()
                    self.populate_all_channels_sampling_frequency_and_first_packet_in_config()
                    self.populate_all_channels_sync_dispersion_delay_packet()
                else:
                    valid_option = False
            else:
                valid_option = False

            if not valid_option:
                print(f"Invalid input: \"{option}\"\nEnter valid input(1,2,3,4,5,Q,q)\n8")

            if valid_option:
                print(f"Option {option} execution complete. Printing new config\n")
                with open(config_filename, "r") as config_file:
                    print(config_file.read())


def main(file_name):
    psr = PulsarInformationUtility(file_name)  # "B0834+06_20090725_114903"
    print(psr.dm)
    psr.run()

if __name__ == '__main__':
    main(sys.argv[1])

# psr = PulsarInformationUtility("B0834+06_20090725_114903")
# cf = psr.populate_all_channels_central_frequency_in_config(False, False)
# print(cf)
# print(cf.get(3))
#
# psr.populate_all_channels_sampling_frequency_and_first_packet_in_config()
# psr.populate_all_channels_sync_dispersion_delay_packet()
