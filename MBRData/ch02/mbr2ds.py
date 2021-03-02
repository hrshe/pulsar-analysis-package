
from pylab import *
from os.path import isfile
from os.path import getsize
import gc
import time


#####	Function Defs	#####

# return freq in GHz

# command to be given:
# python3 mbr2DynSpec_int_update_after_pgre <name_of_file_w/o_seq_number>

# returns time delay in ms
# ref_chan is 0(ie, ref_freq is 233 -(16/2)	MHz)
# updates true ventral frequencies and bandwidth for ch01 and ch02


def get_central_freq(ch):  # in MHz
    if (ch == 1):
        return 116
    elif (ch == 2):
        return 171
    elif (ch == 3):
        return 232
    elif (ch == 4):
        return 329
    elif (ch == 5):
        return 420
    elif (ch == 6):
        return 617
    elif (ch == 7):
        return 729
    elif (ch == 8):
        return 809
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
        return (25573722 + 200065)
    elif (band_number == 2):
        return (25573722 + 100098)
    elif (band_number == 3):
        return (27005851 + 54818)
    elif (band_number == 4):
        return (27005851 + 26707)
    elif (band_number == 5):
        return (27005851 + 15759)
    elif (band_number == 6):
        return (27005851 + 6092)
    elif (band_number == 7):
        return (27005851 + 3711)
    elif (band_number == 8):
        return (27005851 + 2575)
    elif (band_number == 9):
        return (27005851 + 0)


################################

FILENAME = sys.argv[1]  # name of file without sequence
ch_nmbr = int(FILENAME[2:4])
central_freq = get_central_freq(ch_nmbr)
psr_name = FILENAME[5:13]

packet_number = 0
n_parts = 32  # divide one mbr file into this many parts(to decrease/increase RAM usage)
n_chn = 256
n_int = int(input("Input number packets to integrate	:"))
# DM 				=	float(input("Input Dispersion Measure		:"))

###########################################################
output_path = "/OutputData/B0834+06_20090725_114903/DynamicSpectrum/"
###########################################################

######Function to skip n packets for synchronization######
skip_to_n_packets = 0  # int(skip_cols_synch(ch_nmbr))
seq_number = 0  # start at zero sequence
last_seq_number = int(input("Enter last sequence number 		:"))

first_pkt_number = 0
first_pkt_flg = 1
number_of_packets = getsize(FILENAME + '_' + "{0:0=3d}".format(seq_number) + ".mbr") / (1056)

temp_list = [-9999] * n_chn
temp_list_complex = [-9999] * n_chn

