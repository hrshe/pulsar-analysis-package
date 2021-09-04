import sys

import numpy as np

from AnalysisPackages.utilities import utils

"""
Purpose of this file is to execute rough patches of code... Not to be included in final project
"""


def main():
    #band_to_frequency_array = [120+ 31.25/2, 172+ 31.25/2, 233+33/2, 330+33/2, 618+33/2, 730+33/2, 810+33/2, 1170+33/2]
    band_to_frequency_array = [120 , 172 , 233 , 330, 618, 730 ,810 , 1170 ]
    channel_to_time_delay_array = get_time_delay_array(band_to_frequency_array)
    print(channel_to_time_delay_array)
    for index, time_delay in enumerate(channel_to_time_delay_array):
        print(ms_time_delay_to_packets(time_delay, index))


def get_time_delay_array(channel_to_frequency_array):
    frequency_squares = np.square(channel_to_frequency_array)
    return np.array([4.15 * (-(1 / frequency_squares[7]) + (1 / frequency_squares[ch]))
                     for ch in range(8)]) * np.power(10, 6) * 11.21


def ms_time_delay_to_packets(t, index):
    if index in [0, 1]:
        return t * (31.25 * 1000) / 512
    else:
        return t * (33 * 1000) / 512


if __name__ == '__main__':
    main()  # ch03_B0834+06_20090725_114903 XX

# 91596
# 45828
# 25098
# 12227
# 7215
# 2789
# 1699
# 1179
# 0

'''
        if(band_number == 1):
                return (14282218 + 184799)
        elif(band_number == 2):
                return (14282218 + 92460)
        elif(band_number == 3):
                return (15082023 + 50635)
        elif(band_number == 4):
                return (15082023 + 24669)
        elif(band_number == 5):
                return (15082023 + 14556)
        elif(band_number == 6):
                return (15082023 + 5627)
        elif(band_number == 7):
                return (15082023 + 3428)
        elif(band_number == 8):
                return (15082023 + 2378)
        elif(band_number == 9):
                return (15082023 + 0)'''