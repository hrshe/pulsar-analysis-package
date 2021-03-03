import time
import random
from functools import partial

import numpy as np
from multiprocessing.pool import ThreadPool
from multiprocessing import Pool


def get_robust_mean_rms(input_arr, sigma_threshold):
    arr = np.copy(input_arr)
    ok = False
    iter_i, rms, mean = 0, 0.0, 0.0
    while not ok:
        iter_i += 1
        threshold = rms * sigma_threshold

        mean = np.nanmean(arr)
        rms0 = rms

        if iter_i > 1:
            arr = np.where(abs(arr - mean) <= threshold, arr, np.nan)
        rms = np.nanstd(arr)

        if iter_i > 1:
            if rms == 0.0:
                ok = True  # return
            elif np.isnan(rms):
                ok = True
            elif abs((rms0 / rms) - 1.0) < 0.01:
                ok = True
    return mean, rms


def method1(arr):
    mean, rms = np.zeros(arr.shape[1]), np.zeros(arr.shape[1])
    for i in range(arr.shape[1]):
        mean[i], rms[i] = get_robust_mean_rms(arr[:, i], 3)
    #print(mean)


def f(arr, i):
    return get_robust_mean_rms(arr[:, i], 3)

def method2(arr):
    pool = Pool(3)
    func = partial(f, arr)
    #params = [(i, arr, mean) for i in range(arr.shape[1])]
    results = pool.map(func, range(arr.shape[1]))
    mean = [result[0] for result in results]
    #print(mean)

    # pool.map(f, range(arr.shape[1]))
    # print(mean)


if __name__ == '__main__':
    timeList = []
    n_channels = 256
    a = np.random.random(256 * 100000).reshape(-1, n_channels)
    for i in range(1):
        start = time.perf_counter()
        method1(a)
        timeList.append(time.perf_counter() - start)
    avgTime1 = np.mean(timeList)
    print('average time 1: ', avgTime1)

    timeList = []
    for i in range(1):
        start = time.perf_counter()
        method2(a)
        timeList.append(time.perf_counter() - start)

    avgTime2 = np.mean(timeList)
    print('average time 2: ', avgTime2)

    print("1 is ", str(avgTime2 / avgTime1), " times faster than 2")

# map(l.__getitem__, indexes) is ~100x faster than [l[i] for i in indexes] for getting sublist from indices
# new robust mean/rms 2 is 3.669222832593684 times faster than old implementation
