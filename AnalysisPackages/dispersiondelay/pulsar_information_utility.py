"""
To perform the following tasks:
1) get central frequency and populate in resources
2) get packet number delay for dispersion and populate in resources
"""
import os
from pathlib import Path
import numpy as np


def get_intermediate_frequency(channel_number):
    if channel_number in (1, 2):
        return 70
    return 140


class PulsarInformationUtility:
    def __init__(self, mbr_pulsar_name_date_time):
        self.psr_name = mbr_pulsar_name_date_time

    def all_channels_central_frequency(self, populate_resources=False):
        root_dirname = str(Path(__file__).parent.parent.parent.absolute())
        if populate_resources:
            output_filename = str(root_dirname +
                                  "/AnalysisPackages/resources/ChannelVsDispersionPacketDelay_"
                                  + self.psr_name + ".txt")
            print("output file name     : ", output_filename)
            output_file = open(output_filename, "w")
            output_file.truncate(0)
            output_file.close()

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
            if populate_resources:
                output_file = open(output_filename, "a")
                output_file.write(str(channel_number) + "\t" + str(central_freq)+"\n")
                output_file.close()
            output_array.append([channel_number, central_freq])

        return output_array


psr = PulsarInformationUtility("B0834+06_20090725_114903")
print(np.array(psr.all_channels_central_frequency()))
