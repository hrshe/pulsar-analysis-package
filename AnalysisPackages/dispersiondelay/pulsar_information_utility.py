"""
To perform the following tasks:
1) get central frequency and option to populate in resources
2) get packet number delay for dispersion and option to populate in resources

Also holds the information in resources to be used in actual code
"""
import os
import numpy as np
from pathlib import Path
import configparser
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


def populate_config(filename):
    config.read(filename)
    print("\n\n" + filename + " will be updated")


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


class PulsarInformationUtility:
    def __init__(self, mbr_pulsar_name_date_time):
        self.root_dirname = str(Path(__file__).parent.parent.parent.absolute())
        self.config_filename = self.root_dirname + '/AnalysisPackages/resources/config.txt'
        config.read(self.config_filename)
        self.psr_name = mbr_pulsar_name_date_time
        self.dm = float(config.get('pulsar-config', 'dm'))
        self.n_channels = int(config.get('pulsar-config', 'n_channels'))

    """
    returns a dictionary of channel_number and central_frequency as key(int):value(float) pairs
    
    eg: {1: 120, 2: 172, 3: 233, 4: 330}
    cf.get(3) gives 233.0.
    """

    def populate_all_channels_central_frequency_in_config(self, populate_config=True, populate_resources_file=False):
        root_dirname = self.root_dirname
        config_filename = self.config_filename
        output_filename = (root_dirname + "/AnalysisPackages/resources/ChannelVsDispersionPacketDelay_"
                           + self.psr_name + ".txt")

        populate_resources_setup(self.psr_name, config_filename, output_filename, populate_config,
                                 populate_resources_file, root_dirname)

        output_array = []
        input_dirname = str(root_dirname + "/MBRData")
        print("input directory name : ", input_dirname)

        for channel_number in range(1, 10):
            if not os.path.exists(str(input_dirname) + "/ch0" + str(channel_number)):
                print("PATH NOT FOUND: " + str(input_dirname) + "/ch0" + str(channel_number))
                print("Continuing to next available channel number\n")
                continue

            mbr_filename = input_dirname + "/ch0" + str(channel_number) + "/ch0" + str(
                channel_number) + "_" + self.psr_name + "_000.mbr"
            print("\nreading file         : ", mbr_filename)
            file = open(mbr_filename, "rb")
            file.read(22)
            lo_freq = int.from_bytes(file.read(2), byteorder='big')
            central_freq = float(lo_freq - get_intermediate_frequency(channel_number))
            print("ch:0" + str(channel_number) + "	LO: " + str(lo_freq) + "	CF: "
                  + str(central_freq))

            populate_resources(central_freq, channel_number, output_filename, populate_config,
                               populate_resources_file)
            output_array.append([channel_number, central_freq])

        if populate_config:
            config_write(config_filename)

        return dict(output_array)

    def populate_all_channels_sampling_frequency_and_first_packet_in_config(self):
        synchronization_all.main(self.psr_name)

    def populate_all_channels_sync_dispersion_delay_packet(self):
        populate_config(self.config_filename)
        ref_band = 9
        n_channels = self.n_channels
        dm = self.dm
        time_delay = np.zeros(n_channels)

        # for i in range(9):
        #     time_delay[0, i] = calculate_time_delay(dm, i + 1, ref_band)  # other dm is 5.7

        print("Skip packets for dispersion delay compensation:")
        for i in range(n_channels):
            time_delay[i] = time_delay_2_col_delay(calculate_time_delay(dm, i + 1, ref_band))
            print("ch:" + str(i + 1) + "	" + str(time_delay[i]))

        for i in range(1, n_channels + 1):
            config_set_sync_dispersion_delay_packet_frequency(i, int(time_delay[i - 1]))
        config_write(self.config_filename)


psr = PulsarInformationUtility("B0834+06_20090725_114903")
cf = psr.populate_all_channels_central_frequency_in_config(False, False)
print(cf)
print(cf.get(3))

psr.populate_all_channels_sampling_frequency_and_first_packet_in_config()
psr.populate_all_channels_sync_dispersion_delay_packet()
