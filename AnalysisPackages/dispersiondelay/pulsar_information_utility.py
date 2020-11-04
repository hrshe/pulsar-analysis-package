"""
To perform the following tasks:
1) get central frequency and option to populate in resources
2) get packet number delay for dispersion and option to populate in resources

Also holds the information in resources to be used in actual code
"""
import os
from pathlib import Path
import numpy as np
import configparser

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


class PulsarInformationUtility:
    def __init__(self, mbr_pulsar_name_date_time):
        self.psr_name = mbr_pulsar_name_date_time

    def all_channels_central_frequency(self, populate_config=True, populate_resources_file=False):
        root_dirname = str(Path(__file__).parent.parent.parent.absolute())
        config_filename = root_dirname + '/AnalysisPackages/resources/config.txt'
        output_filename = (root_dirname + "/AnalysisPackages/resources/ChannelVsDispersionPacketDelay_"
                           + self.psr_name + ".txt")

        if populate_config:
            config.read(config_filename)
            print("populate_config set to True. " + config_filename + " will be updated")
        else:
            print("populate_config set to False. " + config_filename + " will not be updated")

        if populate_resources_file:
            output_filename = str(root_dirname +
                                  "/AnalysisPackages/resources/ChannelVsDispersionPacketDelay_"
                                  + self.psr_name + ".txt")
            with open(output_filename, "w") as output_file:
                output_file.truncate(0)
            print("populate_resources_file set to True. " + output_filename + " will be updated\n\n")
        else:
            print("populate_resources_file set to False. " + output_filename + " will not be updated\n\n")

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
            central_freq = lo_freq - get_intermediate_frequency(channel_number)
            print("ch:0" + str(channel_number) + "	LO: " + str(lo_freq) + "	CF: "
                  + str(central_freq))
            if populate_resources_file:
                with open(output_filename, "a") as output_file:
                    output_file.write(str(channel_number) + "\t" + str(central_freq) + "\n")
            if populate_config:
                config_set_central_frequency(channel_number, central_freq)
            output_array.append([channel_number, central_freq])
        config_write(config_filename)
        return output_array


psr = PulsarInformationUtility("B0834+06_20090725_114903")
print(np.array(psr.all_channels_central_frequency(False, False)))
