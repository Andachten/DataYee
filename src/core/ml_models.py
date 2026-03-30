"""ML Models for force curve classification.

.. deprecated::
    This module is deprecated and will be removed in a future version.
    The ML classification functionality has been commented out.
    To re-enable, uncomment the relevant sections and ensure torch is installed.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
from typing import Optional
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# NOTE: ML module is deprecated. Commenting out torch-related imports and functions.
# Uncomment if you need ML functionality:
# import torch
# import torch.nn as nn
# import torchvision.transforms as transforms
# from torch.utils.data import Dataset, DataLoader


# ============================================================================
# Feature Extraction (deprecated)
# ============================================================================

def feature_extract(
    fc,
    get_data: bool = False,
    data_len: int = 250,
) -> plt.Figure:
    """Extract features from force curve for ML classification.

    .. deprecated::
        ML classification is deprecated.

    Args:
        fc: Force curve object
        get_data: Return data instead of figure
        data_len: Output data length

    Returns:
        Figure or data array
    """
    # NOTE: This function used to use global `b, a` filter coefficients
    # which caused issues. Global variables are now eliminated.

    # Filter coefficients (moved from global scope)
    b, a = _get_filter_coefficients()

    data = fc.get_prodata(tip_correc=False)["retract"]
    data_y = data["vDeflection"] * 1e12
    d = np.diff(data_y.reshape(-1), prepend=data_y[0])

    from scipy.signal import find_peaks as fp
    from scipy.ndimage import gaussian_filter

    p, _ = fp(gaussian_filter(data_y.reshape(-1), 11), height=20, prominence=10, width=10)
    data_y[np.delete(np.arange(len(data_y)), p)] = 0
    data_y = data_y / data_y.max()
    d = _filtfilt(b, a, d)
    d = d / np.abs(d).max()
    d[np.where(d > -0.11)] = 0

    if get_data:
        d = np.abs(d)
        pk = find_peaks(d)[0]
        new_d = np.zeros(len(d))
        new_d[pk] = d[pk]
        d = new_d
        data_y = data_y.reshape(-1)
        zoom_d = (np.where(d > 0)[0] / len(d) * data_len).astype(np.int16)
        zoom_datay = (np.where(data_y > 0)[0] / len(data_y) * data_len).astype(np.int16)
        new_d, new_datay = np.zeros(data_len), np.zeros(data_len)
        new_d[zoom_d], new_datay[zoom_datay] = d[np.where(d > 0)[0]], data_y[np.where(data_y > 0)[0]]
        return new_d.reshape(-1), new_datay.reshape(-1)

    fig, ax = plt.subplots(figsize=(2.24, 2.24))
    plt.axis("off")
    plt.subplots_adjust(top=1, bottom=0.1, right=1, left=0.1)
    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.gca().yaxis.set_major_locator(plt.NullLocator())
    ax.plot(data_y, color="#364fc7", linewidth=1)
    ax.plot(d, "#c92a2a", linewidth=1)
    plt.close()
    return fig


def _get_filter_coefficients() -> tuple:
    """Get lowpass filter coefficients.

    Returns:
        Tuple of (b, a) filter coefficients
    """
    from scipy.signal import butter, filtfilt
    return _butter_lowpass()


def _butter_lowpass() -> tuple:
    """Create lowpass Butterworth filter.

    Returns:
        Tuple of (b, a) coefficients
    """
    from scipy.signal import butter
    b, a = butter(8, 0.08, "lowpass")
    return b, a


def _filtfilt(b: np.ndarray, a: np.ndarray, data: np.ndarray) -> np.ndarray:
    """Apply zero-phase filtering.

    Args:
        b: Filter numerator coefficients
        a: Filter denominator coefficients
        data: Data to filter

    Returns:
        Filtered data
    """
    from scipy.signal import filtfilt
    return filtfilt(b, a, data)


# ============================================================================
# ML Model Classes (deprecated - commented out)
# ============================================================================

# NOTE: All torch-based models are deprecated. Uncomment if needed.

# class MobileNet:
#     """MobileNet model for image-based classification.
#
#     .. deprecated::
#         ML classification is deprecated.
#     """
#
#     def __init__(self, modeldir: str = "./model/2021-05-20-08-method1.0-acc82-1.7.1+cpu.model"):
#         self.modeldir = modeldir
#         self.loadmodel()
#
#     def loadmodel(self) -> None:
#         self.model = torch.load(self.modeldir, map_location="cpu")
#         self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#         self.model = self.model.to(self.device)
#         self.model.eval()
#         self.transform = transforms.Compose([
#             transforms.Resize(224),
#             transforms.ToTensor(),
#         ])
#
#     def predict_batch(self, batch) -> np.ndarray:
#         with torch.no_grad():
#             out = self.model(batch)
#             _, predicted = torch.max(out, 1)
#             predicted = predicted.numpy()
#         return predicted
#
#     def predict(self, img) -> int:
#         img = self.transform(img)
#         img = img.unsqueeze(0)
#         img = img.to(self.device)
#         with torch.no_grad():
#             py = self.model(img)
#         pb = torch.nn.functional.softmax(py, dim=1)
#         _, predicted = torch.max(pb, 1)
#         classIndex_ = predicted[0]
#         return classIndex_.item()


