packetSize = 1056
headerSize = 32
dataSize = 1024


def mbr2packetList(byteData):
    if len(byteData) % packetSize == 0:  # todo - can be made efficient since modulo is expensive?
        return [Packet(byteData[i: i + packetSize]) for i in range(0, len(byteData), packetSize)]
    raise ValueError("incomplete packet found")


class Packet:
    def __init__(self, byteData):
        self.lo_freq = int.from_bytes(byteData[22:24], byteorder='big')
        self.packetNumber = int.from_bytes(byteData[28:32], byteorder='big')
        self.xpolarizationdata = list(byteData[headerSize::2])
        self.ypolarizationdata = list(byteData[headerSize + 1::2])
