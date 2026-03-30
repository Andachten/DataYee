"""Core data processing functions for force curve analysis

This module contains functions for:
- Noise filtering (Savitzky-Golay filter)
- Baseline correction
- Peak detection
- WLC (Worm-Like Chain) fitting
- DLC (Contour Length Difference) calculation
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
from scipy.signal import savgol_filter, find_peaks
from scipy.optimize import curve_fit
from scipy.ndimage import gaussian_filter
import matplotlib.pyplot as plt
from PIL import Image
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.force_curve import ForceCurveData

# Constants
KB = 1.3806e-23
T = 298.0


def lcfunc(x: npt.NDArray[np.float64], lc: float, lp: float) -> npt.NDArray[np.float64]:
    """WLC (Worm-Like Chain) force function.

    Args:
        x: Distance in meters
        lc: Contour length in meters
        lp: Persistence length in meters

    Returns:
        Force in Newtons
    """
    return KB * T / lp * (1 / 4 * (1 - x / lc) ** (-2) + x / lc - 1 / 4)


def wlc2lc(
    x: npt.NDArray[np.float64],
    f: npt.NDArray[np.float64],
    lp: npt.NDArray[np.float64],
) -> npt.NDArray[np.float64]:
    """Convert force and extension to contour length using WLC model.

    Args:
        x: Extension in meters
        f: Force in Newtons
        lp: Persistence length in meters

    Returns:
        Contour length in meters
    """
    kb = KB
    T_val = T
    lc = (
        4 * f * lp * x + 3 * kb * T_val * x
    ) / (6 * f * lp) - (
        -16 * f**2 * lp**2 * x**2
        + 12 * f * kb * lp * T_val * x**2
        - 36 * kb**2 * T_val**2 * x**2
    ) / (
        12 * 2**(2 / 3) * f * lp
        * (
            -16 * f**3 * lp**3 * x**3
            + 72 * f**2 * kb * lp**2 * T_val * x**3
            - 27 * f * kb**2 * lp * T_val**2 * x**3
            + 54 * kb**3 * T_val**3 * x**3
            + 3
            * (3) ** 0.5
            * (
                -64 * f**5 * kb * lp**5 * T_val * x**6
                + 144 * f**4 * kb**2 * lp**4 * T_val**2 * x**6
                - 108 * f**3 * kb**3 * lp**3 * T_val**3 * x**6
                + 135 * f**2 * kb**4 * lp**2 * T_val**4 * x**6
            )
            ** 0.5
        )
        ** (1 / 3)
    ) + (
        -16 * f**3 * lp**3 * x**3
        + 72 * f**2 * kb * lp**2 * T_val * x**3
        - 27 * f * kb**2 * lp * T_val**2 * x**3
        + 54 * kb**3 * T_val**3 * x**3
        + 3
        * (3) ** 0.5
        * (
            -64 * f**5 * kb * lp**5 * T_val * x**6
            + 144 * f**4 * kb**2 * lp**4 * T_val**2 * x**6
            - 108 * f**3 * kb**3 * lp**3 * T_val**3 * x**6
            + 135 * f**2 * kb**4 * lp**2 * T_val**4 * x**6
        )
        ** 0.5
    ) ** (1 / 3) / (6 * 2 ** (1 / 3) * f * lp)
    return lc


def lcfunc1d(x: float, lc: float, lp: float) -> float:
    """Simplified 1D WLC force function.

    Args:
        x: Distance in nm
        lc: Contour length in nm
        lp: Persistence length in nm

    Returns:
        Force in pN
    """
    return 4.114188 * (1 / lc + 0.5 / (lc * (1 - x / lc) ** 3)) / lp


def rotate(
    data_x: npt.NDArray[np.float64],
    data_y: npt.NDArray[np.float64],
    index: int | tuple,
    k: float,
) -> npt.NDArray[np.float64]:
    """Rotate data around a point.

    Args:
        data_x: X data array
        data_y: Y data array
        index: Rotation point (index or tuple of coordinates)
        k: Rotation coefficient

    Returns:
        Rotated y data
    """
    theta = np.arctan(k) * -1
    if isinstance(index, int):
        return (
            (data_x - data_x[index]) * np.sin(theta)
            + (data_y - data_y[index]) * np.cos(theta)
            + data_y[index]
        )
    elif isinstance(index, tuple):
        return (
            (data_x - index[0]) * np.sin(theta)
            + (data_y - index[1]) * np.cos(theta)
            + index[1]
        )
    return data_y


def get_slope(
    x_arr: npt.NDArray[np.float64],
    y_arr: npt.NDArray[np.float64],
    index: int = -1,
) -> float:
    """Calculate slope at a point using polynomial fit.

    Args:
        x_arr: X data array
        y_arr: Y data array
        index: Index at which to calculate slope

    Returns:
        Slope value
    """
    p = np.polyfit(x_arr, y_arr, 1)
    d = np.polyder(p)
    return float(np.polyval(d, x_arr[index]))


def fig2img(fig: plt.Figure) -> Image.Image:
    """Convert matplotlib figure to PIL Image.

    Args:
        fig: Matplotlib figure

    Returns:
        PIL Image
    """
    fig.canvas.draw()
    return Image.frombytes("RGB", fig.canvas.get_width_height(), fig.canvas.tostring_rgb())


def wlc_k_f_nox(lc: float, k: float) -> float:
    """Calculate force from WLC parameters.

    Args:
        lc: Contour length
        k: Loading rate

    Returns:
        Force in pN
    """
    lp = 0.36
    x = (
        -1.028547**6 * lc + 250000 * k * lc**2 * lp
    ) / (-1.028547**6 + 250000 * k * lc * lp) + (
        80.11823662350369
        * (
            -1.057908931209**12 * lc**3
            + 5.142735**11 * k * lc**4 * lp
            - 6.25**10 * k**2 * lc**5 * lp**2
        )
        ** (1 / 3)
    ) / (-1.028547**6 + 250000 * k * lc * lp)
    f = KB * T / (lp * 1e-9) * (1 / 4 * (1 - x / lc) ** (-2) + x / lc - 1 / 4) * 1e12
    return f


def is_number(s: str) -> bool:
    """Check if a string represents a number.

    Args:
        s: String to check

    Returns:
        True if s is a number
    """
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False


# ============================================================================
# Force Curve Processing Functions
# ============================================================================


def noise_down(fc: ForceCurveData) -> None:
    """Apply Savitzky-Golay noise filtering to force curve.

    Args:
        fc: Force curve data object
    """
    data_y = fc.data["rawdata"]["retract"]["vDeflection"] * 1e12
    r = 0.9
    data_y_right = data_y[:, 0][int(r * len(data_y)) :]
    data_y_right_smth = gaussian_filter(data_y_right, 21)
    for s in np.arange(17)[3::2]:
        err = np.abs(
            savgol_filter(data_y[:, 0][int(r * len(data_y)) :], s, 2)
            - data_y_right_smth
        ).mean()
        if err < 4:
            break
    fc.data["filters"]["win_lens"] = 19


def cal_baseline_drift(fc: ForceCurveData) -> None:
    """Calculate baseline drift correction.

    Args:
        fc: Force curve data object
    """
    fc.data["offset"]["k"] = 0
    data = fc.get_prodata()["retract"]
    data_x, data_y = data["measuredHeight"], data["vDeflection"]
    if len(fc.data["peakindex"]) == 0:
        index = int(len(data_x) * 0.9)
        k = get_slope(data_x[index:].reshape(-1), data_y[index:].reshape(-1))
    else:
        k = 0
    fc.data["offset"]["k"] = k


def cal_baseline_y(fc: ForceCurveData) -> None:
    """Calculate baseline Y offset.

    Args:
        fc: Force curve data object
    """
    fc.data["offset"]["y"] = 0
    data = fc.get_prodata()["retract"]
    data_y = data["vDeflection"]
    index = int(len(data_y) * 0.9)
    fc.data["offset"]["y"] = data_y[index:].mean() * -1


def cal_baseline_x(fc: ForceCurveData) -> None:
    """Calculate baseline X offset.

    Args:
        fc: Force curve data object
    """
    fc.data["offset"]["x"] = 0
    data = fc.get_prodata()["retract"]
    data_x = data["measuredHeight"]
    fc.data["offset"]["x"] = data_x[0]


def cal_highspeed_drift(fc: ForceCurveData) -> None:
    """Calculate high-speed drift correction.

    Args:
        fc: Force curve data object
    """
    fc.data["offset"]["highspeed"] = 0
    if not fc.data["arg"]["highspeed"]:
        return None
    data = fc.get_prodata()
    data_retract_y = data["retract"]["vDeflection"]
    data_extend_y = data["extend"]["vDeflection"]
    data_retract_x = data["retract"]["measuredHeight"]
    data_extend_x = data["extend"]["measuredHeight"]
    retract_index = int(0.9 * len(data_retract_y))
    extend_index = int(0.1 * len(data_extend_y))
    if data_extend_x[0] > data_retract_x[retract_index]:
        corr = data_extend_y[:extend_index].mean() - data_retract_y[retract_index:].mean()
    else:
        corr = 0
    if corr > 40e-12 or corr < 0:
        return None
    fc.data["offset"]["highspeed"] = 0.5 * corr


def findpeak(fc: ForceCurveData) -> None:
    """Find peaks (unfolding events) in force curve.

    Args:
        fc: Force curve data object
    """
    fc.data["peakindex"] = np.array([], dtype=np.uint16)
    fc.data["bottomindex"] = np.array([], dtype=np.uint16)
    data = fc.get_prodata(tip_correc=False)["retract"]
    data_x = data["measuredHeight"] * 1e9
    data_y = data["vDeflection"] * 1e12
    d = np.gradient(np.gradient(gaussian_filter(data_y[:, 0], 13)))
    index_noise = int(len(d) * 0.9)
    noise = np.abs(d[index_noise:]).max() * 1.1
    index_xlim = np.where(data_x > fc.data["arg"]["xlim"])[0][0]
    d = d[index_xlim:]
    distance = len(data_x) - np.where(data_x < data_x[-1] - fc.data["arg"]["xsens"])[0][-1]
    p = find_peaks(d * -1, height=noise, distance=distance)[0] + index_xlim
    b = find_peaks(d, height=noise, distance=distance)[0] + index_xlim
    for p_i in p:
        temp_array = data_x[b] - data_x[p_i]
        i = np.where(temp_array > 0, temp_array, np.inf)
        if len(i) == 0:
            continue
        b_i = b[i.argmin()]
        if p_i < b_i:
            if (
                len(fc.data["peakindex"]) != 0
                and data_x[int(p_i)] - data_x[int(fc.data["peakindex"][-1])]
                < fc.data["arg"]["xsens"]
            ):
                continue
            y = rotate(
                data_x[p_i - distance : b_i],
                data_y[p_i - distance : b_i],
                distance,
                -0.07,
            )
            p_i = p_i - distance + np.argmax(y)
            k = np.polyval(
                np.polyder(
                    np.polyfit(
                        data_x[b_i : b_i + 300][:, 0],
                        data_y[b_i : b_i + 300][:, 0],
                        1,
                    )
                ),
                data_x[b_i],
            )
            y = rotate(
                data_x[p_i : b_i + distance],
                data_y[p_i : b_i + distance],
                b_i - p_i,
                k - 0.07,
            )
            b_i = p_i + np.argmin(y)
            fsens = data_y[p_i] - data_y[b_i]
            if fsens > fc.data["arg"]["sens"]:
                fc.data["peakindex"] = np.append(fc.data["peakindex"], p_i)
                fc.data["bottomindex"] = np.append(fc.data["bottomindex"], b_i)
    fc.data["peakindex"] = list(fc.data["peakindex"].astype(np.uint16))
    fc.data["bottomindex"] = list(fc.data["bottomindex"].astype(np.uint16))


def wlcfit(fc: ForceCurveData) -> None:
    """Fit WLC model to peaks.

    Args:
        fc: Force curve data object
    """
    fc.data["wlcarg"] = []
    fc.data["slopepre"] = []
    n = 50
    data = fc.get_prodata()["retract"]
    data_x = data["measuredHeight"].reshape(-1) * 1e9
    data_y = data["vDeflection"].reshape(-1) * 1e12
    lp = fc.data["arg"]["lp"]
    for i, p_i in enumerate(fc.data["peakindex"]):
        try:
            b_i_arr = np.where(p_i > fc.data["bottomindex"])[0]
        except Exception:
            b_i_arr = np.array([], dtype=np.uint16)
        if len(b_i_arr) != 0:
            b_i = fc.data["bottomindex"][b_i_arr[-1]]
        else:
            temp = int(p_i)
            while temp - n > 0:
                k_slope = get_slope(
                    data_x[temp - n : temp], data_y[temp - n : temp]
                )
                if k_slope < 0.01 or data_x[temp] < 10:
                    if temp == p_i:
                        temp -= 10
                    break
                else:
                    temp -= n
            b_i = temp
            if b_i == p_i:
                b_i -= 3
        if data_y[p_i] > 150:
            dy = data_y[p_i] - data_y[b_i]
            fitpoint = np.where(data_y[b_i:] > data_y[b_i] + 0.6 * dy)[0][0] + b_i
        else:
            fitpoint = p_i
        if fitpoint == b_i:
            fitpoint += 20
        try:
            popt, _ = curve_fit(
                lcfunc,
                data_x[b_i:fitpoint],
                data_y[b_i:fitpoint],
                bounds=([data_x[p_i], lp[0]], [data_x[p_i] + 50, lp[1]]),
            )
        except Exception:
            popt = (
                WRC_transformer(
                    data_y[b_i:fitpoint], data_x[b_i:fitpoint], thr=5
                )[1].mean(),
                0.36,
            )
        try:
            popt_pre, _ = curve_fit(
                lcfunc,
                data_x[b_i:p_i],
                data_y[b_i:p_i],
                bounds=([data_x[p_i], 0], [data_x[p_i] + 50, 0.5]),
            )
        except Exception:
            popt_pre = (
                WRC_transformer(
                    data_y[b_i:p_i], data_x[b_i:p_i], thr=5
                )[1].mean(),
                0.36,
            )
        lc, p = popt
        fc.data["wlcarg"].append((lc, p))
        fc.data["slopepre"].append((popt_pre[0], popt_pre[1]))
    fc.data["wlcarg"] = list(fc.data["wlcarg"])


def peakH(fc: ForceCurveData) -> None:
    """Filter peaks by height.

    Args:
        fc: Force curve data object
    """
    peakindex = list(fc.data["peakindex"].copy())
    fc.data["peakindex"] = []
    data = fc.get_prodata()["retract"]
    data_y = data["vDeflection"].reshape(-1) * 1e12
    for p_i in peakindex:
        if data_y[p_i] >= fc.data["arg"]["peakH"]:
            fc.data["peakindex"].append(p_i)


def peakN(fc: ForceCurveData) -> None:
    """Check if number of peaks is within acceptable range.

    Args:
        fc: Force curve data object
    """
    peakN_range = fc.data["arg"]["peakN"]
    peaknum = len(fc.data["peakindex"])
    if peaknum >= peakN_range[0] and peaknum <= peakN_range[1]:
        fc.data["peaknum_judge"] = True
    else:
        fc.data["peaknum_judge"] = False


def slope(fc: ForceCurveData) -> None:
    """Calculate loading rates for peaks.

    Args:
        fc: Force curve data object
    """
    fc.data["k"] = np.array([])
    data = fc.get_prodata()["retract"]
    data_x = data["measuredHeight"].reshape(-1) * 1e9
    data_y = data["vDeflection"].reshape(-1) * 1e12
    if fc.data["tasktype"] == "smfs":
        for i, arg in enumerate(fc.data["slopepre"]):
            k_val = lcfunc1d(data_x[fc.data["peakindex"][i]], *arg)
            fc.data["k"] = np.append(fc.data["k"], k_val)
    elif fc.data["tasktype"] == "cell_curve":
        n = int(0.05 * len(data_x))
        for i, p_i in enumerate(fc.data["peakindex"]):
            if len(data_x[p_i - n : p_i]) > 0:
                x = data_x[p_i - n : p_i]
                y = data_y[p_i - n : p_i]
                k_val = get_slope(x, y)
            else:
                k_val = 5
            fc.data["k"] = np.append(fc.data["k"], k_val)
    fc.data["k"] = list(fc.data["k"])


def countdlc(fc: ForceCurveData) -> None:
    """Calculate contour length differences between consecutive peaks.

    Args:
        fc: Force curve data object
    """
    lc = np.array([])
    for arg in fc.data["wlcarg"]:
        lc = np.append(lc, arg[0])
    fc.data["dlc"] = np.diff(lc)


def mkbaseondlc(fc: ForceCurveData) -> None:
    """Assign markers to peaks based on DLC ranges.

    Args:
        fc: Force curve data object
    """
    dic = fc.data["arg"]["mark"]
    fc.data["mark"] = []
    dlc = fc.data["dlc"]
    for i in range(len(dlc)):
        found = False
        for m, rang in dic.items():
            if dlc[i] > rang[0] and dlc[i] < rang[1]:
                fc.data["mark"].append(m)
                found = True
                break
        if not found:
            fc.data["mark"].append("none")


def findpeak_smallrange(data_y: npt.NDArray[np.float64], height: float = 10) -> np.ndarray:
    """Find peaks in a small range of data.

    Args:
        data_y: Y data array
        height: Minimum peak height

    Returns:
        Array of peak indices
    """
    for prominence in range(3, 60, 2):
        p, _ = find_peaks(data_y, height=height, prominence=15, distance=10)
        if len(p) < 3:
            break
    return p


# ============================================================================
# Data Transformation Functions
# ============================================================================


def qmWLC_transformer(
    f: npt.NDArray[np.float64],
    x: npt.NDArray[np.float64],
    thr: float = 30,
    p: float = 0.36,
) -> tuple:
    """Quantum mechanical WLC transformation.

    Args:
        f: Force array
        x: Extension array
        thr: Threshold force
        p: Persistence length

    Returns:
        Tuple of (force, contour_length)
    """
    x = x[np.where(f > thr)] * 1e-9
    f = f[np.where(f > thr)] * 1e-12
    kb = 1.38e-23
    T_val = 298
    p = p * 1e-9
    gama1 = 27.4e-9
    gama2 = 109.8e-9
    ff = f * p / kb / T_val
    b = np.exp(np.sqrt(900 / ff))
    Lc = x / (
        4 / 3
        - 4 / 3 / np.sqrt(ff + 1)
        - 10 * b / np.sqrt(ff) / ((b - 1) ** 2)
        + ff**1.62 / (3.55 + 3.8 * ff**2.2)
    )
    L_0 = Lc / (1 / 2 / gama1 * np.sqrt(gama1**2 + 4 * gama2 * f + 2 * gama2 - gama1))
    state_L = L_0 / 2 / gama2 * (np.sqrt(4 * f * gama2 + gama1**2) - gama1 + 2 * gama2)
    return f * 1e12, state_L * 1e13


def WRC_transformer(
    f: npt.NDArray[np.float64],
    x: npt.NDArray[np.float64],
    thr: float = 20,
) -> tuple:
    """Worm-like chain transformation using Warner-Ratch method.

    Args:
        f: Force array
        x: Extension array
        thr: Threshold force

    Returns:
        Tuple of (force, contour_length)
    """
    b, gama = 0.11e-9, 41 / 180 * np.pi
    kb = 1.38e-23
    T_val = 298
    x = x[np.where(f > thr)] * 1e-9
    f = f[np.where(f > thr)] * 1e-12
    l = b * np.cos(gama / 2) / np.abs(np.log(np.cos(gama)))
    f_b = kb * T_val * l / b**2
    x1 = x[np.where(f < f_b)] / (1 - (4 * f[np.where(f < f_b)] * l / kb / T_val) ** (-0.5))
    x2 = x[np.where(f >= f_b)] / (1 - (2 * f[np.where(f >= f_b)] * b / kb / T_val) ** (-1))
    return np.hstack((f[np.where(f < f_b)], f[np.where(f >= f_b)])) * 1e12, np.hstack((x1, x2)) * 1e9


def WLC_transformer(
    f: npt.NDArray[np.float64],
    x: npt.NDArray[np.float64],
    thr: float = 20,
) -> tuple:
    """WLC transformation.

    Args:
        f: Force array
        x: Extension array
        thr: Threshold force

    Returns:
        Tuple of (force, contour_length)
    """
    x = x[np.where(f > thr)].astype(complex) * 1e-9
    f = f[np.where(f > thr)].astype(complex) * 1e-12
    p = np.array([0.36e-9], dtype=complex)
    lc = wlc2lc(x, f, p)
    return f, lc


def mlti_Gaussian(
    x: npt.NDArray[np.float64], *params: float
) -> npt.NDArray[np.float64]:
    """Multi-Gaussian function for peak fitting.

    Args:
        x: X data array
        *params: Gaussian parameters (center, amplitude, width) triplets

    Returns:
        Y values of multi-Gaussian function
    """
    y = np.zeros_like(x)
    for i in range(0, len(params), 3):
        ctr = params[i]
        amp = params[i + 1]
        wid = params[i + 2]
        y = y + amp * np.exp(-((x - ctr) / wid) ** 2)
    return y


def Lc_transformer(
    data_x: npt.NDArray[np.float64],
    data_y: npt.NDArray[np.float64],
    plottype: str = "hist",
) -> Image.Image:
    """Transform force curve to contour length histogram.

    Args:
        data_x: X data (height)
        data_y: Y data (force)
        plottype: 'hist' or 'scatter'

    Returns:
        PIL Image of the plot
    """
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    f, x = WRC_transformer(data_y, data_x)
    if plottype == "scatter":
        ax.scatter(x, f, s=2, c="#495057")
        img = fig2img(fig)
        plt.close()
        return img
    a = ax.hist(x, bins=int(x.max() - x.min()))
    from sklearn.neighbors import KernelDensity

    kde = KernelDensity(kernel="gaussian", bandwidth=1.5).fit(x.reshape(-1, 1))
    x_ = np.linspace(x.min(), x.max(), int(x.max() - x.min()))
    log_dens = kde.score_samples(x_.reshape(-1, 1))
    p, _ = find_peaks(np.exp(log_dens) / np.exp(log_dens).max(), height=0.15, distance=5)
    guess = []
    bound_start = []
    bound_end = []
    for i in p:
        guess += [x_[i], 25, 1]
        bound_start += [x_[i] - 20, 0, 0]
        bound_end += [x_[i] + 20, 100, 20]
    X = a[1]
    Y = np.append(a[0], 0)
    popt, _ = curve_fit(mlti_Gaussian, X, Y, p0=guess, bounds=(bound_start, bound_end))
    lc = popt[::3]
    for i, l in enumerate(lc):
        if i < len(lc) - 1:
            if i % 2 == 0:
                ax.text(l, a[0].max() + 10, str(round(lc[i + 1] - l, 1)), c="b")
            else:
                ax.text(l, a[0].max() + 5, str(round(lc[i + 1] - l, 1)), c="b")
    fit = mlti_Gaussian(x_, *popt)
    ax.plot(x_, fit, "r")
    ax.set_xlim((lc[0] - 30, lc[-1] + 50))
    img = fig2img(fig)
    plt.close()
    return img


def Lc_transformer_(
    x: npt.NDArray[np.float64], y: npt.NDArray[np.float64]
) -> np.ndarray:
    """Alternative contour length transformation.

    Args:
        x: X data
        y: Y data

    Returns:
        Array of contour lengths
    """
    f, x = WRC_transformer(y, x)
    a = np.histogram(x, bins=int(x.max() - x.min()))
    from sklearn.neighbors import KernelDensity

    kde = KernelDensity(kernel="gaussian", bandwidth=1.5).fit(x.reshape(-1, 1))
    x_ = np.linspace(x.min(), x.max(), int(x.max() - x.min()))
    log_dens = kde.score_samples(x_.reshape(-1, 1))
    p, _ = find_peaks(np.exp(log_dens) / np.exp(log_dens).max(), height=0.15, distance=5)
    guess = []
    bound_start = []
    bound_end = []
    for i in p:
        guess += [x_[i], 25, 1]
        bound_start += [x_[i] - 20, 0, 0]
        bound_end += [x_[i] + 20, 100, 20]
    X = a[1]
    Y = np.append(a[0], 0)
    popt, _ = curve_fit(mlti_Gaussian, X, Y, p0=guess, bounds=(bound_start, bound_end))
    lc = popt[::3]
    return lc


def plotmap(arr: npt.NDArray[np.float64]) -> Image.Image:
    """Create adhesion force map image.

    Args:
        arr: Array of force values

    Returns:
        PIL Image of the map
    """
    lens = int(np.sqrt(len(arr)))
    arr = arr[: lens**2]
    d = arr.reshape((lens, lens))
    d[1::2] = d[1::2][:, ::-1]
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    plt.axis("off")
    cmap = plt.get_cmap("YlOrBr_r")
    im = ax.pcolormesh(np.arange(lens), np.arange(lens), d, cmap=cmap, shading="auto")
    bar = fig.colorbar(im)
    bar.set_label("Force(pN)")
    img = fig2img(fig)
    plt.close()
    return img


def plothist(arr: npt.NDArray[np.float64]) -> Image.Image:
    """Create adhesion force histogram image.

    Args:
        arr: Array of force values

    Returns:
        PIL Image of the histogram
    """
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    ax.hist(arr, bins=50)
    img = fig2img(fig)
    plt.close()
    return img
