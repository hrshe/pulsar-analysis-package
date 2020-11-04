#	> Needs at least 3 GB of free RAM to run
#	> Takes name of file without seq number as input
#	> Keep updating the get_central_freq function

import scipy as sp
from pylab import *
from os.path import isfile
from os.path import getsize
from tqdm import tqdm, trange
import gc


#####	Function Defs	#####

# return freq in GHz
def spec_channel_to_freq(chan_number):
    return ((233 + ((chan_number / 256) * 16.5)) / 1000)  # central_freq for ch03 is 233MHz


# returns time delay in ms
# ref_chan is 0(ie, ref_freq is 233 -(16/2)	MHz)

def time_delay(current_chan, DM):
    return (int(4.15 * DM * (((1 / spec_channel_to_freq(0)) ** 2) - ((1 / spec_channel_to_freq(current_chan)) ** 2))))


def new_time(old_time, current_chan, DM):
    t_delay = time_delay(current_chan, DM)
    if (old_time + t_delay <= 999):
        t = old_time + t_delay
    else:
        t = old_time + t_delay - 1000

    return t


def de_disperse(dyn_spec, DM):
    dim = dyn_spec.shape  # dim[0] is rows, dim[1] is cols
    new_dyn_spec = np.zeros(dyn_spec.shape)

    for i in range(dim[0]):
        for j in range(dim[1]):
            new_dyn_spec[i, j] = dyn_spec[i, new_time(j, i, DM)]

    return new_dyn_spec


def sec_to_packets(n_sec):
    return n_sec * 33 * 1000000 / 512


def get_central_freq(ch):  # in MHz
    if (ch == 1):
        return 120
    elif (ch == 2):
        return 172
    elif (ch == 3):
        return 233
    elif (ch == 4):
        return 330
    elif (ch == 5):
        return 420
    elif (ch == 6):
        return 618
    elif (ch == 7):
        return 730
    elif (ch == 8):
        return 810
    elif (ch == 9):
        return 1170


def extract_name_from_path(a):
    flag = 0
    for i in range(len(a) - 1, 0, -1):
        if (a[i] == '/'):
            flag = i + 1
            break
    return a[flag:]


def skip_cols_synch(band_number):
    if (band_number == 1):
        return (25573722 + 91596)
    elif (band_number == 2):
        return (25573722 + 45828)
    elif (band_number == 3):
        return (27005851 + 25098)
    elif (band_number == 4):
        return (27005851 + 12227)
    elif (band_number == 5):
        return (27005851 + 7215)
    elif (band_number == 6):
        return (27005851 + 2789)
    elif (band_number == 7):
        return (27005851 + 1699)
    elif (band_number == 8):
        return (27005851 + 1179)
    elif (band_number == 9):
        return (27005851 + 0)


################################

FILENAME = sys.argv[1]  # name of file without sequence
ch_nmbr = int(FILENAME[2:4])
central_freq = get_central_freq(ch_nmbr)

packet_number = 0
n_parts = 8  # divide one mbr file into this many parts(to decrease/increase RAM usage)
n_chn = 256
n_int = int(input("Input number packets to integrate	:"))
# DM 				=	float(input("Input Dispersion Measure		:"))

######Function to skip n packets for synchronization######
skip_to_n_packets = int(skip_cols_synch(ch_nmbr))
seq_number = 0  # start at zero sequence
last_seq_number = int(input("Enter last sequence number 		:"))

first_pkt_number = 0
first_pkt_flg = 1
number_of_packets = getsize(FILENAME + '_' + "{0:0=3d}".format(seq_number) + ".mbr") / (1056)

