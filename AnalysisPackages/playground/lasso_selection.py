import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import LassoSelector
from matplotlib import path
from matplotlib.widgets import Button

from AnalysisPackages.utilities import utils

app = np.loadtxt(
    "/Users/hrishikesh.s/RRIProject/pulsar-analysis-package/OutputData/B0809+74/AveragePulseProfile/ch04/ch04_B0809+74_XX.app").T
mean_subtracted = (app.T - utils.get_robust_mean_rms_2d(app.T, 3)[0]).T

app[32: 37, :], mean_subtracted[32: 37, :] = np.nan, np.nan
app[102: 109, :], mean_subtracted[102: 109, :] = np.nan, np.nan
app[194: 200, :], mean_subtracted[194: 200, :] = np.nan, np.nan
mean_subtracted_original = np.copy(mean_subtracted)

fig, ax1 = plt.subplots()
# plt.subplots_adjust(left=0.1, bottom=0.3)
msk = plt.imshow(mean_subtracted, cmap="gray")
# ax1 = fig.add_subplot(111)
# ax1.set_title('lasso selection:')
# msk = ax1.imshow(mean_subtracted, cmap="gray")
# ax1.set_aspect('equal')

# Empty array to be filled with lasso selector
# array = np.copy(mean_subtracted)
# ax2 = fig.add_subplot(212)
# ax2.set_title('numpy array:')
# msk = ax2.imshow(array, vmax=1)
# fig.colorbar(msk)


# Pixel coordinates
xv, yv = np.meshgrid(np.arange(mean_subtracted.shape[1]), np.arange(mean_subtracted.shape[0]))
pix = np.vstack((xv.flatten(), yv.flatten())).T


def updateArray(array, indices):
    lin = np.arange(array.size)
    newArray = array.flatten()
    newArray[lin[indices]] = -9999
    return newArray.reshape(array.shape)


def onselect(verts):
    global mean_subtracted, pix
    p = path.Path(verts)
    ind = p.contains_points(pix, radius=1)
    mean_subtracted = updateArray(mean_subtracted, ind)
    msk.set_data(mean_subtracted)
    fig.canvas.draw_idle()


def close_plot(event):
    plt.close()


def reset_plot(event):
    global mean_subtracted
    mean_subtracted = mean_subtracted_original
    msk.set_data(mean_subtracted)

    
axButtonReset = plt.axes([0.2, 0.1, 0.1, 0.1])
btnReset = Button(ax=axButtonReset, label="Reset", hovercolor="red")
#
axButtonOk = plt.axes([0.7, 0.1, 0.1, 0.1])
btnOk = Button(ax=axButtonOk, label="OK", hovercolor="green")
btnOk.on_clicked(close_plot)
btnReset.on_clicked(reset_plot)
lasso = LassoSelector(ax1, onselect)
plt.show()

print("hello world")
print(mean_subtracted)
mean_subtracted[mean_subtracted != -9999] = 1
mean_subtracted[np.isnan(mean_subtracted)] = 1
mean_subtracted[mean_subtracted == -9999] = np.nan
# np.savetxt("ch04_B0809+74_YY.mask", mean_subtracted)
plt.imshow(mean_subtracted)
plt.show()