time_arr = []
while (1):
    print("Reading file	:" + FILENAME + '_' + "{0:0=3d}".format(seq_number) + ".mbr")
    # open file
    f1 = open(FILENAME + '_' + "{0:0=3d}".format(seq_number) + ".mbr", 'rb')

    for part_i in range(n_parts):
        print("timer started")
        start = time.perf_counter()
        dyn_spectrum_X = []
        dyn_spectrum_Y = []
        dyn_spectrum_cross = []

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
                    for miss_count in range(current_pkt_number - packet_number):
                        dyn_spectrum_X.append(temp_list)
                        dyn_spectrum_Y.append(temp_list)
                        dyn_spectrum_cross.append(temp_list_complex)
                    packet_number = packet_number + (current_pkt_number - packet_number)

                    # save data of read packet
                    Xpol = np.empty(512, dtype=("complex64"))
                    Ypol = np.empty(512, dtype=("complex64"))

                    for cnt in range(512):
                        Xpol[cnt] = data[pkt_start_index + 32 + 2 * cnt] + 0j
                        Ypol[cnt] = data[pkt_start_index + 33 + 2 * cnt] + 0j

                    fft_col_X = (np.fft.fft(Xpol)) / 512
                    fft_col_Y = (np.fft.fft(Ypol)) / 512

                    dyn_spectrum_X_t = (abs(fft_col_X[0:256])) ** 2
                    dyn_spectrum_Y_t = (abs(fft_col_Y[0:256])) ** 2
                    dyn_spectrum_cross_t = fft_col_X[0:256] * np.conj(fft_col_Y[0:256])

                    dyn_spectrum_X.append(dyn_spectrum_X_t)
                    dyn_spectrum_Y.append(dyn_spectrum_Y_t)
                    dyn_spectrum_cross.append(dyn_spectrum_cross_t)

                    packet_number = packet_number + 1

                # if not missing packet
                else:
                    packet_number = packet_number + 1
                    Xpol = np.empty(512, dtype=("complex64"))
                    Ypol = np.empty(512, dtype=("complex64"))

                    for cnt in range(512):
                        Xpol[cnt] = data[pkt_start_index + 32 + 2 * cnt] + 0j
                        Ypol[cnt] = data[pkt_start_index + 33 + 2 * cnt] + 0j

                    fft_col_X = (np.fft.fft(Xpol)) / 512
                    fft_col_Y = (np.fft.fft(Ypol)) / 512

                    dyn_spectrum_X_t = (abs(fft_col_X[0:256])) ** 2
                    dyn_spectrum_Y_t = (abs(fft_col_Y[0:256])) ** 2
                    dyn_spectrum_cross_t = fft_col_X[0:256] * np.conj(fft_col_Y[0:256])

                    dyn_spectrum_X.append(dyn_spectrum_X_t)
                    dyn_spectrum_Y.append(dyn_spectrum_Y_t)
                    dyn_spectrum_cross.append(dyn_spectrum_cross_t)

            # If first packet
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

                fft_col_X = (np.fft.fft(Xpol)) / 512
                fft_col_Y = (np.fft.fft(Ypol)) / 512

                dyn_spectrum_X_t = (abs(fft_col_X[0:256])) ** 2
                dyn_spectrum_Y_t = (abs(fft_col_Y[0:256])) ** 2
                dyn_spectrum_cross_t = fft_col_X[0:256] * np.conj(fft_col_Y[0:256])

                dyn_spectrum_X.append(dyn_spectrum_X_t)
                dyn_spectrum_Y.append(dyn_spectrum_Y_t)
                dyn_spectrum_cross.append(dyn_spectrum_cross_t)

                packet_number = packet_number + 1

        # delete data array for saving memory 
        del data
        gc.collect()

        # Covert to numpy arrays
        dyn_spectrum_X_np = np.array(dyn_spectrum_X).T
        dyn_spectrum_Y_np = np.array(dyn_spectrum_Y).T
        dyn_spectrum_cross_np = np.array(dyn_spectrum_cross).T

        # set values in first and last channels to 0
        dyn_spectrum_X_np[0, :] = 0
        dyn_spectrum_Y_np[0, :] = 0
        dyn_spectrum_cross_np[0, :] = 0

        dyn_spectrum_X_np[255, :] = 0
        dyn_spectrum_Y_np[255, :] = 0
        dyn_spectrum_cross_np[255, :] = 0

        # # Synchronization
        # if (seq_number == 0 and part_i == 0):
        #     temp_1 = dyn_spectrum_X_np.shape[1] - (skip_to_n_packets - first_pkt_number)
        #     col_temp = temp_1 + (n_int - (temp_1 % n_int))

        #     new_dyn_spectrum_X = np.zeros((n_chn, col_temp)) - 9999
        #     new_dyn_spectrum_Y = np.zeros((n_chn, col_temp)) - 9999
        #     new_dyn_spectrum_cross = np.zeros((n_chn, col_temp), dtype="complex64") - (9999 + 9999j)

        #     new_dyn_spectrum_X[:, 0:temp_1] = dyn_spectrum_X_np[:, (skip_to_n_packets - first_pkt_number):]
        #     new_dyn_spectrum_Y[:, 0:temp_1] = dyn_spectrum_Y_np[:, (skip_to_n_packets - first_pkt_number):]
        #     new_dyn_spectrum_cross[:, 0:temp_1] = dyn_spectrum_cross_np[:, (skip_to_n_packets - first_pkt_number):]

        #     dyn_spectrum_X_np = np.array(new_dyn_spectrum_X)
        #     dyn_spectrum_Y_np = np.array(new_dyn_spectrum_Y)
        #     dyn_spectrum_cross_np = np.array(new_dyn_spectrum_cross)

        dyn_spectrum_X_int = np.zeros((n_chn, int(dyn_spectrum_X_np.shape[1] / n_int)))
        dyn_spectrum_Y_int = np.zeros((n_chn, int(dyn_spectrum_Y_np.shape[1] / n_int)))
        dyn_spectrum_cross_int = np.zeros((n_chn, int(dyn_spectrum_cross_np.shape[1] / n_int)), dtype="complex64")

        # Time Integration
        print("before integration")
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

        # Save DS in parts		
        f_x = open(output_path + psr_name + "_XX_ch0" + str(ch_nmbr) + "_seq_00_to_" + str(
            last_seq_number) + "_int60_final.spec", "ab")
        f_y = open(output_path + psr_name + "_YY_ch0" + str(ch_nmbr) + "_seq_00_to_" + str(
            last_seq_number) + "_int60_final.spec", "ab")
        f_RE_XconjY = open(output_path + psr_name + "_RE_XY_ch0" + str(ch_nmbr) + "_seq_00_to_" + str(
            last_seq_number) + "_int60_final.spec", "ab")
        f_IM_XconjY = open(output_path + psr_name + "_IM_XY_ch" + str(ch_nmbr) + "1_seq_00_to_" + str(
            last_seq_number) + "_int60_final.spec", "ab")

        print("Writing XX")
        np.savetxt(f_x, dyn_spectrum_X_int.T, fmt="%f")
        print("Writing YY")
        np.savetxt(f_y, dyn_spectrum_Y_int.T, fmt="%f")
        print("Writing RE_XY")
        np.savetxt(f_RE_XconjY, np.real(dyn_spectrum_cross_int.T), fmt="%f")
        print("Writing IM_XY")
        np.savetxt(f_IM_XconjY, np.imag(dyn_spectrum_cross_int.T), fmt="%f")

        # input("pt 5:")
        f_x.close()
        f_y.close()
        f_RE_XconjY.close()
        f_IM_XconjY.close()

        # To view temp DS, un-comment the following lines(306-312). Note that flagged valued of -9999 are to be converted to zero 
        # for row in range(dyn_spectrum_X_int.shape[0]):
        #	for col in range(dyn_spectrum_X_int.shape[1]):
        #		if(dyn_spectrum_X_int[row,col] == -9999):
        #			dyn_spectrum_X_int[row,col] = 0

        # plt.imshow(dyn_spectrum_X_int, interpolation = "nearest")
        # plt.show()

        del dyn_spectrum_X_np
        del dyn_spectrum_Y_np
        del dyn_spectrum_cross_np
        # if (seq_number == 0 and part_i == 0):
        #     del new_dyn_spectrum_X
        #     del new_dyn_spectrum_Y
        #     del new_dyn_spectrum_cross
        del dyn_spectrum_X_int
        del dyn_spectrum_Y_int
        del dyn_spectrum_cross_int
        ####print("Before gc")
        gc.collect()
        ####print("after gc")
        print(f"time taken for {part_i} is {str(time.perf_counter() - start)}")
        time_arr.append(time.perf_counter() - start)
        print(time_arr)
        print("")

    # plt.imshow(dyn_spectrum_X_int, interpolation = "nearest")
    # plt.show()
    seq_number = seq_number + 1
    if (not (isfile(FILENAME + '_' + "{0:0=3d}".format(seq_number) + ".mbr")) or seq_number > last_seq_number):
        break