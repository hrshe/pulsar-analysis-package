#!/usr/bin/python

import numpy as np
import matplotlib.pyplot as plt
import gc
import sys


# takes Raw Dynmaic Spectrum as input
# gives averege pulse profile as output for each channel
# edited to read in chunks after desh suggested
# Gives two outputs; one is robust mean subtracted to be used for getting pulse_template_mask while other is without robust mean subtraction to get template of spectrum

def integrate_col(mat):
    n_rows = mat.shape[0]
    n_cols = mat.shape[1]

    output = np.zeros(n_cols)
    count = np.zeros(n_cols)

    for c in range(n_cols):
        for r in range(n_rows):
            if (mat[r, c] != 0):
                output[c] = output[c] + mat[r, c]
                count[c] = count[c] + 1

    for i in range(n_cols):
        if (count[i] > 0):
            output[i] = output[i] / count[i]

    return output


def rms(a, meana):
    rmsa = np.zeros(a.shape[0])
    for i in range(a.shape[0]):
        count = 0
        for j in range(a.shape[1]):
            if not np.isnan(a[i][j]):
                rmsa[i] += (a[i][j] - meana[i]) ** 2
                count = count + 1
        if (count == 0):
            rmsa[i] = 0
        else:
            rmsa[i] = np.sqrt(rmsa[i] / count)
    return rmsa


def mean1(a):
    mean_a = np.zeros(a.shape[0])
    for i in range(a.shape[0]):
        count = 0
        for j in range(a.shape[1]):
            if not np.isnan(a[i][j]):
                mean_a[i] += a[i][j]
                count = count + 1
        if (count == 0):
            mean_a[i] = 0
        else:
            mean_a[i] = mean_a[i] / count
    return mean_a


def get_robust_mean_rms(a, sigma_threshold):
    ok = False
    iter_i = 0
    mean_last = 0.0
    rms = 0.0

    while (not (ok)):
        iter_i += 1
        mean = 0.0
        pts_used = 0

        # computing the mean

        threshold = rms * sigma_threshold

        for i in range(len(a)):
            diff = abs(a[i] - mean_last)
            # include all points for first time, else include only those within threshold

            if (((iter_i == 1) or (diff <= threshold)) and not np.isnan(a[i])):
                mean = a[i] + mean
                pts_used += 1

        if (pts_used != 0):
            mean = mean / pts_used

        # note the old value of rms
        rms0 = rms

        # compute rms using new mean

        rms = 0.0
        pts_used = 0
        threshold = rms0 * 3

        for i in range(len(a)):
            diff = abs(a[i] - mean)
            # first time include all points, otherwise only within the threshold
            if (((iter_i == 1) or (diff <= threshold)) and not np.isnan(a[i])):
                rms = rms + diff * diff
                pts_used += 1

        if (pts_used != 0):
            rms = np.sqrt(rms / pts_used)

        # note this mean as old value of mean
        mean_last = mean

        # first time make no checks
        if (iter_i > 1):
            # see if we are unfortunate; if yes .. then return
            if (rms == 0.0):
                ok = True  # return
            elif (abs((rms0 / rms) - 1.0) < 0.01):
                ok = True

    # print("Mean: "+str(mean)+", RMS: "+str(rms)+", Pts Used: "+str(pts_used))
    return (mean, rms)


def get_robust_mean_rms_changed_for_decomp(a, sigma_threshold):
    ok = False
    iter_i = 0
    mean_last = 1
    rms = 0.0

    while (not (ok)):
        iter_i += 1
        mean = 0.0
        pts_used = 0

        # computing the mean

        threshold = rms * sigma_threshold

        for i in range(len(a)):

            diff = abs(a[i] - mean_last)
            # include all points for first time, else include only those within threshold

            if (((iter_i == 1) or (diff <= threshold)) and not np.isnan(a[i])):
                mean = a[i] + mean
                pts_used += 1

        if (pts_used != 0):
            mean = mean / pts_used

        # note the old value of rms
        rms0 = rms

        # compute rms using new mean

        rms = 0.0
        pts_used = 0
        threshold = rms0 * sigma_threshold

        for i in range(len(a)):
            diff = a[i] - mean
            # first time include all points, otherwise only within the threshold
            if (((iter_i == 1) or (diff <= threshold)) and not np.isnan(a[i])):
                rms = rms + diff * diff
                pts_used += 1

        if (pts_used != 0):
            rms = np.sqrt(rms / pts_used)

        # note this mean as old value of mean
        mean_last = mean
        if (pts_used < (a.shape[0]) / 2):
            sigma_threshold = sigma_threshold + 0.5
            ok = False
            iter_i = 0
            mean_last = 1
            rms = 0.0
            continue
        print("escaped")
        # first time make no checks
        if (iter_i > 1):
            # see if we are unfortunate; if yes .. then return
            if (rms == 0.0):
                ok = True  # return
            elif (abs((rms0 / rms) - 1.0) < 0.01):
                ok = True

    # print("Mean: "+str(mean)+", RMS: "+str(rms)+", Pts Used: "+str(pts_used))
    return (mean, rms)


