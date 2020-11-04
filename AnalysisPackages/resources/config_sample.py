import numpy as np
import configparser
from pathlib import Path

config = configparser.ConfigParser()


def populate_config(filename):
    config.read(filename)
    print("\n\n" + filename + " will be updated")


def time_delay_2_col_delay(t):
    return t * (32150 / 512)


def calculate_time_delay(dm, band, reference_band):
    return 4.15 * 1000000 * dm * ((1 / get_band_upper_freq(band)) ** 2 - (1 / get_band_upper_freq(reference_band)) ** 2)


def get_band_upper_freq(band):  # in MHz
    try:
        bw = float(config.get('channel-' + str(band) + '-specific', 'sampling_frequency')) / 2
        cf = float(config.get('channel-' + str(band) + '-specific', 'central_frequency'))
    except configparser.NoSectionError:
        print('section ' + '[channel-' + str(band) + '-specific] does not exist... skipping')
    return cf + (bw / 2)


def config_write(filename):
    with open(filename, 'w') as configfile:
        config.write(configfile)


def config_set_sync_dispersion_delay_packet_frequency(channel_number, sync_dispersion_delay_packet):
    try:
        config.set('channel-' + str(channel_number) + '-specific', 'sync_dispersion_delay_packet',
                   str(sync_dispersion_delay_packet))
    except configparser.NoSectionError:
        print('[channel-' + str(channel_number) + '-specific] section not found. Creating new section')
        config['channel-' + str(channel_number) + '-specific'] = {
            'sync_dispersion_delay_packet': str(sync_dispersion_delay_packet)}


def populate_all_channels_sync_dispersion_delay_packet():
    root_dirname = str(Path(__file__).parent.parent.parent.absolute())
    config_filename = root_dirname + '/AnalysisPackages/resources/config.txt'
    populate_config(config_filename)
    ref_band = 9
    n_channels = int(config.get('pulsar-config', 'n_channels'))
    dm = float(config.get('pulsar-config', 'dm'))
    time_delay = np.zeros(n_channels)

    # for i in range(9):
    #     time_delay[0, i] = calculate_time_delay(dm, i + 1, ref_band)  # other dm is 5.7

    print("Skip packets for dispersion delay compensation:")
    for i in range(n_channels):
        time_delay[i] = time_delay_2_col_delay(calculate_time_delay(dm, i + 1, ref_band))
        print("ch:" + str(i + 1) + "	" + str(time_delay[i]))

    for i in range(1, n_channels + 1):
        config_set_sync_dispersion_delay_packet_frequency(i, int(time_delay[i - 1]))
    config_write(config_filename)


populate_all_channels_sync_dispersion_delay_packet()
