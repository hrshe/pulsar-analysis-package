import numpy as np

"""
Purpose of this file is to execute rough patches of code... Not to be included in final project
"""

dyn_spectrum = np.arange(1, 34).reshape(-1, 3)
n_integration = 5
n_channels = 3

remainder = len(dyn_spectrum) % n_integration
dyn_spectrum = np.vstack([dyn_spectrum, [np.array([np.nan, np.nan, np.nan])] * (n_integration - remainder)])
print(len(dyn_spectrum) % n_integration)
reshaped = dyn_spectrum.reshape(n_integration, -1, n_channels, order="F")

print("dyn spec:\n")
print(dyn_spectrum)

print("\n\nreshaped dyn spec: \n")
print(reshaped)

print("\n\nintegrated dyn spec: \n")
print(np.nanmean(reshaped, axis=0))


f_x 	=	open("sample.txt", "ab")
np.savetxt(f_x, dyn_spectrum, fmt='%1.3f')
f_x.close()