def sum1(a):
    result = 0
    for temp_count in range(a.shape[0]):
        if not np.isnan(a[temp_count]):
            result = result + a[temp_count]
    return result


def millisec2col(t, n_int):
    return int(t * 33000 / (n_int * 512))


###############
######		Initialize Variables		###### REMOVE UNWANTED LATER
# DM 		=		4.5
# cf = get_central_freq(4)		#enter channel number
# n_int	=		60
# N_col	=		int(506880*4/(3*n_int))		#~10 sec
# n_ch	=		256
# max_delay_ch	=	int(time_delay_2_col_delay(calculate_T_delay(255, DM,cf)))
# total_number_col	=	int(506880*4*20/n_int)			#to be either read from log file or calculated as (n_pkt_per_seq * n_seq / n_int)
# P			=  		1292.2414
# P 			=		1273.482

##############################################
P = 1273.485
n_int = 60
total_seq_number = 1
total_number_col = int(506880 * 4 * total_seq_number / n_int)
N_col = int(506880 * 4 / (3 * n_int))  # ~10 sec
n_ch = 256
filename = sys.argv[1]
psr_name = filename[0:7]
polarization = filename[8:10]
ch_nmbr = filename[13:15]
f = open(filename, "r")
temp_TS = np.array(())
N_bins = millisec2col(P, n_int)
avg_pulse_prof_wo_robust = np.zeros((n_ch, N_bins))
avg_pulse_prof_w_robust = np.zeros((n_ch, N_bins))

