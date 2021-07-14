import sys

import numpy as np

from AnalysisPackages.utilities import utils

"""
Purpose of this file is to execute rough patches of code... Not to be included in final project
"""


def main(file_name, polarization):
    a = np.random.normal(0.5, 0.1, 400)
    a[20:25] = 0.9
    print("first")
    print(f"({np.mean(a)}, {np.std(a)}")
    print("second")
    print(utils.get_robust_mean_rms(a, 3))
    print(utils.get_robust_mean_rms_nan(a, 3))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])  # ch03_B0834+06_20090725_114903 XX
