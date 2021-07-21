import warnings

import numpy as np
import matplotlib.pyplot as plt


def ch2freq(ch, cent_freq):
    cf = cent_freq
    bw = 16.5
    return cf + (bw / 2) - (ch * bw / 255)


def timequanta_to_millisec(n, psr, channel_number):
    return (n * 512 * psr.n_packet_integration) / (psr.band[channel_number].sampling_frequency * 1000)


# def calculate_dispersion_delay(channel_number, psr, ref_ch):
#     cent_freq = psr.get_central_frequency(channel_number)
#     return 4.15 * 1000000 * psr.dm * (
#             (1 / ch2freq(channel_number, cent_freq)) ** 2 - (1 / ch2freq(ref_ch, cent_freq)) ** 2)


def time_delay_to_quanta(t, n_int):
    return np.rint(t * (33000 / (512 * n_int)))


# def millisec2timequanta(t, psr, channel_number):
#     return int(t * psr.band[channel_number].sampling_frequency * 1000 / (psr.n_packet_integration * 512))

def ms_time_delay_to_time_quanta(t, channel_number, psr):
    return t * ((psr.band[channel_number].sampling_frequency * 1000) / (512 * psr.n_packet_integration))


def get_robust_mean_rms_2d(arr, sigma_threshold):
    '''
    :param arr: a 2D array
    computes mean across axis 0. (mean for each row)
    :return: list of mean and rms. Each list is of dim arr.shape[1]
    '''
    mean, rms = np.zeros(arr.shape[1]), np.zeros(arr.shape[1])
    for i in range(arr.shape[1]):
        mean[i], rms[i] = get_robust_mean_rms(arr[:, i], sigma_threshold)
    return mean, rms


def interpolate2d_new(dyn_spect, time_quanta_start, avg_pulse_prof_wo_robust, psr, n_bins):
    """
    not completed. using old for now
    """
    n_channel = psr.n_channels
    P = psr.period

    n_int = psr.n_packet_integration
    replace_nan_with_mean(dyn_spect, psr.sigma_threshold)
    time_arr = np.zeros(dyn_spect.shape[0])
    for t_count in range(time_arr.shape[0]):
        time_arr[t_count] = (time_quanta_start + t_count) * 512 * n_int / 33000

    interpolated = np.zeros((n_bins, n_channel))
    for n_ch in range(dyn_spect.shape[1]):
        interpolated[:, n_ch] = np.interp(list(range(n_bins)), time_arr, dyn_spect[:, n_ch], period=P)
    print(interpolated.shape)
    plot_DS(interpolated)
    return 0


def plot_DS(integrated_dynamic_spectrum, color='gray'):
    plt.imshow(np.transpose(integrated_dynamic_spectrum), interpolation="nearest", aspect='auto', cmap=color)
    plt.colorbar()
    plt.show()


def replace_nan_with_mean(dyn_spec, sigma_threshold):
    mean, rms = get_robust_mean_rms_2d(dyn_spec, sigma_threshold)
    mean_of_mean = np.nanmean(mean)
    mean = np.where(np.isnan(mean), mean_of_mean, mean)
    nan_indices = np.where(np.isnan(dyn_spec))
    dyn_spec[nan_indices] = np.take(mean, nan_indices[1])


def interpolate2d_old(a, time_quanta_start, avg_pulse_prof_wo_robust, psr, n_bins):
    time_arr = np.zeros(a.shape[0])
    for t_count in range(time_arr.shape[0]):
        time_arr[t_count] = (time_quanta_start + t_count) * 512 * psr.n_packet_integration / 33000
    app_wo_robust = np.zeros((psr.n_channels, n_bins))
    app_count_wo_robust = np.zeros((psr.n_channels, n_bins))
    for t in range(a.shape[0]):
        f_p = (time_arr[t] / psr.period) - int(time_arr[t] / psr.period)
        n_bin = f_p * n_bins

        j = int(n_bin)
        if j == n_bins - 1:
            k = 0
        else:
            k = j + 1
        delta = n_bin - j

        if 0 <= j < n_bins - 1:
            for ch in range(a.shape[1]):
                if not np.isnan(a[t, ch]):
                    app_wo_robust[ch, j] = app_wo_robust[ch, j] + a[t, ch] * (1 - delta)
                    app_wo_robust[ch, k] = app_wo_robust[ch, k] + a[t, ch] * delta
                    app_count_wo_robust[ch, j] = app_count_wo_robust[ch, j] + 1 - delta
                    app_count_wo_robust[ch, k] = app_count_wo_robust[ch, k] + delta

    for row in range(avg_pulse_prof_wo_robust.shape[0]):
        for col in range(avg_pulse_prof_wo_robust.shape[1]):
            if app_count_wo_robust[row, col] > 0 and avg_pulse_prof_wo_robust[row, col] != 0:
                avg_pulse_prof_wo_robust[row, col] = (avg_pulse_prof_wo_robust[row, col] + app_wo_robust[row, col] /
                                                      app_count_wo_robust[row, col]) / 2
            elif avg_pulse_prof_wo_robust[row, col] == 0 and app_count_wo_robust[row, col] > 0:
                avg_pulse_prof_wo_robust[row, col] = app_wo_robust[row, col] / app_count_wo_robust[row, col]


