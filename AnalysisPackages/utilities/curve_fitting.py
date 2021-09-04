import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy as np


# Fitting function
def func(x, a, b):
    return a / (x**2) + b


# Experimental x and y data points
xData = np.array([120 + 31.25/2, 172 + 31.25/2, 233 + 33/2, 330 + 33/2])
yData = np.array([0, 0.02, 0.03, 0.028])*1291.929 # mili seconds
# yData = np.array([0, 0.02, 0.03, 0.033])

# Plot experimental data points
plt.plot(xData, yData, 'bo', label='experimental-data')

# Initial guess for the parameters
initialGuess = [1.0, 1.0]

# Perform the curve-fit
popt, pcov = curve_fit(func, xData, yData, initialGuess)
print(popt)
print(pcov)

# x values for the fitted function
xFit = np.arange(100, 350, 0.01)

# Plot the fitted function
plt.plot(xFit, func(xFit, *popt), 'r', label='fit params: a=%5.3f, b=%5.3f \n'
                                             ' y = a / (x**2) + b' % tuple(popt))

plt.xlabel("Frequency")
plt.ylabel(u"Δ"+" T (milli sec)")
plt.title(f"Overcompensated DM\nresidual DM = {round(abs(popt[0]) / (4.15 * 10**6), 3)}")
plt.legend()
plt.show()

print(f"\nresidual DM = {abs(popt[0]) / (4.15 * 10**6)}")

