import time
import random
import numpy as np

a = [list(np.arange(500)) for i in range(10000)]
b = list(np.arange(500))

timeList = []
for i in range(10):
    start = time.perf_counter()
    a.extend([b]*1000)
    timeList.append(time.perf_counter() - start)
avgTime1 = np.mean(timeList)
print('average time 1: ', avgTime1)

timeList = []
for i in range(10):
    start = time.perf_counter()
    a = a + [b]*1000
    timeList.append(time.perf_counter() - start)

avgTime2 = np.mean(timeList)
print('average time 1: ', avgTime2)

print("1 is ",str(avgTime2/avgTime1), " times faster than 2")


#map(l.__getitem__, indexes) is ~100x faster than [l[i] for i in indexes] for getting sublist from indices