# class myNet:
#     """Wrapper for ML models (MobileNet or custom CNN).
#
#     .. deprecated::
#         ML classification is deprecated.
#     """
#
#     def __init__(self, datatype: str = "img"):
#         resnetdir = "./model/2021-06-19-12-method3.0-acc80-lr0.004-batch30-1.7.1+cpu.pt"
#         mobilenetdir = "./model/2021-05-20-08-method1.0-acc82-1.7.1+cpu.model"
#         self.datatype = datatype
#         if self.datatype == "img":
#             self.modeldir = mobilenetdir
#         elif self.datatype == "series":
#             self.modeldir = resnetdir
#         self.loadmodel()
#
#     def loadmodel(self) -> None:
#         if self.datatype == "series":
#             self.model = Net()
#             pt = torch.load(self.modeldir, map_location="cpu")
#             self.model.load_state_dict(pt)
#         elif self.datatype == "img":
#             self.model = torch.load(self.modeldir, map_location="cpu")
#         self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#         self.model = self.model.to(self.device)
#         self.model.eval()
#         if self.datatype == "img":
#             self.transform = transforms.Compose([
#                 transforms.Resize(224),
#                 transforms.ToTensor(),
#             ])
#
#     def predict(self, data) -> int:
#         if self.datatype == "img":
#             img = self.transform(data)
#             img = img.unsqueeze(0)
#             img = img.to(self.device)
#             data = img
#         elif self.datatype == "series":
#             data = torch.tensor(data)
#         with torch.no_grad():
#             outputs = self.model(data)
#             _, preds = torch.max(outputs, 1)
#         return preds.detach().numpy()[0]


# class Net(nn.Module):
#     """Custom 1D CNN for series data classification.
#
#     .. deprecated::
#         ML classification is deprecated.
#     """
#
#     def __init__(self, n_output: int = 6):
#         super(Net, self).__init__()
#         self.n_output = n_output
#         self.c1 = nn.Sequential(
#             nn.Conv1d(in_channels=2, out_channels=16, kernel_size=3, padding=1),
#             nn.ReLU(True),
#             nn.Conv1d(in_channels=16, out_channels=32, kernel_size=3, padding=1),
#             nn.MaxPool1d(kernel_size=5),
#         )
#         self.rblock1 = ResidualBlock(32)
#         self.c2 = nn.Sequential(
#             nn.Conv1d(in_channels=32, out_channels=16, kernel_size=3, padding=1),
#             nn.ReLU(True),
#             nn.Conv1d(in_channels=16, out_channels=8, kernel_size=3, padding=1),
#             nn.MaxPool1d(kernel_size=2),
#         )
#         self.rblock2 = ResidualBlock(8)
#         self.c3 = nn.Sequential(
#             nn.Conv1d(in_channels=16, out_channels=8, kernel_size=3, padding=1),
#             nn.ReLU(True),
#             nn.MaxPool1d(kernel_size=5),
#         )
#         self.rblock3 = ResidualBlock(8)
#         self.L = nn.Linear(200, self.n_output)
#         self.r = nn.ReLU(True)
#         self.leakr = nn.LeakyReLU(0.2, inplace=True)
#         self.dropout = nn.Dropout(0.3)
#
#     def forward(self, x):
#         x = self.c1(x)
#         x = self.rblock1(x)
#         x = self.rblock1(x)
#         x = self.c2(x)
#         x = self.rblock2(x)
#         x = self.rblock2(x)
#         x = x.view(x.size(0), -1)
#         x = self.L(x)
#         return x


# class ResidualBlock(nn.Module):
#     """Residual block for CNN.
#
#     .. deprecated::
#         ML classification is deprecated.
#     """
#
#     def __init__(self, channels: int):
#         super(ResidualBlock, self).__init__()
#         self.channels = channels
#         self.conv1 = nn.Conv1d(channels, channels, kernel_size=3, padding=1)
#         self.conv2 = nn.Conv1d(channels, channels, kernel_size=3, padding=1)
#         self.relu = nn.ReLU(inplace=True)
#
#     def forward(self, x):
#         y = self.relu(self.conv1(x))
#         y = self.conv2(y)
#         return self.relu(x + y)


# class DataSet(Dataset):
#     """PyTorch Dataset for force curves.
#
#     .. deprecated::
#         ML classification is deprecated.
#     """
#
#     def __init__(self, path: str, task: str = "train"):
#         import pickle
#         with open(path, "rb") as f:
#             self.dic = pickle.load(f)
#         self.data = self.dic[task]
#         self.seq = torch.tensor(np.vstack([i for i in self.data.values()]).astype(np.float32))
#         self.classes = torch.tensor(
#             np.hstack([[k] * len(v) for k, v in self.data.items()]).astype(np.int64)
#         )
#
#     def __len__(self) -> int:
#         return len(self.seq)
#
#     def __getitem__(self, index: int):
#         data = self.seq[index]
#         cla = self.classes[index]
#         return data, cla
