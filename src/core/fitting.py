"""Energy landscape fitting module.

Supports:
- Bell-Evans model
- Friddle model
- DHS model (placeholder)
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
from itertools import product
import matplotlib.pyplot as plt

T = 298.0
KB = 1.38e-23
GAMA = 0.577216


def BE(x_arr: npt.NDArray[np.float64], x_beta: float, k_off: float) -> npt.NDArray[np.float64]:
    """Bell-Evans model for force spectroscopy.

    Args:
        x_arr: Loading rate array
        x_beta: Distance to barrier
        k_off: Unfolding rate at zero force

    Returns:
        Most probable force values
    """
    f_beta = KB * T / x_beta
    return f_beta * np.log(x_arr / f_beta / k_off)


def Friddle(
    x_arr: npt.NDArray[np.float64], x_beta: float, k_off: float, Feq: float
) -> npt.NDArray[np.float64]:
    """Friddle model for force spectroscopy.

    Args:
        x_arr: Loading rate array
        x_beta: Distance to barrier
        k_off: Unfolding rate at zero force
        Feq: Equilibrium force

    Returns:
        Most probable force values
    """
    f_beta = KB * T / x_beta
    return Feq + f_beta * np.log(1 + np.e ** (-1 * GAMA) * x_arr / (k_off * f_beta))


def DHS(
    x_arr: npt.NDArray[np.float64], x_beta: float, k_off: float, dG: float
) -> npt.NDArray[np.float64]:
    """DHS (Dudko-Hummer-Szabo) model placeholder.

    Args:
        x_arr: Loading rate array
        x_beta: Distance to barrier
        k_off: Unfolding rate at zero force
        dG: Activation energy

    Returns:
        Empty array (not implemented)
    """
    return np.array([])


def r2_calculate(
    y_actual: npt.NDArray[np.float64], y_predicted: npt.NDArray[np.float64]
) -> np.float64:
    """Calculate R-squared coefficient of determination.

    Args:
        y_actual: Actual values
        y_predicted: Predicted values

    Returns:
        R-squared value
    """
    sse = np.sum((y_actual - y_predicted) ** 2, axis=1)
    sst = np.sum((y_actual - np.mean(y_actual)) ** 2, axis=1)
    r2 = 1 - sse / sst
    return float(r2)


def fit(
    x_arr: npt.NDArray[np.float64],
    y_arr: npt.NDArray[np.float64],
    bounds: list,
    methods: str = "BE",
    scale_factor: float = 0.3,
    max_iter: int = 5,
) -> dict | bool:
    """Fit energy landscape model to force data.

    Args:
        x_arr: Loading rate array
        y_arr: Force array
        bounds: Parameter bounds
        methods: Fitting method ('BE', 'Friddle', 'DHS')
        scale_factor: Search scale factor
        max_iter: Maximum iterations

    Returns:
        Dictionary with 'r_2' and 'arg' keys, or False if failed
    """
    if methods == "BE":
        arg_num = 2
        if len(bounds) != arg_num:
            return False
        func = BE
    elif methods == "Friddle":
        arg_num = 3
        if len(bounds) == 2:
            bounds = np.vstack((bounds, np.array([[0, y_arr.min()]])))
        if len(bounds) != arg_num:
            return False
        func = Friddle
    elif methods == "DHS":
        return False
        func = DHS
    else:
        return False

    max_r2 = 0.0
    best_arg = np.array([])
    for i in range(max_iter):
        b = np.array(list(product(*[np.linspace(x, y) for x, y in bounds]))).T
        arg = [np.tile(x.reshape(-1, 1), (1, len(x_arr))) for x in b]
        res = func(x_arr, *arg)
        r2 = r2_calculate(res, y_arr)
        index0_1 = np.where((r2 > 0) & (r2 < 1))[0]
        if len(index0_1) == 0:
            break
        max_index = index0_1[r2[index0_1].argmax(axis=0)]
        if max_r2 < r2[max_index]:
            max_r2 = float(r2[max_index])
            max_r2_index = r2.argmax(axis=0)
            best_arg = b.T[max_r2_index]
            bounds = (
                np.tile(best_arg.reshape(-1, 1), (1, 2))
                + np.tile(np.diff(bounds), (1, 2)) * scale_factor * np.array([-1, 1])
            )
            bounds[np.where(bounds < 0)] = 1e-13
        else:
            break

    if len(best_arg) == 0:
        return False
    return {"r_2": max_r2, "arg": best_arg}


def plot(
    x_arr: npt.NDArray[np.float64],
    y_arr: npt.NDArray[np.float64],
    arg: npt.NDArray[np.float64],
    methods: str = "BE",
) -> plt.Figure:
    """Plot fitting results.

    Args:
        x_arr: Loading rate array
        y_arr: Force array
        arg: Fitted parameters
        methods: Fitting method

    Returns:
        Matplotlib figure
    """
    if methods == "BE":
        func = BE
    elif methods == "Friddle":
        func = Friddle
    elif methods == "DHS":
        return plt.figure()
        func = DHS
    else:
        return plt.figure()

    fig, ax = plt.subplots(dpi=100)
    ax.set_xscale("log")
    ax.plot(x_arr * 1e12, y_arr * 1e12, "ro")

    x_ = np.linspace(x_arr.min(), x_arr.max())
    y_ = func(x_, *arg)
    ax.plot(x_ * 1e12, y_ * 1e12)
    ax.set_title(methods)
    ax.set_ylabel("Force(pN)")
    ax.set_xlabel("Loading rate(pN/s)")
    return fig
