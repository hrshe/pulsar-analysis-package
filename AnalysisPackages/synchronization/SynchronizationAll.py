import os
import sys
from pathlib import Path

psrDetails = sys.argv[1]  # B0834+06_20090725_114903
psr_name = psrDetails[0:8]
date = psrDetails[9:17]
time = psrDetails[18:22]

print("")
print("PSR name 	: " + psr_name)
print("Date 	: " + date)
print("Time	: " + time)
print()

dirname = Path(__file__).parent.parent.absolute()
output_file = open(str(dirname)+"/resources/ChannelVsFirstPacket_" + psrDetails + ".txt", "w")
output_file.truncate(0)
output_file.close()

for channelNumber in range(1,10):
    if not os.path.exists(str(dirname.parent)+"/MBRData/ch0" + str(channelNumber)):
        print("PATH NOT FOUND: "+str(dirname.parent)+"/MBRData/ch0" + str(channelNumber))
        print("Continuing to next available channel number")
        continue

    print("\n\n")
    print("###############################################")
    print("##  Synchronization Task Starting for Ch:0"+str(channelNumber)+"  ##")
    print("###############################################")

    os.system(
        "python3 "+str(dirname)+"/synchronization/synchronization.py MBRData/ch0" + str(channelNumber) + "/ch0" + str(
            channelNumber) + "_" + psrDetails)
    print("################################################")
    print("##  Synchronization Task Completed for Ch:0"+str(channelNumber)+"  ##")
    print("################################################")
