"""
Packet level synchronization for one channel.

Input:
Channel number is extracted from input file name.
Accepts mbr file name without the sequence number as input.
Example command run from project root for mbr data ch01_B0834+06_20090725_114903:
> python3 -m AnalysisPackages.synchronization.synchronization_single MBRData/ch01/ch01_B0834+06_20090725_114903

Output:
Channel number and first packet of synchronization is saved in the path:
        AnalysisPackages/resources/ChannelVsFirstPacket_B0834+06_20090725_114903.txt
"""
import sys
from os.path import getsize
from os.path import isfile
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def int2str(number, digits):
    return str(number).zfill(digits)


def double_arr_to_list(a):
    b = []
    for i_fun in range(len(a)):
        for j_fun in range(len(a[i_fun])):
            b.append(a[i_fun][j_fun])
    return b


def slope(a, b):
    s = [0 for i in range(len(a) - 1)]
    for i in range(len(a) - 1):
        s[i] = float(b[i + 1] - b[i]) / (a[i + 1] - a[i])
    return s


def linear_fit(a, b):
    z = np.polyfit(a, b, 1)
    r = np.poly1d(z)
    a_new = np.linspace(a[0], a[-1], len(a))
    b_new = r(a_new)
    return a_new, b_new


def main(file_name):
    #  START  #
    dirname = Path(__file__).parent.parent.absolute()
    psrDetails = file_name[18:42]
    channelNumber = int(file_name[15:17])
    plot_graph = False
    # True if \
    # (input("Do you want to plot packet_num vs gps_count graph?(yes/no) 		:")).lower() == "yes" \
    # else False

    for n in range(1):
        G_BLIP = []
        P_BLIP = []
        F_G_BLIP = []
        F_P_BLIP = []
        stop = []
        SLOPE = []
        stability = []
        stability_fpga = []
        conv = []
        conv_fpga = []
        julian_day = []
        j = 0
        st = '_' + int2str(j, 3)

        stop.append(0)

        while j < 999:

            print("Reading file " + file_name + st + ".mbr")

            size = getsize(file_name + st + ".mbr")
            i = 26  # start of every gps count and packet number
            q = 0
            fpga = np.empty(2)  # Think it is to detect missing packets
            gps = np.empty(2)  # Think it is to detect missing packets
            p_num = np.empty(2)  # Think it is to detect missing packets
            g_blip = []
            p_blip = []
            f_g_blip = []
            f_p_blip = []

            with open(file_name + st + ".mbr", "rb") as file:
                while i < size:
                    file.read(24)
                    if i != 26:
                        file.read(1024)
                    fpga[q % 2] = int.from_bytes(file.read(2), byteorder='big')  # reading FPGA mon
                    gps[q % 2] = int.from_bytes(file.read(2), byteorder='big')  # reading GPS count
                    p_num[q % 2] = int.from_bytes(file.read(4), byteorder='big')  # reading packet count
                    if gps[q % 2] - gps[(q + 1) % 2] == 1:  # when increment in gps# and pkt#
                        g_blip.append(gps[q % 2])
                        p_blip.append(p_num[q % 2])
                        if fpga[q % 2] != fpga[(q + 1) % 2]:
                            f_g_blip.append(gps[q % 2])
                            f_p_blip.append(p_num[q % 2])
                    i += 1056
                    q += 1

            s = slope(g_blip, p_blip)

            g_blip_new, p_blip_new = linear_fit(g_blip, p_blip)
            f_g_blip_new, f_p_blip_new = linear_fit(f_g_blip, f_p_blip)

            G_BLIP.append(g_blip)
            P_BLIP.append(p_blip)
            F_G_BLIP.append(f_g_blip)
            F_P_BLIP.append(f_p_blip)

            G_BLIP_c = double_arr_to_list(G_BLIP)
            P_BLIP_c = double_arr_to_list(P_BLIP)
            F_G_BLIP_c = double_arr_to_list(F_G_BLIP)
            F_P_BLIP_c = double_arr_to_list(F_P_BLIP)
            SLOPE_c = double_arr_to_list(SLOPE)

            G_BLIP_new, P_BLIP_new = linear_fit(G_BLIP_c, P_BLIP_c)
            F_G_BLIP_new, F_P_BLIP_new = linear_fit(F_G_BLIP_c, F_P_BLIP_c)

            temp = np.polyfit(F_G_BLIP_c, F_P_BLIP_c, 1)
            temp_line_func = np.poly1d(temp)

            j += 1
            st = '_' + int2str(j, 3)

            if (not (isfile(file_name + st + ".mbr"))):
                print("\n\t\t---For Ch " + str(channelNumber) + "---")
                print("P_Num for first transition:\t\t\t" + str(P_BLIP_c[0]))
                print("Estimate of P_Num for first transition(by GPS count vs Pkt count fitting):\t\t" + str(
                    P_BLIP_new[0]))
                print("Estimate of P_Num for first transition(by FPGA blip vs Pkt count fitting):\t\t" + str(
                    temp_line_func(G_BLIP_new[0])))
                print("\nEstimated Sampling Freq.(FPGA Blip):\t\t" + str(
                    np.mean(slope(F_G_BLIP_new, F_P_BLIP_new)) * 512))
                frac_part = temp_line_func(G_BLIP_new[0]) - int(temp_line_func(G_BLIP_new[0]))
                int_part = temp_line_func(G_BLIP_new[0])
                print("Sample in " + str(int_part) + "th packet:\t\t" + str(512 * frac_part) + "\n")

                with open(str(dirname) + "/resources/ChannelVsFirstPacket_" + psrDetails + ".txt", "a") as output_file:
                    a = np.zeros((1, 2))
                    a[0, 0] = channelNumber
                    a[0, 1] = temp_line_func(int(G_BLIP_new[0]))
                    np.savetxt(output_file, a, fmt='%d')

                if (plot_graph):
                    plt.figure()
                    plt.plot(G_BLIP_c, P_BLIP_c, "ro")
                    plt.plot(G_BLIP_new, P_BLIP_new)
                    plt.plot(F_G_BLIP_new, F_P_BLIP_new, "b+")
                    plt.xlabel("GPS Counter")
                    plt.ylabel("Packet Counter")
                    plt.show()

                break

    exit()


if __name__ == '__main__':
    main(sys.argv[1])
