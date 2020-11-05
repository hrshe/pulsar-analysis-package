"""
Packet level synchronization for all channels.
Also populates sampling frequency and first packet in config.txt and resources file for particular channel.

Input:
MBR data files should be present channel wise in MBRData directory.
Accepts mbr file name details without the sequence number as input.
Example command to run from project root for mbr data B0834+06_20090725_114903:
> python3 -m AnalysisPackages.synchronization.synchronization_all B0834+06_20090725_114903

Output:
Channel number and first packet of synchronization for all channels is saved in the path:
        AnalysisPackages/resources/ChannelVsFirstPacket_B0834+06_20090725_114903.txt
"""
import os
import sys
from AnalysisPackages.synchronization import synchronization_single
from pathlib import Path


def main(psrDetails):
    psr_name = psrDetails[0:8]
    date = psrDetails[9:17]
    time = psrDetails[18:22]

    print("")
    print("PSR name : " + psr_name)
    print("Date 	 : " + date)
    print("Time	 : " + time)

    dirname = Path(__file__).parent.parent.absolute()
    output_file = open(str(dirname) + "/resources/ChannelVsFirstPacket_" + psrDetails + ".txt", "w")
    output_file.truncate(0)
    output_file.close()

    for channelNumber in range(1, 10):
        if not os.path.exists(str(dirname.parent) + "/MBRData/ch0" + str(channelNumber)):
            print("PATH NOT FOUND: " + str(dirname.parent) + "/MBRData/ch0" + str(channelNumber))
            print("Continuing to next available channel number")
            continue

        print("\n\n")
        print("###############################################")
        print("##  Synchronization Task Starting for Ch:0" + str(channelNumber) + "  ##")
        print("###############################################")
        synchronization_single.main("MBRData/ch0" + str(channelNumber) + "/ch0" + str(channelNumber) + "_" + psrDetails,
                                    populate_config=True)
        print("################################################")
        print("##  Synchronization Task Completed for Ch:0" + str(channelNumber) + "  ##")
        print("################################################")


if __name__ == '__main__':
    main(sys.argv[1])  # B0834+06_20090725_114903