temp_list = [-9999] * n_chn
temp_list_complex = [-9999] * n_chn
while (1):
    print("Reading file	:" + FILENAME + '_' + "{0:0=3d}".format(seq_number) + ".mbr")
    f1 = open(FILENAME + '_' + "{0:0=3d}".format(seq_number) + ".mbr", 'rb')

    pbar = tqdm(total=int(number_of_packets))
    for part_i in range(n_parts):
        # input("pt 0:")
        dyn_spectrum_X = []
        dyn_spectrum_Y = []
        dyn_spectrum_cross = []

        # input("pt 0.5:")

        print_count = 0  # just for printing status of completion

        data = f1.read(int(number_of_packets * 1056 / n_parts))
        print("Data Read")


        for pkt_count in range(int(number_of_packets / n_parts)):
            pkt_start_index = 1056 * pkt_count
            current_pkt_number = int.from_bytes(data[pkt_start_index + 28:pkt_start_index + 32], byteorder='big')
            if (print_count % 25000 == 1):
                print("Ch:" + str(ch_nmbr) + "	Seq Number:" + str(seq_number) + "		" + "{:.2f}".format(
                    ((number_of_packets / n_parts) * part_i + pkt_count) * 100 / number_of_packets) + "% complete")

            print_count = print_count + 1

            if (first_pkt_flg == 0):
                if (packet_number != current_pkt_number):
                    # if missing packet, set to -9999
                    # print("missed packet")
                    for miss_count in range(current_pkt_number - packet_number):
                        dyn_spectrum_X.append(temp_list)
                        dyn_spectrum_Y.append(temp_list)
                        dyn_spectrum_cross.append(temp_list_complex)
                    packet_number = packet_number + (current_pkt_number - packet_number)

                    # save data of read packet
                    Xpol = np.empty(512, dtype=("complex64"))
                    Ypol = np.empty(512, dtype=("complex64"))

                    for cnt in range(512):
                        # print(str(pkt_start_index+32+2*cnt)+"	"+str(cnt)+"	"+str(pkt_count))
                        Xpol[cnt] = data[pkt_start_index + 32 + 2 * cnt] + 0j
                        Ypol[cnt] = data[pkt_start_index + 33 + 2 * cnt] + 0j

                    fft_col_X = (sp.fft.fft(Xpol)) / 512
                    fft_col_Y = (sp.fft.fft(Ypol)) / 512

                    dyn_spectrum_X_t = (abs(fft_col_X[0:256])) ** 2
                    dyn_spectrum_Y_t = (abs(fft_col_Y[0:256])) ** 2
                    dyn_spectrum_cross_t = fft_col_X[0:256] * np.conj(fft_col_Y[0:256])

                    dyn_spectrum_X.append(dyn_spectrum_X_t)
                    dyn_spectrum_Y.append(dyn_spectrum_Y_t)
                    dyn_spectrum_cross.append(dyn_spectrum_cross_t)

                    packet_number = packet_number + 1


                else:
                    # print("A")
                    packet_number = packet_number + 1
                    Xpol = np.empty(512, dtype=("complex64"))
                    Ypol = np.empty(512, dtype=("complex64"))

                    for cnt in range(512):
                        # print(str(pkt_start_index+32+2*cnt)+"	"+str(cnt)+"	"+str(pkt_count))
                        Xpol[cnt] = data[pkt_start_index + 32 + 2 * cnt] + 0j
                        Ypol[cnt] = data[pkt_start_index + 33 + 2 * cnt] + 0j

                    fft_col_X = (sp.fft.fft(Xpol)) / 512
                    fft_col_Y = (sp.fft.fft(Ypol)) / 512

                    dyn_spectrum_X_t = (abs(fft_col_X[0:256])) ** 2
                    dyn_spectrum_Y_t = (abs(fft_col_Y[0:256])) ** 2
                    dyn_spectrum_cross_t = fft_col_X[0:256] * np.conj(fft_col_Y[0:256])

                    dyn_spectrum_X.append(dyn_spectrum_X_t)
                    dyn_spectrum_Y.append(dyn_spectrum_Y_t)
                    dyn_spectrum_cross.append(dyn_spectrum_cross_t)

            elif (first_pkt_flg == 1):
                print("---")
                first_pkt_number = current_pkt_number
                packet_number = current_pkt_number
                first_pkt_flg = 0

                Xpol = np.empty(512, dtype=("complex64"))
                Ypol = np.empty(512, dtype=("complex64"))

                for cnt in range(512):
                    Xpol[cnt] = data[pkt_start_index + 32 + 2 * cnt] + 0j
                    Ypol[cnt] = data[pkt_start_index + 33 + 2 * cnt] + 0j

                fft_col_X = (sp.fft.fft(Xpol)) / 512
                fft_col_Y = (sp.fft.fft(Ypol)) / 512

                dyn_spectrum_X_t = (abs(fft_col_X[0:256])) ** 2
                dyn_spectrum_Y_t = (abs(fft_col_Y[0:256])) ** 2
                dyn_spectrum_cross_t = fft_col_X[0:256] * np.conj(fft_col_Y[0:256])

                dyn_spectrum_X.append(dyn_spectrum_X_t)
                dyn_spectrum_Y.append(dyn_spectrum_Y_t)
                dyn_spectrum_cross.append(dyn_spectrum_cross_t)

                packet_number = packet_number + 1
            pbar.update(1)
        del data
        print("Before gc")
        gc.collect()
        print("after gc")
        print("")
        ##	Integration code	##
        # input("pt 1:")

        print("Before np dec")
        dyn_spectrum_X_np = np.array(dyn_spectrum_X).T
        dyn_spectrum_Y_np = np.array(dyn_spectrum_Y).T
        dyn_spectrum_cross_np = np.array(dyn_spectrum_cross).T

        dyn_spectrum_X_np[0, :] = 0
        dyn_spectrum_Y_np[0, :] = 0
        dyn_spectrum_cross_np[0, :] = 0

        dyn_spectrum_X_np[255, :] = 0
        dyn_spectrum_Y_np[255, :] = 0
        dyn_spectrum_cross_np[255, :] = 0

        print("after np dec")
        print("")
        # input("pt 2:")
        # Synchronization
        print("Before synch")
        if (seq_number == 0 and part_i == 0):
            temp_1 = dyn_spectrum_X_np.shape[1] - (skip_to_n_packets - first_pkt_number)
            col_temp = temp_1 + (n_int - (temp_1 % n_int))

            new_dyn_spectrum_X = np.zeros((n_chn, col_temp)) - 9999
            new_dyn_spectrum_Y = np.zeros((n_chn, col_temp)) - 9999
            new_dyn_spectrum_cross = np.zeros((n_chn, col_temp), dtype="complex64") - (9999 + 9999j)

            new_dyn_spectrum_X[:, 0:temp_1] = dyn_spectrum_X_np[:, (skip_to_n_packets - first_pkt_number):]
            new_dyn_spectrum_Y[:, 0:temp_1] = dyn_spectrum_Y_np[:, (skip_to_n_packets - first_pkt_number):]
            new_dyn_spectrum_cross[:, 0:temp_1] = dyn_spectrum_cross_np[:, (skip_to_n_packets - first_pkt_number):]

            dyn_spectrum_X_np = np.array(new_dyn_spectrum_X)
            dyn_spectrum_Y_np = np.array(new_dyn_spectrum_Y)
            dyn_spectrum_cross_np = np.array(new_dyn_spectrum_cross)
        print("after synch")
        print("")
        # input("pt 3:")
        dyn_spectrum_X_int = np.zeros((n_chn, int(dyn_spectrum_X_np.shape[1] / n_int)))
        dyn_spectrum_Y_int = np.zeros((n_chn, int(dyn_spectrum_Y_np.shape[1] / n_int)))
        dyn_spectrum_cross_int = np.zeros((n_chn, int(dyn_spectrum_cross_np.shape[1] / n_int)), dtype="complex64")
        # plt.imshow(dyn_spectrum_X_np, interpolation = 'nearest', aspect = 'auto')
        # plt.colorbar()
        # plt.show()

        # Time Integration
        # for avg_start in range(int(dyn_spectrum_X_np.shape[1]/(n_int))):
        #	for ch in range(256):
        #		count = 0
        #		for i in range(n_int):
        #			if(dyn_spectrum_X_np[ch, (avg_start*n_int)+i] != -9999):
        #				count = count+1
        #				dyn_spectrum_X_int[ch, avg_start]	= 	dyn_spectrum_X_int[ch, avg_start] + dyn_spectrum_X_np[ch, (avg_start*n_int)+i]
        #				dyn_spectrum_Y_int[ch, avg_start]	= 	dyn_spectrum_Y_int[ch, avg_start] + dyn_spectrum_Y_np[ch, (avg_start*n_int)+i]
        #				dyn_spectrum_cross_int[ch, avg_start]	= 	dyn_spectrum_cross_int[ch, avg_start] + dyn_spectrum_cross_np[ch, (avg_start*n_int)+i]
        #		if(count>0):
        #			dyn_spectrum_X_int[ch, avg_start] = dyn_spectrum_X_int[ch, avg_start]/count
        #			dyn_spectrum_Y_int[ch, avg_start] = dyn_spectrum_Y_int[ch, avg_start]/count
        #			dyn_spectrum_cross_int[ch, avg_start] = dyn_spectrum_cross_int[ch, avg_start]/count

        print("before int")
        print(dyn_spectrum_X_np.shape)
        print(dyn_spectrum_X_int.shape)
        for avg_start in range(int(dyn_spectrum_X_np.shape[1] / (n_int))):
            count = 0
            for i in range(n_int):
                if (dyn_spectrum_X_np[100, (avg_start * n_int) + i] != -9999):  ############condition can be imporived?
                    count = count + 1
                    dyn_spectrum_X_int[:, avg_start] = dyn_spectrum_X_int[:, avg_start] + dyn_spectrum_X_np[:,
                                                                                          (avg_start * n_int) + i]
                    dyn_spectrum_Y_int[:, avg_start] = dyn_spectrum_Y_int[:, avg_start] + dyn_spectrum_Y_np[:,
                                                                                          (avg_start * n_int) + i]
                    dyn_spectrum_cross_int[:, avg_start] = dyn_spectrum_cross_int[:, avg_start] + dyn_spectrum_cross_np[
                                                                                                  :, (
                                                                                                                 avg_start * n_int) + i]
            if (count > 0):
                dyn_spectrum_X_int[:, avg_start] = dyn_spectrum_X_int[:, avg_start] / count
                dyn_spectrum_Y_int[:, avg_start] = dyn_spectrum_Y_int[:, avg_start] / count
                dyn_spectrum_cross_int[:, avg_start] = dyn_spectrum_cross_int[:, avg_start] / count
            elif (count == 0):
                dyn_spectrum_X_int[:, avg_start] = -9999
                dyn_spectrum_Y_int[:, avg_start] = -9999
                dyn_spectrum_cross_int[:, avg_start] = -9999 - 9999j

        print("after int")
        print("")
        # input("pt 4:")
        #### Flag zero data to -9999

        # for row in range(dyn_spectrum_X_int.shape[0]):
        #	for col in range(dyn_spectrum_X_int.shape[1]):
        #		if(dyn_spectrum_X_int[row,col] == -9999):
        #			dyn_spectrum_X_int[row,col] = 0

        # np.savetxt("temp_DS_X_int.dat", dyn_spectrum_X_int)

        f_x = open("/home/desh/Desktop/Hrishi_DynSpec_B0834+06/ch0" + str(ch_nmbr) + "/0834+06_XX_ch0" + str(
            ch_nmbr) + "_seq_00_to_" + str(last_seq_number) + "_int60_final.spec", "ab")
        f_y = open("/home/desh/Desktop/Hrishi_DynSpec_B0834+06/ch0" + str(ch_nmbr) + "/0834+06_YY_ch0" + str(
            ch_nmbr) + "_seq_00_to_" + str(last_seq_number) + "_int60_final.spec", "ab")
        f_RE_XconjY = open("/home/desh/Desktop/Hrishi_DynSpec_B0834+06/ch0" + str(ch_nmbr) + "/0834+06_RE_XY_ch0" + str(
            ch_nmbr) + "_seq_00_to_" + str(last_seq_number) + "_int60_final.spec", "ab")
        f_IM_XconjY = open("/home/desh/Desktop/Hrishi_DynSpec_B0834+06/ch0" + str(ch_nmbr) + "/0834+06_IM_XY_ch" + str(
            ch_nmbr) + "1_seq_00_to_" + str(last_seq_number) + "_int60_final.spec", "ab")

        print("Writing XX")
        np.savetxt(f_x, dyn_spectrum_X_int.T)
        print("Writing YY")
        np.savetxt(f_y, dyn_spectrum_Y_int.T)
        print("Writing RE_XY")
        np.savetxt(f_RE_XconjY, np.real(dyn_spectrum_cross_int.T))
        print("Writing IM_XY")
        np.savetxt(f_IM_XconjY, np.imag(dyn_spectrum_cross_int.T))

        # input("pt 5:")
        f_x.close()
        f_y.close()
        f_RE_XconjY.close()
        f_IM_XconjY.close()

        del dyn_spectrum_X_np
        del dyn_spectrum_Y_np
        del dyn_spectrum_cross_np
        if (seq_number == 0 and part_i == 0):
            del new_dyn_spectrum_X
            del new_dyn_spectrum_Y
            del new_dyn_spectrum_cross
        del dyn_spectrum_X_int
        del dyn_spectrum_Y_int
        del dyn_spectrum_cross_int
        print("Before gc")
        gc.collect()
        print("after gc")
        print("")
    pbar.close()
    # plt.imshow(dyn_spectrum_X_int, interpolation = "nearest")
    # plt.show()
    seq_number = seq_number + 1
    if (not (isfile(FILENAME + '_' + "{0:0=3d}".format(seq_number) + ".mbr")) or seq_number > last_seq_number):
        break