def remove_rfi(dynamic_spectrum, psr):
    dynamic_spectrum[:, :10], dynamic_spectrum[:, psr.n_channels - 10:] = np.nan, np.nan
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        mean, rms = np.nanmean(dynamic_spectrum, axis=0), np.nanstd(dynamic_spectrum, axis=0)
    # option for robust mean/rms
    snr = float(np.sqrt(psr.n_packet_integration))
    efficiency_x = mean / rms * snr
    mean_x, std_x = get_robust_mean_rms(efficiency_x[10:psr.n_channels - 10], psr.sigma_threshold)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        dynamic_spectrum = np.where(abs(mean_x - efficiency_x) > psr.sigma_threshold * std_x, np.nan, dynamic_spectrum)
    return dynamic_spectrum


def get_robust_mean_rms_2d(arr, sigma_threshold):
    '''
    :param sigma_threshold:
    :param arr: a 2D array
    computes mean across axis 0. (mean for each row)
    :return: list of mean and rms. Each list is of dim arr.shape[1]
    '''
    mean, rms = np.zeros(arr.shape[1]), np.zeros(arr.shape[1])
    for i in range(arr.shape[1]):
        mean[i], rms[i] = get_robust_mean_rms(arr[:, i], sigma_threshold)
    return mean, rms


def get_robust_mean_rms(input_arr, sigma_threshold):
    arr = np.copy(input_arr)
    ok = False
    iter_i, rms, mean = 0, 0.0, 0.0
    while not ok:
        iter_i += 1
        threshold = rms * sigma_threshold

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            mean = np.nanmean(arr)
        rms0 = rms

        if iter_i > 1:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                arr[abs(arr - mean) > threshold] = np.nan
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            rms = np.nanstd(arr)

        if iter_i > 1:
            if rms == 0.0:
                ok = True  # return
            elif np.isnan(rms):
                ok = True
            elif abs((rms0 / rms) - 1.0) < 0.01:
                ok = True
    return mean, rms


def get_spec_file_name(root_dirname, psr, channel_number, polarization):
    return root_dirname + f"OutputData/{psr.psr_name_date_time}/DynamicSpectrum/ch0{str(channel_number)}/" + \
           f"ch0{str(channel_number)}_{psr.psr_name_date_time}" + '_' + polarization + ".spec"


def get_average_pulse_file_name(root_dirname, psr, channel_number, polarization):
    return root_dirname + f"OutputData/{psr.psr_name_date_time}/AveragePulseProfile/ch0{str(channel_number)}/" + \
           f"ch0{str(channel_number)}_{psr.psr_name_date_time}" + '_' + polarization + ".app"


def get_pulse_mask_filename(channel_number, root_dirname, polarization, psr):
    return root_dirname + f"OutputData/{psr.psr_name_date_time}/AveragePulseProfile/ch0{str(channel_number)}/" + \
           f"ch0{str(channel_number)}_{psr.psr_name_date_time}" + '_' + polarization + ".mask"


def get_average_spectrum_filename(channel_number, root_dirname, polarization, psr):
    return root_dirname + f"OutputData/{psr.psr_name_date_time}/AveragePulseProfile/ch0{str(channel_number)}/" + \
           f"ch0{str(channel_number)}_{psr.psr_name_date_time}" + '_' + polarization + ".avs"


def get_time_series_filename(channel_number, root_dirname, polarization, psr):
    return root_dirname + f"OutputData/{psr.psr_name_date_time}/TimeSeries/ch0{str(channel_number)}/" + \
           f"ch0{str(channel_number)}_{psr.psr_name_date_time}" + '_' + polarization + ".ts"


def get_binned_time_series_filename(channel_number, root_dirname, polarization, psr):
    return root_dirname + f"OutputData/{psr.psr_name_date_time}/TimeSeries/ch0{str(channel_number)}/" + \
           f"ch0{str(channel_number)}_{psr.psr_name_date_time}" + '_' + polarization + "_binned.ts"


def get_pulse_stack_filename(channel_number, root_dirname, polarization, psr):
    return root_dirname + f"OutputData/{psr.psr_name_date_time}/TimeSeries/ch0{str(channel_number)}/" + \
           f"ch0{str(channel_number)}_{psr.psr_name_date_time}" + '_' + polarization + ".pstack"


def get_integrated_pulse_stack_filename(channel_number, root_dirname, polarization, psr):
    return root_dirname + f"OutputData/{psr.psr_name_date_time}/TimeSeries/ch0{str(channel_number)}/" + \
           f"ch0{str(channel_number)}_{psr.psr_name_date_time}" + '_' + polarization + ".integrated"


def get_pulse_stack_properties_filename(root_dirname):
    return root_dirname + f"AnalysisPackages/resources/pulse_stack_properties.txt"
