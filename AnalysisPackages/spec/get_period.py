import configparser
import sys
import warnings
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

#np.linspace(1272, 1275, 301)
from AnalysisPackages.spec.getaveragepulse import main

config = configparser.ConfigParser()

if __name__ == '__main__':
    #1273.485
    period_linspace = np.linspace(1272, 1275, 301)
    root_dirname = str(Path(__file__).parent.parent.parent.absolute())
    config_filename = root_dirname + '/AnalysisPackages/resources/config.txt'
    config.read(config_filename)
    result = np.zeros(period_linspace.shape)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        for i in range(period_linspace.shape[0]):
            config.set('pulsar-config', 'period', str(period_linspace[i]))
            with open(config_filename, 'w') as configfile:
                config.write(configfile)

            pulse_profile = main(sys.argv[1], sys.argv[2], sys.argv[3])  # B0834+06_20090725_114903 ch03 XX
            result[i] = np.nansum(np.square(pulse_profile))
            print(period_linspace[i], " , ", result[i])

    plt.plot(period_linspace, result)
    plt.show()