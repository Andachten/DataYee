"""Clustering module for force curve similarity analysis.

Supports:
- DTW (Dynamic Time Warping) distance matrix
- KMeans clustering
- Similarity sorting
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
from sklearn.cluster import KMeans
from sklearn.neighbors import KernelDensity
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.file_io import forcecurve, loadjpkfile, zipfileopera

from src.core.data_processing import wlc2lc


def WLC_transformer(
    f: npt.NDArray[np.float64],
    x: npt.NDArray[np.float64],
    thre: float = 30,
) -> tuple:
    """Transform force-extension data to contour length.

    Args:
        f: Force array
        x: Extension array
        thre: Force threshold

    Returns:
        Tuple of (force, contour_length)
    """
    x = x[np.where(f > thre)].astype(complex) * 1e-9
    f = f[np.where(f > thre)].astype(complex) * 1e-12
    p = np.array([0.36e-9], dtype=complex)
    lc = wlc2lc(x, f, p)
    return f, lc


def Lc_transformer(
    data_x: npt.NDArray[np.float64],
    data_y: npt.NDArray[np.float64],
    length: int = 400,
    step: int = 2,
    thre: float = 30,
) -> npt.NDArray[np.float64]:
    """Transform force curve to contour length distribution.

    Args:
        data_x: Height data
        data_y: Force data
        length: Output array length
        step: Step size
        thre: Force threshold

    Returns:
        KDE density values
    """
    f, x = WLC_transformer(data_y, data_x, thre=thre)
    x, f = x.real * 1e9, f.real * 1e12
    if len(x) <= 10:
        return np.zeros(len(np.arange(0, length, step)))
    kde = KernelDensity(kernel="gaussian", bandwidth=2).fit(x.reshape(-1, 1))
    x_ = np.arange(0, length, step)
    log_dens = kde.score_samples(x_.reshape(-1, 1))
    return np.exp(log_dens)


def count_0(x: npt.NDArray[np.float64]) -> int:
    """Count non-overlapping maximum points.

    Args:
        x: Array of (dlc, force) points

    Returns:
        Count of non-overlapping maxima
    """
    x_ = np.array([])
    for i in x:
        if len(x_) == 0:
            x_ = i.reshape(1, 2)
        if i[0] > x_[:, 0].max() and i[1] > x_[:, 1].max():
            x_ = np.vstack((x_, i))
    return len(x_)


def wlc_dist(s1: npt.NDArray[np.float64], s2: npt.NDArray[np.float64], dlc_thre: float = 5, f_thre: float = 30) -> float:
    """Calculate WLC distance between two force curves.

    Args:
        s1: First curve data
        s2: Second curve data
        dlc_thre: DLC threshold
        f_thre: Force threshold

    Returns:
        Distance value (0-1)
    """
    s1 = np.delete(s1, np.where(s1 == 0)[0])
    s2 = np.delete(s2, np.where(s2 == 0)[0])
    s1_dlc = s1[: len(s1) // 2]
    s2_dlc = s2[: len(s1) // 2]
    score = max(len(s1_dlc), len(s2_dlc))
    s1_ = np.tile(s1_dlc, (len(s2_dlc), 1))
    s2_ = np.tile(s2_dlc.reshape(-1, 1), (1, len(s1_dlc)))
    matrix_dlc = np.abs(s1_ - s2_)
    arr_coor = np.dstack(np.where(matrix_dlc <= dlc_thre))[0]
    reduct = max(count_0(arr_coor), count_0(arr_coor[arr_coor[:, 1].argsort()]))
    return 1 - reduct / score


def distance(s1: npt.NDArray[np.float64], s2: npt.NDArray[np.float64]) -> float:
    """Calculate DTW distance between two sequences.

    Args:
        s1: First sequence
        s2: Second sequence

    Returns:
        DTW distance
    """
    from dtaidistance import dtw
    return dtw.distance(s1, s2, window=int(0.25 * len(s1)), penalty=0.2, use_c=True)


def get_lcseq(
    zpo: "zipfileopera",
    ljp: "loadjpkfile",
    indexlst: list,
    length: int = 400,
    step: int = 2,
    thre: float = 30,
) -> npt.NDArray[np.float64]:
    """Get contour length sequences for multiple force curves.

    Args:
        zpo: Archive manager
        ljp: File loader
        indexlst: List of curve indices
        length: Sequence length
        step: Step size
        thre: Force threshold

    Returns:
        Array of contour length sequences
    """
    from src.core.file_io import forcecurve

    fc = forcecurve()
    arr = np.array([])
    for i, index in enumerate(indexlst):
        fc.data = zpo[index]
        fc.recover_force(ljp)
        data = fc.get_prodata()["retract"]
        data_x = data["measuredHeight"] * 1e9
        data_y = data["vDeflection"] * 1e12
        res = Lc_transformer(data_x, data_y, length=length, step=step, thre=thre)
        if res.max() > 0:
            res = res / res.max()
        if len(arr) != 0:
            try:
                arr = np.vstack((arr, res))
            except Exception as err:
                print(i, err)
        else:
            arr = res
    return arr


def get_distmatrix(
    zpo: "zipfileopera",
    ljp: "loadjpkfile",
    m_run,
    length: int = 400,
    step: int = 2,
    thre: float = 30,
    parallel: bool = True,
    multip_n: int = 1,
) -> npt.NDArray[np.float64]:
    """Calculate DTW distance matrix for all force curves.

    Args:
        zpo: Archive manager
        ljp: File loader
        m_run: Multiprocessing runner
        length: Sequence length
        step: Step size
        thre: Force threshold
        parallel: Use multiprocessing
        multip_n: Number of processes

    Returns:
        Distance matrix
    """
    from dtaidistance import dtw

    if not parallel:
        arr = np.array(get_lcseq(zpo, ljp, range(len(zpo)), length, step, thre))
    else:
        print("multiprocessing")
        lens = len(zpo)
        step = int(lens / multip_n) + 1
        arg_lst = []
        m_run.createPool(multip_n)
        for i in range(0, lens, step):
            if i + step < len(zpo):
                arg_lst.append((zpo, ljp, range(i, i + step), length, step, thre))
            else:
                arg_lst.append((zpo, ljp, range(i, len(zpo)), length, step, thre))
        m_run.inputTask(get_lcseq, arg_lst)
        arr = np.vstack(m_run.results)

    matrix = dtw.distance_matrix(
        arr, window=25, penalty=0.2, use_c=True, parallel=True
    )
    return matrix


def sort_similar(index: int, matrix: npt.NDArray[np.float64]) -> npt.NDArray[np.int64]:
    """Sort indices by similarity to a reference curve.

    Args:
        index: Reference curve index
        matrix: Distance matrix

    Returns:
        Sorted indices
    """
    arr = matrix[index, :]
    return arr.argsort()


def KMsClustering(matrix: npt.NDArray[np.float64], n_clusters: int = 8) -> npt.NDArray[np.int64]:
    """Perform KMeans clustering on distance matrix.

    Args:
        matrix: Distance matrix
        n_clusters: Number of clusters

    Returns:
        Cluster labels
    """
    km = KMeans(n_clusters=n_clusters, precompute_distances=True).fit(matrix)
    return km.labels_


def multi_run(
    zpo: "zipfileopera",
    ljp: "loadjpkfile",
    length: int,
    step: int,
    thre: float,
    multip_n: int = 4,
) -> list:
    """Run multiprocessed LC sequence extraction.

    Args:
        zpo: Archive manager
        ljp: File loader
        length: Sequence length
        step: Step size
        thre: Force threshold
        multip_n: Number of processes

    Returns:
        List of results
    """
    from multiprocessing import Pool

    lens = len(zpo)
    step = int(lens / multip_n) + 1
    lst = []
    for i in range(0, lens, step):
        if i + step < len(zpo):
            lst.append(range(i, i + step))
        else:
            lst.append(range(i, i + step - 1))
    pool = Pool(len(lst))
    result = []
    print(lst)
    for indexlst in lst:
        result.append(pool.apply_async(get_lcseq, (zpo, ljp, indexlst, 400, 2, 30)))
    pool.close()
    pool.join()
    return result