for i in range(int(total_number_col / N_col)):
    if (i == 4):
        break
    app_wo_robust = np.zeros((n_ch, N_bins))
    app_count_wo_robust = np.zeros((n_ch, N_bins))
    app_w_robust = np.zeros((n_ch, N_bins))
    app_count_w_robust = np.zeros((n_ch, N_bins))
    dyn_spec = np.zeros((n_ch, N_col))
    count_lines_read = 0
    arr_temp = []
    for lines in f:
        arr_temp.append(np.fromstring(lines, dtype=float, sep=' ').tolist())
        count_lines_read = count_lines_read + 1
        # print("count_lines_read  "+str(count_lines_read))
        if (count_lines_read == N_col):
            dyn_spec = np.array(arr_temp).T
            break

    time = np.zeros(dyn_spec.shape[1])
    for t_count in range(time.shape[0]):
        time[t_count] = (i * N_col + t_count) * 512 * n_int / 33000
    # remove bad channels

    ################## use robust mean and rms instead of just mean and rms and check

    dyn_spec[:10, :] = np.nan
    dyn_spec[246:, :] = np.nan

    robust_mean_X = np.zeros(n_ch)
    robust_rms_X = np.zeros(n_ch)

    for cnt in range(n_ch):
        m_r_X = get_robust_mean_rms(dyn_spec[cnt, :], 3)
        robust_mean_X[cnt] = m_r_X[0]
        robust_rms_X[cnt] = m_r_X[1]

    xmean = mean1(dyn_spec)  # robust_mean_X

    xrms = rms(dyn_spec, xmean)

    SNR2 = float(np.sqrt(60))

    efficiency_x = np.zeros(256)

    # plt.plot(xrms)
    # plt.plot(xmean)
    # plt.show()

    for temp_count in range(256):
        if (xrms[temp_count] != 0):
            efficiency_x[temp_count] = xmean[temp_count] / (xrms[temp_count] * SNR2)

    # plt.plot(efficiency_x)
    # plt.xlim(0,255)
    # plt.show()

    mean_std_x = get_robust_mean_rms(efficiency_x[10:245], 3)
    std_x = mean_std_x[1]  # np.std(efficiency_x[10:245])
    mean_x = mean_std_x[0]  # np.mean(efficiency_x[10:245])

    for cnt_temp in range(256):
        if (abs(mean_x - efficiency_x[cnt_temp]) > 3 * std_x):
            dyn_spec[cnt_temp - 5:cnt_temp + 5, :] = np.nan  # Flagging the bad channels

    for t in range(dyn_spec.shape[1]):
        f_p = (time[t] / P) - int(time[t] / P)
        n_bin = f_p * N_bins

        j = int(n_bin)
        if (j == N_bins - 1):
            k = 0
        else:
            k = j + 1
        delta = n_bin - j

        if (j >= 0 and j < N_bins - 1):
            for ch in range(dyn_spec.shape[0]):
                if not np.isnan(dyn_spec[ch, t]):
                    app_wo_robust[ch, j] = app_wo_robust[ch, j] + dyn_spec[ch, t] * (1 - delta)
                    app_wo_robust[ch, k] = app_wo_robust[ch, k] + dyn_spec[ch, t] * delta
                    app_count_wo_robust[ch, j] = app_count_wo_robust[ch, j] + 1 - delta
                    app_count_wo_robust[ch, k] = app_count_wo_robust[ch, k] + delta

    for row in range(avg_pulse_prof_wo_robust.shape[0]):
        for col in range(avg_pulse_prof_wo_robust.shape[1]):
            if (app_count_wo_robust[row, col] > 0 and avg_pulse_prof_wo_robust[row, col] != 0):
                avg_pulse_prof_wo_robust[row, col] = (avg_pulse_prof_wo_robust[row, col] + app_wo_robust[row, col] /
                                                      app_count_wo_robust[row, col]) / 2
            elif (avg_pulse_prof_wo_robust[row, col] == 0 and app_count_wo_robust[row, col] > 0):
                avg_pulse_prof_wo_robust[row, col] = app_wo_robust[row, col] / app_count_wo_robust[row, col]

    ###	Subtract Robust Mean
    robust_mean_X = np.zeros(n_ch)

    for cnt in range(n_ch):
        m_r_X = get_robust_mean_rms(dyn_spec[cnt, :], 3)
        robust_mean_X[cnt] = m_r_X[0]

    for cnt2 in range(n_ch):
        for cnt3 in range(N_col):
            if not np.isnan(dyn_spec[cnt2, cnt3]):
                dyn_spec[cnt2, cnt3] = dyn_spec[cnt2, cnt3] - robust_mean_X[cnt2]

    ####	End of Robust mean

    for t in range(dyn_spec.shape[1]):
        f_p = (time[t] / P) - int(time[t] / P)
        n_bin = f_p * N_bins

        j = int(n_bin)
        if (j == N_bins - 1):
            k = 0
        else:
            k = j + 1
        delta = n_bin - j

        if (j >= 0 and j < N_bins - 1):
            for ch in range(dyn_spec.shape[0]):
                if not np.isnan(dyn_spec[ch, t]):
                    app_w_robust[ch, j] = app_w_robust[ch, j] + dyn_spec[ch, t] * (1 - delta)
                    app_w_robust[ch, k] = app_w_robust[ch, k] + dyn_spec[ch, t] * delta
                    app_count_w_robust[ch, j] = app_count_w_robust[ch, j] + 1 - delta
                    app_count_w_robust[ch, k] = app_count_w_robust[ch, k] + delta

    print(str(i) + "/" + str(int(total_number_col / N_col)) + "			" + str(
        100 * i * N_col / total_number_col) + "% complete")

    for row in range(avg_pulse_prof_w_robust.shape[0]):
        for col in range(avg_pulse_prof_w_robust.shape[1]):
            if (app_count_w_robust[row, col] > 0 and avg_pulse_prof_w_robust[row, col] != 0):
                avg_pulse_prof_w_robust[row, col] = (avg_pulse_prof_w_robust[row, col] + app_w_robust[row, col] /
                                                     app_count_w_robust[row, col]) / 2
            if (app_count_w_robust[row, col] > 0 and avg_pulse_prof_w_robust[row, col] == 0):
                avg_pulse_prof_w_robust[row, col] = app_w_robust[row, col] / app_count_w_robust[row, col]

# plt.figure("without robust mean")
# plt.imshow(avg_pulse_prof_wo_robust, interpolation = "nearest", aspect = "auto", cmap = 'hot')
# plt.colorbar()
# plt.figure("with robust mean")
# plt.imshow(avg_pulse_prof_w_robust, interpolation = "nearest", aspect = "auto", cmap = 'hot')
# plt.colorbar()
# plt.show()
plt.figure("without robust mean")
plt.imshow(avg_pulse_prof_wo_robust, interpolation="nearest", aspect="auto", cmap='hot')
plt.colorbar()
plt.figure("with robust mean")
plt.imshow(avg_pulse_prof_w_robust, interpolation="nearest", aspect="auto", cmap='hot')
plt.colorbar()
plt.show()

np.savetxt("average_pulse_wout_robust_mean_sub_DS_ch" + ch_nmbr + "_" + psr_name + "_" + polarization + ".dat",
           avg_pulse_prof_wo_robust)
np.savetxt("average_pulse_with_robust_mean_sub_DS_ch" + ch_nmbr + "_" + psr_name + "_" + polarization + ".dat",
           avg_pulse_prof_w_robust)

quit()