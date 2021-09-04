import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy as np


# Fitting function
def func(x, a, b):
    return a * (x**b)
    #return a /(x**2) + b


# Experimental x and y data points
# xData = np.array([120 + 31.25/2, 172 + 31.25/2, 233 + 33/2, 330 + 33/2])
xData = np.array([120, 172, 233, 330])
#yData = np.array([0, 0.02, 0.03, 0.028])*1291.929 # mili seconds
#yData = np.array([0.72, 0.68, 0.61, 0.54])
#yData = np.array([20.5, 19.5, 17.5, 15.5]) *-1
yData = np.array([0.03738847, 0.03541186, 0.03152988, 0.02773245])#delta_phi from angle
#yData = np.array([0.0402, 0.0337, 0.0321, 0.0302])#delta_phi from plot
#yData = np.array([0, 0.02, 0.03, 0.028])

# Plot experimental data points
plt.plot(xData, yData, 'bo', label='data')

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
                                             ' y = a * (b^x)' % tuple(popt))

plt.xlabel("Frequency")
#plt.ylabel(u"Δ"+" T (milli sec)")
plt.ylabel("")
#plt.title(f"Overcompensated DM\nresidual DM = {round(abs(popt[0]) / (4.15 * 10**6), 3)}")
plt.legend()
plt.show()

print(f"\nresidual DM = {abs(popt[0]) / (4.15 * 10**6)}")



# 91596
# 45828
# 25098
# 12227
# 7215
# 2789
# 1699
# 1179
# 0


